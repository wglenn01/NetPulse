import React, { useState } from 'react';
import { usePoll, api } from '@/lib/api';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { severityColor, timeAgo } from '@/lib/format';
import { toast } from 'sonner';
import { Check, X, CheckCheck, BellOff } from 'lucide-react';

function AlertRow({ a, onAck, onResolve }) {
  return (
    <div className="flex gap-3 rounded-lg bg-white/[0.02] border border-white/5 p-3" data-testid={`alert-${a.id}`}>
      <div className="w-1 rounded-full shrink-0" style={{ background: severityColor(a.severity) }} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] uppercase tracking-wide font-semibold" style={{ color: severityColor(a.severity) }}>{a.severity}</span>
          <span className="text-[13px] font-medium">{a.message}</span>
          {a.acknowledged && <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-muted-foreground">ack</span>}
        </div>
        {a.detail && <div className="text-[12px] text-muted-foreground mt-0.5">{a.detail}</div>}
        <div className="text-[11px] text-muted-foreground mt-1 font-mono">{a.device_name}{a.if_name ? ` · ${a.if_name}` : ''} · {timeAgo(a.last_seen)}</div>
      </div>
      {a.state === 'firing' && (
        <div className="flex items-center gap-1.5 shrink-0">
          {!a.acknowledged && <button onClick={() => onAck(a)} data-testid={`alerts-acknowledge-button-${a.id}`} title="Acknowledge" className="h-7 w-7 rounded-lg flex items-center justify-center hover:bg-white/5 text-muted-foreground hover:text-foreground"><Check size={15} /></button>}
          <button onClick={() => onResolve(a)} data-testid={`alerts-resolve-button-${a.id}`} title="Resolve" className="h-7 w-7 rounded-lg flex items-center justify-center hover:bg-status-ok/10 text-muted-foreground hover:text-status-ok"><CheckCheck size={15} /></button>
        </div>
      )}
    </div>
  );
}

function Rules() {
  const { data, refresh } = usePoll('/rules', 0);
  const [edits, setEdits] = useState({});
  const rules = data || [];
  const save = async (r, patch) => {
    try { await api.put(`/rules/${r.id}`, patch); toast.success(`Updated ${r.name}`); refresh(); }
    catch { toast.error('Update failed'); }
  };
  return (
    <div className="space-y-2">
      {rules.map((r) => (
        <div key={r.id} className="flex items-center gap-4 rounded-lg bg-white/[0.02] border border-white/5 p-3" data-testid={`rule-${r.id}`}>
          <Switch checked={r.enabled} onCheckedChange={(v) => save(r, { enabled: v })} data-testid={`rule-toggle-${r.id}`} />
          <div className="flex-1">
            <div className="text-[13px] font-medium">{r.name}</div>
            <div className="text-[11px]" style={{ color: severityColor(r.severity) }}>{r.severity}</div>
          </div>
          {['high_latency', 'packet_loss', 'high_util'].includes(r.type) && (
            <div className="flex items-center gap-2">
              <Input type="number" defaultValue={r.threshold} onChange={(e) => setEdits((p) => ({ ...p, [r.id]: e.target.value }))} className="w-24 font-mono" data-testid={`rule-threshold-${r.id}`} />
              <span className="text-xs text-muted-foreground w-8">{r.type === 'high_latency' ? 'ms' : '%'}</span>
              <Button size="sm" variant="secondary" className="border border-white/10" onClick={() => save(r, { threshold: Number(edits[r.id] ?? r.threshold) })}>Save</Button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function Alerts() {
  const { data, refresh } = usePoll('/alerts', 5000);
  const all = data || [];
  const firing = all.filter((a) => a.state === 'firing');
  const resolved = all.filter((a) => a.state === 'resolved');

  const onAck = async (a) => { try { await api.post(`/alerts/${a.id}/ack`); refresh(); } catch { toast.error('Failed'); } };
  const onResolve = async (a) => { try { await api.post(`/alerts/${a.id}/resolve`); toast.success('Resolved'); refresh(); } catch { toast.error('Failed'); } };
  const clearResolved = async () => { try { await api.delete('/alerts'); refresh(); } catch { toast.error('Failed'); } };

  return (
    <div className="p-6">
      <Tabs defaultValue="active">
        <TabsList className="bg-card border border-white/5">
          <TabsTrigger value="active" data-testid="alerts-tab-active">Active <span className="ml-1.5 text-xs opacity-70">{firing.length}</span></TabsTrigger>
          <TabsTrigger value="history" data-testid="alerts-tab-history">History <span className="ml-1.5 text-xs opacity-70">{resolved.length}</span></TabsTrigger>
          <TabsTrigger value="rules" data-testid="alerts-tab-rules">Alert Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4 space-y-2">
          {firing.length === 0 && <div className="py-16 text-center text-muted-foreground flex flex-col items-center gap-2"><BellOff size={28} /> No active alerts — everything is healthy</div>}
          {firing.map((a) => <AlertRow key={a.id} a={a} onAck={onAck} onResolve={onResolve} />)}
        </TabsContent>

        <TabsContent value="history" className="mt-4 space-y-2">
          {resolved.length > 0 && <div className="flex justify-end"><Button variant="secondary" size="sm" className="border border-white/10" onClick={clearResolved} data-testid="clear-history-button">Clear history</Button></div>}
          {resolved.length === 0 && <div className="py-16 text-center text-muted-foreground">No resolved alerts yet</div>}
          {resolved.map((a) => <AlertRow key={a.id} a={a} onAck={onAck} onResolve={onResolve} />)}
        </TabsContent>

        <TabsContent value="rules" className="mt-4"><Rules /></TabsContent>
      </Tabs>
    </div>
  );
}
