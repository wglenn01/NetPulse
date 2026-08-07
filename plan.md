# plan.md — NetPulse Network Visibility App (FastAPI + MongoDB + React)

## STATUS LOG
- Phase 2 (Main App): BUILT ✔ — Full backend (SNMP/ICMP poller against real snmpsim demo network of 13 devices, topology, alerting+Discord, discovery, metrics, dashboards, settings) + full dark-themed frontend (Overview, animated Topology Map, Devices+discovery+drawer, Alerts+rules, drag/drop Dashboards, NOC/TV mode, Settings). All pages render, 0 compile errors.
- Phase 1 (Core POC): COMPLETE ✔ — `/app/poc/test_core.py` 14/14 checks pass against a real snmpsim v2c agent.
- Topology API port data: COMPLETE ✔ — `GET /api/topology` verified via curl to return per-node `ports[]` and per-edge `a_ifname/b_ifname/speed_mbps/util`.
- Phase A (Console/HUD redesign): COMPLETED ✔ — Green-console + cyan telemetry theme applied app-wide with medium CRT overlay.
- Phase B (Link Labels): COMPLETED ✔ — Edge labels show `portA ⇄ portB · speed` + util/throughput, with a toolbar toggle.
- Phase C (Drag-to-Connect): COMPLETED ✔ — Per-port handles + confirm dialog + link persistence.
- Phase D (Vendor APIs framework + Settings + simulated enrichment): COMPLETED ✔ — Vendor config endpoints + Settings UI + DeviceDrawer enrichment panel (SIMULATED · PREVIEW).
- Phase E (End-to-End Testing): COMPLETED ✔ — `testing_agent_v3` 100% pass (backend 38/38; frontend pass). Demo cleaned back to 12 links.
- **Current focus:** Phase F (P1) — Optional NOC alarm chime + screen flash on NEW device-down while `/tv` open, and a full-screen NOC topology view.

---

## 1) Objectives
### Primary
- Deliver an operator-grade network visibility app for Linux that monitors via **SNMP v2c + ICMP**.
- Provide a **beautiful, sleek, intuitive** interface suitable for daily NOC use and **large-screen wallboard** display:
  - moveable topology map with **animated dashed traffic lines**
  - device inventory + discovery
  - dashboards (customizable, drag/drop)
  - full alerting system with **Discord webhook**
  - NOC/TV mode

### Product requirements (locked)
- **SNMP v2c only**
- **NOC/TV mode**
- **Discord webhook** alerts
- Vendor API integrations framework for **MikroTik**, **UniFi**, **Cambium** (preview uses simulated enrichment payloads)

### Updated objectives (new)
- Improve **wallboard incident signaling**:
  - optional NOC alarm sound (user-armed)
  - photosensitivity-safe screen flash on NEW critical device-down alerts
- Provide **topology map as a full-screen NOC window** (read-only NOC map view)

### Preview compatibility
- Must continue to function in the cloud preview:
  - Realistic SNMP/ICMP demo network using `snmpsim`.
  - Vendor API enrichment must be **SIMULATED** in preview due to private LAN controller access limits.

---

## 2) Implementation Steps

### Phase 1 — Core POC: SNMP/ICMP polling + bandwidth + Discord (isolation)
**Status:** COMPLETE ✔

**Exit criteria (met):**
- `test_core.py` prints valid sysInfo, interface list, changing counters, computed bps, ping stats, and successfully posts (or dry-runs) Discord payload.

---

### Phase 2 — V1 App Development (build around proven core)
**Status:** COMPLETE ✔

**Delivered:**
- Backend: FastAPI + MongoDB models, poller loop, discovery, alerting rules, Discord webhook, topology endpoints.
- Frontend: app shell, overview, animated topology map, device inventory, alerts, dashboards, NOC/TV mode, settings.

---

## Phase A — Futuristic Console/HUD Redesign (COMPLETED ✔, P0)
**Goal:** Redesign UI to look “futuristic and console-like” (medium CRT intensity), per `/app/design_guidelines.md` **NetPulse // CRT-HUD Green Console**.

**User approvals:**
- Do console redesign **FIRST**
- CRT intensity: **Medium**
- Primary accent: **Green**
- Secondary accent / telemetry: **Cyan**

**Implementation (delivered):**
1. Token swap (global theme) in `/app/frontend/src/index.css` (kept token names).
2. CRT/HUD overlay helpers (`.crt-shell`, `.glow-primary`, `.hud-panel`, `.hud-label`, reduced-motion support).
3. Applied `.crt-shell` at app root.
4. Layout/nav/header updated to green active state + HUD labeling.
5. ReactFlow pane, edges, and nodes updated to match the new theme.
6. NOC mode updated to match theme + reduced-motion aware ticker.
7. Page-level consistency pass across app.

**Verification (met):**
- Visual spot-check screenshots across `/`, `/topology`, `/devices`, `/alerts`, `/dashboards`, `/settings`, `/tv`.

---

## Phase B — Link Labels Enhancement (COMPLETED ✔, P0)
**Goal:** Show link labels with **port names + link speed**, optionally toggled in the map toolbar.

**Implementation (delivered):**
- `TrafficEdge.js`: label shows `a_ifname ⇄ b_ifname · speed` + util + throughput.
- `Topology.js`: toolbar toggle `Link Labels` to show all labels.

---

## Phase C — Drag-to-Connect (COMPLETED ✔, P0)
**Goal:** Drag a cable directly between two ports on the topology map; confirm before saving.

**User-approved behavior:**
- On drag connect, open a **confirm dialog** (label + detected speed) before saving.

**Implementation (delivered):**
- `DeviceNode.js`: per-port handle dots (outer wrapper avoids clipping).
- `Topology.js`: `connectionMode=Loose`, `onConnect` opens confirm dialog, POST `/api/links` on confirm.

---

## Phase D — Vendor APIs Framework + Settings Config + Simulated Enrichment (COMPLETED ✔, P1)
**Goal:** Add vendor API integration framework for MikroTik/UniFi/Cambium with a Settings UI.

**Preview constraint:** Cloud preview cannot reach private controllers → enrichment is **SIMULATED** but uses an on-prem-compatible response contract.

**Implementation (delivered):**
- Backend:
  - `vendor_api.py`: deterministic simulated payloads for MikroTik/UniFi/Cambium.
  - `GET/PUT /api/vendor-config`, `POST /api/vendor-config/test`, `GET /api/devices/{id}/enrichment`.
- Frontend:
  - `Settings.js`: Vendor API Integrations section with enable toggles, fields, Test, Save.
  - `DeviceDrawer.js`: Vendor Enrichment panel (badged **SIMULATED · PREVIEW**).

---

## Phase E — End-to-End Testing (COMPLETED ✔, P2)
**Goal:** Run a full regression pass after Phase A–D.

**Result (met):**
- `testing_agent_v3` clean pass (backend 38/38, frontend pass), no issues.

---

## Phase F — NOC Alarm + Full-screen NOC Topology (COMPLETED ✔, P1)
**Goal:** Improve NOC wallboard incident response and add a full-screen topology view for the NOC.

### F1) Optional NOC alarm chime + screen flash on NEW device-down while `/tv` open
**Requirements (locked):**
- **Single “Alarm” toggle** in NOC header (bell icon)
  - OFF by default
  - persisted to `localStorage`
- User gesture requirement:
  - enabling Alarm should create/unlock **WebAudio AudioContext** and play a short confirm blip
- Detection logic:
  - poll `/alerts?state=firing`
  - track **seen critical alert ids** in a `useRef`
  - initialize seen-set on first load so pre-existing downs do **not** alarm on open
  - when a **NEW** critical (device-down) alert appears AND alarm armed:
    - play synthesized alarm chime (square-wave 3-beep)
    - trigger screen flash overlay
- Flash overlay:
  - fixed `inset-0`, red (`--status-crit`), `pointer-events:none`, `z-45` (above content, below modals)
  - ~1.4s pulse animation
  - `prefers-reduced-motion`: single gentle fade (photosensitivity-safe)

**Implementation steps:**
1. **CSS**: `/app/frontend/src/index.css`
   - add `.noc-flash` keyframes + reduced-motion variant.
2. **NOC UI toggle**: `/app/frontend/src/pages/NocMode.js`
   - add Alarm toggle (bell icon) in header.
   - persist to localStorage.
3. **WebAudio alarm**: `/app/frontend/src/pages/NocMode.js`
   - on arm: instantiate AudioContext; play short “armed” blip.
   - on new critical device-down: play 3-beep square-wave pattern.
4. **New-alert detection**: `/app/frontend/src/pages/NocMode.js`
   - maintain a `seenAlertIdsRef`.
   - on first alerts load: seed ref and do nothing.
   - on subsequent polls: diff → if new matching critical-down → trigger alarm+flash.

**Testing / verification:**
- Manual + screenshot:
  - toggle Alarm ON (blip)
  - simulate or force a new device-down alert (or temporarily create a test alert) → confirm flash overlay and audible alarm.
  - ensure no alarm on first open when downs already exist.

### F2) Full-screen NOC topology view
**Requirements (locked):**
- Add read-only full-screen topology map as a NOC window.

**Implementation steps:**
1. Create `/app/frontend/src/components/topology/NocMap.js`
   - reuse `DeviceNode` + `TrafficEdge`
   - polls `/topology` every 4s
   - labels always on
   - **read-only**:
     - `nodesConnectable={false}`
     - `elementsSelectable={false}`
     - `nodesDraggable={false}`
   - `fitView`, Background dots, large Legend
   - uses backend-provided `x/y` saved positions
2. Update `/app/frontend/src/pages/NocMode.js`
   - add **Panels ↔ Map** segmented toggle in header
   - initialize from query param `?view=map` via `useSearchParams`
   - Panels view keeps auto-rotation
   - Map view disables rotation and hides page dots
   - Alarm + flash + ticker remain active in BOTH views
3. Update `/app/frontend/src/pages/Topology.js`
   - add a “NOC Map” launch button on toolbar that navigates to `/tv?view=map`

**Testing / verification:**
- Screenshot `/tv?view=map` shows full-screen topology.
- Confirm ticker remains visible and alarms work while in map view.

---

## 3) Next Actions (Updated)
1. **Phase F (P1):** NOC alarm sound + red flash overlay on NEW device-down alerts.
2. **Phase F (P1):** Full-screen NOC topology view (`/tv?view=map`) + Topology toolbar launcher.
3. **Phase G (P2):** Optional enhancements after Phase F:
   - Link throughput history charts on edge click
   - alert sound profiles + quiet hours
   - map auto-layout button

---

## 4) Success Criteria (Updated)
- UI redesign:
  - Green-console + cyan telemetry theme applied app-wide
  - medium CRT overlay visible but does not hurt readability
  - `/tv` is wallboard-readable with reduced clutter
- Topology:
  - Link labels show port names + speed and remain legible
  - Drag-to-connect between specific ports works with confirm dialog
- Vendor APIs:
  - Settings config UI exists for MikroTik/UniFi/Cambium
  - Preview shows simulated enrichment data per device (clearly labeled)
  - On-prem deployment can swap simulated feed for real controller polling without changing UI contracts
- NOC wallboard (NEW):
  - Alarm is OFF by default and can be armed via explicit user gesture
  - When armed, a **NEW** critical device-down alert triggers:
    - audible 3-beep chime
    - photosensitivity-safe red flash overlay
  - No false alarm on initial `/tv` load with pre-existing downs
  - `/tv?view=map` provides a read-only full-screen topology view with labels always on
- Reliability:
  - SNMP dispatcher sockets always closed (no FD leaks)
  - snmpsim demo remains stable (HOME env preserved)
  - Alerts continue to dispatch to Discord correctly when configured

## Phase G — Productionization + Self-host Packaging (COMPLETED ✔)
- Added `DEMO_MODE` env switch (db.py). Preview keeps `DEMO_MODE=true` (13-device snmpsim demo + simulated vendor feed). Production package sets `DEMO_MODE=false` → no snmpsim, no demo seed, clean/empty inventory, prod discovery defaults (161).
- Real vendor polling (BETA) in `backend/vendor_clients.py`: MikroTik (librouteros), UniFi (controller REST, classic + UniFi OS), Cambium (cnMaestro OAuth2). `build_enrichment` = simulated when demo, real when prod, with 9s timeout + graceful `available:false`+reason on any failure (verified never raises).
- Layout footer shows Demo vs Live based on settings.demo_mode.
- Docker Compose package: `docker-compose.yml` (mongo+backend+frontend), `deploy/backend.Dockerfile`, `deploy/frontend.Dockerfile` (nginx serves SPA + proxies `/api` same-origin so it's server-IP agnostic), `deploy/nginx.conf`, curated `deploy/requirements.txt` (excludes preview-only/private pkgs), `.env.docker.example`, `.dockerignore`. ICMP handled via `cap_add: NET_RAW` + `net.ipv4.ping_group_range` sysctl.
- `DEPLOYMENT.md`: full Ubuntu + Docker Compose guide (LAN/HTTP), first-run config, SNMP/vendor setup, ops/backups/troubleshooting.
- Code transfer: via GitHub (Save to GitHub → clone on server).

## Phase H — Add Device: Detailed Error Reporting (COMPLETED ✔, P0)
**Goal (user request):** "When adding a device I need better error reporting as to why it failed to add."

**Implementation (delivered):**
- Backend `POST /api/devices` (`server.py`): full validation + **pre-flight reachability check** before insert, returning structured `HTTPException` detail `{code,title,message,can_force}`:
  - `invalid_ip` (400) — bad IP format
  - `validation` (400) — missing name
  - `invalid_port` (400) — SNMP port out of range
  - `duplicate` (409) — same IP+SNMP port already monitored (names the existing device)
  - `icmp_unreachable` (400) — no ping reply (can_force)
  - `snmp_failed` (400) — pings but SNMP v2c GET failed; names community/port to check (can_force)
  - Added `force: bool` to `DeviceCreate` to skip the pre-flight and add anyway.
  - `_preflight_device()` helper runs ICMP then SNMP v2c using the same engine as the poller; uses `snmp_timeout` from settings.
  - `discovery/add` now dedupes existing IP+port and returns `{added, skipped}`.
- Frontend `Devices.js` (`AddDeviceDialog`): `parseApiError()` reads `detail` (object or string); shows an inline themed destructive `Alert` with title + message; **"Add anyway (skip check)"** button when `can_force`; button shows a "Verifying…" spinner during the pre-flight. Discovery toast now reports added/skipped and parses errors.

**Verification (met):**
- Backend curl: all 8 paths verified (invalid IP, missing name, bad port, ICMP unreachable, SNMP failed, happy path vs demo sim, duplicate 409, force override 200).
- Frontend screenshot: inline "HOST UNREACHABLE" alert + Add-anyway button render correctly in the CRT theme; test devices cleaned up.

### Phase H.2 — Robustness refinement (COMPLETED ✔) after user report of generic error on self-hosted Docker
- Root cause (self-host): first version's pre-flight ran a **full SNMP interface walk** + required ICMP-first. On a real device with a large iface table the walk could overrun nginx's 65s proxy timeout → 504 HTML → browser had no JSON `detail` → generic fallback shown.
- Fixes:
  - Added `snmp_engine.snmp_probe()` — lightweight single GET of sysDescr/sysName (no walks). Happy path ~0.3s.
  - Rewrote `_preflight_device()` to be **SNMP-first**: SNMP OK ⇒ accept (even if ICMP blocked); only if SNMP fails do we ping to classify `snmp_failed` (pings) vs `unreachable` (no ping). Timeouts trimmed (SNMP retries=0, ICMP count=1) ⇒ worst case ~3s.
  - Wrapped pre-flight in `create_device` so unexpected errors return a clean 400 (`preflight_error`, can_force) instead of a bare 500.
  - Frontend `parseApiError()` now distinguishes: no-response (network/timeout), non-JSON 5xx (offers Add-anyway), object detail, and string detail — no more misleading generic message.
- Verified via curl: happy ~0.36s (200), reachable+wrong-SNMP ~4.5s→snmp_failed(400), fully-unreachable ~3.4s→unreachable(400).

### Phase H.3 — Self-host 502 root cause: backend crash-loop (COMPLETED ✔)
- User's self-hosted Docker backend was `Restarting (1)` → every `/api` call returned **502** (not an Add-Device bug).
- Real cause (from `docker compose logs backend`): `ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'`. `deploy/requirements.txt` pinned `motor==3.3.1` but left **pymongo unpinned**, so pip installed pymongo 4.9+ which dropped the symbol motor 3.3.1 imports → app couldn't load.
- Fix: pinned **`pymongo==4.6.3`** in `deploy/requirements.txt` (matches the working preview: motor 3.3.1 + pymongo 4.6.3).
- Also hardened `deploy/nginx.conf`: re-resolve `backend` via Docker DNS (127.0.0.11) using a variable in `proxy_pass` so a backend restart never causes persistent 502s; bumped read/send timeouts to 120s.
- User action: Save to GitHub → on server `git pull` → `docker compose up -d --build` (requirements change forces backend image rebuild with correct pymongo).

## Pending / Next
- **Topology Map "Tidy" button (P1, NOT STARTED):** one-click auto-layout arranging nodes by role (core → dist → AP → CPE) and clearing overlaps in `frontend/src/pages/Topology.js` (dagre or role-based heuristic). Requested by user earlier; deferred during deployment work.


