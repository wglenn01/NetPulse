import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Router, Server, Radio, Wifi, MonitorSmartphone, HelpCircle } from 'lucide-react';
import { vendorColor, VENDOR_LABEL, fmtBpsShort } from '@/lib/format';

const ROLE_ICON = {
  router: Router, switch: Server, ap: Wifi, backhaul: Radio, cpe: MonitorSmartphone, device: HelpCircle,
};

export function DeviceNode({ data, selected }) {
  const Icon = ROLE_ICON[data.role] || HelpCircle;
  const vcolor = vendorColor(data.vendor);
  const down = !data.up;
  const statusColor = down ? 'hsl(var(--status-crit))' : 'hsl(var(--status-ok))';

  return (
    <div
      data-testid={`topology-node-${data.id}`}
      className="relative rounded-xl border bg-card overflow-hidden"
      style={{
        width: 172,
        borderColor: selected ? 'hsl(var(--primary))' : down ? 'hsl(var(--status-crit) / 0.5)' : 'rgba(255,255,255,0.08)',
        boxShadow: selected ? '0 0 0 2px hsl(var(--primary) / 0.4)' : '0 8px 24px rgba(0,0,0,0.4)',
        opacity: down ? 0.85 : 1,
      }}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="absolute left-0 top-0 bottom-0 w-1" style={{ background: vcolor }} />
      <div className="pl-3 pr-2.5 py-2.5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <Icon size={14} style={{ color: vcolor }} />
            <span className="text-[13px] font-semibold truncate">{data.name}</span>
          </div>
          <span className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                style={{ background: statusColor, boxShadow: down ? `0 0 8px ${statusColor}` : 'none' }} />
        </div>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-[10px] font-mono text-muted-foreground truncate">{data.ip}</span>
          <span className="text-[9px] uppercase tracking-wide" style={{ color: vcolor }}>{VENDOR_LABEL[data.vendor]}</span>
        </div>
        {down ? (
          <div className="mt-2 text-[10px] font-medium text-status-crit">OFFLINE</div>
        ) : (
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            <div className="rounded-md bg-white/[0.03] px-1.5 py-1">
              <div className="text-[9px] text-muted-foreground">RTT</div>
              <div className="text-[11px] font-mono tabular">{data.latency_ms != null ? `${data.latency_ms}ms` : '—'}</div>
            </div>
            <div className="rounded-md bg-white/[0.03] px-1.5 py-1">
              <div className="text-[9px] text-muted-foreground">Thrpt</div>
              <div className="text-[11px] font-mono tabular text-traffic-active">
                {fmtBpsShort((data.total_in_bps || 0) + (data.total_out_bps || 0))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
