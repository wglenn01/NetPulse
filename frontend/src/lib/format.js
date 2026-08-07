// Formatting + color helpers for network metrics.

export function fmtBps(bps) {
  if (bps === null || bps === undefined) return '—';
  const n = Number(bps);
  if (n < 1000) return `${n.toFixed(0)} bps`;
  if (n < 1e6) return `${(n / 1e3).toFixed(1)} Kbps`;
  if (n < 1e9) return `${(n / 1e6).toFixed(1)} Mbps`;
  return `${(n / 1e9).toFixed(2)} Gbps`;
}

export function fmtBpsShort(bps) {
  const n = Number(bps || 0);
  if (n < 1e6) return `${(n / 1e3).toFixed(0)}K`;
  if (n < 1e9) return `${(n / 1e6).toFixed(0)}M`;
  return `${(n / 1e9).toFixed(1)}G`;
}

// Interface link speed (Mbps) -> compact label: 10000 -> "10G", 1000 -> "1G", 300 -> "300M"
export function fmtSpeed(mbps) {
  const n = Number(mbps || 0);
  if (n <= 0) return '';
  if (n >= 1000) {
    const g = n / 1000;
    return `${Number.isInteger(g) ? g : g.toFixed(1)}G`;
  }
  return `${n}M`;
}

export function fmtUptime(secs) {
  if (!secs) return '—';
  const d = Math.floor(secs / 86400);
  const h = Math.floor((secs % 86400) / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function timeAgo(iso) {
  if (!iso) return '—';
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 5) return 'just now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export const VENDOR_COLORS = {
  mikrotik: 'hsl(var(--vendor-mikrotik))',
  ubiquiti: 'hsl(var(--vendor-ubiquiti))',
  cambium: 'hsl(var(--vendor-cambium))',
  mimosa: 'hsl(var(--vendor-mimosa))',
  generic: 'hsl(215 14% 60%)',
};

export const VENDOR_LABEL = {
  mikrotik: 'MikroTik', ubiquiti: 'Ubiquiti', cambium: 'Cambium', mimosa: 'Mimosa', generic: 'Generic',
};

export const ROLE_LABEL = {
  router: 'Router', switch: 'Switch', ap: 'Access Point', backhaul: 'Backhaul', cpe: 'CPE', device: 'Device',
};

export function vendorColor(v) { return VENDOR_COLORS[v] || VENDOR_COLORS.generic; }

export function utilColor(util) {
  if (util >= 85) return 'hsl(var(--status-crit))';
  if (util >= 60) return 'hsl(var(--status-warn))';
  if (util >= 1) return 'hsl(var(--status-ok))';
  return 'hsl(var(--muted-foreground))';
}

export function severityColor(sev) {
  return {
    critical: 'hsl(var(--status-crit))',
    warning: 'hsl(var(--status-warn))',
    info: 'hsl(var(--status-info))',
    ok: 'hsl(var(--status-ok))',
  }[sev] || 'hsl(var(--muted-foreground))';
}

// Edge dash speed: higher utilization => a bit faster, but overall calm. util is 0..100
export function edgeSpeed(util) {
  const u = Math.min(1, (util || 0) / 100);
  return (Math.max(3, 8 - u * 5)).toFixed(2) + 's';
}

export const REDUCED_MOTION =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;
