# plan.md — Network Visibility App (FastAPI + MongoDB + React)

## STATUS LOG
- Phase 2 (Main App): BUILT ✔ — Full backend (SNMP/ICMP poller against real snmpsim demo network of 13 devices, topology, alerting+Discord, discovery, metrics, dashboards, settings) + full dark-themed frontend (Overview, animated Topology Map, Devices+discovery+drawer, Alerts+rules, drag/drop Dashboards, NOC/TV mode, Settings). All pages render, 0 compile errors. Next: automated E2E testing.
- Phase 1 (Core POC): COMPLETE ✔ — `/app/poc/test_core.py` 14/14 checks pass against a real snmpsim v2c agent.

## 1) Objectives
- Deliver a dark-themed network visibility app for Linux that monitors via **SNMP v2c + ICMP**, supports **auto-discovery + manual devices**, shows a **moveable topology map with animated dashed traffic edges**, provides **alerting (in-app + Discord webhook)**, and offers **custom dashboards + NOC/TV mode**.
- **Preview-compatible**: include an SNMP/ICMP **simulator + demo dataset** so the cloud preview fully works; same poller can be pointed at real devices when deployed on-prem.
- Prove the **core polling + bandwidth delta + alert dispatch** in isolation **before** building the full app UI.

## 2) Implementation Steps

### Phase 1 — Core POC: SNMP/ICMP polling + bandwidth + Discord (isolation)
**User stories**
1. As a user, I want to poll a device’s sysInfo via SNMP so I can validate connectivity and identity.
2. As a user, I want to walk interface tables so I can see ports, statuses, and speeds.
3. As a user, I want bandwidth (bps in/out) computed from counter deltas so I can see real utilization.
4. As a user, I want ICMP latency/loss so I can detect partial outages and poor links.
5. As a user, I want an alert payload built and sent to Discord so my NOC gets notified.

**Steps**
1. Web-search quick validation (best practices/known pitfalls): pysnmp asyncio hlapi v1arch usage, snmpsim counter variation modules, ICMP permissions/capabilities.
2. Add **snmpsim-command-responder** with demo device profiles (Mikrotik/Cambium/Mimosa/Ubiquiti-like) and ensure **ifHCIn/OutOctets increase over time**.
3. Implement `test_core.py` (single script) that:
   - Starts/targets snmpsim agents (or assumes running) and runs SNMP v2c GET: `sysDescr/sysName/sysUpTime/sysLocation/sysContact`.
   - WALK: `ifDescr/ifName/ifAdminStatus/ifOperStatus/ifHighSpeed/ifHCInOctets/ifHCOutOctets`.
   - Poll twice with known interval; compute per-iface `bps_in/bps_out` and utilization.
   - Run ICMP ping (icmplib; fallback to system ping if raw sockets blocked).
   - Build Discord webhook payload + send if URL present (else print).
4. **Fix until POC passes** (no app work until: stable walks, sane deltas, no blocking, errors handled).

**Exit criteria**
- `test_core.py` prints valid sysInfo, interface list, changing counters, computed bps, ping stats, and successfully posts (or dry-runs) Discord payload.

---

### Phase 2 — V1 App Development (build around proven core)
**User stories**
1. As a user, I want to add a device manually (IP, name, vendor, SNMP community) and see it turn green when reachable.
2. As a user, I want to scan a CIDR range to discover devices and quickly add them.
3. As a user, I want a topology map where I can drag devices and see animated dashed edges when traffic is active.
4. As a user, I want an alerts page that shows active/resolved alerts and sends critical ones to Discord.
5. As a user, I want a large-screen NOC/TV mode that auto-rotates panels and is readable from far away.

**Backend (FastAPI + MongoDB)**
1. Data models/collections:
   - `devices` (ip, name, vendor, type, snmp community/port, coords, poll interval, enabled)
   - `interfaces` (deviceId, ifIndex, names, speed, admin/oper)
   - `metrics` (deviceId, ifIndex?, ts, in_bps/out_bps, util%, oper/admin, latency_ms, loss%)
   - `links` (a_device/ifIndex, b_device/ifIndex, label, enabled)
   - `alerts` (ruleId, entity, state firing/resolved, firstSeen/lastSeen, severity, message)
   - `rules` (thresholds for down/latency/loss/util/ifOper)
   - `dashboards` + `noc_playlists`
2. Polling engine:
   - Async poller loop (single scheduler) using **pysnmp asyncio hlapi v1arch** + ICMP.
   - Store latest snapshot + time-series points; compute bps from last counters.
   - Demo mode: route polling to **snmpsim endpoints** + synthetic ICMP results in preview.
3. Discovery:
   - ICMP sweep of CIDR → candidate IPs → SNMP probe `sysDescr/sysName` to fingerprint vendor.
   - Bulk-add discovered devices.
4. Alerting:
   - Rule evaluation on each poll; state machine (firing/resolved), dedupe, cooldown.
   - Discord webhook dispatch (config + test endpoint) + in-app feed.
5. API endpoints (MVP): devices CRUD, discovery run/status, links CRUD, map positions update, metrics queries (latest + timeseries), alerts/rules CRUD, dashboards save/load, NOC playlists.

**Frontend (React, dark theme)**
1. App shell: dark NOC aesthetic, left nav (Overview, Map, Devices, Alerts, Dashboards, NOC Mode, Settings).
2. Overview: fleet health tiles, active alerts feed, top interfaces by utilization, small charts.
3. Map (react-flow / @xyflow/react):
   - Vendor-styled nodes with status color; draggable positions persisted.
   - Edges represent `links`; **animated dashed moving lines** when link traffic > threshold; speed/opacity scales with utilization.
   - Click node → side drawer: sysInfo, ping stats, interface table + mini charts.
4. Devices: table + add/edit; per-device page with interfaces + history charts.
5. Alerts: active + history; acknowledge/silence (MVP); rules CRUD; Discord webhook settings + test.
6. Dashboards: react-grid-layout widgets (status tile, time-series, top-N, alerts feed, map embed) with save/load.
7. NOC/TV mode: full-screen panels (overview tiles, map, alerts ticker) with auto-rotate playlist.

**End of Phase 2 testing**
- Run one end-to-end testing round: add device (demo), see metrics populate, traffic animation on map, trigger alert, verify Discord webhook (if configured), verify NOC mode rotation.

---

### Phase 3 — Hardening + feature expansion (still SNMP/ICMP only)
**User stories**
1. As a user, I want per-site/groups so I can organize devices by region/tower/customer.
2. As a user, I want alert suppression schedules so maintenance doesn’t spam Discord.
3. As a user, I want better link inference helpers so I can build topology faster.
4. As a user, I want retention controls so MongoDB storage stays bounded.
5. As a user, I want exports (CSV/JSON) for devices, alerts, and interface inventory.

**Steps**
1. Improve vendor fingerprinting heuristics from `sysDescr` patterns (Mikrotik/Cambium/Mimosa/Ubiquiti).
2. Add alert enhancements: severity levels, routing, maintenance windows, per-rule cooldown.
3. Metrics/query performance: indexes, downsampling option, “latest” cache.
4. Map UX polish: bulk layout tools, edge labeling, offline/unknown states.
5. Packaging: docker-compose for on-prem (api + ui + mongo + optional snmpsim demo), env-based config.
6. End-to-end testing round.

---

### Phase 4 — Later (optional): Vendor APIs + Auth
**User stories**
1. As a user, I want RouterOS API enrichment so I get deeper Mikrotik metrics.
2. As a user, I want UniFi/cnMaestro integration so inventory matches controllers.
3. As a user, I want user accounts/roles so NOC staff have controlled access.
4. As a user, I want audit logs so changes are traceable.
5. As a user, I want multi-tenant/sites separation if I manage multiple networks.

## 3) Next Actions
1. Implement snmpsim demo agents + `.snmprec` data + counter-variation so counters grow.
2. Implement `test_core.py` and iterate until all POC exit criteria pass.
3. Scaffold FastAPI + MongoDB models + poller service (reusing proven POC functions).
4. Build React shell + Overview + Map (animated dashed edges) + Devices + Alerts.
5. Add dashboards + NOC/TV mode + final V1 testing.

## 4) Success Criteria
- POC: reliable SNMP GET/WALK, bandwidth delta correct, ICMP latency/loss reported, Discord webhook payload works.
- V1: devices can be discovered/added, polled continuously, metrics stored and charted; topology map animates active links; alerting works in-app + Discord; dashboards save/load; NOC/TV mode runs full-screen and rotates panels.
- On-prem deploy: switching config to real subnets/devices works without code changes (env-based settings).