import React from 'react';
import { usePoll } from '@/lib/api';
import { StatTile } from '@/components/StatTile';
import { VendorBadge } from '@/components/VendorBadge';
import { fmtBps, utilColor, severityColor, timeAgo, VENDOR_LABEL, vendorColor } from '@/lib/format';
import { DeviceDrawer } from '@/components/DeviceDrawer';
import { Server, WifiOff, Bell, Gauge, ArrowDownRight, ArrowUpRight } from 'lucide-react';

export default function Overview() {
  const { data } = usePoll('/overview', 5000);
  const [drawer, setDrawer] = React.useState(null);
  const c = data?.counts || {};
  const bw = data?.bandwidth || {};
  const top = data?.top_interfaces || [];
  const alerts = (data?.recent_alerts || []).filter((a) => a.state === 'firing');
  const vendors = data?.vendors || {};

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile testid="tile-devices-up" label="Devices Online" value={c.up ?? '—'} sub={`${c.total ?? 0} total monitored`} accent="hsl(var(--status-ok))" icon={Server} />
        <StatTile testid="tile-devices-down" label="Devices Down" value={c.down ?? '—'} sub="not responding to ICMP" accent="hsl(var(--status-crit))" icon={WifiOff} />
        <StatTile testid="tile-active-alerts" label="Active Alerts" value={c.active_alerts ?? '—'} sub={`${c.critical_alerts ?? 0} critical`} accent="hsl(var(--status-warn))" icon={Bell} />
        <StatTile testid="tile-total-bandwidth" label="Aggregate Traffic" value={fmtBps(bw.total_bps)} sub={`↓ ${fmtBps(bw.in_bps)}  ↑ ${fmtBps(bw.out_bps)}`} accent="hsl(var(--traffic-active))" icon={Gauge} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Top interfaces */}
        <div className="lg:col-span-8 rounded-xl bg-card border border-primary/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <h2 className="hud-label !text-xs text-primary/80">Top Interfaces by Utilization</h2>
            <span className="hud-label flex items-center gap-1.5"><span className="pulse-dot inline-block w-1.5 h-1.5 rounded-full bg-status-ok" />live</span>
          </div>
          <div className="p-2">
            {top.length === 0 && <div className="py-10 text-center text-sm text-muted-foreground">Collecting metrics…</div>}
            {top.map((t, idx) => (
              <button key={idx} onClick={() => setDrawer(t.device_id)} data-testid={`top-iface-${idx}`}
                className="w-full text-left flex items-center gap-4 px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors duration-150">
                <div className="w-1 h-9 rounded-full" style={{ background: vendorColor(t.vendor) }} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium truncate">{t.device_name}</span>
                    <span className="text-[12px] font-mono text-muted-foreground truncate">{t.if_name}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${Math.min(100, t.util)}%`, background: utilColor(t.util) }} />
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-[13px] font-semibold tabular" style={{ color: utilColor(t.util) }}>{t.util.toFixed(1)}%</div>
                  <div className="text-[11px] font-mono text-muted-foreground flex items-center gap-1.5">
                    <ArrowDownRight size={11} />{fmtBps(t.in_bps)}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* right column */}
        <div className="lg:col-span-4 space-y-6">
          <div className="rounded-xl bg-card border border-primary/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
            <div className="px-5 py-4 border-b border-border"><h2 className="hud-label !text-xs text-primary/80">Active Alerts</h2></div>
            <div className="p-3 space-y-2 max-h-[360px] overflow-auto">
              {alerts.length === 0 && <div className="py-8 text-center text-sm text-muted-foreground">No active alerts — all clear</div>}
              {alerts.map((a) => (
                <div key={a.id} className="flex gap-3 rounded-lg bg-white/[0.02] border border-white/5 p-3" data-testid={`overview-alert-${a.id}`}>
                  <div className="w-1 rounded-full" style={{ background: severityColor(a.severity) }} />
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-medium truncate">{a.message}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">{a.device_name} · {timeAgo(a.last_seen)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl bg-card border border-primary/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)] p-5">
            <h2 className="hud-label !text-xs text-primary/80 mb-3">Fleet by Vendor</h2>
            <div className="space-y-2.5">
              {Object.entries(vendors).map(([v, n]) => (
                <div key={v} className="flex items-center justify-between">
                  <VendorBadge vendor={v} />
                  <span className="text-sm font-semibold tabular">{n}</span>
                </div>
              ))}
              {Object.keys(vendors).length === 0 && <div className="text-sm text-muted-foreground">No devices</div>}
            </div>
          </div>
        </div>
      </div>

      <DeviceDrawer deviceId={drawer} open={!!drawer} onOpenChange={(o) => !o && setDrawer(null)} />
    </div>
  );
}
