import React, { useEffect, useState } from 'react';
import { usePoll, api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Save, Send, Radio, Bell, Gauge, Search } from 'lucide-react';

function Section({ title, icon: Icon, children }) {
  return (
    <div className="rounded-xl bg-card border border-white/5 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="px-5 py-3.5 border-b border-white/5 flex items-center gap-2"><Icon size={16} className="text-primary" /><h2 className="text-sm font-semibold">{title}</h2></div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Field({ label, children, hint }) {
  return (<div><Label className="text-xs">{label}</Label>{children}{hint && <p className="text-[11px] text-muted-foreground mt-1">{hint}</p>}</div>);
}

export default function Settings() {
  const { data } = usePoll('/settings', 0);
  const [f, setF] = useState(null);
  const [testing, setTesting] = useState(false);
  useEffect(() => { if (data && !f) setF(data); }, [data, f]);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  if (!f) return <div className="p-6 text-muted-foreground">Loading settings…</div>;

  const save = async () => {
    try {
      await api.put('/settings', {
        snmp_community: f.snmp_community, snmp_port: Number(f.snmp_port), snmp_timeout: Number(f.snmp_timeout), snmp_retries: Number(f.snmp_retries),
        poll_interval: Number(f.poll_interval),
        discovery_range: f.discovery_range, discovery_community: f.discovery_community, discovery_port: Number(f.discovery_port),
        discord_webhook_url: f.discord_webhook_url, alerts_enabled: f.alerts_enabled,
        threshold_latency_ms: Number(f.threshold_latency_ms), threshold_loss_pct: Number(f.threshold_loss_pct), threshold_util_pct: Number(f.threshold_util_pct),
        tv_rotate_seconds: Number(f.tv_rotate_seconds),
      });
      toast.success('Settings saved');
    } catch { toast.error('Save failed'); }
  };
  const testDiscord = async () => {
    setTesting(true);
    try { await api.post('/settings/test-discord', { webhook_url: f.discord_webhook_url }); toast.success('Test message sent to Discord'); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Discord test failed'); }
    finally { setTesting(false); }
  };

  return (
    <div className="p-6 max-w-4xl space-y-5">
      <div className="flex justify-end"><Button onClick={save} className="bg-primary text-primary-foreground hover:bg-primary/90" data-testid="settings-save-button"><Save size={16} className="mr-1.5" />Save Settings</Button></div>

      <Section title="SNMP & Polling" icon={Radio}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Default Community"><Input value={f.snmp_community} onChange={(e) => set('snmp_community', e.target.value)} data-testid="snmp-community-input" /></Field>
          <Field label="Default SNMP Port"><Input type="number" value={f.snmp_port} onChange={(e) => set('snmp_port', e.target.value)} /></Field>
          <Field label="Poll Interval (sec)"><Input type="number" value={f.poll_interval} onChange={(e) => set('poll_interval', e.target.value)} data-testid="poll-interval-input" /></Field>
          <Field label="SNMP Timeout (sec)"><Input type="number" value={f.snmp_timeout} onChange={(e) => set('snmp_timeout', e.target.value)} /></Field>
          <Field label="SNMP Retries"><Input type="number" value={f.snmp_retries} onChange={(e) => set('snmp_retries', e.target.value)} /></Field>
        </div>
      </Section>

      <Section title="Discovery Defaults" icon={Search}>
        <div className="grid grid-cols-3 gap-4">
          <Field label="CIDR Range" hint="Preloaded for the discovery scanner"><Input value={f.discovery_range} onChange={(e) => set('discovery_range', e.target.value)} /></Field>
          <Field label="Community"><Input value={f.discovery_community} onChange={(e) => set('discovery_community', e.target.value)} /></Field>
          <Field label="SNMP Port"><Input type="number" value={f.discovery_port} onChange={(e) => set('discovery_port', e.target.value)} /></Field>
        </div>
      </Section>

      <Section title="Alert Thresholds" icon={Gauge}>
        <div className="grid grid-cols-3 gap-4">
          <Field label="High Latency (ms)"><Input type="number" value={f.threshold_latency_ms} onChange={(e) => set('threshold_latency_ms', e.target.value)} /></Field>
          <Field label="Packet Loss (%)"><Input type="number" value={f.threshold_loss_pct} onChange={(e) => set('threshold_loss_pct', e.target.value)} /></Field>
          <Field label="High Utilization (%)"><Input type="number" value={f.threshold_util_pct} onChange={(e) => set('threshold_util_pct', e.target.value)} /></Field>
        </div>
      </Section>

      <Section title="Alerting & Discord" icon={Bell}>
        <div className="flex items-center justify-between mb-4">
          <div><div className="text-sm font-medium">Enable Alerting</div><div className="text-[11px] text-muted-foreground">Evaluate rules on every poll and dispatch notifications</div></div>
          <Switch checked={f.alerts_enabled} onCheckedChange={(v) => set('alerts_enabled', v)} data-testid="alerts-enabled-switch" />
        </div>
        <Field label="Discord Webhook URL" hint="Firing/resolved alerts are posted here as rich embeds">
          <div className="flex gap-2">
            <Input value={f.discord_webhook_url} onChange={(e) => set('discord_webhook_url', e.target.value)} placeholder="https://discord.com/api/webhooks/…" data-testid="discord-webhook-input" className="font-mono text-xs" />
            <Button variant="secondary" className="border border-white/10 shrink-0" onClick={testDiscord} disabled={testing} data-testid="discord-test-button"><Send size={15} className="mr-1.5" />{testing ? 'Sending…' : 'Test'}</Button>
          </div>
        </Field>
      </Section>

      <Section title="NOC / TV Mode" icon={Gauge}>
        <Field label="Panel Rotation (sec)" hint="How long each panel is shown in full-screen NOC mode"><Input type="number" value={f.tv_rotate_seconds} onChange={(e) => set('tv_rotate_seconds', e.target.value)} className="w-40" /></Field>
      </Section>
    </div>
  );
}
