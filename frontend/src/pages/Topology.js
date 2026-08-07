import React, { useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow, ReactFlowProvider, Background, Controls, BackgroundVariant,
  useNodesState, useEdgesState,
} from '@xyflow/react';
import { usePoll, api } from '@/lib/api';
import { DeviceNode } from '@/components/topology/DeviceNode';
import { TrafficEdge } from '@/components/topology/TrafficEdge';
import { DeviceDrawer } from '@/components/DeviceDrawer';
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
    <div className="absolute bottom-4 left-4 z-10 rounded-xl bg-card/90 border border-white/10 px-3 py-2.5 backdrop-blur">
      <div className="text-[11px] font-medium text-muted-foreground mb-1.5">Link Traffic</div>
      <div className="space-y-1">
        {items.map(([l, c]) => (
          <div key={l} className="flex items-center gap-2 text-[11px]">
            <span className="inline-block w-4 h-0.5 rounded" style={{ background: c }} />{l}
          </div>
        ))}
      </div>
    </div>
  );
}

function TopologyInner() {
  const { data } = usePoll('/topology', 4000);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selected, setSelected] = React.useState(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  useEffect(() => {
    if (!data) return;
    setNodes((prev) => {
      const pos = Object.fromEntries(prev.map((n) => [n.id, n.position]));
      return data.nodes.map((n) => ({
        id: n.id,
        type: 'device',
        position: pos[n.id] || { x: n.x, y: n.y },
        data: n,
      }));
    });
    setEdges(
      data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'traffic',
        data: { ...e, speed: REDUCED_MOTION ? '0s' : edgeSpeed(e.util) },
      }))
    );
  }, [data, setNodes, setEdges]);

  const onNodeDragStop = useCallback((_e, node) => {
    api.patch(`/devices/${node.id}/position`, { x: node.position.x, y: node.position.y }).catch(() => {});
  }, []);

  const onNodeClick = useCallback((_e, node) => {
    setSelected(node.id);
    setDrawerOpen(true);
  }, []);

  return (
    <div className="absolute inset-0" data-testid="topology-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        nodesConnectable={false}
        elementsSelectable
      >
        <Background variant={BackgroundVariant.Dots} gap={26} size={1} color="rgba(255,255,255,0.06)" />
        <Controls showInteractive={false} />
      </ReactFlow>
      <Legend />
      <DeviceDrawer deviceId={selected} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

export default function Topology() {
  return (
    <div className="relative h-[calc(100vh-4rem)]">
      <ReactFlowProvider>
        <TopologyInner />
      </ReactFlowProvider>
    </div>
  );
}
