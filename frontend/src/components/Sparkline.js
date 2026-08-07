import React from 'react';
import { ResponsiveContainer, AreaChart, Area, YAxis } from 'recharts';

export function Sparkline({ data, dataKey = 'v', color = 'hsl(var(--chart-1))', height = 40 }) {
  const id = React.useId().replace(/:/g, '');
  if (!data || data.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-xs text-muted-foreground">no data</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.4} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <YAxis hide domain={[0, 'dataMax']} />
        <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.6}
              fill={`url(#spark-${id})`} isAnimationActive={false} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
