import React, { useState, useMemo } from 'react';
import { usePoll, api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { StatusDot } from '@/components/StatusDot';
import { VendorBadge } from '@/components/VendorBadge';
import { DeviceDrawer } from '@/components/DeviceDrawer';
import { fmtBps, timeAgo, ROLE_LABEL } from '@/lib/format';
import { toast } from 'sonner';
import { Plus, Radar, Search, Trash2, Loader2, AlertTriangle } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

const VENDORS = ['mikrotik', 'ubiquiti', 'cambium', 'mimosa', 'generic'];
const ROLES = ['router', 'switch', 'ap', 'backhaul', 'cpe', 'device'];

// Normalize an Axios error into { title, message, canForce } for display.
function parseApiError(e, fallback) {
  // No HTTP response at all -> network error, timeout, CORS, or API unreachable.
  if (!e?.response) {
    const net = e?.code === 'ECONNABORTED'
      ? 'The request timed out before the server replied.'
      : 'Could not reach the NetPulse API (network error). Check that the backend is running and reachable.';
    return { title: 'Cannot reach server', message: net, canForce: false };
  }
  const { status, data } = e.response;
  const d = data?.detail;
  if (d && typeof d === 'object') {
    return {
      title: d.title || 'Could not add device',
      message: [d.message, d.detail].filter(Boolean).join(' \u2014 '),
      canForce: !!d.can_force,
    };
  }
  if (typeof d === 'string' && d) {
    return { title: 'Could not add device', message: d, canForce: false };
  }
  // Response present but no JSON detail (e.g. 500/502/504 HTML from a proxy).
  return {
    title: `Server error (HTTP ${status})`,
    message: `${fallback} The server returned an unexpected ${status} response. You can try "Add anyway" to skip the reachability check.`,
    canForce: status >= 500,
  };
}

function AddDeviceDialog({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [f, setF] = useState({ name: '', ip: '', vendor: 'mikrotik', role: 'router', community: 'public', snmp_port: 161, site: '' });
  const set = (k, v) => { setF((p) => ({ ...p, [k]: v })); if (err) setErr(null); };

  const reset = () => {
    setF({ name: '', ip: '', vendor: 'mikrotik', role: 'router', community: 'public', snmp_port: 161, site: '' });
    setErr(null); setBusy(false);
  };
  const onOpenChange = (v) => { setOpen(v); if (!v) reset(); };

  const submit = async (force = false) => {
    if (!f.name || !f.ip) { setErr({ title: 'Missing fields', message: 'Name and IP address are required.', canForce: false }); return; }
    setBusy(true); setErr(null);
    try {
      await api.post('/devices', { ...f, snmp_port: Number(f.snmp_port), force });
      toast.success(`Added ${f.name}`);
      setOpen(false); reset();
      onAdded?.();
    } catch (e) {
      setErr(parseApiError(e, 'Failed to add device. Please check the details and try again.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button data-testid="add-device-button" className="bg-primary text-primary-foreground hover:bg-primary/90"><Plus size={16} className="mr-1.5" />Add Device</Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-white/10">
        <DialogHeader><DialogTitle>Add Device</DialogTitle><DialogDescription>Monitor a device via SNMP v2c + ICMP. We verify reachability before adding.</DialogDescription></DialogHeader>
        {err && (
          <Alert variant="destructive" data-testid="add-device-error"
                 className="border-[hsl(var(--status-crit)/0.5)] bg-[hsl(var(--status-crit)/0.10)] text-[hsl(var(--status-crit))]">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle className="font-mono uppercase tracking-[0.14em] text-xs">{err.title}</AlertTitle>
            <AlertDescription className="text-[hsl(var(--foreground)/0.9)]">
              {err.message}
              {err.canForce && (
                <div className="mt-2">
                  <Button data-testid="add-device-force-button" size="sm" variant="secondary"
                          className="border border-[hsl(var(--status-warn)/0.4)] text-[hsl(var(--status-warn))] hover:bg-[hsl(var(--status-warn)/0.10)]"
                          disabled={busy} onClick={() => submit(true)}>
                    Add anyway (skip check)
                  </Button>
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-1"><Label>Name</Label><Input data-testid="device-name-input" value={f.name} onChange={(e) => set('name', e.target.value)} placeholder="core-rtr-02" /></div>
          <div className="col-span-1"><Label>IP Address</Label><Input data-testid="device-ip-input" value={f.ip} onChange={(e) => set('ip', e.target.value)} placeholder="10.0.0.1" /></div>
          <div><Label>Vendor</Label>
            <Select value={f.vendor} onValueChange={(v) => set('vendor', v)}>
              <SelectTrigger data-testid="device-vendor-select"><SelectValue /></SelectTrigger>
              <SelectContent>{VENDORS.map((v) => <SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div><Label>Role</Label>
            <Select value={f.role} onValueChange={(v) => set('role', v)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{ROLES.map((v) => <SelectItem key={v} value={v}>{ROLE_LABEL[v]}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div><Label>SNMP Community</Label><Input data-testid="device-community-input" value={f.community} onChange={(e) => set('community', e.target.value)} /></div>
          <div><Label>SNMP Port</Label><Input data-testid="device-port-input" type="number" value={f.snmp_port} onChange={(e) => set('snmp_port', e.target.value)} /></div>
          <div className="col-span-2"><Label>Site (optional)</Label><Input value={f.site} onChange={(e) => set('site', e.target.value)} placeholder="Tower North" /></div>
        </div>
        <DialogFooter>
          <Button data-testid="submit-device-button" onClick={() => submit(false)} disabled={busy}
                  className="bg-primary text-primary-foreground hover:bg-primary/90">
            {busy ? <><Loader2 size={16} className="mr-1.5 animate-spin" />Verifying…</> : <>Add Device</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DiscoveryDialog({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [running, setRunning] = useState(false);
  const [form, setForm] = useState({ range: '127.0.0.1/32', community: 'public', port: 1612 });
  const [result, setResult] = useState(null);
  const [sel, setSel] = useState({});

  const run = async () => {
    setRunning(true); setResult(null);
    try {
      const r = await api.post('/discovery/run', { ...form, port: Number(form.port) });
      setResult(r.data);
      const pre = {};
      r.data.found.forEach((f) => { if (f.snmp_ok && !f.already_added) pre[f.ip] = true; });
      setSel(pre);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Discovery failed'); }
    finally { setRunning(false); }
  };
  const addSelected = async () => {
    const chosen = (result?.found || []).filter((f) => sel[f.ip]);
    if (chosen.length === 0) { toast.error('Select at least one device'); return; }
    try {
      const r = await api.post('/discovery/add', {
        devices: chosen.map((f) => ({ ip: f.ip, port: result.port, community: result.community, name: f.sys_name || f.ip, vendor: f.vendor, role: f.role })),
      });
      const added = r.data?.added?.length ?? chosen.length;
      const skipped = r.data?.skipped?.length ?? 0;
      toast.success(`Added ${added} device(s)${skipped ? ` \u00b7 ${skipped} already monitored` : ''}`);
      setOpen(false); setResult(null); onAdded?.();
    } catch (e) { toast.error(parseApiError(e, 'Failed to add selected devices').message); }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="run-discovery-button" variant="secondary" className="border border-white/10"><Radar size={16} className="mr-1.5" />Discover</Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-white/10 max-w-2xl">
        <DialogHeader><DialogTitle>Network Discovery</DialogTitle><DialogDescription>Scan a CIDR range with ICMP, then fingerprint via SNMP v2c.</DialogDescription></DialogHeader>
        <div className="grid grid-cols-3 gap-3">
          <div><Label>CIDR Range</Label><Input data-testid="discovery-range-input" value={form.range} onChange={(e) => setForm((p) => ({ ...p, range: e.target.value }))} /></div>
          <div><Label>Community</Label><Input value={form.community} onChange={(e) => setForm((p) => ({ ...p, community: e.target.value }))} /></div>
          <div><Label>SNMP Port</Label><Input type="number" value={form.port} onChange={(e) => setForm((p) => ({ ...p, port: e.target.value }))} /></div>
        </div>
        <Button data-testid="discovery-scan-button" onClick={run} disabled={running} className="bg-primary text-primary-foreground hover:bg-primary/90 w-full">
          {running ? <><Loader2 size={16} className="mr-1.5 animate-spin" />Scanning…</> : <>Run Scan</>}
        </Button>
        {result && (
          <div className="mt-2 max-h-[300px] overflow-auto space-y-1.5">
            <div className="text-xs text-muted-foreground">Scanned {result.scanned} host(s) · {result.found.length} responding</div>
            {result.found.map((f) => (
              <label key={f.ip} className="flex items-center gap-3 rounded-lg bg-white/[0.02] border border-white/5 px-3 py-2 cursor-pointer">
                <Checkbox checked={!!sel[f.ip]} disabled={f.already_added || !f.snmp_ok} onCheckedChange={(v) => setSel((p) => ({ ...p, [f.ip]: !!v }))} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[13px]">{f.ip}</span>
                    {f.snmp_ok ? <VendorBadge vendor={f.vendor} /> : <span className="text-[11px] text-muted-foreground">no SNMP</span>}
                    {f.already_added && <span className="text-[11px] text-status-info">already added</span>}
                  </div>
                  {f.sys_descr && <div className="text-[11px] text-muted-foreground truncate">{f.sys_name} — {f.sys_descr}</div>}
                </div>
              </label>
            ))}
            {result.found.length === 0 && <div className="text-sm text-muted-foreground py-4 text-center">No live hosts found in range</div>}
          </div>
        )}
        {result && result.found.some((f) => f.snmp_ok && !f.already_added) && (
          <DialogFooter><Button data-testid="discovery-add-button" onClick={addSelected} className="bg-primary text-primary-foreground hover:bg-primary/90">Add Selected</Button></DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function Devices() {
  const { data, refresh } = usePoll('/devices', 5000);
  const [q, setQ] = useState('');
  const [vendor, setVendor] = useState('all');
  const [status, setStatus] = useState('all');
  const [drawer, setDrawer] = useState(null);
  const devices = data || [];

  const filtered = useMemo(() => devices.filter((d) => {
    if (q && !(`${d.name} ${d.ip} ${d.site}`.toLowerCase().includes(q.toLowerCase()))) return false;
    if (vendor !== 'all' && d.vendor !== vendor) return false;
    if (status === 'up' && !d.up) return false;
    if (status === 'down' && d.up) return false;
    return true;
  }), [devices, q, vendor, status]);

  const del = async (e, d) => {
    e.stopPropagation();
    if (!window.confirm(`Delete ${d.name}?`)) return;
    try { await api.delete(`/devices/${d.id}`); toast.success(`Deleted ${d.name}`); refresh(); }
    catch { toast.error('Delete failed'); }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Search size={15} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input data-testid="device-search-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search devices…" className="pl-8 w-56" />
          </div>
          <Select value={vendor} onValueChange={setVendor}>
            <SelectTrigger className="w-36" data-testid="vendor-filter"><SelectValue placeholder="Vendor" /></SelectTrigger>
            <SelectContent><SelectItem value="all">All vendors</SelectItem>{VENDORS.map((v) => <SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-32" data-testid="status-filter"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent><SelectItem value="all">All status</SelectItem><SelectItem value="up">Up</SelectItem><SelectItem value="down">Down</SelectItem></SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <DiscoveryDialog onAdded={refresh} />
          <AddDeviceDialog onAdded={refresh} />
        </div>
      </div>

      <div className="rounded-xl bg-card border border-primary/10 overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.35)]" data-testid="devices-table">
        <table className="w-full text-sm">
          <thead className="bg-secondary/70 backdrop-blur text-muted-foreground">
            <tr className="border-b border-border [&>th]:hud-label [&>th]:!text-[10px] [&>th]:py-3">
              <th className="text-left px-4">Device</th>
              <th className="text-left px-3">Vendor</th>
              <th className="text-left px-3">Role</th>
              <th className="text-right px-3">Latency</th>
              <th className="text-right px-3">Loss</th>
              <th className="text-right px-3">Throughput</th>
              <th className="text-right px-3">Ports</th>
              <th className="text-right px-4"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id} onClick={() => setDrawer(d.id)} data-testid={`device-row-${d.id}`}
                  className="border-b border-border last:border-0 hover:bg-[hsl(var(--primary)/0.06)] transition-colors duration-150 cursor-pointer">
                <td className="py-2.5 px-4">
                  <div className="flex items-center gap-2.5">
                    <StatusDot up={d.up} />
                    <div>
                      <div className="font-medium">{d.name}</div>
                      <div className="text-[11px] font-mono text-muted-foreground">{d.ip}{d.snmp_port !== 161 ? `:${d.snmp_port}` : ''}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3"><VendorBadge vendor={d.vendor} /></td>
                <td className="px-3 text-muted-foreground">{ROLE_LABEL[d.role] || d.role}</td>
                <td className="px-3 text-right font-mono tabular">{d.latency_ms != null ? `${d.latency_ms}ms` : '—'}</td>
                <td className="px-3 text-right font-mono tabular">{d.loss_pct != null ? `${d.loss_pct}%` : '—'}</td>
                <td className="px-3 text-right font-mono tabular text-traffic-active">{fmtBps((d.total_in_bps || 0) + (d.total_out_bps || 0))}</td>
                <td className="px-3 text-right font-mono tabular">{d.iface_up}/{d.iface_count}</td>
                <td className="px-4 text-right">
                  <button onClick={(e) => del(e, d)} data-testid={`delete-device-${d.id}`} className="text-muted-foreground hover:text-status-crit transition-colors"><Trash2 size={15} /></button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={8} className="py-10 text-center text-muted-foreground">No devices match your filters</td></tr>}
          </tbody>
        </table>
      </div>

      <DeviceDrawer deviceId={drawer} open={!!drawer} onOpenChange={(o) => !o && setDrawer(null)} />
    </div>
  );
}
