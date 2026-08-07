import React, { useEffect, useState, useMemo } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout/legacy';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { usePoll, api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { fmtBps, utilColor, severityColor, timeAgo } from '@/lib/format';
import { toast } from 'sonner';
import { Plus, Save, Pencil, X, Trash2, Server, WifiOff, Bell, Gauge } from 'lucide-react';

const RGL = WidthProvider(Responsive);

const WIDGET_DEFS = {
  stat: { title: 'Stat', w: 3, h: 2 },
  top_interfaces: { title: 'Top Interfaces', w: 6, h: 5 },
  alerts_feed: { title: 'Alerts Feed', w: 4, h: 5 },
};
const STAT_META = {
  devices_up: { label: 'Devices Online', icon: Server, accent: 'hsl(var(--status-ok))' },
  devices_down: { label: 'Devices Down', icon: WifiOff, accent: 'hsl(var(--status-crit))' },
  active_alerts: { label: 'Active Alerts', icon: Bell, accent: 'hsl(var(--status-warn))' },
  total_bandwidth: { label: 'Aggregate Traffic', icon: Gauge, accent: 'hsl(var(--traffic-active))' },
};

function StatWidget({ metric, ov }) {
  const meta = STAT_META[metric] || STAT_META.devices_up;
  const c = ov?.counts || {}; const bw = ov?.bandwidth || {};
  const val = metric === 'devices_up' ? c.up : metric === 'devices_down' ? c.down
    : metric === 'active_alerts' ? c.active_alerts : fmtBps(bw.total_bps);
  const Icon = meta.icon;
  return (
    <div className="h-full p-4 flex flex-col justify-between">
      <div className="flex items-start justify-between">
        <span className="text-sm text-muted-foreground">{meta.label}</span>
        <Icon size={16} style={{ color: meta.accent }} />
      </div>
      <div className="text-3xl font-semibold tabular" style={{ color: meta.accent }}>{val ?? '—'}</div>
    </div>
  );
}

function TopInterfacesWidget({ ov }) {
  const top = (ov?.top_interfaces || []).slice(0, 8);
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-white/5 text-sm font-semibold">Top Interfaces</div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {top.map((t, i) => (
          <div key={i} className="flex items-center gap-3 px-2 py-1.5">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-[12px]"><span className="font-medium truncate">{t.device_name}</span><span className="font-mono text-muted-foreground truncate">{t.if_name}</span></div>
              <div className="mt-1 h-1.5 rounded-full bg-white/5 overflow-hidden"><div className="h-full" style={{ width: `${Math.min(100, t.util)}%`, background: utilColor(t.util) }} /></div>
            </div>
            <span className="text-[12px] font-semibold tabular" style={{ color: utilColor(t.util) }}>{t.util.toFixed(0)}%</span>
          </div>
        ))}
        {top.length === 0 && <div className="text-center text-muted-foreground text-sm py-6">No data</div>}
      </div>
    </div>
  );
}

function AlertsWidget({ ov }) {
  const alerts = (ov?.recent_alerts || []).filter((a) => a.state === 'firing').slice(0, 8);
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-white/5 text-sm font-semibold">Active Alerts</div>
      <div className="flex-1 overflow-auto p-2 space-y-1.5">
        {alerts.map((a) => (
          <div key={a.id} className="flex gap-2 px-2 py-1.5"><div className="w-1 rounded-full" style={{ background: severityColor(a.severity) }} /><div className="min-w-0"><div className="text-[12px] font-medium truncate">{a.message}</div><div className="text-[10px] text-muted-foreground">{a.device_name} · {timeAgo(a.last_seen)}</div></div></div>
        ))}
        {alerts.length === 0 && <div className="text-center text-muted-foreground text-sm py-6">All clear</div>}
      </div>
    </div>
  );
}

function Widget({ item, ov, editing, onRemove }) {
  return (
    <div className="h-full rounded-xl bg-card border border-white/5 shadow-[0_8px_24px_rgba(0,0,0,0.3)] overflow-hidden relative">
      {editing && (
        <button onClick={() => onRemove(item.i)} data-testid={`widget-remove-${item.i}`} className="absolute top-1.5 right-1.5 z-10 h-6 w-6 rounded-md bg-black/40 flex items-center justify-center text-muted-foreground hover:text-status-crit"><X size={13} /></button>
      )}
      {item.widget === 'stat' && <StatWidget metric={item.config?.metric} ov={ov} />}
      {item.widget === 'top_interfaces' && <TopInterfacesWidget ov={ov} />}
      {item.widget === 'alerts_feed' && <AlertsWidget ov={ov} />}
    </div>
  );
}

export default function Dashboards() {
  const { data: dashboards, refresh: refreshDash } = usePoll('/dashboards', 0);
  const { data: ov } = usePoll('/overview', 5000);
  const [current, setCurrent] = useState(null);
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (dashboards && dashboards.length && !current) setCurrent(dashboards[0]);
  }, [dashboards, current]);
  useEffect(() => { if (current) setItems(current.layout || []); }, [current]);

  const layout = useMemo(() => items.map((it) => ({ i: it.i, x: it.x, y: it.y, w: it.w, h: it.h, minW: 2, minH: 2 })), [items]);

  const onLayoutChange = (l) => {
    if (!editing) return;
    setItems((prev) => prev.map((it) => { const g = l.find((x) => x.i === it.i); return g ? { ...it, x: g.x, y: g.y, w: g.w, h: g.h } : it; }));
  };
  const addWidget = (widget, config = {}) => {
    const def = WIDGET_DEFS[widget];
    const id = `w${Date.now()}`;
    setItems((p) => [...p, { i: id, x: 0, y: Infinity, w: def.w, h: def.h, widget, config }]);
  };
  const removeWidget = (i) => setItems((p) => p.filter((it) => it.i !== i));
  const save = async () => {
    try { await api.put(`/dashboards/${current.id}`, { name: current.name, layout: items, is_default: current.is_default }); toast.success('Dashboard saved'); setEditing(false); refreshDash(); }
    catch { toast.error('Save failed'); }
  };
  const createDash = async () => {
    const name = window.prompt('Dashboard name', 'New Dashboard'); if (!name) return;
    try { const r = await api.post('/dashboards', { name, layout: [] }); toast.success('Created'); refreshDash(); setCurrent(r.data); setEditing(true); }
    catch { toast.error('Failed'); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Select value={current?.id} onValueChange={(id) => setCurrent(dashboards.find((d) => d.id === id))}>
            <SelectTrigger className="w-56" data-testid="dashboard-select"><SelectValue placeholder="Select dashboard" /></SelectTrigger>
            <SelectContent>{(dashboards || []).map((d) => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="secondary" size="sm" className="border border-white/10" onClick={createDash} data-testid="create-dashboard-button"><Plus size={15} className="mr-1" />New</Button>
        </div>
        <div className="flex items-center gap-2">
          {editing && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild><Button variant="secondary" size="sm" className="border border-white/10" data-testid="add-widget-button"><Plus size={15} className="mr-1" />Add Widget</Button></DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => addWidget('stat', { metric: 'devices_up' })}>Stat: Devices Online</DropdownMenuItem>
                <DropdownMenuItem onClick={() => addWidget('stat', { metric: 'devices_down' })}>Stat: Devices Down</DropdownMenuItem>
                <DropdownMenuItem onClick={() => addWidget('stat', { metric: 'active_alerts' })}>Stat: Active Alerts</DropdownMenuItem>
                <DropdownMenuItem onClick={() => addWidget('stat', { metric: 'total_bandwidth' })}>Stat: Aggregate Traffic</DropdownMenuItem>
                <DropdownMenuItem onClick={() => addWidget('top_interfaces')}>Top Interfaces</DropdownMenuItem>
                <DropdownMenuItem onClick={() => addWidget('alerts_feed')}>Alerts Feed</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {editing
            ? <Button size="sm" onClick={save} className="bg-primary text-primary-foreground hover:bg-primary/90" data-testid="save-dashboard-button"><Save size={15} className="mr-1" />Save</Button>
            : <Button size="sm" variant="secondary" className="border border-white/10" onClick={() => setEditing(true)} data-testid="edit-dashboard-button"><Pencil size={15} className="mr-1" />Edit</Button>}
        </div>
      </div>

      {items.length === 0 && (
        <div className="rounded-xl border border-dashed border-white/10 py-20 text-center text-muted-foreground">
          Empty dashboard. {editing ? 'Use “Add Widget” to build your view.' : 'Click Edit to add widgets.'}
        </div>
      )}

      <RGL className="layout" layouts={{ lg: layout }} cols={{ lg: 12, md: 12, sm: 6, xs: 4, xxs: 2 }}
           breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
           rowHeight={64} isDraggable={editing} isResizable={editing} onLayoutChange={onLayoutChange} margin={[16, 16]}>
        {items.map((it) => (
          <div key={it.i} data-testid={`dashboard-widget-${it.i}`}>
            <Widget item={it} ov={ov} editing={editing} onRemove={removeWidget} />
          </div>
        ))}
      </RGL>
    </div>
  );
}
