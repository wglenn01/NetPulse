import React from 'react';
import { getBezierPath, EdgeLabelRenderer } from '@xyflow/react';
import { fmtBpsShort } from '@/lib/format';

export function TrafficEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data }) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  });
  const status = data?.status || 'idle';
  const util = data?.util || 0;
  const showLabel = status !== 'idle';

  return (
    <>
      <path
        id={id}
        d={path}
        className={`np-edge edge--${status}`}
        style={{ '--edge-dash-speed': data?.speed || '1.6s' }}
      />
      {showLabel && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: 'none',
            }}
            className="px-1.5 py-0.5 rounded-md text-[10px] font-mono tabular border border-white/10 bg-card/90"
          >
            {status === 'down'
              ? <span className="text-status-crit">down</span>
              : <span style={{ color: util >= 85 ? 'hsl(var(--status-crit))' : util >= 60 ? 'hsl(var(--status-warn))' : 'hsl(var(--traffic-active))' }}>
                  {util.toFixed(0)}% · {fmtBpsShort((data?.in_bps || 0) + (data?.out_bps || 0))}
                </span>}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
