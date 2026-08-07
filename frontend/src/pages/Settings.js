import React, { useEffect, useState } from 'react';
import { usePoll, api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Save, Send, Radio, Bell, Gauge, Search, Plug, Router, Wifi, RadioTower, Loader2 } from 'lucide-react';

function Section({ title, icon: Icon, children }) {
  return (
    <div className="hud-panel rounded-xl bg-card border border-primary/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="px-5 py-3.5 border-b border-border flex items-center gap-2"><Icon size={16} className="text-primary" /><h2 className="hud-label !text-xs text-primary/80">{title}</h2></div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Field({ label, children, hint }) {
  return (<div><Label className="text-xs">{label}</Label>{children}{hint && <p className="text-[11px] text-muted-foreground mt-1">{hint}</p>}</div>);
}

const VENDOR_META = {
  mikrotik: {
    label: 'MikroTik RouterOS', icon: Router,
    fields: [
      { k: 'host', label: 'Host / IP' }, { k: 'port', label: 'API Port', type: 'number' },
      { k: 'username', label: 'Username' }, { k: 'password', label: 'Password', type: 'password' },
    ],
    toggles: [{ k: 'use_tls', label: 'Use TLS (api-ssl)' }],
  },
  unifi: {
    label: 'UniFi Controller', icon: Wifi,
    fields: [
      { k: 'host', label: 'Controller Host' }, { k: 'port', label: 'Port', type: 'number' },
      { k: 'site', label: 'Site' }, { k: 'api_key', label: 'API Key', type: 'password' },
      { k: 'username', label: 'Username' }, { k: 'password', label: 'Password', type: 'password' },
    ],
    toggles: [{ k: 'verify_tls', label: 'Verify TLS certificate' }],
  },
  cambium: {
    label: 'Cambium cnMaestro', icon: RadioTower,
    fields: [
      { k: 'base_url', label: 'cnMaestro Base URL' }, { k: 'client_id', label: 'Client ID' },
      { k: 'client_secret', label: 'Client Secret', type: 'password' },
    ],
    toggles: [],
  },
};

function VendorIntegrations() {
  const { data } = usePoll('/vendor-config', 0);
  const [vc, setVc] = useState(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState('');
  useEffect(() => { if (data && !vc) setVc(data); }, [data, vc]);

  const setField = (vk, k, v) => setVc((p) => ({ ...p, [vk]: { ...p[vk], [k]: v } }));

  const save = async () => {
    setSaving(true);
    try {
      await api.put('/vendor-config', { mikrotik: vc.mikrotik, unifi: vc.unifi, cambium: vc.cambium });
      toast.success('Vendor integrations saved');
    } catch { toast.error('Save failed'); }
    finally { setSaving(false); }
  };

  const test = async (vk) => {
    setTesting(vk);
    try {
      const r = await api.post('/vendor-config/test', { vendor: vk });
      toast.success(r.data?.message || 'Connection OK');
    } catch (e) { toast.error(e?.response?.data?.detail || 'Test failed'); }
    finally { setTesting(''); }
  };

  if (!vc) return <div className="text-sm text-muted-foreground">Loading integrations…</div>;

  return (
    <div className="space-y-4" data-testid="vendor-integrations">
      <div className="flex items-center gap-2 rounded-lg border border-accent/25 bg-accent/[0.06] px-3 py-2">
        <span className="hud-label text-accent">Preview Mode</span>
        <span className="text-xs text-muted-foreground">Config is stored only. The preview shows a <span className="text-accent font-medium">simulated</span> enrichment feed; live polling activates on-prem once controllers are reachable.</span>
      </div>

      {['mikrotik', 'unifi', 'cambium'].map((vk) => {
        const meta = VENDOR_META[vk];
        const cfg = vc[vk] || {};
        const Icon = meta.icon;
        return (
          <div key={vk} className="rounded-lg border border-border bg-white/[0.02] p-4" data-testid={`vendor-block-${vk}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Icon size={16} className="text-primary" />
                <span className="text-sm font-semibold">{meta.label}</span>
              </div>
              <div className="flex items-center gap-3">
                <Button size="sm" variant="secondary" className="border border-border" onClick={() => test(vk)} disabled={testing === vk} data-testid={`vendor-${vk}-test-button`}>
                  {testing === vk ? <Loader2 size={14} className="mr-1.5 animate-spin" /> : <Send size={14} className="mr-1.5" />}Test
                </Button>
                <div className="flex items-center gap-2">
                  <span className="hud-label !text-[10px]">Enabled</span>
                  <Switch checked={!!cfg.enabled} onCheckedChange={(v) => setField(vk, 'enabled', v)} data-testid={`vendor-${vk}-enabled-switch`} />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {meta.fields.map((f) => (
                <Field key={f.k} label={f.label}>
                  <Input
                    type={f.type || 'text'}
                    value={cfg[f.k] ?? ''}
                    onChange={(e) => setField(vk, f.k, f.type === 'number' ? e.target.value : e.target.value)}
                    className={f.type === 'password' ? 'font-mono text-xs' : ''}
                    data-testid={`vendor-${vk}-${f.k}-input`}
                  />
                </Field>
              ))}
            </div>
            {meta.toggles.length > 0 && (
              <div className="flex flex-wrap gap-6 mt-3">
                {meta.toggles.map((t) => (
                  <label key={t.k} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Switch checked={!!cfg[t.k]} onCheckedChange={(v) => setField(vk, t.k, v)} data-testid={`vendor-${vk}-${t.k}-switch`} />
                    {t.label}
                  </label>
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="flex justify-end">
        <Button onClick={save} disabled={saving} className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary" data-testid="settings-vendor-api-save-button">
          <Save size={16} className="mr-1.5" />{saving ? 'Saving…' : 'Save Integrations'}
        </Button>
      </div>
    </div>
  );
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

      <Section title="Vendor API Integrations" icon={Plug}>
        <VendorIntegrations />
      </Section>

      <Section title="NOC / TV Mode" icon={Gauge}>
        <Field label="Panel Rotation (sec)" hint="How long each panel is shown in full-screen NOC mode"><Input type="number" value={f.tv_rotate_seconds} onChange={(e) => set('tv_rotate_seconds', e.target.value)} className="w-40" /></Field>
      </Section>
    </div>
  );
}
