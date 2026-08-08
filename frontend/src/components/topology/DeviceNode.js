import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Router, Server, Radio, Wifi, MonitorSmartphone, HelpCircle } from 'lucide-react';
import { vendorColor, VENDOR_LABEL, fmtBpsShort } from '@/lib/format';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';

const ROLE_ICON = {
  router: Router, switch: Server, ap: Wifi, backhaul: Radio, cpe: MonitorSmartphone, device: HelpCircle,
};

const ALL = '__all__';

export function DeviceNode({ data, selected }) {
  const Icon = ROLE_ICON[data.role] || HelpCircle;
  const vcolor = vendorColor(data.vendor);
  const down = !data.up;
  const statusColor = down ? 'hsl(var(--status-crit))' : 'hsl(var(--status-ok))';
  const ports = data.ports || [];

  // THRPT source: a specific interface (persisted) or the aggregate of all.
  const editable = typeof data.onIfaceChange === 'function';
  const selIface = data.thrpt_iface || ALL;
  const isAll = selIface === ALL;
  const selPort = isAll ? null : ports.find((p) => p.name === selIface);
  const thrptBps = isAll
    ? (data.total_in_bps || 0) + (data.total_out_bps || 0)
    : (selPort ? (selPort.in_bps || 0) + (selPort.out_bps || 0) : 0);

  return (
    // Outer wrapper (no overflow) so per-port connection handles can sit on the edges.
    <div data-testid={`topology-node-${data.id}`} className="relative" style={{ width: 172, opacity: down ? 0.85 : 1 }}>
      {/* default handles keep existing edges attached top/bottom (hidden + non-interactive via CSS) */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      {/* per-port connection handles (drag-to-connect); connectionMode=loose links any port to any port */}
      {ports.map((p, idx) => {
        const top = `${((idx + 1) / (ports.length + 1)) * 100}%`;
        return (
          <React.Fragment key={p.name}>
            <Handle id={p.name} type="source" position={Position.Right}
              className="np-port-handle" style={{ top }} title={p.name}
              data-testid={`port-handle-${data.id}-${p.name}`} />
            <Handle id={`L::${p.name}`} type="source" position={Position.Left}
              className="np-port-handle" style={{ top }} title={p.name} />
          </React.Fragment>
        );
      })}

      {/* Visual card (clips the vendor stripe & rounded corners) */}
      <div
        className="relative rounded-xl border bg-card/80 backdrop-blur-[2px] overflow-hidden transition-shadow duration-150"
        style={{
          borderColor: selected ? 'hsl(var(--primary))' : down ? 'hsl(var(--status-crit) / 0.5)' : 'hsl(var(--primary) / 0.22)',
          boxShadow: selected
            ? '0 0 0 2px hsl(var(--primary) / 0.55), 0 0 22px hsl(var(--primary) / 0.28)'
            : down ? '0 8px 24px rgba(0,0,0,0.5)' : '0 0 0 1px hsl(var(--primary) / 0.14), 0 8px 24px rgba(0,0,0,0.45)',
        }}
      >
        <div className="absolute left-0 top-0 bottom-0 w-1" style={{ background: vcolor }} />
        <div className="pl-3 pr-2.5 py-2.5">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              <Icon size={14} style={{ color: vcolor }} />
              <span className="text-[13px] font-mono font-semibold tracking-tight truncate">{data.name}</span>
            </div>
            <span className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ background: statusColor, boxShadow: `0 0 8px ${statusColor}` }} />
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-[10px] font-mono text-muted-foreground truncate">{data.ip}</span>
            <span className="text-[9px] font-mono uppercase tracking-[0.14em]" style={{ color: vcolor }}>{VENDOR_LABEL[data.vendor]}</span>
          </div>
          {down ? (
            <div className="mt-2 text-[10px] font-mono font-medium text-status-crit tracking-[0.14em]">OFFLINE</div>
          ) : (
            <div className="mt-2 space-y-1.5">
              <div className="grid grid-cols-2 gap-1.5">
                <div className="rounded-md bg-white/[0.03] border border-primary/10 px-1.5 py-1">
                  <div className="hud-label !text-[8px] !tracking-[0.12em]">RTT</div>
                  <div className="text-[11px] font-mono tabular">{data.latency_ms != null ? `${data.latency_ms}ms` : '—'}</div>
                </div>
                <div className="rounded-md bg-white/[0.03] border border-primary/10 px-1.5 py-1 overflow-hidden">
                  <div className="hud-label !text-[8px] !tracking-[0.12em]">THRPT</div>
                  <div className="text-[11px] font-mono tabular text-traffic-active leading-tight">
                    {fmtBpsShort(thrptBps)}
                  </div>
                  {!isAll && (
                    <div className="text-[8px] font-mono text-accent/80 truncate leading-tight" title={selIface}>{selIface}</div>
                  )}
                </div>
              </div>
              {editable && ports.length > 0 && (
                <div className="nodrag nowheel" onPointerDown={(e) => e.stopPropagation()} onClick={(e) => e.stopPropagation()}>
                  <Select value={selIface} onValueChange={(v) => data.onIfaceChange(v)}>
                    <SelectTrigger
                      data-testid={`thrpt-iface-select-${data.id}`}
                      className="h-6 min-h-0 py-0 px-1.5 text-[9px] font-mono bg-white/[0.03] border-primary/15 focus:ring-1 focus:ring-primary/40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-64">
                      <SelectItem value={ALL} className="text-[11px]">All interfaces</SelectItem>
                      {ports.map((p) => (
                        <SelectItem key={p.name} value={p.name} className="text-[11px] font-mono">{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
