"""Background polling engine: ICMP + SNMP per device, stores metrics, runs alerts."""
import asyncio
import time
import logging

from db import db, get_settings, now_utc
from snmp_engine import poll_snmp, icmp_ping, compute_bandwidth
from alerting import evaluate_device

logger = logging.getLogger("poller")
_task = None


async def poll_device(dev, settings, rules):
    dev_id = dev["id"]
    ip = dev["ip"]
    port = dev.get("snmp_port", settings.get("snmp_port", 161))
    community = dev.get("community", settings.get("snmp_community", "public"))

    icmp = await icmp_ping(ip, count=2, timeout=1)
    up = icmp["alive"]

    state = await db.device_state.find_one({"device_id": dev_id}) or {}
    prev_map = state.get("prev_counters", {})
    interfaces = []
    sysinfo = state.get("sysinfo", {})
    snmp_ok = False
    new_prev = prev_map

    if up:
        try:
            snmp = await poll_snmp(ip, port, community,
                                   timeout=settings.get("snmp_timeout", 2),
                                   retries=settings.get("snmp_retries", 1))
            snmp_ok = True
            sysinfo = snmp["sysinfo"]
            interfaces, new_prev = compute_bandwidth(prev_map, snmp["interfaces"], time.time())
        except Exception as e:
            logger.debug("SNMP poll failed for %s (%s): %s", dev_id, ip, e)

    total_in = sum(i.get("in_bps", 0) for i in interfaces)
    total_out = sum(i.get("out_bps", 0) for i in interfaces)
    up_ifaces = sum(1 for i in interfaces if i["oper"] == 1)

    doc = {
        "device_id": dev_id,
        "up": up,
        "snmp_ok": snmp_ok,
        "latency_ms": icmp["latency_ms"],
        "loss_pct": icmp["loss_pct"],
        "jitter_ms": icmp["jitter_ms"],
        "sysinfo": sysinfo,
        "interfaces": interfaces,
        "total_in_bps": total_in,
        "total_out_bps": total_out,
        "iface_count": len(interfaces),
        "iface_up": up_ifaces,
        "prev_counters": new_prev,
        "last_polled": now_utc(),
    }
    await db.device_state.update_one({"device_id": dev_id}, {"$set": doc}, upsert=True)

    ts = now_utc()
    await db.metrics.insert_one({
        "device_id": dev_id, "ts": ts, "up": 1 if up else 0,
        "latency_ms": icmp["latency_ms"], "loss_pct": icmp["loss_pct"],
        "in_bps": total_in, "out_bps": total_out,
    })
    if interfaces:
        await db.iface_metrics.insert_many([{
            "device_id": dev_id, "if_name": i["name"], "ts": ts,
            "in_bps": i.get("in_bps", 0), "out_bps": i.get("out_bps", 0),
            "util": i.get("util", 0),
        } for i in interfaces])

    try:
        await evaluate_device(
            dev,
            {"up": up, "latency_ms": icmp["latency_ms"], "loss_pct": icmp["loss_pct"],
             "snmp_ok": snmp_ok, "interfaces": interfaces},
            rules, settings,
        )
    except Exception as e:
        logger.warning("alert eval failed for %s: %s", dev_id, e)


async def poll_all():
    settings = await get_settings()
    rules = await db.rules.find({}).to_list(100)
    devices = await db.devices.find({"enabled": True}).to_list(2000)
    if not devices:
        return
    sem = asyncio.Semaphore(20)

    async def _guarded(d):
        async with sem:
            try:
                await poll_device(d, settings, rules)
            except Exception as e:
                logger.warning("poll_device error %s: %s", d.get("id"), e)

    await asyncio.gather(*[_guarded(d) for d in devices])


async def _loop():
    await asyncio.sleep(4)  # let snmpsim warm up
    logger.info("Poller loop started")
    while True:
        try:
            await poll_all()
        except Exception as e:
            logger.warning("poll_all error: %s", e)
        settings = await get_settings()
        await asyncio.sleep(max(3, int(settings.get("poll_interval", 8))))


def start_poller():
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())
    return _task
