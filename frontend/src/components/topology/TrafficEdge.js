import React from 'react';
import { getBezierPath, EdgeLabelRenderer } from '@xyflow/react';
import { fmtBpsShort, fmtSpeed } from '@/lib/format';

export function TrafficEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data }) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  });
  const status = data?.status || 'idle';
  const util = data?.util || 0;
  const showAll = !!data?.showLabels;
  // Always show for non-idle links; when "Link Labels" toggle is on, show every link.
  const showLabel = showAll || status !== 'idle';
  if (!showLabel) {
    return (
      <path id={id} d={path} className={`np-edge edge--${status}`}
            style={{ '--edge-dash-speed': data?.speed || '1.6s' }} />
    );
  }

  const speed = fmtSpeed(data?.speed_mbps);
  const utilColorVal = util >= 85 ? 'hsl(var(--status-crit))' : util >= 60 ? 'hsl(var(--status-warn))' : 'hsl(var(--traffic-active))';

  return (
    <>
      <path
        id={id}
        d={path}
        className={`np-edge edge--${status}`}
        style={{ '--edge-dash-speed': data?.speed || '1.6s' }}
      />
      <EdgeLabelRenderer>
        <div
          data-testid={`edge-label-${id}`}
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'none',
          }}
          className="rounded-md border border-primary/25 bg-card/90 backdrop-blur px-1.5 py-1 text-center leading-tight"
        >
          {(data?.a_ifname || data?.b_ifname) && (
            <div className="text-[9px] font-mono text-muted-foreground whitespace-nowrap">
              {data?.a_ifname}<span className="text-primary/70 mx-0.5">⇄</span>{data?.b_ifname}
              {speed && <span className="ml-1 text-accent">· {speed}</span>}
            </div>
          )}
          <div className="text-[10px] font-mono tabular whitespace-nowrap">
            {status === 'down'
              ? <span className="text-status-crit">down</span>
              : <span style={{ color: utilColorVal }}>
                  {util.toFixed(0)}% · {fmtBpsShort((data?.in_bps || 0) + (data?.out_bps || 0))}
                </span>}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
