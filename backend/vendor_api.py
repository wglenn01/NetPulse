"""Vendor API integration framework (MikroTik / UniFi / Cambium).

IMPORTANT (preview constraint agreed with user):
The cloud preview cannot route to the customer's private LAN controllers, so this
module returns a **SIMULATED** enrichment feed that mirrors the real data shapes of
each vendor API. On-prem, `poll_*` functions can be swapped to hit the real
controllers (RouterOS API / UniFi Controller / cnMaestro) without changing the
API response contract consumed by the frontend.

All simulated values are deterministic per-device (seeded from device id) with a
gentle time-based wobble so charts/values feel "live".
"""
import hashlib
import math
import time

from db import db, now_utc

SUPPORTED_VENDORS = {"mikrotik", "ubiquiti", "cambium"}

# device.vendor -> vendor_configs key
VENDOR_CONFIG_KEY = {"mikrotik": "mikrotik", "ubiquiti": "unifi", "cambium": "cambium"}

INTEGRATION_LABEL = {
    "mikrotik": "MikroTik RouterOS API",
    "ubiquiti": "UniFi Controller",
    "cambium": "Cambium cnMaestro",
}

DEFAULT_VENDOR_CONFIG = {
    "id": "vendor",
    "mikrotik": {
        "enabled": True, "host": "", "port": 8728, "username": "admin",
        "password": "", "use_tls": False,
    },
    "unifi": {
        "enabled": True, "host": "", "port": 443, "site": "default",
        "api_key": "", "username": "", "password": "", "verify_tls": False,
    },
    "cambium": {
        "enabled": True, "base_url": "", "client_id": "", "client_secret": "",
    },
}


async def get_vendor_config() -> dict:
    c = await db.vendor_configs.find_one({"id": "vendor"}, {"_id": 0})
    if not c:
        return dict(DEFAULT_VENDOR_CONFIG)
    # backfill any missing vendor blocks / keys
    for vk, defaults in DEFAULT_VENDOR_CONFIG.items():
        if vk == "id":
            continue
        block = c.get(vk) or {}
        for k, v in defaults.items():
            block.setdefault(k, v)
        c[vk] = block
    return c


async def save_vendor_config(patch: dict) -> dict:
    current = await get_vendor_config()
    for vk in ("mikrotik", "unifi", "cambium"):
        if vk in patch and isinstance(patch[vk], dict):
            block = current.get(vk, {})
            block.update({k: v for k, v in patch[vk].items() if v is not None})
            current[vk] = block
    current["id"] = "vendor"
    await db.vendor_configs.update_one({"id": "vendor"}, {"$set": current}, upsert=True)
    return await get_vendor_config()


# ---------------------------------------------------------------- helpers
def _seed(s: str) -> float:
    """Deterministic float in [0,1) from a string."""
    h = int(hashlib.sha256(s.encode()).hexdigest(), 16)
    return (h % 1_000_000) / 1_000_000.0


def _rng(device_id: str, salt: str, lo: float, hi: float) -> float:
    return lo + (hi - lo) * _seed(f"{device_id}:{salt}")


def _wobble(base: float, amp_pct: float, phase: float) -> float:
    t = time.time() / 18.0 + phase
    return base * (1 + amp_pct * math.sin(t))


def _status_for(value: float, warn: float, crit: float, invert=False) -> str:
    if invert:  # lower is worse (e.g. SNR, signal)
        if value <= crit:
            return "crit"
        if value <= warn:
            return "warn"
        return "ok"
    if value >= crit:
        return "crit"
    if value >= warn:
        return "warn"
    return "ok"


def _fw_version(device_id: str, kind: str) -> tuple:
    if kind == "routeros":
        majors = ["7.14.3", "7.15.2", "7.16", "7.13.5"]
    elif kind == "unifi":
        majors = ["6.6.55", "6.7.10", "7.0.25", "6.5.28"]
    else:  # cambium
        majors = ["4.7.0.1", "5.6.0.1", "4.6.2", "5.5.1"]
    ver = majors[int(_seed(device_id + kind) * len(majors)) % len(majors)]
    upgrade = _seed(device_id + "fwup" + kind) > 0.6
    return ver, upgrade


def _fmt_uptime(device_id: str) -> str:
    days = int(_rng(device_id, "uptime", 3, 240))
    hrs = int(_rng(device_id, "uphr", 0, 23))
    return f"{days}d {hrs}h"


def _mac(device_id: str, i: int) -> str:
    h = hashlib.sha256(f"{device_id}:mac:{i}".encode()).hexdigest()
    return ":".join(h[j:j + 2] for j in range(0, 12, 2)).upper()


# ---------------------------------------------------------------- MikroTik
def _mikrotik(device) -> dict:
    did = device["id"]
    role = device.get("role", "router")
    cpu = round(_wobble(_rng(did, "cpu", 8, 55), 0.25, 1.0), 0)
    free_ram = round(_rng(did, "ram", 35, 82), 0)
    temp = round(_wobble(_rng(did, "temp", 34, 58), 0.05, 2.0), 0)
    ver, upgrade = _fw_version(did, "routeros")
    boards = ["CCR2004-1G-12S+2XS", "CRS326-24G-2S+", "RB5009UG+S+", "CCR1036-8G-2S+"]
    board = boards[int(_seed(did + "board") * len(boards)) % len(boards)]

    sections = [
        {"title": "System", "type": "metrics", "items": [
            {"label": "CPU Load", "value": f"{cpu:.0f}%", "status": _status_for(cpu, 70, 90)},
            {"label": "Free RAM", "value": f"{free_ram:.0f}%", "status": _status_for(free_ram, 25, 12, invert=True)},
            {"label": "Temperature", "value": f"{temp:.0f}°C", "status": _status_for(temp, 60, 75)},
            {"label": "Uptime", "value": _fmt_uptime(did), "status": "ok"},
            {"label": "Board", "value": board, "status": "ok"},
            {"label": "RouterOS", "value": ver + (" ⬆ update" if upgrade else ""), "status": "warn" if upgrade else "ok"},
        ]},
    ]

    # DHCP leases (routers/switches)
    if role in ("router", "switch"):
        n = int(_rng(did, "dhcp", 24, 210))
        rows = []
        for i in range(min(5, n)):
            rows.append({
                "Address": f"10.{int(_rng(did, f'o{i}', 10, 40))}.{int(_rng(did, f'p{i}', 0, 250))}.{int(_rng(did, f'q{i}', 2, 250))}",
                "MAC": _mac(did, i),
                "Host": f"cpe-{int(_rng(did, f'h{i}', 100, 999))}",
                "Status": "bound",
            })
        sections.append({"title": f"DHCP Leases ({n} active)", "type": "table",
                         "columns": ["Address", "MAC", "Host", "Status"], "rows": rows})

    # wireless registrations (APs)
    if role in ("ap", "backhaul"):
        n = int(_rng(did, "wreg", 4, 40))
        rows = []
        for i in range(min(5, n)):
            sig = int(_rng(did, f"sig{i}", -78, -48))
            rows.append({
                "Interface": f"wlan{i % 2 + 1}",
                "MAC": _mac(did, i + 10),
                "Signal": f"{sig} dBm",
                "TX/RX": f"{int(_rng(did, f'tx{i}', 130, 866))}/{int(_rng(did, f'rx{i}', 130, 866))}M",
            })
        sections.append({"title": f"Wireless Registrations ({n})", "type": "table",
                         "columns": ["Interface", "MAC", "Signal", "TX/RX"], "rows": rows})

    return sections


# ---------------------------------------------------------------- UniFi
def _unifi(device) -> dict:
    did = device["id"]
    role = device.get("role", "ap")
    ver, upgrade = _fw_version(did, "unifi")
    health = int(_rng(did, "health", 82, 99))
    models = ["UAP-AC-Pro", "U6-LR", "Rocket Prism 5AC", "LiteBeam 5AC", "NanoStation 5AC"]
    model = models[int(_seed(did + "model") * len(models)) % len(models)]
    clients = int(_wobble(_rng(did, "clients", 6, 64), 0.15, 1.0))
    guests = int(_rng(did, "guests", 0, max(1, clients // 4)))

    sections = [
        {"title": "Controller", "type": "metrics", "items": [
            {"label": "Model", "value": model, "status": "ok"},
            {"label": "Firmware", "value": ver + (" ⬆ update" if upgrade else ""), "status": "warn" if upgrade else "ok"},
            {"label": "Health", "value": f"{health}/100", "status": _status_for(health, 90, 80, invert=True)},
            {"label": "Adopted", "value": "yes", "status": "ok"},
            {"label": "Uptime", "value": _fmt_uptime(did), "status": "ok"},
            {"label": "Clients", "value": f"{clients} ({guests} guest)", "status": "ok"},
        ]},
    ]

    if role in ("ap", "backhaul", "cpe"):
        chan = int(_rng(did, "chan", 36, 165))
        txp = int(_rng(did, "txp", 14, 26))
        avg_sig = int(_rng(did, "asig", -72, -50))
        sections.append({"title": "Radio", "type": "metrics", "items": [
            {"label": "Channel", "value": str(chan), "status": "ok"},
            {"label": "TX Power", "value": f"{txp} dBm", "status": "ok"},
            {"label": "Clients", "value": str(clients), "status": "ok"},
            {"label": "Avg Signal", "value": f"{avg_sig} dBm", "status": _status_for(avg_sig, -67, -74, invert=True)},
        ]})

    n = clients
    rows = []
    for i in range(min(5, n)):
        sig = int(_rng(did, f"csig{i}", -76, -46))
        rows.append({
            "Client": f"sta-{int(_rng(did, f'c{i}', 100, 999))}",
            "Signal": f"{sig} dBm",
            "Down": f"{int(_rng(did, f'cd{i}', 2, 240))}M",
            "Up": f"{int(_rng(did, f'cu{i}', 1, 90))}M",
        })
    if rows:
        sections.append({"title": f"Top Clients ({n})", "type": "table",
                         "columns": ["Client", "Signal", "Down", "Up"], "rows": rows})

    return sections


# ---------------------------------------------------------------- Cambium
def _cambium(device) -> dict:
    did = device["id"]
    role = device.get("role", "ap")
    ver, upgrade = _fw_version(did, "cambium")
    mode = "AP" if role in ("ap", "backhaul") else "SM"
    snr = round(_wobble(_rng(did, "snr", 18, 38), 0.08, 1.0), 0)
    rssi = int(_wobble(_rng(did, "rssi", -74, -52), 0.03, 2.0))
    dl = int(_rng(did, "dl", 40, 480))
    ul = int(_rng(did, "ul", 10, 160))

    sections = [
        {"title": "cnMaestro", "type": "metrics", "items": [
            {"label": "Mode", "value": mode, "status": "ok"},
            {"label": "Firmware", "value": ver + (" ⬆ update" if upgrade else ""), "status": "warn" if upgrade else "ok"},
            {"label": "GPS Sync", "value": "locked", "status": "ok"},
            {"label": "Uptime", "value": _fmt_uptime(did), "status": "ok"},
        ]},
        {"title": "RF", "type": "metrics", "items": [
            {"label": "SNR", "value": f"{snr:.0f} dB", "status": _status_for(snr, 22, 15, invert=True)},
            {"label": "RSSI", "value": f"{rssi} dBm", "status": _status_for(rssi, -68, -74, invert=True)},
            {"label": "DL Rate", "value": f"{dl} Mbps", "status": "ok"},
            {"label": "UL Rate", "value": f"{ul} Mbps", "status": "ok"},
        ]},
    ]

    if mode == "AP":
        n = int(_rng(did, "sm", 3, 48))
        rows = []
        for i in range(min(5, n)):
            s = int(_rng(did, f"ssnr{i}", 12, 36))
            r = int(_rng(did, f"srssi{i}", -80, -55))
            rows.append({
                "SM": f"sm-{int(_rng(did, f'sm{i}', 100, 999))}",
                "SNR": f"{s} dB",
                "RSSI": f"{r} dBm",
                "Dist": f"{_rng(did, f'd{i}', 0.3, 12.0):.1f} km",
            })
        sections.append({"title": f"Registered SMs ({n})", "type": "table",
                         "columns": ["SM", "SNR", "RSSI", "Dist"], "rows": rows})

    return sections


_BUILDERS = {"mikrotik": _mikrotik, "ubiquiti": _unifi, "cambium": _cambium}


async def build_enrichment(device: dict) -> dict:
    """Return simulated vendor-API enrichment for a device (preview)."""
    vendor = device.get("vendor", "generic")
    envelope = {
        "device_id": device["id"],
        "vendor": vendor,
        "integration": INTEGRATION_LABEL.get(vendor),
        "available": False,
        "simulated": True,
        "polled_at": now_utc().isoformat(),
        "sections": [],
        "reason": None,
    }

    if vendor not in SUPPORTED_VENDORS:
        envelope["reason"] = f"No vendor API integration for '{vendor}'. Supported: MikroTik, UniFi, Cambium."
        return envelope

    cfg = await get_vendor_config()
    settings = await db.settings.find_one({"id": "global"}, {"_id": 0}) or {}
    demo_mode = settings.get("demo_mode", True)
    block = cfg.get(VENDOR_CONFIG_KEY[vendor], {})
    enabled = block.get("enabled", True)

    # In preview/demo we always surface simulated data; on-prem this would gate on
    # a live connection to the configured controller.
    if not enabled and not demo_mode:
        envelope["reason"] = f"{INTEGRATION_LABEL[vendor]} integration is disabled."
        return envelope

    envelope["available"] = True
    envelope["sections"] = _BUILDERS[vendor](device)
    return envelope
