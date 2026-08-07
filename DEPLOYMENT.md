# NetPulse — Deploy on Ubuntu (Docker Compose)

Self-hosted network visibility for your WISP/ISP: SNMP v2c + ICMP monitoring, live
topology map, alerting (Discord), customizable dashboards, and a NOC/TV wallboard.

This guide deploys NetPulse on a single Ubuntu server for **LAN access over HTTP**
(`http://<server-ip>`). Three containers run behind one web port:

```
        ┌────────────────────────────────────────────────────┐
Browser │  frontend (nginx :80)  ──/api/──▶  backend (:8001)  │
 :80 ───▶  serves React SPA                    │              │
        │                                       ▼              │
        │                                 mongo (:27017)       │
        └────────────────────────────────────────────────────┘
        backend also polls your devices:  SNMP/UDP 161 · ICMP · vendor APIs
```

---

## 1. Prerequisites

- Ubuntu 20.04 / 22.04 / 24.04 (a small VM is fine: 2 vCPU / 2 GB RAM / 10 GB disk).
- The server must be able to reach your network gear (UDP **161** for SNMP, ICMP for
  ping) and any vendor controllers you enable.
- Docker Engine + the Compose plugin.

Install Docker (official convenience script):

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER    # then log out/in so 'docker' works without sudo
docker version && docker compose version
```

---

## 2. Get the code (GitHub)

Push this project to GitHub from Emergent (**Save to GitHub**), then on the server:

```bash
cd /opt
sudo git clone https://github.com/<your-org>/<your-repo>.git netpulse
sudo chown -R $USER:$USER netpulse
cd netpulse
```

> Updating later: `git pull && docker compose up -d --build`

---

## 3. Configure

```bash
cp .env.docker.example .env
nano .env
```

Set at minimum:

| Variable              | What to set                                                        |
|-----------------------|--------------------------------------------------------------------|
| `MONGO_ROOT_PASSWORD` | A strong password (DB is internal-only, but still set it).         |
| `DEMO_MODE`           | **`false`** — monitor your real network (this removes all demo data).|
| `HTTP_PORT`           | `80` (or e.g. `8080` if 80 is taken).                              |
| `TZ`                  | Your timezone, e.g. `America/New_York` (affects alert timestamps). |

With `DEMO_MODE=false` the app starts with an **empty inventory** — no simulated
devices, no fabricated stats. You add your real devices in step 5.

---

## 4. Build & start

```bash
docker compose up -d --build
```

First build takes a few minutes (frontend compile + image pulls). Check status/logs:

```bash
docker compose ps
docker compose logs -f backend     # Ctrl-C to stop following
```

Open the UI:

```
http://<server-ip>          # or http://<server-ip>:<HTTP_PORT>
```

Allow the port through the firewall if `ufw` is enabled:

```bash
sudo ufw allow 80/tcp        # match HTTP_PORT
```

---

## 5. First-run configuration (in the UI)

1. **Settings → SNMP & Polling** — set your default SNMP **v2c community** (e.g.
   `public`) and poll interval. NetPulse uses SNMP **v2c only**.
2. **Add your devices** — either:
   - **Devices → Add Device** (hostname, IP, vendor, role, community), or
   - **Settings → Discovery** — set your subnet (e.g. `192.168.88.0/24`), port `161`,
     community, then run discovery to auto-add responders.
3. **Topology Map** — drag nodes to arrange; drag a port dot to another to create
   links (with speed/label). Toggle **Link Labels** to show port names + speeds.
4. **Settings → Alerting & Discord** — paste your Discord **webhook URL** and hit
   *Test*. Tune thresholds (latency, loss, utilization).
5. **NOC / TV Mode** (`/tv`) — full-screen wallboard. Use the **Panels ⇄ Map** switch,
   and the **Alarm** toggle to arm the chime + red flash on a device-down.
6. **Settings → Vendor API Integrations** (optional, see below).

### Make sure SNMP is enabled on your gear
- **MikroTik (RouterOS v7):**
  ```
  /snmp community add name=public addresses=<netpulse-server-ip>/32
  /snmp set enabled=yes contact="noc" location="core"
  ```
- **UniFi / Cambium / Mimosa:** enable SNMP v2c with a read community and allow the
  NetPulse server's IP.

---

## 6. Vendor API live polling (BETA)

`Settings → Vendor API Integrations`. Enable a vendor, enter its details, click
**Test**, then **Save**. Enriched stats then appear in each device's drawer.

> ⚠️ **Beta:** live polling clients (MikroTik/UniFi/Cambium) are new and best
> validated against your own gear. They **fail gracefully** — if a controller is
> unreachable, the device drawer simply shows a reason instead of stats, and the core
> SNMP/ICMP monitoring is never affected.

- **MikroTik (RouterOS API):** enable the API service on each router/switch:
  ```
  /ip service enable api            # TCP 8728 (or api-ssl / 8729 with "Use TLS")
  /ip service set api address=<netpulse-server-ip>/32
  ```
  NetPulse connects to **each device's own IP** using the username/password you set.
- **UniFi Controller:** enter the controller host/port (usually `443`), site, and a
  read-only **username/password** (classic self-hosted controllers and UniFi OS are
  both attempted). API-key-only mode is not supported in this beta.
- **Cambium cnMaestro:** enter the base URL and an API **Client ID / Client Secret**
  (cnMaestro → App Client). On-prem and cloud cnMaestro are supported.

---

## 7. Operations

```bash
# Logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart / stop / start
docker compose restart backend
docker compose down             # stop (keeps data volume)
docker compose up -d            # start

# Update to a new version
git pull && docker compose up -d --build
```

### Backups (MongoDB data)
Data lives in the `netpulse_mongo_data` volume.

```bash
# Dump to ./backup
docker compose exec mongo sh -c \
  'mongodump --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive' \
  > netpulse-$(date +%F).archive

# Restore
cat netpulse-YYYY-MM-DD.archive | docker compose exec -T mongo sh -c \
  'mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive'
```

---

## 8. Troubleshooting

- **A device shows DOWN / no SNMP:** confirm the community matches, SNMP v2c is
  enabled, and the device allows UDP 161 from the server IP:
  `docker compose exec backend python -c "import asyncio,icmplib;print('ok')"`
  and test SNMP from the host: `snmpwalk -v2c -c public <device-ip> 1.3.6.1.2.1.1`.
- **Everything is DOWN:** likely a firewall between the server and your gear, or the
  server can't route to that VLAN. Check `ip route` and switch/router ACLs.
- **ICMP/ping issues:** the backend service already runs with `NET_RAW` +
  `net.ipv4.ping_group_range` (see `docker-compose.yml`). On locked-down hosts that
  block namespaced sysctls, remove the `sysctls:` block and keep `cap_add: [NET_RAW]`.
- **Vendor drawer shows an error reason:** that's the beta client reporting why it
  couldn't reach/parse the controller (timeout, auth, path). Verify the API service,
  credentials, and reachability. It never blocks SNMP monitoring.
- **UI loads but API calls fail:** `docker compose logs backend`; ensure the `mongo`
  container is healthy and `MONGO_URL` in compose matches your `.env` credentials.

---

## 9. Security notes

This setup is intended for a **trusted LAN over HTTP**. Before exposing it beyond your
LAN, put it behind a VPN or a TLS-terminating reverse proxy, and restrict
`CORS_ORIGINS` to your real origin. MongoDB is not published to the host by default.
