import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Network, Server, Bell, LayoutGrid, MonitorPlay, Settings as SettingsIcon,
  Activity, Radio,
} from 'lucide-react';
import { usePoll } from '@/lib/api';

const NAV = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, testid: 'sidebar-nav-overview-link', end: true },
  { to: '/topology', label: 'Topology Map', icon: Network, testid: 'sidebar-nav-topology-link' },
  { to: '/devices', label: 'Devices', icon: Server, testid: 'sidebar-nav-devices-link' },
  { to: '/alerts', label: 'Alerts', icon: Bell, testid: 'sidebar-nav-alerts-link' },
  { to: '/dashboards', label: 'Dashboards', icon: LayoutGrid, testid: 'sidebar-nav-dashboards-link' },
  { to: '/tv', label: 'NOC Mode', icon: MonitorPlay, testid: 'sidebar-nav-noc-link' },
  { to: '/settings', label: 'Settings', icon: SettingsIcon, testid: 'sidebar-nav-settings-link' },
];

function Metric({ label, value, color }) {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-block w-2 h-2 rounded-full" style={{ background: color, boxShadow: `0 0 8px ${color}` }} />
      <span className="hud-label">{label}</span>
      <span className="text-sm font-mono font-semibold tabular" style={{ color }}>{value}</span>
    </div>
  );
}

export function Layout({ children }) {
  const { data: ov } = usePoll('/overview', 5000);
  const { data: settings } = usePoll('/settings', 0);
  const c = ov?.counts || {};
  const demo = settings?.demo_mode !== false;
  const location = useLocation();
  const page = NAV.find((n) => (n.end ? location.pathname === n.to : location.pathname.startsWith(n.to)));

  return (
    <div className="flex h-full min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-[236px] shrink-0 border-r border-border bg-card/60 flex flex-col" data-testid="app-sidebar">
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-border">
          <div className="h-9 w-9 rounded-lg flex items-center justify-center glow-primary"
               style={{ background: 'linear-gradient(135deg, hsl(142 92% 52%), hsl(160 88% 38%))' }}>
            <Radio size={18} className="text-background" />
          </div>
          <div>
            <div className="text-[15px] font-semibold leading-tight tracking-tight">NetPulse</div>
            <div className="hud-label leading-tight">Network Visibility</div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to} to={n.to} end={n.end} data-testid={n.testid}
              className={({ isActive }) =>
                `relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors duration-150 ${
                  isActive
                    ? 'bg-primary/10 text-primary font-medium before:absolute before:left-0 before:top-2 before:bottom-2 before:w-[2px] before:rounded-full before:bg-primary before:shadow-[0_0_12px_hsl(var(--primary)/0.5)]'
                    : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                }`}
            >
              <n.icon size={18} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-border hud-label leading-relaxed flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: demo ? 'hsl(var(--status-warn))' : 'hsl(var(--status-ok))' }} />
          SNMP v2c · ICMP<br />{demo ? 'Demo network active' : 'Live monitoring'}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 shrink-0 border-b border-border bg-card/40 backdrop-blur flex items-center justify-between px-6">
          <div className="flex items-center gap-2.5">
            <span className="hud-label text-primary/70">NETPULSE //</span>
            <h1 className="text-lg font-semibold tracking-tight">{page?.label || 'NetPulse'}</h1>
          </div>
          <div className="flex items-center gap-5">
            <Metric label="Up" value={c.up ?? '—'} color="hsl(var(--status-ok))" />
            <Metric label="Down" value={c.down ?? '—'} color="hsl(var(--status-crit))" />
            <Metric label="Alerts" value={c.active_alerts ?? '—'} color="hsl(var(--status-warn))" />
            <div className="flex items-center gap-2 pl-4 border-l border-border" data-testid="live-indicator">
              <span className="pulse-dot inline-block w-2 h-2 rounded-full" style={{ background: 'hsl(var(--status-ok))', boxShadow: '0 0 8px hsl(var(--status-ok))' }} />
              <span className="hud-label flex items-center gap-1"><Activity size={13} /> Live polling</span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
