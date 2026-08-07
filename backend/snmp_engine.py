"""SNMP v2c polling + ICMP + bandwidth math. Proven in /app/poc/test_core.py.

Uses pysnmp 7.x v1arch asyncio hlapi (v2c via CommunityData mpModel=1).
All OIDs are numeric to avoid MIB compilation dependencies.
"""
import time
import warnings

warnings.filterwarnings("ignore")

from pysnmp.hlapi.v1arch.asyncio import (  # noqa: E402
    SnmpDispatcher, CommunityData, UdpTransportTarget,
    ObjectType, ObjectIdentity, get_cmd, bulk_walk_cmd,
)
from icmplib import async_ping  # noqa: E402

# system group
SYS = {
    "descr": "1.3.6.1.2.1.1.1.0",
    "object_id": "1.3.6.1.2.1.1.2.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
    "contact": "1.3.6.1.2.1.1.4.0",
    "name": "1.3.6.1.2.1.1.5.0",
    "location": "1.3.6.1.2.1.1.6.0",
}
IF_BASE = "1.3.6.1.2.1.2.2.1"
IFX_BASE = "1.3.6.1.2.1.31.1.1.1"


async def icmp_ping(ip, count=2, timeout=1, interval=0.2):
    try:
        h = await async_ping(ip, count=count, interval=interval, timeout=timeout, privileged=False)
        return {
            "alive": h.is_alive,
            "latency_ms": round(h.avg_rtt, 2) if h.is_alive else None,
            "loss_pct": round(h.packet_loss * 100, 1),
            "jitter_ms": round(h.jitter, 2) if h.is_alive else None,
        }
    except Exception:
        return {"alive": False, "latency_ms": None, "loss_pct": 100.0, "jitter_ms": None}


def _col(walk, prefix):
    out = {}
    plen = len(prefix) + 1
    for oid, val in walk.items():
        if oid.startswith(prefix + "."):
            tail = oid[plen:]
            if tail.isdigit():
                out[int(tail)] = val
    return out


async def _walk(dispatcher, community, target, base):
    results = {}
    async for errI, errS, errIdx, varBinds in bulk_walk_cmd(
        dispatcher, CommunityData(community, mpModel=1), target, 0, 25,
        ObjectType(ObjectIdentity(base)),
    ):
        if errI:
            raise RuntimeError(str(errI))
        if errS:
            raise RuntimeError(errS.prettyPrint())
        for vb in varBinds:
            results[str(vb[0])] = vb[1]
    return results


def _parse_interfaces(iftable, ifx):
    descr = _col(iftable, IF_BASE + ".2")
    oper = _col(iftable, IF_BASE + ".8")
    admin = _col(iftable, IF_BASE + ".7")
    ifspeed = _col(iftable, IF_BASE + ".5")
    in32 = _col(iftable, IF_BASE + ".10")
    out32 = _col(iftable, IF_BASE + ".16")
    name = _col(ifx, IFX_BASE + ".1")
    hcin = _col(ifx, IFX_BASE + ".6")
    hcout = _col(ifx, IFX_BASE + ".10")
    hispeed = _col(ifx, IFX_BASE + ".15")
    alias = _col(ifx, IFX_BASE + ".18")

    ifaces = []
    for idx in sorted(descr.keys()):
        try:
            speed_mbps = int(hispeed.get(idx)) if hispeed.get(idx) else int(int(ifspeed.get(idx, 0)) / 1_000_000)
        except Exception:
            speed_mbps = 0
        in_oct = int(hcin.get(idx, in32.get(idx, 0)))
        out_oct = int(hcout.get(idx, out32.get(idx, 0)))
        ifaces.append({
            "index": idx,
            "descr": str(descr.get(idx, "")),
            "name": str(name.get(idx, "")) or str(descr.get(idx, "")),
            "alias": str(alias.get(idx, "")),
            "oper": int(oper.get(idx, 0)),
            "admin": int(admin.get(idx, 0)),
            "speed_mbps": speed_mbps,
            "in_octets": in_oct,
            "out_octets": out_oct,
        })
    return ifaces


async def snmp_probe(ip, port, community, timeout=2, retries=1):
    """Lightweight reachability probe: a single SNMP v2c GET of sysDescr/sysName.

    Much faster and more robust than a full poll (no interface walks) — ideal for
    a pre-flight check when adding a device. Returns sysinfo dict on success,
    raises on any failure. Always closes the dispatcher socket.
    """
    dispatcher = SnmpDispatcher()
    try:
        target = await UdpTransportTarget.create((ip, int(port)), timeout=timeout, retries=retries)
        errI, errS, errIdx, varBinds = await get_cmd(
            dispatcher, CommunityData(community, mpModel=1), target,
            ObjectType(ObjectIdentity(SYS["descr"])),
            ObjectType(ObjectIdentity(SYS["name"])),
        )
        if errI:
            raise RuntimeError(str(errI))
        if errS:
            raise RuntimeError(errS.prettyPrint())
        vals = {str(vb[0]): vb[1] for vb in varBinds}
        return {
            "descr": str(vals.get(SYS["descr"], "")),
            "name": str(vals.get(SYS["name"], "")),
        }
    finally:
        try:
            dispatcher.close()
        except Exception:
            pass


async def poll_snmp(ip, port, community, timeout=2, retries=1):
    """Return {'sysinfo': {...}, 'interfaces': [...]} or raise on failure.

    IMPORTANT: the SnmpDispatcher owns a UDP socket; it MUST be closed after
    every poll or the backend leaks file descriptors (Errno 24).
    """
    dispatcher = SnmpDispatcher()
    try:
        target = await UdpTransportTarget.create((ip, int(port)), timeout=timeout, retries=retries)

        errI, errS, errIdx, varBinds = await get_cmd(
            dispatcher, CommunityData(community, mpModel=1), target,
            *[ObjectType(ObjectIdentity(o)) for o in SYS.values()],
        )
        if errI:
            raise RuntimeError(str(errI))
        if errS:
            raise RuntimeError(errS.prettyPrint())
        vals = {str(vb[0]): vb[1] for vb in varBinds}
        sysinfo = {}
        for key, oid in SYS.items():
            v = vals.get(oid)
            sysinfo[key] = str(v) if v is not None else ""
        try:
            sysinfo["uptime_secs"] = int(vals.get(SYS["uptime"], 0)) // 100
        except Exception:
            sysinfo["uptime_secs"] = 0

        iftable = await _walk(dispatcher, community, target, IF_BASE)
        ifx = await _walk(dispatcher, community, target, IFX_BASE)
        interfaces = _parse_interfaces(iftable, ifx)
        return {"sysinfo": sysinfo, "interfaces": interfaces}
    finally:
        try:
            dispatcher.close()
        except Exception:
            pass


def compute_bandwidth(prev_map, interfaces, now):
    """Augment interfaces with in_bps/out_bps/util and return (interfaces, new_prev_map)."""
    new_prev = {}
    for i in interfaces:
        key = i["name"] or i["descr"]
        new_prev[key] = {"in": i["in_octets"], "out": i["out_octets"], "ts": now}
        prev = prev_map.get(key)
        bps_in = bps_out = 0.0
        if prev and now > prev["ts"]:
            dt = now - prev["ts"]
            din = i["in_octets"] - prev["in"]
            dout = i["out_octets"] - prev["out"]
            # A negative delta means the counter was reset (device/agent reboot)
            # -> we cannot compute a rate for this interval, report 0.
            if din < 0:
                din = 0
            if dout < 0:
                dout = 0
            bps_in = din * 8 / dt
            bps_out = dout * 8 / dt
        cap = (i["speed_mbps"] or 0) * 1_000_000
        i["in_bps"] = round(bps_in)
        i["out_bps"] = round(bps_out)
        i["util_in"] = round(bps_in / cap * 100, 2) if cap else 0.0
        i["util_out"] = round(bps_out / cap * 100, 2) if cap else 0.0
        i["util"] = max(i["util_in"], i["util_out"])
    return interfaces, new_prev


def fingerprint_vendor(descr: str) -> str:
    d = (descr or "").lower()
    if "routeros" in d or "mikrotik" in d:
        return "mikrotik"
    if "ubiquiti" in d or "unifi" in d or "airmax" in d or "edgeos" in d or "airos" in d:
        return "ubiquiti"
    if "cambium" in d or "epmp" in d or "canopy" in d or "cnpilot" in d:
        return "cambium"
    if "mimosa" in d or "airspan" in d:
        return "mimosa"
    return "generic"


def guess_role(descr: str, vendor: str) -> str:
    d = (descr or "").lower()
    if vendor == "mikrotik":
        return "switch" if ("crs" in d or "switch" in d) else "router"
    if vendor == "mimosa":
        return "backhaul"
    if vendor in ("ubiquiti", "cambium"):
        return "ap"
    return "device"
