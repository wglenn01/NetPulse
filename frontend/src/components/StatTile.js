import React from 'react';

export function StatTile({ label, value, sub, accent = 'hsl(var(--primary))', icon: Icon, testid }) {
  return (
    <div
      data-testid={testid}
      className="rounded-xl bg-card text-card-foreground border border-white/5 p-4 sm:p-5 shadow-[0_10px_30px_rgba(0,0,0,0.35)] relative overflow-hidden"
    >
      <div className="absolute inset-x-0 top-0 h-1" style={{ background: accent, opacity: 0.8 }} />
      <div className="flex items-start justify-between gap-3">
        <div className="text-sm font-medium text-muted-foreground">{label}</div>
        {Icon && (
          <div className="h-8 w-8 rounded-lg flex items-center justify-center"
               style={{ background: 'rgba(255,255,255,0.04)', color: accent }}>
            <Icon size={16} />
          </div>
        )}
      </div>
      <div className="mt-2 text-2xl sm:text-3xl font-semibold tracking-tight tabular">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}
