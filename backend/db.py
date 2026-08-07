"""MongoDB access, serialization helpers, indexes and default seed config."""
import os
from pathlib import Path
from datetime import datetime, timezone, date
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent / ".env")

MONGO_URL = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ["DB_NAME"]]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ser(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _ser(x) for k, x in v.items() if k != "_id"}
    if isinstance(v, list):
        return [_ser(x) for x in v]
    return v


def serialize(doc):
    """Recursively strip _id and convert datetimes to ISO strings."""
    if doc is None:
        return None
    return {k: _ser(v) for k, v in doc.items() if k != "_id"}


DEFAULT_SETTINGS = {
    "id": "global",
    "snmp_community": "public",
    "snmp_port": 161,
    "snmp_timeout": 2,
    "snmp_retries": 1,
    "poll_interval": 8,
    "discovery_range": "127.0.0.1/32",
    "discovery_community": "public",
    "discovery_port": 1612,
    "discord_webhook_url": "",
    "alerts_enabled": True,
    "threshold_latency_ms": 150,
    "threshold_loss_pct": 20,
    "threshold_util_pct": 85,
    "demo_mode": True,
    "tv_rotate_seconds": 15,
}

DEFAULT_RULES = [
    {"id": "device_down", "type": "device_down", "name": "Device Down (ICMP)",
     "severity": "critical", "threshold": 0, "enabled": True},
    {"id": "iface_down", "type": "iface_down", "name": "Interface Down",
     "severity": "warning", "threshold": 0, "enabled": True},
    {"id": "high_latency", "type": "high_latency", "name": "High Latency",
     "severity": "warning", "threshold": 150, "enabled": True},
    {"id": "packet_loss", "type": "packet_loss", "name": "Packet Loss",
     "severity": "warning", "threshold": 20, "enabled": True},
    {"id": "high_util", "type": "high_util", "name": "High Bandwidth Utilization",
     "severity": "warning", "threshold": 85, "enabled": True},
]


async def ensure_indexes():
    await db.devices.create_index("id", unique=True)
    await db.device_state.create_index("device_id", unique=True)
    await db.metrics.create_index([("device_id", 1), ("ts", 1)])
    await db.metrics.create_index("ts", expireAfterSeconds=6 * 3600)
    await db.iface_metrics.create_index([("device_id", 1), ("if_name", 1), ("ts", 1)])
    await db.iface_metrics.create_index("ts", expireAfterSeconds=6 * 3600)
    await db.alerts.create_index("id", unique=True)
    await db.alerts.create_index([("state", 1), ("type", 1), ("device_id", 1), ("if_name", 1)])
    await db.links.create_index("id", unique=True)
    await db.rules.create_index("id", unique=True)
    await db.dashboards.create_index("id", unique=True)


async def ensure_defaults():
    existing = await db.settings.find_one({"id": "global"})
    if not existing:
        await db.settings.insert_one(dict(DEFAULT_SETTINGS))
    else:
        # backfill any missing keys
        patch = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in existing}
        if patch:
            await db.settings.update_one({"id": "global"}, {"$set": patch})
    if await db.rules.count_documents({}) == 0:
        await db.rules.insert_many([dict(r) for r in DEFAULT_RULES])


async def get_settings() -> dict:
    s = await db.settings.find_one({"id": "global"})
    return s or dict(DEFAULT_SETTINGS)
