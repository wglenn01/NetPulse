import React from 'react';

export function StatusDot({ up, size = 8, crit = false, className = '' }) {
  const color = up === false
    ? 'hsl(var(--status-crit))'
    : crit ? 'hsl(var(--status-warn))' : 'hsl(var(--status-ok))';
  return (
    <span
      className={`inline-block rounded-full ${className}`}
      style={{
        width: size, height: size, background: color,
        boxShadow: up === false ? '0 0 8px hsl(var(--status-crit))' : 'none',
      }}
    />
  );
}
