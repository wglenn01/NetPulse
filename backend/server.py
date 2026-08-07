"""NetPulse — Network Visibility API (FastAPI + MongoDB).

SNMP v2c + ICMP monitoring, topology, alerting (Discord), dashboards & NOC mode.
"""
import os
import uuid
import ipaddress
import asyncio
import logging
from datetime import timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import (db, client, serialize, now_utc, ensure_indexes, ensure_defaults,
                get_settings, DEMO_MODE)
from snmp_engine import poll_snmp, icmp_ping, fingerprint_vendor, guess_role
from poller import start_poller
from demo_network import start_snmpsim, stop_snmpsim, seed_demo
from alerting import _build_embed, send_discord
from vendor_api import (get_vendor_config, save_vendor_config, build_enrichment,
                        INTEGRATION_LABEL)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("netpulse")

app = FastAPI(title="NetPulse Network Visibility")
api = APIRouter(prefix="/api")


# ------------------------------------------------------------------ models
class DeviceCreate(BaseModel):
    name: str
    ip: str
    vendor: str = "generic"
    role: str = "device"
    site: str = ""
    community: str = "public"
    snmp_port: int = 161
    x: float = 200
    y: float = 200
    enabled: bool = True
    # When true, skip the ICMP/SNMP pre-flight reachability check and add anyway.
    force: bool = False


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    vendor: Optional[str] = None
    role: Optional[str] = None
    site: Optional[str] = None
    community: Optional[str] = None
    snmp_port: Optional[int] = None
    enabled: Optional[bool] = None


class Position(BaseModel):
    x: float
    y: float


class LinkCreate(BaseModel):
    a_device: str
    a_ifname: str
    b_device: str
    b_ifname: str
    label: str = ""


class DiscoveryRun(BaseModel):
    range: Optional[str] = None
    community: Optional[str] = None
    port: Optional[int] = None


class DiscoveryAddItem(BaseModel):
    ip: str
    port: int = 161
    community: str = "public"
    name: str
    vendor: str = "generic"
    role: str = "device"


class DiscoveryAdd(BaseModel):
    devices: List[DiscoveryAddItem]


class RuleUpdate(BaseModel):
    enabled: Optional[bool] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None


class SettingsUpdate(BaseModel):
    snmp_community: Optional[str] = None
    snmp_port: Optional[int] = None
    snmp_timeout: Optional[int] = None
    snmp_retries: Optional[int] = None
    poll_interval: Optional[int] = None
    discovery_range: Optional[str] = None
    discovery_community: Optional[str] = None
    discovery_port: Optional[int] = None
    discord_webhook_url: Optional[str] = None
    alerts_enabled: Optional[bool] = None
    threshold_latency_ms: Optional[int] = None
    threshold_loss_pct: Optional[int] = None
    threshold_util_pct: Optional[int] = None
    tv_rotate_seconds: Optional[int] = None


class DashboardBody(BaseModel):
    name: str
    layout: list = []
    is_default: bool = False


class TestDiscord(BaseModel):
    webhook_url: Optional[str] = None


class VendorConfigUpdate(BaseModel):
    mikrotik: Optional[dict] = None
    unifi: Optional[dict] = None
    cambium: Optional[dict] = None


class VendorTest(BaseModel):
    vendor: str


# ------------------------------------------------------------------ helpers
async def _state_map():
    states = await db.device_state.find({}, {"_id": 0}).to_list(5000)
    return {s["device_id"]: s for s in states}


def _iface_by_name(state, ifname):
    for i in (state or {}).get("interfaces", []):
        if i["name"] == ifname:
            return i
    return None


# ------------------------------------------------------------------ health
@api.get("/")
async def root():
    return {"service": "NetPulse", "status": "ok"}


# ------------------------------------------------------------------ overview
@api.get("/overview")
async def overview():
    settings = await get_settings()
    util_thr = settings.get("threshold_util_pct", 85)
    devices = await db.devices.find({}, {"_id": 0}).to_list(5000)
    smap = await _state_map()

    up = down = 0
    total_in = total_out = 0
    vendors = {}
    top = []
    for d in devices:
        st = smap.get(d["id"], {})
        if st.get("up"):
            up += 1
        else:
            down += 1
        total_in += st.get("total_in_bps", 0)
        total_out += st.get("total_out_bps", 0)
        vendors[d["vendor"]] = vendors.get(d["vendor"], 0) + 1
        for i in st.get("interfaces", []):
            if i["oper"] == 1 and (i.get("in_bps", 0) or i.get("out_bps", 0)):
                top.append({
                    "device_id": d["id"], "device_name": d["name"], "vendor": d["vendor"],
                    "if_name": i["name"], "util": i.get("util", 0),
                    "in_bps": i.get("in_bps", 0), "out_bps": i.get("out_bps", 0),
                    "speed_mbps": i.get("speed_mbps", 0),
                })
    top.sort(key=lambda x: x["util"], reverse=True)

    active_alerts = await db.alerts.count_documents({"state": "firing"})
    critical = await db.alerts.count_documents({"state": "firing", "severity": "critical"})
    recent = await db.alerts.find({}, {"_id": 0}).sort("last_seen", -1).to_list(10)

    return {
        "counts": {"total": len(devices), "up": up, "down": down,
                   "active_alerts": active_alerts, "critical_alerts": critical},
        "bandwidth": {"in_bps": total_in, "out_bps": total_out, "total_bps": total_in + total_out},
        "vendors": vendors,
        "top_interfaces": top[:12],
        "recent_alerts": [serialize(a) for a in recent],
        "util_threshold": util_thr,
    }


# ------------------------------------------------------------------ devices
@api.get("/devices")
async def list_devices():
    devices = await db.devices.find({}, {"_id": 0}).sort("name", 1).to_list(5000)
    smap = await _state_map()
    out = []
    for d in devices:
        st = smap.get(d["id"], {})
        lp = st.get("last_polled")
        out.append({**d,
                    "up": st.get("up", False),
                    "snmp_ok": st.get("snmp_ok", False),
                    "latency_ms": st.get("latency_ms"),
                    "loss_pct": st.get("loss_pct"),
                    "total_in_bps": st.get("total_in_bps", 0),
                    "total_out_bps": st.get("total_out_bps", 0),
                    "iface_count": st.get("iface_count", 0),
                    "iface_up": st.get("iface_up", 0),
                    "last_polled": lp.isoformat() if lp else None,
                    "sys_name": st.get("sysinfo", {}).get("name", "")})
    return out


async def _preflight_device(ip: str, port: int, community: str, timeout: int = 2):
    """Verify a device is reachable before adding it.

    Runs ICMP first, then an SNMP v2c GET. Raises HTTPException(400) with a
    structured, human-readable detail explaining exactly what failed so the
    operator knows how to fix it. Returns the SNMP sysinfo on success.
    """
    icmp = await icmp_ping(ip, count=2, timeout=1)
    if not icmp.get("alive"):
        raise HTTPException(400, {
            "code": "icmp_unreachable",
            "title": "Host unreachable",
            "message": (
                f"No ICMP (ping) reply from {ip}. The device looks offline or is "
                f"dropping ping. Check the IP address, power/cabling, VLAN/subnet, "
                f"and any firewall that might block ICMP."
            ),
            "can_force": True,
        })
    try:
        snmp = await poll_snmp(ip, port, community, timeout=timeout, retries=1)
    except Exception as ex:  # SNMP timeout / wrong community / v2c disabled
        raise HTTPException(400, {
            "code": "snmp_failed",
            "title": "SNMP query failed",
            "message": (
                f"{ip} replies to ping but did not answer SNMP v2c on UDP port {port}. "
                f"Verify SNMP is enabled on the device, SNMP v2c is allowed, the "
                f"community string \"{community}\" is correct, and UDP {port} is not "
                f"blocked by a firewall/ACL."
            ),
            "detail": str(ex)[:200],
            "can_force": True,
        })
    return snmp.get("sysinfo", {})


@api.post("/devices")
async def create_device(body: DeviceCreate):
    dev = body.model_dump()
    force = bool(dev.pop("force", False))

    # --- basic validation -------------------------------------------------
    dev["name"] = (dev.get("name") or "").strip()
    dev["ip"] = (dev.get("ip") or "").strip()
    dev["community"] = (dev.get("community") or "public").strip()

    if not dev["name"]:
        raise HTTPException(400, {"code": "validation", "title": "Missing name",
                                  "message": "Device name is required.", "can_force": False})
    try:
        ipaddress.ip_address(dev["ip"])
    except ValueError:
        raise HTTPException(400, {"code": "invalid_ip", "title": "Invalid IP address",
                                  "message": f"\"{dev['ip'] or '(empty)'}\" is not a valid IPv4/IPv6 address.",
                                  "can_force": False})

    try:
        port = int(dev.get("snmp_port") or 161)
    except (TypeError, ValueError):
        port = 0
    if not (1 <= port <= 65535):
        raise HTTPException(400, {"code": "invalid_port", "title": "Invalid SNMP port",
                                  "message": "SNMP port must be a number between 1 and 65535.",
                                  "can_force": False})
    dev["snmp_port"] = port

    # --- duplicate check --------------------------------------------------
    dup = await db.devices.find_one({"ip": dev["ip"], "snmp_port": port}, {"_id": 0, "name": 1})
    if dup:
        raise HTTPException(409, {
            "code": "duplicate",
            "title": "Device already monitored",
            "message": (
                f"IP {dev['ip']} (SNMP port {port}) is already being monitored as "
                f"\"{dup.get('name', 'unknown')}\". Delete or edit that device instead."
            ),
            "can_force": False,
        })

    # --- pre-flight reachability (ICMP + SNMP v2c) ------------------------
    if not force:
        settings = await get_settings()
        timeout = int(settings.get("snmp_timeout", 2) or 2)
        await _preflight_device(dev["ip"], port, dev["community"], timeout=timeout)

    dev["id"] = str(uuid.uuid4())
    dev["is_demo"] = False
    dev["created_at"] = now_utc()
    await db.devices.insert_one(dict(dev))
    return serialize(await db.devices.find_one({"id": dev["id"]}))


@api.get("/devices/{device_id}")
async def get_device(device_id: str):
    d = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Device not found")
    st = await db.device_state.find_one({"device_id": device_id}, {"_id": 0})
    d["state"] = serialize(st) if st else None
    return d


@api.put("/devices/{device_id}")
async def update_device(device_id: str, body: DeviceUpdate):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(400, "No fields to update")
    res = await db.devices.update_one({"id": device_id}, {"$set": patch})
    if res.matched_count == 0:
        raise HTTPException(404, "Device not found")
    return serialize(await db.devices.find_one({"id": device_id}))


@api.patch("/devices/{device_id}/position")
async def set_position(device_id: str, pos: Position):
    res = await db.devices.update_one({"id": device_id}, {"$set": {"x": pos.x, "y": pos.y}})
    if res.matched_count == 0:
        raise HTTPException(404, "Device not found")
    return {"ok": True}


@api.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    await db.devices.delete_one({"id": device_id})
    await db.device_state.delete_one({"device_id": device_id})
    await db.links.delete_many({"$or": [{"a_device": device_id}, {"b_device": device_id}]})
    await db.alerts.delete_many({"device_id": device_id})
    await db.metrics.delete_many({"device_id": device_id})
    await db.iface_metrics.delete_many({"device_id": device_id})
    return {"ok": True}


@api.get("/devices/{device_id}/enrichment")
async def device_enrichment(device_id: str):
    """Vendor-API enrichment for a device.

    NOTE: In the cloud preview this returns a SIMULATED feed (the environment cannot
    reach private LAN controllers). On-prem, vendor_api.build_enrichment can be
    pointed at the real RouterOS/UniFi/cnMaestro controllers without changing this
    response contract.
    """
    d = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Device not found")
    return await build_enrichment(d)


# ------------------------------------------------------------------ topology
@api.get("/topology")
async def topology():
    settings = await get_settings()
    util_thr = settings.get("threshold_util_pct", 85)
    devices = await db.devices.find({}, {"_id": 0}).to_list(5000)
    links = await db.links.find({}, {"_id": 0}).to_list(5000)
    smap = await _state_map()

    nodes = []
    for d in devices:
        st = smap.get(d["id"], {})
        nodes.append({
            "id": d["id"], "name": d["name"], "vendor": d["vendor"], "role": d["role"],
            "ip": d["ip"], "site": d.get("site", ""), "x": d.get("x", 200), "y": d.get("y", 200),
            "up": st.get("up", False), "snmp_ok": st.get("snmp_ok", False),
            "latency_ms": st.get("latency_ms"), "loss_pct": st.get("loss_pct"),
            "total_in_bps": st.get("total_in_bps", 0), "total_out_bps": st.get("total_out_bps", 0),
            "iface_count": st.get("iface_count", 0), "iface_up": st.get("iface_up", 0),
            "sys_name": st.get("sysinfo", {}).get("name", ""),
            "ports": [{"name": i["name"], "oper": i["oper"], "util": i.get("util", 0),
                       "speed_mbps": i.get("speed_mbps", 0)} for i in st.get("interfaces", [])],
        })

    edges = []
    node_up = {n["id"]: n["up"] for n in nodes}
    for l in links:
        a_state = smap.get(l["a_device"], {})
        iface = _iface_by_name(a_state, l["a_ifname"]) or {}
        b_iface = _iface_by_name(smap.get(l["b_device"], {}), l["b_ifname"]) or {}
        util = max(iface.get("util", 0), b_iface.get("util", 0))
        in_bps = iface.get("in_bps", 0)
        out_bps = iface.get("out_bps", 0)
        both_up = node_up.get(l["a_device"], False) and node_up.get(l["b_device"], False)
        active = both_up and (in_bps + out_bps) > 500_000
        if not both_up:
            status = "down"
        elif util >= util_thr:
            status = "crit"
        elif util >= 60:
            status = "warn"
        elif active:
            status = "active"
        else:
            status = "idle"
        edges.append({
            "id": l["id"], "source": l["a_device"], "target": l["b_device"],
            "a_ifname": l["a_ifname"], "b_ifname": l["b_ifname"],
            "util": round(util, 1), "in_bps": in_bps, "out_bps": out_bps,
            "speed_mbps": iface.get("speed_mbps", 0), "status": status, "active": active,
        })
    return {"nodes": nodes, "edges": edges}


# ------------------------------------------------------------------ links
@api.get("/links")
async def list_links():
    return [serialize(l) for l in await db.links.find({}).to_list(5000)]


@api.post("/links")
async def create_link(body: LinkCreate):
    link = body.model_dump()
    link["id"] = str(uuid.uuid4())
    link["enabled"] = True
    link["is_demo"] = False
    await db.links.insert_one(dict(link))
    return serialize(await db.links.find_one({"id": link["id"]}))


@api.delete("/links/{link_id}")
async def delete_link(link_id: str):
    await db.links.delete_one({"id": link_id})
    return {"ok": True}


# ------------------------------------------------------------------ metrics
@api.get("/metrics/device/{device_id}")
async def device_metrics(device_id: str, minutes: int = 30):
    cutoff = now_utc() - timedelta(minutes=minutes)
    pts = await db.metrics.find({"device_id": device_id, "ts": {"$gte": cutoff}},
                                {"_id": 0}).sort("ts", 1).to_list(5000)
    return [serialize(p) for p in pts]


@api.get("/metrics/interface/{device_id}")
async def iface_metrics(device_id: str, if_name: str, minutes: int = 30):
    cutoff = now_utc() - timedelta(minutes=minutes)
    pts = await db.iface_metrics.find(
        {"device_id": device_id, "if_name": if_name, "ts": {"$gte": cutoff}},
        {"_id": 0}).sort("ts", 1).to_list(5000)
    return [serialize(p) for p in pts]


# ------------------------------------------------------------------ discovery
@api.post("/discovery/run")
async def discovery_run(body: DiscoveryRun):
    settings = await get_settings()
    cidr = body.range or settings.get("discovery_range", "127.0.0.1/32")
    community = body.community or settings.get("discovery_community", "public")
    port = body.port or settings.get("discovery_port", 161)
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except Exception:
        raise HTTPException(400, "Invalid CIDR range")
    hosts = [str(h) for h in net.hosts()] or [str(net.network_address)]
    if len(hosts) > 256:
        raise HTTPException(400, "Range too large (max 256 hosts)")

    existing = await db.devices.find({}, {"_id": 0, "ip": 1, "snmp_port": 1}).to_list(5000)
    existing_set = {(e["ip"], e.get("snmp_port", 161)) for e in existing}

    sem = asyncio.Semaphore(50)

    async def probe(ip):
        async with sem:
            icmp = await icmp_ping(ip, count=1, timeout=1)
            if not icmp["alive"]:
                return None
            entry = {"ip": ip, "alive": True, "latency_ms": icmp["latency_ms"],
                     "snmp_ok": False, "sys_name": "", "sys_descr": "",
                     "vendor": "generic", "role": "device",
                     "already_added": (ip, port) in existing_set}
            try:
                snmp = await poll_snmp(ip, port, community, timeout=1, retries=0)
                si = snmp["sysinfo"]
                entry["snmp_ok"] = True
                entry["sys_name"] = si.get("name", "")
                entry["sys_descr"] = si.get("descr", "")
                entry["vendor"] = fingerprint_vendor(si.get("descr", ""))
                entry["role"] = guess_role(si.get("descr", ""), entry["vendor"])
            except Exception:
                pass
            return entry

    results = await asyncio.gather(*[probe(h) for h in hosts])
    found = [r for r in results if r]
    found.sort(key=lambda x: x["ip"])
    return {"scanned": len(hosts), "community": community, "port": port, "found": found}


@api.post("/discovery/add")
async def discovery_add(body: DiscoveryAdd):
    existing = await db.devices.find({}, {"_id": 0, "ip": 1, "snmp_port": 1}).to_list(5000)
    existing_set = {(e["ip"], e.get("snmp_port", 161)) for e in existing}
    added, skipped = [], []
    base_x, base_y = 1320, 80
    for i, item in enumerate(body.devices):
        if (item.ip, item.port) in existing_set:
            skipped.append(item.ip)
            continue
        existing_set.add((item.ip, item.port))
        dev = {
            "id": str(uuid.uuid4()), "name": item.name, "ip": item.ip,
            "vendor": item.vendor, "role": item.role, "site": "Discovered",
            "community": item.community, "snmp_port": item.port,
            "x": base_x, "y": base_y + i * 120, "enabled": True,
            "is_demo": False, "created_at": now_utc(),
        }
        await db.devices.insert_one(dict(dev))
        added.append(serialize(dev))
    return {"added": added, "skipped": skipped}


# ------------------------------------------------------------------ alerts
@api.get("/alerts")
async def list_alerts(state: Optional[str] = None, limit: int = 200):
    q = {}
    if state:
        q["state"] = state
    alerts = await db.alerts.find(q, {"_id": 0}).sort("last_seen", -1).to_list(limit)
    return [serialize(a) for a in alerts]


@api.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: str):
    res = await db.alerts.update_one({"id": alert_id}, {"$set": {"acknowledged": True}})
    if res.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    return {"ok": True}


@api.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    res = await db.alerts.update_one(
        {"id": alert_id},
        {"$set": {"state": "resolved", "resolved_at": now_utc(), "last_seen": now_utc()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Alert not found")
    return {"ok": True}


@api.delete("/alerts")
async def clear_resolved():
    await db.alerts.delete_many({"state": "resolved"})
    return {"ok": True}


# ------------------------------------------------------------------ rules
@api.get("/rules")
async def list_rules():
    return [serialize(r) for r in await db.rules.find({}).sort("name", 1).to_list(100)]


@api.put("/rules/{rule_id}")
async def update_rule(rule_id: str, body: RuleUpdate):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    res = await db.rules.update_one({"id": rule_id}, {"$set": patch})
    if res.matched_count == 0:
        raise HTTPException(404, "Rule not found")
    return serialize(await db.rules.find_one({"id": rule_id}))


# ------------------------------------------------------------------ settings
@api.get("/settings")
async def read_settings():
    return serialize(await get_settings())


@api.put("/settings")
async def write_settings(body: SettingsUpdate):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if patch:
        await db.settings.update_one({"id": "global"}, {"$set": patch}, upsert=True)
    return serialize(await get_settings())


@api.post("/settings/test-discord")
async def test_discord(body: TestDiscord):
    url = (body.webhook_url or "").strip()
    if url:
        await db.settings.update_one({"id": "global"}, {"$set": {"discord_webhook_url": url}})
    sample = {
        "id": "test", "type": "info", "device_name": "NetPulse", "severity": "info",
        "message": "Test alert from NetPulse", "detail": "Your Discord webhook is configured correctly.",
    }
    status = await send_discord(_build_embed(sample))
    if status in (200, 204):
        return {"ok": True, "status": status}
    if status == "no-webhook":
        raise HTTPException(400, "No Discord webhook URL configured")
    raise HTTPException(502, f"Discord webhook failed (status={status})")


# ------------------------------------------------------------------ vendor APIs
@api.get("/vendor-config")
async def read_vendor_config():
    return serialize(await get_vendor_config())


@api.put("/vendor-config")
async def write_vendor_config(body: VendorConfigUpdate):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    return serialize(await save_vendor_config(patch))


@api.post("/vendor-config/test")
async def test_vendor_config(body: VendorTest):
    """Validate a vendor integration.

    In the preview we cannot reach private controllers, so we return a simulated
    success. On-prem this would open a real session to the configured controller.
    """
    vendor = body.vendor
    key = {"mikrotik": "mikrotik", "unifi": "unifi", "cambium": "cambium",
           "ubiquiti": "unifi"}.get(vendor)
    if not key:
        raise HTTPException(400, f"Unknown vendor '{vendor}'")
    cfg = await get_vendor_config()
    block = cfg.get(key, {})
    label = INTEGRATION_LABEL.get(
        {"mikrotik": "mikrotik", "unifi": "ubiquiti", "cambium": "cambium"}[key], key)
    return {
        "ok": True,
        "simulated": True,
        "vendor": vendor,
        "message": f"{label}: simulated connection OK. Live polling activates on-prem "
                   f"once this controller ({block.get('host') or block.get('base_url') or 'not set'}) is reachable.",
    }


# ------------------------------------------------------------------ dashboards
@api.get("/dashboards")
async def list_dashboards():
    return [serialize(d) for d in await db.dashboards.find({}).sort("name", 1).to_list(100)]


@api.get("/dashboards/{dash_id}")
async def get_dashboard(dash_id: str):
    d = await db.dashboards.find_one({"id": dash_id}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Dashboard not found")
    return serialize(d)


@api.post("/dashboards")
async def create_dashboard(body: DashboardBody):
    dash = body.model_dump()
    dash["id"] = str(uuid.uuid4())
    dash["created_at"] = now_utc()
    await db.dashboards.insert_one(dict(dash))
    return serialize(await db.dashboards.find_one({"id": dash["id"]}))


@api.put("/dashboards/{dash_id}")
async def update_dashboard(dash_id: str, body: DashboardBody):
    patch = body.model_dump()
    res = await db.dashboards.update_one({"id": dash_id}, {"$set": patch})
    if res.matched_count == 0:
        raise HTTPException(404, "Dashboard not found")
    return serialize(await db.dashboards.find_one({"id": dash_id}))


@api.delete("/dashboards/{dash_id}")
async def delete_dashboard(dash_id: str):
    await db.dashboards.delete_one({"id": dash_id})
    return {"ok": True}


# ------------------------------------------------------------------ app wiring
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    await ensure_defaults()
    # keep the persisted flag in sync with the DEMO_MODE env so the UI/vendor feed
    # reflect reality (demo vs live) regardless of a stale settings document.
    await db.settings.update_one({"id": "global"}, {"$set": {"demo_mode": DEMO_MODE}})
    if DEMO_MODE:
        try:
            start_snmpsim()
            await seed_demo()
        except Exception as e:
            logger.warning("Demo network init failed: %s", e)
    else:
        logger.info("Production mode: demo network disabled (polling real devices).")
    start_poller()
    logger.info("NetPulse started (demo_mode=%s)", DEMO_MODE)


@app.on_event("shutdown")
async def on_shutdown():
    if DEMO_MODE:
        stop_snmpsim()
    client.close()
