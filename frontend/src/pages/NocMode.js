import React, { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { usePoll } from '@/lib/api';
import { fmtBps, utilColor, severityColor, VENDOR_LABEL, vendorColor, REDUCED_MOTION } from '@/lib/format';
import { NocMap } from '@/components/topology/NocMap';
import { X, Server, WifiOff, Bell, Gauge, LayoutGrid, Network, BellRing, BellOff } from 'lucide-react';

function Clock() {
  const [t, setT] = useState(new Date());
  useEffect(() => { const i = setInterval(() => setT(new Date()), 1000); return () => clearInterval(i); }, []);
  return <div className="font-mono tabular text-2xl">{t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</div>;
}

function BigTile({ label, value, accent, Icon }) {
  return (
    <div className="rounded-2xl bg-card/80 border border-primary/15 p-8 flex flex-col justify-between hud-panel" style={{ boxShadow: '0 0 0 1px hsl(var(--primary) / 0.08), 0 12px 40px rgba(0,0,0,0.45)' }}>
      <div className="flex items-center justify-between"><span className="hud-label !text-sm">{label}</span><Icon size={28} style={{ color: accent }} /></div>
      <div className="text-6xl font-mono font-semibold tabular mt-4" style={{ color: accent, textShadow: `0 0 24px ${accent}55` }}>{value}</div>
    </div>
  );
}

function PanelFleet({ ov }) {
  const c = ov?.counts || {}; const bw = ov?.bandwidth || {}; const vendors = ov?.vendors || {};
  return (
    <div className="h-full grid grid-rows-[auto_1fr] gap-6">
      <div className="grid grid-cols-4 gap-6">
        <BigTile label="Online" value={c.up ?? '—'} accent="hsl(var(--status-ok))" Icon={Server} />
        <BigTile label="Down" value={c.down ?? '—'} accent="hsl(var(--status-crit))" Icon={WifiOff} />
        <BigTile label="Active Alerts" value={c.active_alerts ?? '—'} accent="hsl(var(--status-warn))" Icon={Bell} />
        <BigTile label="Aggregate" value={fmtBps(bw.total_bps)} accent="hsl(var(--traffic-active))" Icon={Gauge} />
      </div>
      <div className="rounded-2xl bg-card/80 border border-primary/15 p-8 hud-panel">
        <div className="hud-label !text-base mb-6">Fleet by Vendor</div>
        <div className="grid grid-cols-4 gap-6">
          {Object.entries(vendors).map(([v, n]) => (
            <div key={v} className="flex items-center gap-4">
              <span className="w-3 h-12 rounded-full" style={{ background: vendorColor(v) }} />
              <div><div className="text-4xl font-semibold tabular">{n}</div><div className="text-lg text-muted-foreground">{VENDOR_LABEL[v]}</div></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PanelTop({ ov }) {
  const top = (ov?.top_interfaces || []).slice(0, 8);
  return (
    <div className="h-full rounded-2xl bg-card/80 border border-primary/15 p-8 hud-panel">
      <div className="hud-label !text-lg mb-6 text-primary/80">Top Interfaces by Utilization</div>
      <div className="space-y-4">
        {top.map((t, i) => (
          <div key={i} className="flex items-center gap-6">
            <div className="w-72 truncate text-xl"><span className="font-medium">{t.device_name}</span> <span className="font-mono text-muted-foreground text-lg">{t.if_name}</span></div>
            <div className="flex-1 h-4 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full" style={{ width: `${Math.min(100, t.util)}%`, background: utilColor(t.util) }} /></div>
            <div className="w-40 text-right text-2xl font-semibold tabular" style={{ color: utilColor(t.util) }}>{t.util.toFixed(0)}%</div>
            <div className="w-40 text-right font-mono text-lg text-traffic-active">{fmtBps(t.in_bps)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PanelAlerts({ alerts }) {
  const firing = (alerts || []).filter((a) => a.state === 'firing');
  return (
    <div className="h-full rounded-2xl bg-card/80 border border-primary/15 p-8 hud-panel">
      <div className="hud-label !text-lg mb-6 text-primary/80">Active Alerts</div>
      {firing.length === 0 && <div className="text-3xl text-status-ok py-20 text-center">All systems healthy</div>}
      <div className="space-y-4">
        {firing.slice(0, 7).map((a) => (
          <div key={a.id} className="flex gap-4 items-center rounded-xl bg-white/[0.02] border border-white/5 p-5">
            <div className="w-2 h-14 rounded-full" style={{ background: severityColor(a.severity) }} />
            <div className="flex-1"><div className="text-2xl font-medium">{a.message}</div><div className="text-lg text-muted-foreground font-mono">{a.device_name}{a.if_name ? ` · ${a.if_name}` : ''}</div></div>
            <div className="text-xl uppercase font-semibold" style={{ color: severityColor(a.severity) }}>{a.severity}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SegBtn({ active, onClick, icon: Icon, label, testid }) {
  return (
    <button
      onClick={onClick} data-testid={testid}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 ${
        active ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'}`}
    >
      <Icon size={15} />{label}
    </button>
  );
}

export default function NocMode() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { data: ov } = usePoll('/overview', 5000);
  const { data: alerts } = usePoll('/alerts?state=firing', 5000);
  const { data: settings } = usePoll('/settings', 0);

  const [view, setView] = useState(params.get('view') === 'map' ? 'map' : 'panels');
  const [panel, setPanel] = useState(0);
  const [paused, setPaused] = useState(false);
  const rotate = (settings?.tv_rotate_seconds || 15) * 1000;

  // ---- alarm (optional, user-armed) --------------------------------------
  const [alarm, setAlarm] = useState(() => localStorage.getItem('noc_alarm') === '1');
  const alarmRef = useRef(alarm);
  useEffect(() => { alarmRef.current = alarm; }, [alarm]);

  const audioRef = useRef(null);
  const ensureAudio = useCallback(() => {
    if (!audioRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) audioRef.current = new AC();
    }
    if (audioRef.current && audioRef.current.state === 'suspended') audioRef.current.resume();
    return audioRef.current;
  }, []);

  const beep = useCallback((freq, start, dur, vol = 0.16) => {
    const ctx = audioRef.current; if (!ctx) return;
    const t = ctx.currentTime + start;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(freq, t);
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(vol, t + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t); osc.stop(t + dur + 0.02);
  }, []);

  const playAlarm = useCallback(() => {
    ensureAudio();
    // urgent 3-beep alternating pattern
    beep(880, 0.0, 0.22);
    beep(660, 0.30, 0.22);
    beep(880, 0.60, 0.30);
  }, [ensureAudio, beep]);

  const playBlip = useCallback(() => { ensureAudio(); beep(720, 0, 0.14, 0.12); }, [ensureAudio, beep]);

  const toggleAlarm = useCallback(() => {
    setAlarm((prev) => {
      const next = !prev;
      localStorage.setItem('noc_alarm', next ? '1' : '0');
      if (next) { ensureAudio(); setTimeout(playBlip, 30); }
      return next;
    });
  }, [ensureAudio, playBlip]);

  // ---- screen flash -------------------------------------------------------
  const [flash, setFlash] = useState(false);
  const [flashKey, setFlashKey] = useState(0);
  const flashTimer = useRef(null);
  const triggerFlash = useCallback(() => {
    setFlashKey((k) => k + 1);
    setFlash(true);
    if (flashTimer.current) clearTimeout(flashTimer.current);
    flashTimer.current = setTimeout(() => setFlash(false), 1500);
  }, []);

  // ---- new critical (device-down) detection ------------------------------
  const seenRef = useRef(null);
  useEffect(() => {
    if (!alerts) return;
    const critIds = alerts
      .filter((a) => a.state === 'firing' && a.severity === 'critical')
      .map((a) => a.id);
    if (seenRef.current === null) { seenRef.current = new Set(critIds); return; } // seed silently
    const hasNew = critIds.some((id) => !seenRef.current.has(id));
    seenRef.current = new Set(critIds);
    if (hasNew && alarmRef.current) { playAlarm(); triggerFlash(); }
  }, [alerts, playAlarm, triggerFlash]);

  useEffect(() => () => { if (flashTimer.current) clearTimeout(flashTimer.current); }, []);

  // ---- panel rotation (panels view only) ---------------------------------
  const panels = [<PanelFleet ov={ov} />, <PanelTop ov={ov} />, <PanelAlerts alerts={alerts} />];
  useEffect(() => {
    if (view !== 'panels' || paused) return;
    const i = setInterval(() => setPanel((p) => (p + 1) % 3), rotate);
    return () => clearInterval(i);
  }, [view, paused, rotate]);

  const firing = (alerts || []);
  const tickerItems = firing.length ? firing : [{ id: 'ok', message: 'All systems healthy', severity: 'ok', device_name: '' }];

  return (
    <div className="h-screen w-screen bg-background flex flex-col overflow-hidden"
         onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} data-testid="noc-mode">
      {flash && <div key={flashKey} className="noc-flash" data-testid="noc-flash" aria-hidden="true" />}

      <header className="h-20 shrink-0 flex items-center justify-between px-10 border-b border-primary/15 relative z-10">
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-4">
            <div className="h-11 w-11 rounded-xl flex items-center justify-center glow-primary" style={{ background: 'linear-gradient(135deg, hsl(142 92% 52%), hsl(160 88% 38%))' }}><Gauge size={22} className="text-background" /></div>
            <div><div className="text-2xl font-semibold tracking-tight">NetPulse NOC</div><div className="hud-label">Network Operations Center</div></div>
          </div>
          <div className="flex items-center rounded-lg border border-primary/20 bg-card/60 p-1 ml-2">
            <SegBtn active={view === 'panels'} onClick={() => setView('panels')} icon={LayoutGrid} label="Panels" testid="noc-view-panels" />
            <SegBtn active={view === 'map'} onClick={() => setView('map')} icon={Network} label="Map" testid="noc-view-map" />
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex gap-6 text-lg font-mono">
            <span className="text-status-ok tabular">● {ov?.counts?.up ?? '—'} up</span>
            <span className="text-status-crit tabular">● {ov?.counts?.down ?? '—'} down</span>
            <span className="text-status-warn tabular">● {ov?.counts?.active_alerts ?? '—'} alerts</span>
          </div>
          <button
            onClick={toggleAlarm} data-testid="noc-alarm-toggle"
            title={alarm ? 'Alarm armed — chime + flash on new device-down' : 'Alarm muted'}
            className={`flex items-center gap-2 px-3 h-10 rounded-lg border text-sm font-medium transition-colors duration-150 ${
              alarm ? 'border-status-crit/50 bg-status-crit/10 text-status-crit glow-cyan' : 'border-border text-muted-foreground hover:text-foreground'}`}
          >
            {alarm ? <BellRing size={16} className="pulse-dot" /> : <BellOff size={16} />}
            {alarm ? 'Armed' : 'Alarm'}
          </button>
          <Clock />
          <button onClick={() => navigate('/')} data-testid="noc-exit-button" className="h-10 w-10 rounded-lg flex items-center justify-center hover:bg-white/5 text-muted-foreground"><X size={22} /></button>
        </div>
      </header>

      <div className="flex-1 relative">
        {view === 'map' ? (
          <NocMap />
        ) : (
          <div className="h-full p-10 relative">
            <AnimatePresence mode="wait">
              <motion.div key={panel} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.4 }} className="h-full">
                {panels[panel]}
              </motion.div>
            </AnimatePresence>
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
              {panels.map((_, i) => <button key={i} onClick={() => setPanel(i)} className="h-2 rounded-full transition-all" style={{ width: i === panel ? 28 : 8, background: i === panel ? 'hsl(var(--primary))' : 'rgba(255,255,255,0.2)' }} />)}
            </div>
          </div>
        )}
      </div>

      <div className="h-14 shrink-0 border-t border-primary/15 bg-card/60 flex items-center overflow-hidden relative z-10">
        <div className="px-6 h-full flex items-center hud-label !text-sm border-r border-primary/15 shrink-0" style={{ color: firing.length ? 'hsl(var(--status-crit))' : 'hsl(var(--status-ok))' }}>ALERT TICKER</div>
        <motion.div className="flex gap-12 whitespace-nowrap px-8" animate={REDUCED_MOTION ? undefined : { x: ['0%', '-50%'] }} transition={REDUCED_MOTION ? undefined : { duration: 28, repeat: Infinity, ease: 'linear' }}>
          {[...tickerItems, ...tickerItems].map((a, i) => (
            <span key={i} className="flex items-center gap-2 text-sm font-mono"><span className="w-2 h-2 rounded-full" style={{ background: severityColor(a.severity) }} />{a.message}{a.device_name ? ` — ${a.device_name}` : ''}</span>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
