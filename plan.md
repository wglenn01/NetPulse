# plan.md — NetPulse Network Visibility App (FastAPI + MongoDB + React)

## STATUS LOG
- Phase 2 (Main App): BUILT ✔ — Full backend (SNMP/ICMP poller against real snmpsim demo network of 13 devices, topology, alerting+Discord, discovery, metrics, dashboards, settings) + full dark-themed frontend (Overview, animated Topology Map, Devices+discovery+drawer, Alerts+rules, drag/drop Dashboards, NOC/TV mode, Settings). All pages render, 0 compile errors.
- Phase 1 (Core POC): COMPLETE ✔ — `/app/poc/test_core.py` 14/14 checks pass against a real snmpsim v2c agent.
- Topology API port data: COMPLETE ✔ — `GET /api/topology` verified via curl to return per-node `ports[]` and per-edge `a_ifname/b_ifname/speed_mbps/util`.
- Current focus: **User-approved continuation** — Futuristic Console/HUD Redesign FIRST (P0), then map enhancements (Link Labels + Drag-to-Connect), then Vendor API framework + Settings + simulated enrichment feed.

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

**Implementation**
1. **Token swap (global theme)**
   - Update `/app/frontend/src/index.css`:
     - Overwrite existing `:root` token **VALUES** (keep names) using the provided HSL values.
     - Add new tokens:
       - `--hud-grid`, `--hud-glow`, `--hud-glow-cyan`, `--tv-safe`, `--panel-tint`, `--panel-tint-2`.

2. **CRT/HUD global overlays & helpers**
   - Add `.crt-shell` overlay (scanlines + subtle grid + vignette) per guideline snippet:
     - `pointer-events: none`
     - `position: fixed`
     - reduced-motion aware
   - Add optional utility classes/snippets:
     - `.glow-primary`
     - `.hud-panel` corner brackets
     - `::selection`
     - optional HUD label helper class (mono uppercase + tracking)

3. **Apply `.crt-shell` wrapper**
   - Wrap app root with `.crt-shell` (either in `App.js` root wrapper or within `Layout.js` top-level wrapper) so overlay covers all routes including `/tv`.

4. **App chrome updates (Layout + nav + header)**
   - Update `/app/frontend/src/components/Layout.js`:
     - logo background: shift to green-forward (remove cyan gradient dominance)
     - active nav state: add green bar + glow treatment
     - promote mono HUD labels where appropriate (header labels)

5. **Topology map visual alignment**
   - Update `/app/frontend/src/index.css` ReactFlow section:
     - `.react-flow__pane` background to greenish near-black + faint green/cyan radials
     - edge glow colors aligned to `--traffic-active` (cyan)
   - Update `/app/frontend/src/components/topology/DeviceNode.js`:
     - HUD-like node header style, green focus/selection glow

6. **NOC / TV mode theme alignment**
   - Update `/app/frontend/src/pages/NocMode.js`:
     - logo gradient and any hardcoded cyan accent should match green primary + cyan secondary
     - ensure TV-safe readability (larger type, reduced fine borders)
     - respect reduced-motion for ticker/marquee

7. **Page-level consistency pass**
   - Review all pages and shared components:
     - Overview, Devices, Alerts, Dashboards, Settings, DeviceDrawer
   - Remove/adjust any hardcoded hues that conflict with the new token scheme.

**Testing / Verification**
- Frontend builds with no errors.
- Visual spot-check via screenshots for:
  - `/` Overview
  - `/topology`
  - `/devices`
  - `/alerts`
  - `/dashboards`
  - `/settings`
  - `/tv`

---

## Phase B — Link Labels Enhancement (COMPLETED ✔, P0)
**Goal:** Show link labels with **port names + link speed**, optionally toggled in the map toolbar.

**Pre-req:** Backend already returns `a_ifname`, `b_ifname`, `speed_mbps`, `util`, `in_bps/out_bps`.

**Implementation**
1. Update `/app/frontend/src/components/topology/TrafficEdge.js`:
   - Extend label to include:
     - `a_ifname → b_ifname`
     - `speed_mbps` (format: `10G`, `1G`, `300M`)
     - keep util + throughput
   - Add a UI toggle (“Show link labels”) in `Topology.js` toolbar and pass into edge data.

2. Ensure label does not clutter wallboard:
   - show only when active/warn/crit/down by default
   - allow user toggle to always show or show-on-activity

**Testing**
- Confirm labels render and update on live utilization.

---

## Phase C — Drag-to-Connect (COMPLETED ✔, P0)
**Goal:** Drag a cable directly between two ports on the topology map; replace/augment modal flow.

**Behavior (user-approved):**
- On drag connect, open a **small confirm popover** (label + optional speed) before saving.

**Implementation**
1. Enable connection in ReactFlow
   - In `/app/frontend/src/pages/Topology.js`:
     - set `nodesConnectable={true}`
     - implement `onConnect` handler

2. Add dynamic port handles to device nodes
   - In `/app/frontend/src/components/topology/DeviceNode.js`:
     - Use `data.ports[]` to render a set of `<Handle>` elements
     - Use stable handle IDs, e.g. `${deviceId}:${portName}`
     - Decide handle placement strategy (left/right column; cap visible handles + overflow UI if needed)

3. Confirm popover
   - On connect attempt:
     - open a `Popover` anchored near cursor or centered on canvas
     - prefill fields:
       - Device A, Port A, Device B, Port B
       - optional label
       - optional speed field (informational or user-entered)
     - on confirm: POST `/api/links`

4. Keep existing LinkManager dialog
   - Keep `/app/frontend/src/components/topology/LinkManager.js` as a fallback and bulk link manager.

**Testing**
- Create links via drag-to-connect and verify:
  - link persists in backend
  - topology refresh shows new edge
  - edge label and traffic animation behave

---

## Phase D — Vendor APIs Framework + Settings Config + Simulated Enrichment (COMPLETED ✔, P1)
**Goal:** Add vendor API integration framework for MikroTik/UniFi/Cambium with a Settings UI.

**Preview constraint:** Cloud preview cannot reach private controllers → enrichment data must be **SIMULATED** but delivered through the same API shape used on-prem.

**Backend implementation**
1. Create `vendor_api.py`
   - Define config models and simulated pollers:
     - MikroTik: CPU/RAM/temp, DHCP leases, wireless registrations, firmware
     - UniFi: client counts, AP signal, adoption/health summary
     - Cambium: SM count, RF SNR/RSSI, AP status summary

2. Add persistence
   - New `vendor_configs` collection:
     - store config only (per user: “config only until deploy”)
     - support enable/disable per integration

3. New endpoints
   - `GET /api/vendor-config` (all integrations)
   - `PUT /api/vendor-config`
   - `POST /api/vendor-config/test` (optional: validate shape; in preview return simulated success)
   - `GET /api/devices/{id}/enrichment`
     - return deterministic simulated payload based on device vendor + id

4. UI integration points
   - Merge enrichment into `DeviceDrawer` view (clearly marked “Simulated (Preview)”):
     - add a new section/tab for “Enrichment”

**Frontend implementation**
1. Update `/app/frontend/src/pages/Settings.js`
   - Add “Vendor API Integrations” section:
     - MikroTik / UniFi / Cambium config forms (URL, username, tokens, etc.)
     - **store but do not require secrets** in preview; label clearly as “Config only until deploy”
     - include enable toggles + test buttons

2. Update `/app/frontend/src/components/DeviceDrawer.js`
   - Call enrichment endpoint when drawer open.
   - Render a compact enrichment panel with mono HUD labels.

**Testing**
- Validate endpoint responses via curl.
- Confirm Settings saves configs and Drawer displays enrichment.

---

## Phase E — End-to-End Testing (P2)
**Goal:** Run a full regression pass after Phase A–D.

**Steps**
1. Run `testing_agent_v3` (backend + frontend).
2. Fix all issues found.
3. Re-run tests until clean.

---

## 3) Next Actions (Updated)
1. **Phase A (P0):** Apply CRT-HUD Green Console redesign (tokens + overlays + chrome + map styling + TV mode).
2. **Phase B (P0):** Link Labels (port names + speed + toggle).
3. **Phase C (P0):** Drag-to-Connect (dynamic handles + confirm popover + save link).
4. **Phase D (P1):** Vendor API framework + Settings + simulated enrichment feed + DeviceDrawer integration.
5. **Phase E (P2):** End-to-end testing.

---

## 4) Success Criteria (Updated)
- UI redesign:
  - Green-console + cyan telemetry theme applied app-wide
  - medium CRT overlay visible but does not hurt readability
  - `/tv` is wallboard-readable with reduced clutter
- Topology:
  - Link labels show port names + speed and remain legible
  - Drag-to-connect between specific ports works with confirm popover
- Vendor APIs:
  - Settings config UI exists for MikroTik/UniFi/Cambium
  - Preview shows simulated enrichment data per device (clearly labeled)
  - On-prem deployment can swap simulated feed for real controller polling without changing UI contracts
- Reliability:
  - SNMP dispatcher sockets always closed (no FD leaks)
  - snmpsim demo remains stable (HOME env preserved)
  - Alerts continue to dispatch to Discord correctly when configured
