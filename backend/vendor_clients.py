"""Real vendor-API pollers (BETA).

Used when DEMO_MODE is false (production). Each poller connects to the customer's
own equipment/controllers and returns the SAME `sections` shape the frontend already
renders for the simulated feed, so the Device drawer works identically with live data.

Design notes:
- Every poller is fully wrapped by the caller (vendor_api.build_enrichment) with a
  hard timeout; any failure surfaces as `available:false` + a human reason instead of
  crashing the request or the poller loop.
- Network libs are imported lazily so a missing optional dependency never breaks app
  startup — the affected vendor simply reports the import error as its reason.
- These clients are BETA: validate against your own LAN. cnMaestro / UniFi response
  shapes vary by version, so parsing is deliberately defensive (.get with fallbacks).
"""
from __future__ import annotations


# ----------------------------------------------------------------- helpers
def _metric(label, value, status=None):
    return {"label": label, "value": str(value), "status": status}


def _metrics(title, items):
    return {"title": title, "type": "metrics", "items": items}


def _table(title, columns, rows):
    return {"title": title, "type": "table", "columns": columns, "rows": rows}


def _st_high(v, warn, crit):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return "crit" if v >= crit else "warn" if v >= warn else "ok"


def _st_low(v, warn, crit):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return "crit" if v <= crit else "warn" if v <= warn else "ok"


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------- MikroTik
def poll_mikrotik(device: dict, cfg: dict) -> list:
    """Poll a MikroTik RouterOS device directly via the RouterOS API."""
    import librouteros

    host = device.get("ip")
    if not host:
        raise RuntimeError("device has no IP address")
    use_tls = bool(cfg.get("use_tls"))
    port = int(cfg.get("port") or (8729 if use_tls else 8728))
    user = cfg.get("username") or "admin"
    pw = cfg.get("password") or ""

    kwargs = dict(host=host, username=user, password=pw, port=port, timeout=5)
    if use_tls:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_wrapper"] = lambda s: ctx.wrap_socket(s)

    api = librouteros.connect(**kwargs)
    try:
        res = list(api.path("system", "resource"))
        r = res[0] if res else {}
        health = {}
        try:
            for row in api.path("system", "health"):
                if "name" in row and "value" in row:
                    health[row["name"]] = row["value"]
                else:
                    health.update(row)
        except Exception:
            pass
        try:
            leases = list(api.path("ip", "dhcp-server", "lease"))
        except Exception:
            leases = []
        try:
            regs = list(api.path("interface", "wireless", "registration-table"))
        except Exception:
            regs = []
    finally:
        try:
            api.close()
        except Exception:
            pass

    cpu = _num(r.get("cpu-load"))
    total = _num(r.get("total-memory"))
    free = _num(r.get("free-memory"))
    free_pct = round(free / total * 100) if total else None
    temp = health.get("temperature") or r.get("temperature")
    version = r.get("version", "?")
    board = r.get("board-name", "?")
    uptime = r.get("uptime", "?")

    sys_items = [
        _metric("CPU Load", f"{cpu:.0f}%", _st_high(cpu, 70, 90)),
        _metric("Free RAM", f"{free_pct}%" if free_pct is not None else "?", _st_low(free_pct, 20, 10) if free_pct is not None else None),
        _metric("Temperature", f"{temp}°C" if temp not in (None, "") else "n/a", _st_high(temp, 60, 75) if temp not in (None, "") else None),
        _metric("Uptime", uptime),
        _metric("Board", board),
        _metric("RouterOS", version),
    ]
    sections = [_metrics("System", sys_items)]

    if leases:
        rows = [{
            "Address": l.get("address", "?"),
            "MAC": l.get("mac-address", "?"),
            "Host": l.get("host-name", "") or l.get("comment", ""),
            "Status": l.get("status", "?"),
        } for l in leases[:6]]
        sections.append(_table(f"DHCP Leases ({len(leases)} total)",
                               ["Address", "MAC", "Host", "Status"], rows))

    if regs:
        rows = [{
            "Interface": g.get("interface", "?"),
            "MAC": g.get("mac-address", "?"),
            "Signal": str(g.get("signal-strength", "?")),
            "TX/RX": f"{g.get('tx-rate', '?')}/{g.get('rx-rate', '?')}",
        } for g in regs[:6]]
        sections.append(_table(f"Wireless Registrations ({len(regs)})",
                               ["Interface", "MAC", "Signal", "TX/RX"], rows))

    return sections


# ----------------------------------------------------------------- UniFi
def poll_unifi(device: dict, cfg: dict) -> list:
    """Poll a UniFi controller (classic self-hosted or UniFi OS) for this device."""
    import requests
    import urllib3
    urllib3.disable_warnings()

    host = cfg.get("host")
    if not host:
        raise RuntimeError("no controller host configured")
    port = int(cfg.get("port") or 443)
    site = cfg.get("site") or "default"
    verify = bool(cfg.get("verify_tls"))
    user = cfg.get("username")
    pw = cfg.get("password")
    if not (user and pw):
        raise RuntimeError("username/password required (API-key mode not supported in beta)")

    base = f"https://{host}:{port}"
    s = requests.Session()
    s.verify = verify

    prefix, last_err = None, None
    # UniFi OS (UDM/Cloud Key gen2+) then classic controller
    for path, pfx in (("/api/auth/login", "/proxy/network"), ("/api/login", "")):
        try:
            rr = s.post(f"{base}{path}", json={"username": user, "password": pw}, timeout=6)
            rr.raise_for_status()
            tok = rr.headers.get("x-csrf-token") or rr.headers.get("X-CSRF-Token")
            if tok:
                s.headers.update({"X-CSRF-Token": tok})
            prefix = pfx
            break
        except Exception as e:
            last_err = e
    if prefix is None:
        raise RuntimeError(f"controller login failed: {last_err}")

    def _get(pth):
        rr = s.get(f"{base}{prefix}{pth}", timeout=6)
        rr.raise_for_status()
        return rr.json().get("data", [])

    devices = _get(f"/api/s/{site}/stat/device")
    stas = _get(f"/api/s/{site}/stat/sta")

    ip = device.get("ip")
    name = device.get("hostname") or device.get("name")
    match = next((d for d in devices if d.get("ip") == ip), None) \
        or next((d for d in devices if d.get("name") == name), None)

    total_clients = len(stas)
    if not match:
        return [
            _metrics("Controller", [
                _metric("Site", site),
                _metric("Managed Devices", len(devices)),
                _metric("Total Clients", total_clients),
            ]),
            _metrics("Device", [
                _metric("Match", "not found", "warn"),
            ]),
        ]

    fw = match.get("version", "?")
    upgradable = match.get("upgradable")
    uptime = match.get("uptime")
    up_str = f"{int(uptime) // 86400}d" if uptime else "?"
    num_sta = match.get("num_sta", match.get("user-num_sta", "?"))
    model = match.get("model", match.get("type", "?"))

    sections = [
        _metrics("Controller", [
            _metric("Model", model),
            _metric("Firmware", fw + (" ⬆ update" if upgradable else ""), "warn" if upgradable else "ok"),
            _metric("State", "adopted" if match.get("adopted") else "pending", "ok" if match.get("adopted") else "warn"),
            _metric("Uptime", up_str),
            _metric("Clients", num_sta),
        ]),
    ]

    radios = match.get("radio_table_stats") or []
    if radios:
        r0 = radios[0]
        sections.append(_metrics("Radio", [
            _metric("Channel", r0.get("channel", "?")),
            _metric("TX Power", f"{r0.get('tx_power', '?')} dBm"),
            _metric("Clients", r0.get("user-num_sta", num_sta)),
            _metric("Utilization", f"{r0.get('cu_total', '?')}%"),
        ]))

    ap_mac = match.get("mac")
    clients = [c for c in stas if c.get("ap_mac") == ap_mac] if ap_mac else stas
    if clients:
        rows = [{
            "Client": c.get("hostname") or c.get("name") or c.get("mac", "?"),
            "Signal": f"{c.get('signal', '?')} dBm",
            "Down": f"{round(_num(c.get('rx_bytes-r')) / 1e6)}M",
            "Up": f"{round(_num(c.get('tx_bytes-r')) / 1e6)}M",
        } for c in clients[:6]]
        sections.append(_table(f"Clients ({len(clients)})",
                               ["Client", "Signal", "Down", "Up"], rows))

    return sections


# ----------------------------------------------------------------- Cambium
def poll_cambium(device: dict, cfg: dict) -> list:
    """Poll Cambium cnMaestro (on-prem or cloud) for this device."""
    import requests
    import urllib3
    urllib3.disable_warnings()

    base = (cfg.get("base_url") or "").rstrip("/")
    if not base:
        raise RuntimeError("no cnMaestro base_url configured")
    cid = cfg.get("client_id")
    csec = cfg.get("client_secret")
    if not (cid and csec):
        raise RuntimeError("client_id/client_secret required")

    tr = requests.post(f"{base}/api/v2/access/token",
                       data={"grant_type": "client_credentials"},
                       auth=(cid, csec), timeout=6, verify=False)
    tr.raise_for_status()
    token = tr.json().get("access_token")
    if not token:
        raise RuntimeError("no access_token returned")
    headers = {"Authorization": f"Bearer {token}"}

    dr = requests.get(f"{base}/api/v2/devices", params={"limit": 100},
                      headers=headers, timeout=8, verify=False)
    dr.raise_for_status()
    items = dr.json().get("data", []) or []

    ip = device.get("ip")
    name = device.get("hostname") or device.get("name")
    match = next((d for d in items if d.get("ip") == ip or d.get("ip_wan") == ip), None) \
        or next((d for d in items if d.get("name") == name), None)

    if not match:
        return [_metrics("cnMaestro", [
            _metric("Reachable", "yes", "ok"),
            _metric("Devices", len(items)),
            _metric("Match", "not found for this IP/name", "warn"),
        ])]

    mac = match.get("mac")
    stats = {}
    if mac:
        try:
            sr = requests.get(f"{base}/api/v2/devices/{mac}/statistics",
                              headers=headers, timeout=8, verify=False)
            if sr.ok:
                sd = sr.json().get("data", [])
                stats = (sd[0] if isinstance(sd, list) and sd else sd) or {}
        except Exception:
            pass

    fw = match.get("software_version", match.get("active_sw_version", "?"))
    mode = match.get("type", match.get("mode", "?"))
    status = match.get("status", "?")
    radio = stats.get("radio", {}) if isinstance(stats.get("radio"), dict) else {}
    snr = radio.get("dl_snr") or stats.get("snr")
    rssi = radio.get("dl_rssi") or stats.get("rssi")

    sections = [
        _metrics("cnMaestro", [
            _metric("Mode", mode),
            _metric("Status", status, "ok" if str(status).lower() in ("online", "up") else "warn"),
            _metric("Firmware", fw),
        ]),
        _metrics("RF", [
            _metric("SNR", f"{snr} dB" if snr is not None else "n/a", _st_low(snr, 22, 15) if snr is not None else None),
            _metric("RSSI", f"{rssi} dBm" if rssi is not None else "n/a", _st_low(rssi, -68, -74) if rssi is not None else None),
        ]),
    ]
    return sections


POLLERS = {"mikrotik": poll_mikrotik, "ubiquiti": poll_unifi, "cambium": poll_cambium}
