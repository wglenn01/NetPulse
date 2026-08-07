"""Demo network: generate snmprec profiles, run real snmpsim agents, seed DB.

The preview polls these REAL SNMP agents (127.0.0.1:1611) through the exact same
engine used against on-prem gear. A separate agent on :1612 provides a
'discoverable' device for the discovery feature demo. One device points at an
unreachable RFC5737 address to demonstrate device-down alerting.
"""
import os
import sys
import signal
import shutil
import subprocess
import logging
from pathlib import Path

from db import db, now_utc

logger = logging.getLogger("demo")

RESPONDER = os.path.join(os.path.dirname(sys.executable), "snmpsim-command-responder")
if not os.path.exists(RESPONDER):
    RESPONDER = shutil.which("snmpsim-command-responder") or "snmpsim-command-responder"

MAIN_DIR = Path("/app/backend/snmpsim_data/main")
DISCO_DIR = Path("/app/backend/snmpsim_data/disco")
MAIN_ENDPOINT = "127.0.0.1:1611"
DISCO_ENDPOINT = "127.0.0.1:1612"
_procs = []

# ---- vendor sysObjectIDs for realistic fingerprinting ----
OID = {
    "mikrotik": "1.3.6.1.4.1.14988.1",
    "ubiquiti": "1.3.6.1.4.1.41112",
    "cambium": "1.3.6.1.4.1.17713.21",
    "mimosa": "1.3.6.1.4.1.43356",
}

# iface tuple: (ifname, descr, link_mbps, oper, in_mbps, out_mbps)
DEMO_DEVICES = [
    {"id": "core-rtr-01", "name": "core-rtr-01", "vendor": "mikrotik", "role": "router",
     "site": "NOC", "x": 560, "y": 40, "location": "NOC / Rack A1",
     "descr": "RouterOS CCR2004-1G-12S+2XS, RouterOS 7.14 (Mikrotik)",
     "ifaces": [
         ("uplink-transit", "sfp-sfpplus1", 10000, 1, 3200, 1400),
         ("to-dist-1", "sfp-sfpplus2", 10000, 1, 900, 850),
         ("to-dist-2", "sfp-sfpplus3", 10000, 1, 1100, 700),
         ("to-tower-south", "sfp-sfpplus6", 1000, 2, 0, 0),
         ("mgmt", "ether1", 1000, 1, 2, 1),
     ]},
    {"id": "dist-sw-01", "name": "dist-sw-01", "vendor": "mikrotik", "role": "switch",
     "site": "NOC", "x": 300, "y": 190, "location": "NOC / Rack A2",
     "descr": "RouterOS CRS326-24G-2S+, RouterOS 7.14 switch (Mikrotik)",
     "ifaces": [
         ("uplink", "sfp-sfpplus1", 10000, 1, 900, 850),
         ("to-ap-north-1", "ether2", 1000, 1, 220, 40),
         ("to-ap-north-2", "ether3", 1000, 1, 180, 30),
         ("to-bh-ridge", "ether4", 1000, 1, 480, 460),
         ("mgmt", "ether24", 1000, 1, 3, 2),
     ]},
    {"id": "dist-sw-02", "name": "dist-sw-02", "vendor": "mikrotik", "role": "switch",
     "site": "NOC", "x": 860, "y": 190, "location": "NOC / Rack A3",
     "descr": "RouterOS CRS326-24G-2S+, RouterOS 7.14 switch (Mikrotik)",
     "ifaces": [
         ("uplink", "sfp-sfpplus1", 10000, 1, 1100, 700),
         ("to-ap-east", "ether2", 1000, 1, 260, 45),
         ("to-bh-east", "ether3", 1000, 1, 920, 70),
         ("to-ap-west", "ether4", 1000, 1, 190, 35),
         ("mgmt", "ether24", 1000, 1, 3, 2),
     ]},
    {"id": "ap-north-01", "name": "ap-north-01", "vendor": "ubiquiti", "role": "ap",
     "site": "Tower North", "x": 120, "y": 350, "location": "Tower North / Sector 1",
     "descr": "Ubiquiti airMAX Rocket Prism 5AC, airOS 8 (Ubiquiti)",
     "ifaces": [
         ("backhaul", "eth0", 1000, 1, 220, 40),
         ("wlan-sector1", "ath0", 450, 1, 180, 25),
         ("to-cpe-101", "eth1", 300, 1, 60, 8),
     ]},
    {"id": "ap-north-02", "name": "ap-north-02", "vendor": "cambium", "role": "ap",
     "site": "Tower North", "x": 340, "y": 370, "location": "Tower North / Sector 2",
     "descr": "Cambium Networks ePMP 3000 AP, Canopy (Cambium)",
     "ifaces": [
         ("backhaul", "eth0", 1000, 1, 180, 30),
         ("ptmp-sector2", "wlan0", 500, 1, 150, 20),
         ("to-cpe-102", "eth1", 300, 1, 55, 7),
     ]},
    {"id": "bh-ridge-01", "name": "bh-ridge-01", "vendor": "mimosa", "role": "backhaul",
     "site": "Ridge", "x": 540, "y": 350, "location": "Ridge Relay / PtP",
     "descr": "Mimosa B5c Backhaul Radio, Mimosa by Airspan",
     "ifaces": [
         ("ptp-link", "eth0", 1000, 1, 480, 460),
     ]},
    {"id": "ap-east-01", "name": "ap-east-01", "vendor": "cambium", "role": "ap",
     "site": "Tower East", "x": 740, "y": 370, "location": "Tower East / Sector 1",
     "descr": "Cambium Networks ePMP Force 300 AP, Canopy (Cambium)",
     "ifaces": [
         ("backhaul", "eth0", 1000, 1, 260, 45),
         ("ptmp-sector1", "wlan0", 500, 1, 210, 30),
         ("to-cpe-201", "eth1", 300, 1, 70, 9),
     ]},
    {"id": "bh-east-01", "name": "bh-east-01", "vendor": "mimosa", "role": "backhaul",
     "site": "Tower East", "x": 960, "y": 350, "location": "Tower East / PtP",
     "descr": "Mimosa B11 Backhaul Radio, Mimosa by Airspan",
     "ifaces": [
         ("ptp-link", "eth0", 1000, 1, 920, 70),
     ]},
    {"id": "ap-west-01", "name": "ap-west-01", "vendor": "ubiquiti", "role": "ap",
     "site": "Tower West", "x": 1080, "y": 370, "location": "Tower West / Sector 1",
     "descr": "Ubiquiti UniFi UAP airMAX NanoStation 5AC (Ubiquiti)",
     "ifaces": [
         ("backhaul", "eth0", 1000, 1, 190, 35),
         ("wlan-sector1", "ath0", 300, 1, 120, 18),
         ("to-ap-west-02", "eth1", 300, 1, 40, 6),
     ]},
    {"id": "cpe-101", "name": "cpe-101", "vendor": "ubiquiti", "role": "cpe",
     "site": "Tower North", "x": 60, "y": 520, "location": "Customer / North-101",
     "descr": "Ubiquiti LiteBeam 5AC Gen2 CPE, airOS 8 (Ubiquiti)",
     "ifaces": [("eth0", "eth0", 300, 1, 60, 8)]},
    {"id": "cpe-102", "name": "cpe-102", "vendor": "ubiquiti", "role": "cpe",
     "site": "Tower North", "x": 320, "y": 540, "location": "Customer / North-102",
     "descr": "Ubiquiti NanoBeam 5AC CPE, airOS 8 (Ubiquiti)",
     "ifaces": [("eth0", "eth0", 300, 1, 55, 7)]},
    {"id": "cpe-201", "name": "cpe-201", "vendor": "ubiquiti", "role": "cpe",
     "site": "Tower East", "x": 740, "y": 520, "location": "Customer / East-201",
     "descr": "Ubiquiti PowerBeam 5AC CPE, airOS 8 (Ubiquiti)",
     "ifaces": [("eth0", "eth0", 300, 1, 70, 9)]},
    # Unreachable -> device-down alert demo (no snmprec generated)
    {"id": "ap-west-02", "name": "ap-west-02", "vendor": "cambium", "role": "ap",
     "site": "Tower West", "x": 1080, "y": 520, "location": "Tower West / Sector 2",
     "descr": "Cambium ePMP (offline)", "ip": "192.0.2.10", "unreachable": True,
     "ifaces": []},
]

# links: (a_id, a_ifname, b_id, b_ifname)
DEMO_LINKS = [
    ("core-rtr-01", "to-dist-1", "dist-sw-01", "uplink"),
    ("core-rtr-01", "to-dist-2", "dist-sw-02", "uplink"),
    ("dist-sw-01", "to-ap-north-1", "ap-north-01", "backhaul"),
    ("dist-sw-01", "to-ap-north-2", "ap-north-02", "backhaul"),
    ("dist-sw-01", "to-bh-ridge", "bh-ridge-01", "ptp-link"),
    ("dist-sw-02", "to-ap-east", "ap-east-01", "backhaul"),
    ("dist-sw-02", "to-bh-east", "bh-east-01", "ptp-link"),
    ("dist-sw-02", "to-ap-west", "ap-west-01", "backhaul"),
    ("ap-north-01", "to-cpe-101", "cpe-101", "eth0"),
    ("ap-north-02", "to-cpe-102", "cpe-102", "eth0"),
    ("ap-east-01", "to-cpe-201", "cpe-201", "eth0"),
    ("ap-west-01", "to-ap-west-02", "ap-west-02", "eth0"),
]


def _oidt(oid):
    return tuple(int(x) for x in oid.split("."))


def _static(oid, tag, val):
    return (_oidt(oid), f"{oid}|{tag}|{val}")


def _numeric(oid, tag, params):
    return (_oidt(oid), f"{oid}|{tag}:numeric|{params}")


def _counter(oid, mbps, phase):
    """Monotonic 64-bit counter whose rate oscillates (sin) -> lively charts.

    snmpsim numeric(cumulative): per-poll delta = scale*sin(t*rate) + offset*dt*rate.
    Net byte-rate = offset*rate, so offset = target_bytes_per_sec / rate.
    scale = 1.6*target_bytes_per_sec gives ~20% wobble while staying monotonic.
    """
    if mbps <= 0:
        return _static(oid, 70, 5_000_000_000)
    tbps = mbps * 1_000_000 / 8.0
    rate = round(0.5 + 0.03 * (phase % 7), 3)
    off = int(tbps / rate)
    sc = int(tbps * 0.5)
    init = 5_000_000_000 + phase * 1_000_003
    return _numeric(oid, 70, f"initial={init},rate={rate},function=sin,scale={sc},offset={off},cumulative=1")


def _build_records(dev):
    recs = []
    recs.append(_static("1.3.6.1.2.1.1.1.0", 4, dev["descr"]))
    recs.append(_static("1.3.6.1.2.1.1.2.0", 6, OID.get(dev["vendor"], "1.3.6.1.4.1.99999")))
    recs.append(_numeric("1.3.6.1.2.1.1.3.0", 67, "initial=100000,rate=100"))
    recs.append(_static("1.3.6.1.2.1.1.4.0", 4, "noc@wisp.example"))
    recs.append(_static("1.3.6.1.2.1.1.5.0", 4, dev["name"]))
    recs.append(_static("1.3.6.1.2.1.1.6.0", 4, dev["location"]))
    recs.append(_static("1.3.6.1.2.1.1.7.0", 2, 78))
    ifaces = dev["ifaces"]
    recs.append(_static("1.3.6.1.2.1.2.1.0", 2, len(ifaces)))
    for idx, (ifname, descr, mbps, oper, in_mbps, out_mbps) in enumerate(ifaces, start=1):
        speed_bps = min(int(mbps * 1_000_000), 4294967295)
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.1.{idx}", 2, idx))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.2.{idx}", 4, descr))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.3.{idx}", 2, 6))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.4.{idx}", 2, 1500))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.5.{idx}", 66, speed_bps))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.7.{idx}", 2, 1))
        recs.append(_static(f"1.3.6.1.2.1.2.2.1.8.{idx}", 2, oper))
        recs.append(_numeric(f"1.3.6.1.2.1.2.2.1.10.{idx}", 65, f"initial=100000,rate={int(in_mbps*1_000_000/8)}"))
        recs.append(_numeric(f"1.3.6.1.2.1.2.2.1.16.{idx}", 65, f"initial=100000,rate={int(out_mbps*1_000_000/8)}"))
        recs.append(_static(f"1.3.6.1.2.1.31.1.1.1.1.{idx}", 4, ifname))
        recs.append(_counter(f"1.3.6.1.2.1.31.1.1.1.6.{idx}", in_mbps if oper == 1 else 0, idx))
        recs.append(_counter(f"1.3.6.1.2.1.31.1.1.1.10.{idx}", out_mbps if oper == 1 else 0, idx + 6))
        recs.append(_static(f"1.3.6.1.2.1.31.1.1.1.15.{idx}", 66, int(mbps)))
        recs.append(_static(f"1.3.6.1.2.1.31.1.1.1.18.{idx}", 4, f"{dev['name']}:{ifname}"))
    recs.sort(key=lambda r: r[0])
    return "\n".join(line for _, line in recs) + "\n"


DISCO_DEVICE = {
    "id": "edge-rtr-lab", "name": "edge-rtr-lab", "vendor": "mikrotik", "role": "router",
    "location": "Edge / Unmanaged",
    "descr": "RouterOS RB5009UG+S+, RouterOS 7.13 (Mikrotik)",
    "ifaces": [
        ("wan", "sfp-sfpplus1", 10000, 1, 640, 300),
        ("lan-bridge", "bridge1", 1000, 1, 210, 180),
        ("mgmt", "ether1", 1000, 1, 2, 1),
    ],
}


def generate_files():
    for d in (MAIN_DIR, DISCO_DIR):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    for dev in DEMO_DEVICES:
        if dev.get("unreachable"):
            continue
        (MAIN_DIR / f"{dev['id']}.snmprec").write_text(_build_records(dev))
    # discovery agent responds to community 'public'
    (DISCO_DIR / "public.snmprec").write_text(_build_records(DISCO_DEVICE))
    logger.info("Generated snmprec profiles")


def _start_responder(data_dir, endpoint):
    cmd = [
        RESPONDER,
        f"--data-dir={data_dir}",
        f"--agent-udpv4-endpoint={endpoint}",
        "--logging-method=null",
        "--process-user=root", "--process-group=root",
    ]
    env = {**os.environ}
    env.setdefault("HOME", "/root")
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


def start_snmpsim():
    global _procs
    # clean any stale responders from previous reloads
    try:
        subprocess.run(["pkill", "-f", "snmpsim-command-responder"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    generate_files()
    import time
    time.sleep(0.5)
    _procs = [
        _start_responder(MAIN_DIR, MAIN_ENDPOINT),
        _start_responder(DISCO_DIR, DISCO_ENDPOINT),
    ]
    logger.info("snmpsim agents launched on %s and %s", MAIN_ENDPOINT, DISCO_ENDPOINT)


def stop_snmpsim():
    for p in _procs:
        try:
            p.send_signal(signal.SIGTERM)
        except Exception:
            pass


async def seed_demo():
    """Insert demo devices/links/dashboard once."""
    if await db.devices.count_documents({"is_demo": True}) > 0:
        return
    docs = []
    for d in DEMO_DEVICES:
        docs.append({
            "id": d["id"], "name": d["name"], "vendor": d["vendor"], "role": d["role"],
            "site": d.get("site", ""), "ip": d.get("ip", "127.0.0.1"),
            "snmp_port": 1611, "community": d["id"], "x": d["x"], "y": d["y"],
            "enabled": True, "is_demo": True, "created_at": now_utc(),
        })
    if docs:
        await db.devices.insert_many(docs)
    links = []
    for i, (a, ai, b, bi) in enumerate(DEMO_LINKS):
        links.append({
            "id": f"link-{i+1}", "a_device": a, "a_ifname": ai,
            "b_device": b, "b_ifname": bi, "label": "", "enabled": True,
            "is_demo": True,
        })
    if links:
        await db.links.insert_many(links)

    if await db.dashboards.count_documents({}) == 0:
        await db.dashboards.insert_one({
            "id": "default", "name": "Operations Overview", "is_default": True,
            "created_at": now_utc(),
            "layout": [
                {"i": "w1", "x": 0, "y": 0, "w": 3, "h": 2, "widget": "stat", "config": {"metric": "devices_up"}},
                {"i": "w2", "x": 3, "y": 0, "w": 3, "h": 2, "widget": "stat", "config": {"metric": "devices_down"}},
                {"i": "w3", "x": 6, "y": 0, "w": 3, "h": 2, "widget": "stat", "config": {"metric": "active_alerts"}},
                {"i": "w4", "x": 9, "y": 0, "w": 3, "h": 2, "widget": "stat", "config": {"metric": "total_bandwidth"}},
                {"i": "w5", "x": 0, "y": 2, "w": 8, "h": 5, "widget": "top_interfaces", "config": {}},
                {"i": "w6", "x": 8, "y": 2, "w": 4, "h": 5, "widget": "alerts_feed", "config": {}},
            ],
        })
    logger.info("Seeded demo devices, links and default dashboard")
