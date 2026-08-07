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
