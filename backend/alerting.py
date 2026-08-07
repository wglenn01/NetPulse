"""Alert rule evaluation, state machine, and Discord webhook dispatch."""
import asyncio
import uuid
import json
import logging

import requests

from db import db, now_utc, get_settings

logger = logging.getLogger("alerting")

SEV_COLOR = {
    "critical": 0xFF4D4F,
    "warning": 0xFFB020,
    "info": 0x2F9BFF,
    "resolved": 0x2ED47A,
}


def _build_embed(alert: dict, resolved=False) -> dict:
    sev = "resolved" if resolved else alert["severity"]
    fields = [
        {"name": "Device", "value": alert.get("device_name", alert.get("device_id", "?")), "inline": True},
        {"name": "Type", "value": alert["type"], "inline": True},
    ]
    if alert.get("if_name"):
        fields.append({"name": "Interface", "value": alert["if_name"], "inline": True})
    title = ("[RESOLVED] " if resolved else f"[{alert['severity'].upper()}] ") + alert["message"]
    return {
        "username": "NetPulse NOC",
        "embeds": [{
            "title": title[:250],
            "description": alert.get("detail", ""),
            "color": SEV_COLOR.get(sev, 0x888888),
            "fields": fields,
            "footer": {"text": "NetPulse Network Visibility"},
            "timestamp": now_utc().isoformat(),
        }],
    }


def _post_discord(url: str, payload: dict):
    try:
        r = requests.post(url, data=json.dumps(payload),
                          headers={"Content-Type": "application/json"}, timeout=10)
        return r.status_code
    except Exception as e:  # pragma: no cover
        logger.warning("Discord post failed: %s", e)
        return None


async def send_discord(payload: dict):
    settings = await get_settings()
    if not settings.get("alerts_enabled", True):
        return None
    url = (settings.get("discord_webhook_url") or "").strip()
    if not url:
        return "no-webhook"
    return await asyncio.to_thread(_post_discord, url, payload)


async def _fire(rule, device, message, detail, if_name=None, value=None):
    key = {"type": rule["type"], "device_id": device["id"], "if_name": if_name, "state": "firing"}
    existing = await db.alerts.find_one(key)
    if existing:
        await db.alerts.update_one({"id": existing["id"]},
                                   {"$set": {"last_seen": now_utc(), "value": value}})
        return
    alert = {
        "id": str(uuid.uuid4()),
        "type": rule["type"],
        "device_id": device["id"],
        "device_name": device.get("name", device["id"]),
        "if_name": if_name,
        "severity": rule.get("severity", "warning"),
        "state": "firing",
        "message": message,
        "detail": detail,
        "value": value,
        "acknowledged": False,
        "first_seen": now_utc(),
        "last_seen": now_utc(),
        "resolved_at": None,
    }
    await db.alerts.insert_one(dict(alert))
    await send_discord(_build_embed(alert))


async def _resolve(rule_type, device, if_name=None):
    key = {"type": rule_type, "device_id": device["id"], "if_name": if_name, "state": "firing"}
    existing = await db.alerts.find_one(key)
    if not existing:
        return
    await db.alerts.update_one({"id": existing["id"]},
                               {"$set": {"state": "resolved", "resolved_at": now_utc(),
                                         "last_seen": now_utc()}})
    existing["message"] = "Recovered: " + existing.get("message", "")
    await send_discord(_build_embed(existing, resolved=True))


async def evaluate_device(device, result, rules, settings):
    """result = {up, latency_ms, loss_pct, snmp_ok, interfaces:[...]}"""
    rmap = {r["type"]: r for r in rules if r.get("enabled", True)}
    name = device.get("name", device["id"])

    # device down
    if "device_down" in rmap:
        if not result["up"]:
            await _fire(rmap["device_down"], device,
                        f"Device Down: {name}",
                        f"{name} ({device['ip']}) is not responding to ICMP.")
        else:
            await _resolve("device_down", device)

    if not result["up"]:
        return

    # latency
    if "high_latency" in rmap and result.get("latency_ms") is not None:
        thr = rmap["high_latency"].get("threshold", 150)
        if result["latency_ms"] > thr:
            await _fire(rmap["high_latency"], device,
                        f"High Latency: {name}",
                        f"Latency {result['latency_ms']} ms exceeds {thr} ms.",
                        value=result["latency_ms"])
        else:
            await _resolve("high_latency", device)

    # packet loss
    if "packet_loss" in rmap:
        thr = rmap["packet_loss"].get("threshold", 20)
        if (result.get("loss_pct") or 0) > thr:
            await _fire(rmap["packet_loss"], device,
                        f"Packet Loss: {name}",
                        f"Packet loss {result['loss_pct']}% exceeds {thr}%.",
                        value=result["loss_pct"])
        else:
            await _resolve("packet_loss", device)

    # interface based
    for i in result.get("interfaces", []):
        ifn = i["name"]
        if "iface_down" in rmap:
            if i["admin"] == 1 and i["oper"] != 1:
                await _fire(rmap["iface_down"], device,
                            f"Interface Down: {ifn}",
                            f"Interface {ifn} on {name} is admin-up but oper-down.",
                            if_name=ifn)
            else:
                await _resolve("iface_down", device, if_name=ifn)
        if "high_util" in rmap:
            thr = rmap["high_util"].get("threshold", 85)
            if i.get("util", 0) > thr and i["oper"] == 1:
                await _fire(rmap["high_util"], device,
                            f"High Utilization: {ifn}",
                            f"{ifn} on {name} at {i['util']}% (>{thr}%).",
                            if_name=ifn, value=i["util"])
            else:
                await _resolve("high_util", device, if_name=ifn)
