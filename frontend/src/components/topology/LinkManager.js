import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { toast } from 'sonner';
import { Cable, Plus, Trash2, ArrowLeftRight } from 'lucide-react';

function PortSelect({ deviceId, value, onChange, placeholder, testid }) {
  const [ports, setPorts] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let active = true;
    if (!deviceId) { setPorts([]); return; }
    setLoading(true);
    api.get(`/devices/${deviceId}`)
      .then((r) => { if (active) setPorts((r.data?.state?.interfaces || []).map((i) => i.name)); })
      .catch(() => active && setPorts([]))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [deviceId]);
  return (
    <Select value={value} onValueChange={onChange} disabled={!deviceId || loading}>
      <SelectTrigger data-testid={testid}>
        <SelectValue placeholder={loading ? 'Loading ports…' : (ports.length ? placeholder : 'No ports (offline)')} />
      </SelectTrigger>
      <SelectContent>
        {ports.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
      </SelectContent>
    </Select>
  );
}

export function LinkManager({ onChange }) {
  const [open, setOpen] = useState(false);
  const [devices, setDevices] = useState([]);
  const [links, setLinks] = useState([]);
  const [a, setA] = useState(''); const [ai, setAi] = useState('');
  const [b, setB] = useState(''); const [bi, setBi] = useState('');
  const [label, setLabel] = useState('');

  const nameOf = useCallback((id) => devices.find((d) => d.id === id)?.name || id, [devices]);

  const loadDevices = useCallback(() => { api.get('/devices').then((r) => setDevices(r.data || [])).catch(() => {}); }, []);
  const loadLinks = useCallback(() => { api.get('/links').then((r) => setLinks(r.data || [])).catch(() => {}); }, []);

  useEffect(() => { if (open) { loadDevices(); loadLinks(); } }, [open, loadDevices, loadLinks]);

  const reset = () => { setA(''); setAi(''); setB(''); setBi(''); setLabel(''); };

  const create = async () => {
    if (!a || !ai || !b || !bi) { toast.error('Select both devices and ports'); return; }
    if (a === b) { toast.error('Choose two different devices'); return; }
    try {
      await api.post('/links', { a_device: a, a_ifname: ai, b_device: b, b_ifname: bi, label });
      toast.success('Link created');
      reset(); loadLinks(); onChange?.();
    } catch { toast.error('Failed to create link'); }
  };

  const del = async (id) => {
    try { await api.delete(`/links/${id}`); loadLinks(); onChange?.(); }
    catch { toast.error('Delete failed'); }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button data-testid="connect-ports-button" onClick={() => setOpen(true)}
        className="bg-card/90 border border-white/10 text-foreground hover:bg-white/10 backdrop-blur">
        <Cable size={16} className="mr-1.5" />Connect Ports
      </Button>
      <DialogContent className="bg-card border-white/10 max-w-2xl">
        <DialogHeader>
          <DialogTitle>Connect Ports</DialogTitle>
          <DialogDescription>Link a specific interface on one device to an interface on another. The link’s live traffic drives the animated line.</DialogDescription>
        </DialogHeader>

        {/* create form */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="grid grid-cols-[1fr_auto_1fr] gap-3 items-end">
            <div className="space-y-2">
              <div><Label className="text-xs">Device A</Label>
                <Select value={a} onValueChange={(v) => { setA(v); setAi(''); }}>
                  <SelectTrigger data-testid="link-device-a"><SelectValue placeholder="Select device" /></SelectTrigger>
                  <SelectContent>{devices.map((d) => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div><Label className="text-xs">Port A</Label>
                <PortSelect deviceId={a} value={ai} onChange={setAi} placeholder="Select port" testid="link-port-a" />
              </div>
            </div>
            <div className="pb-2 text-muted-foreground"><ArrowLeftRight size={18} /></div>
            <div className="space-y-2">
              <div><Label className="text-xs">Device B</Label>
                <Select value={b} onValueChange={(v) => { setB(v); setBi(''); }}>
                  <SelectTrigger data-testid="link-device-b"><SelectValue placeholder="Select device" /></SelectTrigger>
                  <SelectContent>{devices.map((d) => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div><Label className="text-xs">Port B</Label>
                <PortSelect deviceId={b} value={bi} onChange={setBi} placeholder="Select port" testid="link-port-b" />
              </div>
            </div>
          </div>
          <div className="flex items-end gap-3 mt-3">
            <div className="flex-1"><Label className="text-xs">Label (optional)</Label><Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. Ridge PtP" /></div>
            <Button data-testid="link-create-button" onClick={create} className="bg-primary text-primary-foreground hover:bg-primary/90"><Plus size={16} className="mr-1" />Add Link</Button>
          </div>
        </div>

        {/* existing links */}
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">Existing Links ({links.length})</div>
          <div className="max-h-[240px] overflow-auto space-y-1.5">
            {links.map((l) => (
              <div key={l.id} className="flex items-center justify-between rounded-lg bg-white/[0.02] border border-white/5 px-3 py-2" data-testid={`link-row-${l.id}`}>
                <div className="text-[13px] flex items-center gap-2 min-w-0">
                  <span className="font-medium truncate">{nameOf(l.a_device)}</span>
                  <span className="font-mono text-muted-foreground text-[11px]">{l.a_ifname}</span>
                  <ArrowLeftRight size={13} className="text-muted-foreground shrink-0" />
                  <span className="font-medium truncate">{nameOf(l.b_device)}</span>
                  <span className="font-mono text-muted-foreground text-[11px]">{l.b_ifname}</span>
                </div>
                <button onClick={() => del(l.id)} data-testid={`link-delete-${l.id}`} className="text-muted-foreground hover:text-status-crit shrink-0 ml-2"><Trash2 size={15} /></button>
              </div>
            ))}
            {links.length === 0 && <div className="text-sm text-muted-foreground py-6 text-center">No links yet</div>}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
