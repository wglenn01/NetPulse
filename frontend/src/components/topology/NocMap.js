import React, { useEffect, useMemo } from 'react';
import {
  ReactFlow, ReactFlowProvider, Background, Controls, BackgroundVariant,
  useNodesState, useEdgesState,
} from '@xyflow/react';
import { usePoll } from '@/lib/api';
import { DeviceNode } from '@/components/topology/DeviceNode';
import { TrafficEdge } from '@/components/topology/TrafficEdge';
import { edgeSpeed, REDUCED_MOTION } from '@/lib/format';

const nodeTypes = { device: DeviceNode };
const edgeTypes = { traffic: TrafficEdge };

function Legend() {
  const items = [
    ['Active traffic', 'hsl(var(--traffic-active))'],
    ['High load', 'hsl(var(--status-warn))'],
    ['Congested', 'hsl(var(--status-crit))'],
    ['Idle / down', 'hsl(var(--muted-foreground))'],
  ];
  return (
    <div className="absolute bottom-5 left-5 z-10 rounded-xl bg-card/90 border border-primary/20 px-4 py-3 backdrop-blur">
      <div className="hud-label !text-xs mb-2">Link Traffic</div>
      <div className="space-y-1.5">
        {items.map(([l, c]) => (
          <div key={l} className="flex items-center gap-2.5 text-sm font-mono">
            <span className="inline-block w-5 h-0.5 rounded" style={{ background: c }} />{l}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Read-only, always-labelled topology map for the NOC wallboard. */
function NocMapInner() {
  const { data } = usePoll('/topology', 4000);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!data) return;
    setNodes((prev) => {
      const pos = Object.fromEntries(prev.map((n) => [n.id, n.position]));
      return data.nodes.map((n) => ({
        id: n.id, type: 'device',
        position: pos[n.id] || { x: n.x, y: n.y },
        data: n, draggable: false, selectable: false, connectable: false,
      }));
    });
    setEdges(
      data.edges.map((e) => ({
        id: e.id, source: e.source, target: e.target, type: 'traffic',
        data: { ...e, speed: REDUCED_MOTION ? '0s' : edgeSpeed(e.util), showLabels: true },
      }))
    );
  }, [data, setNodes, setEdges]);

  const fitOpts = useMemo(() => ({ padding: 0.18 }), []);

  return (
    <div className="absolute inset-0" data-testid="noc-topology">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={fitOpts}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        nodesConnectable={false}
        nodesDraggable={false}
        elementsSelectable={false}
        panOnDrag
        zoomOnScroll
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1.2} color="hsl(142 40% 40% / 0.16)" />
        <Controls showInteractive={false} position="top-left" />
      </ReactFlow>
      <Legend />
    </div>
  );
}

export function NocMap() {
  return (
    <ReactFlowProvider>
      <NocMapInner />
    </ReactFlowProvider>
  );
}
