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
      <span className="inline-block w-2 h-2 rounded-full" style={{ background: color }} />
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-semibold tabular" style={{ color }}>{value}</span>
    </div>
  );
}

export function Layout({ children }) {
  const { data: ov } = usePoll('/overview', 5000);
  const c = ov?.counts || {};
  const location = useLocation();
  const page = NAV.find((n) => (n.end ? location.pathname === n.to : location.pathname.startsWith(n.to)));

  return (
    <div className="flex h-full min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-[236px] shrink-0 border-r border-white/5 bg-card/60 flex flex-col" data-testid="app-sidebar">
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-white/5">
          <div className="h-9 w-9 rounded-lg flex items-center justify-center"
               style={{ background: 'linear-gradient(135deg, hsl(190 95% 55%), hsl(198 85% 45%))' }}>
            <Radio size={18} className="text-background" />
          </div>
          <div>
            <div className="text-[15px] font-semibold leading-tight tracking-tight">NetPulse</div>
            <div className="text-[11px] text-muted-foreground leading-tight">Network Visibility</div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to} to={n.to} end={n.end} data-testid={n.testid}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors duration-150 ${
                  isActive ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                }`}
            >
              <n.icon size={18} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-white/5 text-[11px] text-muted-foreground">
          SNMP v2c · ICMP<br />Demo network active
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 shrink-0 border-b border-white/5 bg-card/40 backdrop-blur flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold tracking-tight">{page?.label || 'NetPulse'}</h1>
          </div>
          <div className="flex items-center gap-5">
            <Metric label="Up" value={c.up ?? '—'} color="hsl(var(--status-ok))" />
            <Metric label="Down" value={c.down ?? '—'} color="hsl(var(--status-crit))" />
            <Metric label="Alerts" value={c.active_alerts ?? '—'} color="hsl(var(--status-warn))" />
            <div className="flex items-center gap-2 pl-4 border-l border-white/10" data-testid="live-indicator">
              <span className="pulse-dot inline-block w-2 h-2 rounded-full" style={{ background: 'hsl(var(--status-ok))' }} />
              <span className="text-xs text-muted-foreground flex items-center gap-1"><Activity size={13} /> Live polling</span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
