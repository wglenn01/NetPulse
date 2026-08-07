#!/usr/bin/env python3
"""
CORE POC for the Network Visibility App.

Proves the hardest / most failure-prone parts in ISOLATION against a REAL SNMP
agent (snmpsim) so we know the on-prem polling path genuinely works:

  1. SNMP v2c GET   -> system group (sysDescr/sysName/sysUpTime/...)
  2. SNMP v2c WALK  -> interface table (ifDescr/ifOperStatus/ifHighSpeed/ifHC*Octets)
  3. Bandwidth delta -> two polls, compute bps in/out + utilization from HC counters
  4. ICMP ping      -> latency + packet loss (unprivileged datagram socket)
  5. Discord webhook -> build alert payload (+ real POST if DISCORD_WEBHOOK_URL set)

Run:  python /app/poc/test_core.py
"""
import asyncio
import os
import subprocess
import sys
import time
import json
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# 0) Demo device profiles (vendors the customer actually uses)
# ---------------------------------------------------------------------------
DATA_DIR = Path("/app/poc/data")
SNMP_HOST = "127.0.0.1"
SNMP_PORT = 1611

# ASN.1 snmprec type tags
T_INT = 2      # Integer32
T_STR = 4      # OctetString
T_OID = 6      # ObjectIdentifier
T_TT = 67      # TimeTicks
T_GAUGE = 66   # Gauge32 / Unsigned32
T_CNT32 = 65   # Counter32
T_CNT64 = 70   # Counter64

# Each device: community -> profile. rate_in/out are bytes/sec (drives bandwidth).
DEVICES = {
    "mikrotik-core": {
        "descr": "RouterOS CCR2004-1G-12S+2XS SNMP agent, RouterOS 7.14",
        "oid": "1.3.6.1.4.1.14988.1",
        "name": "core-rtr-01",
        "location": "NOC / Rack A1",
        "ifaces": [
            # (descr, ifname, link_mbps, oper(1/2), in_mbps, out_mbps)
            ("sfp-sfpplus1", "uplink-transit", 10000, 1, 480, 210),
            ("sfp-sfpplus2", "uplink-peering", 10000, 1, 95, 320),
            ("ether1", "mgmt", 1000, 1, 2, 1),
            ("bridge-core", "bridge-core", 10000, 1, 610, 540),
            ("sfp-sfpplus5", "tower-north", 1000, 2, 0, 0),  # down port
        ],
    },
    "ubnt-ap": {
        "descr": "Ubiquiti UniFi AP airMAX / EdgeOS, model NanoStation 5AC",
        "oid": "1.3.6.1.4.1.41112",
        "name": "ap-north-01",
        "location": "Tower North / Sector 2",
        "ifaces": [
            ("eth0", "backhaul", 1000, 1, 88, 12),
            ("ath0", "wlan-sector2", 300, 1, 42, 7),
        ],
    },
    "cambium-ap": {
        "descr": "Cambium Networks ePMP 3000 Access Point, Canopy",
        "oid": "1.3.6.1.4.1.17713.21",
        "name": "ap-east-cambium-01",
        "location": "Tower East / Sector 1",
        "ifaces": [
            ("eth0", "backhaul", 1000, 1, 130, 18),
            ("wlan0", "ptmp-sector1", 500, 1, 76, 9),
        ],
    },
    "mimosa-bh": {
        "descr": "Mimosa B5c Backhaul Radio, Mimosa by Airspan",
        "oid": "1.3.6.1.4.1.43356",
        "name": "bh-ridge-01",
        "location": "Ridge Relay / PtP",
        "ifaces": [
            ("eth0", "ptp-link", 1000, 1, 690, 640),
        ],
    },
}


def _fmt(oid, tag, value):
    """Return (oid_tuple, snmprec_line)."""
    t = tuple(int(x) for x in oid.split("."))
    return (t, f"{oid}|{tag}|{value}")


def _num(oid, tag, initial, rate):
    """Numeric variation record => monotonically growing counter/timeticks."""
    t = tuple(int(x) for x in oid.split("."))
    line = f"{oid}|{tag}:numeric|initial={initial},rate={rate}"
    return (t, line)


def generate_snmprec():
    """Write sorted .snmprec files (one per community) for snmpsim."""
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for community, prof in DEVICES.items():
        recs = []
        # --- system group 1.3.6.1.2.1.1 ---
        recs.append(_fmt("1.3.6.1.2.1.1.1.0", T_STR, prof["descr"]))
        recs.append(_fmt("1.3.6.1.2.1.1.2.0", T_OID, prof["oid"]))
        recs.append(_num("1.3.6.1.2.1.1.3.0", T_TT, initial=1000000, rate=100))  # uptime grows
        recs.append(_fmt("1.3.6.1.2.1.1.4.0", T_STR, "noc@wisp.example"))
        recs.append(_fmt("1.3.6.1.2.1.1.5.0", T_STR, prof["name"]))
        recs.append(_fmt("1.3.6.1.2.1.1.6.0", T_STR, prof["location"]))
        recs.append(_fmt("1.3.6.1.2.1.1.7.0", T_INT, 78))

        ifaces = prof["ifaces"]
        recs.append(_fmt("1.3.6.1.2.1.2.1.0", T_INT, len(ifaces)))  # ifNumber

        for idx, (descr, ifname, mbps, oper, in_mbps, out_mbps) in enumerate(ifaces, start=1):
            speed_bps = min(mbps * 1_000_000, 4294967295)
            # counter rate is in OCTETS/sec => convert desired Mbps to bytes/sec
            in_bps = int(in_mbps * 1_000_000 / 8)
            out_bps = int(out_mbps * 1_000_000 / 8)
            # ifTable 1.3.6.1.2.1.2.2.1
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.1.{idx}", T_INT, idx))
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.2.{idx}", T_STR, descr))
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.3.{idx}", T_INT, 6))       # ethernetCsmacd
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.4.{idx}", T_INT, 1500))    # mtu
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.5.{idx}", T_GAUGE, speed_bps))
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.7.{idx}", T_INT, 1))       # adminStatus up
            recs.append(_fmt(f"1.3.6.1.2.1.2.2.1.8.{idx}", T_INT, oper))    # operStatus
            # low-capacity 32-bit counters
            recs.append(_num(f"1.3.6.1.2.1.2.2.1.10.{idx}", T_CNT32, initial=100000, rate=in_bps if oper == 1 else 0))
            recs.append(_num(f"1.3.6.1.2.1.2.2.1.16.{idx}", T_CNT32, initial=100000, rate=out_bps if oper == 1 else 0))
            # ifXTable 1.3.6.1.2.1.31.1.1.1
            recs.append(_fmt(f"1.3.6.1.2.1.31.1.1.1.1.{idx}", T_STR, ifname))
            recs.append(_num(f"1.3.6.1.2.1.31.1.1.1.6.{idx}", T_CNT64, initial=5_000_000_000, rate=in_bps if oper == 1 else 0))
            recs.append(_num(f"1.3.6.1.2.1.31.1.1.1.10.{idx}", T_CNT64, initial=5_000_000_000, rate=out_bps if oper == 1 else 0))
            recs.append(_fmt(f"1.3.6.1.2.1.31.1.1.1.15.{idx}", T_GAUGE, mbps))  # ifHighSpeed (Mbps)
            recs.append(_fmt(f"1.3.6.1.2.1.31.1.1.1.18.{idx}", T_STR, f"{prof['name']}:{ifname}"))

        recs.sort(key=lambda r: r[0])
        out = DATA_DIR / f"{community}.snmprec"
        out.write_text("\n".join(line for _, line in recs) + "\n")
    print(f"[gen] wrote {len(DEVICES)} device profiles to {DATA_DIR}")


# ---------------------------------------------------------------------------
# snmpsim responder lifecycle
# ---------------------------------------------------------------------------
def start_responder():
    cmd = [
        "snmpsim-command-responder",
        f"--data-dir={DATA_DIR}",
        f"--agent-udpv4-endpoint={SNMP_HOST}:{SNMP_PORT}",
        "--logging-method=null",
        "--process-user=root",
        "--process-group=root",
    ]
    print(f"[sim] starting: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc


# ---------------------------------------------------------------------------
# SNMP helpers (pysnmp 7.x, v1arch asyncio, v2c)
# ---------------------------------------------------------------------------
from pysnmp.hlapi.v1arch.asyncio import (
    SnmpDispatcher, CommunityData, UdpTransportTarget,
    ObjectType, ObjectIdentity, get_cmd, bulk_walk_cmd,
)


async def snmp_get(dispatcher, community, oids):
    target = await UdpTransportTarget.create((SNMP_HOST, SNMP_PORT), timeout=2, retries=1)
    errI, errS, errIdx, varBinds = await get_cmd(
        dispatcher, CommunityData(community, mpModel=1), target,
        *[ObjectType(ObjectIdentity(o)) for o in oids],
    )
    if errI:
        raise RuntimeError(f"SNMP GET error: {errI}")
    if errS:
        raise RuntimeError(f"SNMP GET status: {errS.prettyPrint()} at {errIdx}")
    return {str(vb[0]): vb[1] for vb in varBinds}


async def snmp_walk(dispatcher, community, base_oid):
    target = await UdpTransportTarget.create((SNMP_HOST, SNMP_PORT), timeout=2, retries=1)
    results = {}
    async for errI, errS, errIdx, varBinds in bulk_walk_cmd(
        dispatcher, CommunityData(community, mpModel=1), target,
        0, 25, ObjectType(ObjectIdentity(base_oid)),
    ):
        if errI:
            raise RuntimeError(f"SNMP WALK error: {errI}")
        if errS:
            raise RuntimeError(f"SNMP WALK status: {errS.prettyPrint()}")
        for vb in varBinds:
            results[str(vb[0])] = vb[1]
    return results


async def wait_ready(dispatcher, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = await snmp_get(dispatcher, "mikrotik-core", ["1.3.6.1.2.1.1.5.0"])
            if r:
                return True
        except Exception:
            await asyncio.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Interface parsing + bandwidth calc
# ---------------------------------------------------------------------------
def parse_interfaces(walk):
    """From a full ifTable+ifXTable walk build {ifIndex: {...}}."""
    ifaces = {}

    def col(prefix):
        out = {}
        for oid, val in walk.items():
            if oid.startswith(prefix + "."):
                idx = oid[len(prefix) + 1:]
                if idx.isdigit():
                    out[int(idx)] = val
        return out

    descr = col("1.3.6.1.2.1.2.2.1.2")
    oper = col("1.3.6.1.2.1.2.2.1.8")
    name = col("1.3.6.1.2.1.31.1.1.1.1")
    hcin = col("1.3.6.1.2.1.31.1.1.1.6")
    hcout = col("1.3.6.1.2.1.31.1.1.1.10")
    hispeed = col("1.3.6.1.2.1.31.1.1.1.15")

    for idx in sorted(descr.keys()):
        ifaces[idx] = {
            "index": idx,
            "descr": str(descr.get(idx, "")),
            "name": str(name.get(idx, "")),
            "oper": int(oper.get(idx, 0)),
            "speed_mbps": int(hispeed.get(idx, 0)),
            "hc_in": int(hcin.get(idx, 0)),
            "hc_out": int(hcout.get(idx, 0)),
        }
    return ifaces


def compute_bandwidth(first, second, dt):
    """Return per-index bps_in/out + util% from two HC counter snapshots."""
    rows = []
    for idx, s2 in second.items():
        s1 = first.get(idx)
        if not s1:
            continue
        din = (s2["hc_in"] - s1["hc_in"])
        dout = (s2["hc_out"] - s1["hc_out"])
        # handle counter wrap (64-bit)
        if din < 0:
            din += 2 ** 64
        if dout < 0:
            dout += 2 ** 64
        bps_in = din * 8 / dt
        bps_out = dout * 8 / dt
        cap = s2["speed_mbps"] * 1_000_000 or 1
        rows.append({
            "index": idx,
            "name": s2["name"] or s2["descr"],
            "oper": s2["oper"],
            "bps_in": bps_in,
            "bps_out": bps_out,
            "util_in": round(bps_in / cap * 100, 2),
            "util_out": round(bps_out / cap * 100, 2),
        })
    return rows


# ---------------------------------------------------------------------------
# ICMP
# ---------------------------------------------------------------------------
async def icmp_check(host):
    from icmplib import async_ping
    h = await async_ping(host, count=4, interval=0.2, timeout=1, privileged=False)
    return {
        "host": host,
        "alive": h.is_alive,
        "avg_rtt_ms": h.avg_rtt,
        "min_rtt_ms": h.min_rtt,
        "max_rtt_ms": h.max_rtt,
        "loss_pct": h.packet_loss * 100,
    }


# ---------------------------------------------------------------------------
# Discord webhook payload
# ---------------------------------------------------------------------------
def build_discord_alert(device, severity, title, detail):
    colors = {"critical": 0xE24A4A, "warning": 0xE2A24A, "info": 0x4A9EE2, "resolved": 0x4AE27A}
    return {
        "username": "NetPulse NOC",
        "embeds": [{
            "title": f"[{severity.upper()}] {title}",
            "description": detail,
            "color": colors.get(severity, 0x888888),
            "fields": [
                {"name": "Device", "value": device, "inline": True},
                {"name": "Severity", "value": severity, "inline": True},
            ],
            "footer": {"text": "NetPulse Network Visibility"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }],
    }


def send_discord(payload):
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        print("[discord] DISCORD_WEBHOOK_URL not set -> DRY RUN. Payload:")
        print(json.dumps(payload, indent=2))
        return "dry-run"
    import urllib.request
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"[discord] POST status={resp.status}")
        return resp.status


# ---------------------------------------------------------------------------
# Main test flow
# ---------------------------------------------------------------------------
async def run_tests():
    dispatcher = SnmpDispatcher()
    results = {"pass": [], "fail": []}

    def check(name, cond, extra=""):
        (results["pass"] if cond else results["fail"]).append(name)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name} {extra}")

    print("\n=== Waiting for SNMP agent readiness ===")
    ready = await wait_ready(dispatcher)
    check("snmpsim agent reachable", ready)
    if not ready:
        return results

    # 1) SNMP GET system group
    print("\n=== TEST 1: SNMP v2c GET (system group) ===")
    sysoids = ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0", "1.3.6.1.2.1.1.5.0", "1.3.6.1.2.1.1.6.0"]
    sysinfo = await snmp_get(dispatcher, "mikrotik-core", sysoids)
    descr = str(sysinfo.get("1.3.6.1.2.1.1.1.0", ""))
    name = str(sysinfo.get("1.3.6.1.2.1.1.5.0", ""))
    print(f"    sysDescr = {descr}")
    print(f"    sysName  = {name}")
    print(f"    sysLoc   = {sysinfo.get('1.3.6.1.2.1.1.6.0')}")
    check("GET returns sysDescr (RouterOS)", "RouterOS" in descr)
    check("GET returns sysName", name == "core-rtr-01")

    # 2) SNMP WALK interface table
    print("\n=== TEST 2: SNMP v2c WALK (interfaces) ===")
    walk1 = await snmp_walk(dispatcher, "mikrotik-core", "1.3.6.1.2.1.2.2.1")
    walkx = await snmp_walk(dispatcher, "mikrotik-core", "1.3.6.1.2.1.31.1.1.1")
    walk1.update(walkx)
    ifaces1 = parse_interfaces(walk1)
    print(f"    discovered {len(ifaces1)} interfaces:")
    for idx, i in ifaces1.items():
        print(f"      #{idx} {i['name']:<16} oper={i['oper']} speed={i['speed_mbps']}M in={i['hc_in']}")
    check("WALK finds all 5 interfaces", len(ifaces1) == 5)
    check("interface has HC counters", all(i["hc_in"] >= 0 for i in ifaces1.values()))
    check("detects down port (oper=2)", any(i["oper"] == 2 for i in ifaces1.values()))

    # 3) Bandwidth delta over an interval
    print("\n=== TEST 3: Bandwidth delta (two polls) ===")
    dt = 3.0
    print(f"    waiting {dt}s between polls...")
    await asyncio.sleep(dt)
    walk2 = await snmp_walk(dispatcher, "mikrotik-core", "1.3.6.1.2.1.31.1.1.1")
    # merge ifTable static bits from walk1 for speed/oper
    base = {k: v for k, v in walk1.items() if k.startswith("1.3.6.1.2.1.2.2.1")}
    walk2.update(base)
    ifaces2 = parse_interfaces(walk2)
    rows = compute_bandwidth(ifaces1, ifaces2, dt)
    active = 0
    for r in rows:
        mbps_in = r["bps_in"] / 1e6
        mbps_out = r["bps_out"] / 1e6
        print(f"      {r['name']:<16} in={mbps_in:8.2f} Mbps ({r['util_in']:5.1f}%)  out={mbps_out:8.2f} Mbps ({r['util_out']:5.1f}%)")
        if r["bps_in"] > 1e6 or r["bps_out"] > 1e6:
            active += 1
    check("counters grew => positive bandwidth on active links", active >= 3)
    uplink = next((r for r in rows if r["name"] == "uplink-transit"), None)
    check("uplink-transit bandwidth in sane range (300-700Mbps)",
          bool(uplink) and 300e6 < uplink["bps_in"] < 700e6,
          extra=f"(got {uplink['bps_in']/1e6:.1f} Mbps)" if uplink else "")
    down = next((r for r in rows if r["name"] == "tower-north"), None)
    check("down port shows ~0 bandwidth", bool(down) and down["bps_in"] < 1e6)

    # 3b) multi-device / multi-vendor polling
    print("\n=== TEST 3b: Multi-vendor polling ===")
    for comm, expect in [("ubnt-ap", "Ubiquiti"), ("cambium-ap", "Cambium"), ("mimosa-bh", "Mimosa")]:
        d = await snmp_get(dispatcher, comm, ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.5.0"])
        dd = str(d.get("1.3.6.1.2.1.1.1.0", ""))
        print(f"    {comm:<12} -> {dd[:55]}")
        check(f"{comm} fingerprint contains '{expect}'", expect in dd)

    # 4) ICMP
    print("\n=== TEST 4: ICMP ping ===")
    for host in ["127.0.0.1", "8.8.8.8"]:
        try:
            p = await icmp_check(host)
            print(f"    {host:<12} alive={p['alive']} rtt={p['avg_rtt_ms']}ms loss={p['loss_pct']}%")
            if host == "127.0.0.1":
                check("ICMP localhost alive + measures rtt", p["alive"] and p["avg_rtt_ms"] is not None)
        except Exception as e:
            print(f"    {host} ICMP error: {e}")
            if host == "127.0.0.1":
                check("ICMP localhost alive + measures rtt", False)

    # 5) Discord webhook payload
    print("\n=== TEST 5: Discord webhook alert ===")
    payload = build_discord_alert(
        device="core-rtr-01",
        severity="critical",
        title="Interface Down: tower-north",
        detail="Port sfp-sfpplus5 (tower-north) operational status changed to DOWN.",
    )
    status = send_discord(payload)
    check("Discord payload built + dispatched (or dry-run)", status in ("dry-run", 200, 204))

    return results


def main():
    generate_snmprec()
    proc = start_responder()
    time.sleep(2)  # give responder a head start to bind
    try:
        results = asyncio.run(run_tests())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    print("\n" + "=" * 60)
    print(f"RESULTS: {len(results['pass'])} passed, {len(results['fail'])} failed")
    if results["fail"]:
        print("FAILED:")
        for f in results["fail"]:
            print(f"   - {f}")
        print("=" * 60)
        sys.exit(1)
    print("ALL CORE POC CHECKS PASSED ✔")
    print("=" * 60)


if __name__ == "__main__":
    main()
