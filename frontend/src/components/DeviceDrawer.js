import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { usePoll } from '@/lib/api';
import { VendorBadge } from '@/components/VendorBadge';
import { StatusDot } from '@/components/StatusDot';
import { fmtBps, fmtUptime, utilColor, ROLE_LABEL } from '@/lib/format';
import { ArrowDownRight, ArrowUpRight, Clock, MapPin, Cpu } from 'lucide-react';

function OperBadge({ oper, admin }) {
  const up = oper === 1;
  const label = up ? 'up' : admin === 1 ? 'down' : 'admin-down';
  const color = up ? 'hsl(var(--status-ok))' : 'hsl(var(--status-crit))';
  return <span className="text-[11px] font-mono" style={{ color }}>{label}</span>;
}

export function DeviceDrawer({ deviceId, open, onOpenChange }) {
  const { data: device } = usePoll(open && deviceId ? `/devices/${deviceId}` : null, 5000);
  const { data: metrics } = usePoll(open && deviceId ? `/metrics/device/${deviceId}?minutes=20` : null, 5000);
  const st = device?.state || {};
  const sysinfo = st.sysinfo || {};
  const interfaces = (st.interfaces || []).slice().sort((a, b) => (b.util || 0) - (a.util || 0));

  const chartData = (metrics || []).map((m) => ({
    t: new Date(m.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    in: +(m.in_bps / 1e6).toFixed(2),
    out: +(m.out_bps / 1e6).toFixed(2),
  }));

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-[560px] bg-card border-white/10 overflow-y-auto p-0" data-testid="device-drawer">
        <SheetTitle className="sr-only">Device details</SheetTitle>
        {device && (
          <div>
            <SheetHeader className="p-5 border-b border-white/5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-lg font-semibold">
                  <StatusDot up={st.up} size={10} />
                  <span>{device.name}</span>
                </div>
                <VendorBadge vendor={device.vendor} />
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground pt-1">
                <span className="font-mono">{device.ip}{device.snmp_port !== 161 ? `:${device.snmp_port}` : ''}</span>
                <span>{ROLE_LABEL[device.role] || device.role}</span>
                {device.site && <span className="flex items-center gap-1"><MapPin size={12} />{device.site}</span>}
              </div>
            </SheetHeader>

            <div className="p-5 space-y-5">
              {/* status row */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-white/[0.03] border border-white/5 p-3">
                  <div className="text-[11px] text-muted-foreground">Latency</div>
                  <div className="text-lg font-semibold tabular">{st.latency_ms != null ? `${st.latency_ms} ms` : '—'}</div>
                </div>
                <div className="rounded-lg bg-white/[0.03] border border-white/5 p-3">
                  <div className="text-[11px] text-muted-foreground">Packet Loss</div>
                  <div className="text-lg font-semibold tabular">{st.loss_pct != null ? `${st.loss_pct}%` : '—'}</div>
                </div>
                <div className="rounded-lg bg-white/[0.03] border border-white/5 p-3">
                  <div className="text-[11px] text-muted-foreground">SNMP</div>
                  <div className="text-lg font-semibold" style={{ color: st.snmp_ok ? 'hsl(var(--status-ok))' : 'hsl(var(--status-crit))' }}>
                    {st.snmp_ok ? 'OK' : 'n/a'}
                  </div>
                </div>
              </div>

              {/* sysinfo */}
              {sysinfo.descr && (
                <div className="rounded-lg bg-white/[0.03] border border-white/5 p-3 space-y-1.5">
                  <div className="flex items-start gap-2 text-xs"><Cpu size={13} className="mt-0.5 text-muted-foreground" /><span className="text-muted-foreground">{sysinfo.descr}</span></div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground"><Clock size={13} /> Uptime {fmtUptime(sysinfo.uptime_secs)}</div>
                </div>
              )}

              {/* bandwidth chart */}
              <div className="rounded-lg bg-white/[0.02] border border-white/5 p-3">
                <div className="text-xs font-medium text-muted-foreground mb-2">Aggregate Throughput (Mbps)</div>
                <ResponsiveContainer width="100%" height={150}>
                  <AreaChart data={chartData} margin={{ top: 4, right: 6, left: -18, bottom: 0 }}>
                    <defs>
                      <linearGradient id="dIn" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="hsl(var(--chart-1))" stopOpacity={0.35} /><stop offset="100%" stopColor="hsl(var(--chart-1))" stopOpacity={0.02} /></linearGradient>
                      <linearGradient id="dOut" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="hsl(var(--chart-3))" stopOpacity={0.3} /><stop offset="100%" stopColor="hsl(var(--chart-3))" stopOpacity={0.02} /></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }} minTickGap={40} />
                    <YAxis tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }} />
                    <Tooltip contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                    <Area type="monotone" dataKey="in" name="In" stroke="hsl(var(--chart-1))" fill="url(#dIn)" strokeWidth={1.6} isAnimationActive={false} />
                    <Area type="monotone" dataKey="out" name="Out" stroke="hsl(var(--chart-3))" fill="url(#dOut)" strokeWidth={1.6} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* interfaces */}
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-2">Interfaces ({interfaces.length})</div>
                <div className="space-y-1.5">
                  {interfaces.map((i) => (
                    <div key={i.index} className="rounded-lg bg-white/[0.02] border border-white/5 px-3 py-2" data-testid={`iface-row-${i.name}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-[13px] font-mono">{i.name}</span>
                        <div className="flex items-center gap-3">
                          <OperBadge oper={i.oper} admin={i.admin} />
                          <span className="text-[11px] text-muted-foreground">{i.speed_mbps >= 1000 ? `${i.speed_mbps / 1000}G` : `${i.speed_mbps}M`}</span>
                        </div>
                      </div>
                      <div className="mt-1.5 flex items-center gap-3 text-[11px] font-mono tabular">
                        <span className="flex items-center gap-1 text-chart-1"><ArrowDownRight size={12} />{fmtBps(i.in_bps)}</span>
                        <span className="flex items-center gap-1 text-chart-3"><ArrowUpRight size={12} />{fmtBps(i.out_bps)}</span>
                      </div>
                      <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${Math.min(100, i.util || 0)}%`, background: utilColor(i.util || 0) }} />
                      </div>
                    </div>
                  ))}
                  {interfaces.length === 0 && <div className="text-xs text-muted-foreground py-4 text-center">No interface data (device offline or SNMP unavailable)</div>}
                </div>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
