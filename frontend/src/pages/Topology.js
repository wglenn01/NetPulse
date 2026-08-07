import React, { useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow, ReactFlowProvider, Background, Controls, BackgroundVariant,
  ConnectionMode, useNodesState, useEdgesState,
} from '@xyflow/react';
import { usePoll, api } from '@/lib/api';
import { DeviceNode } from '@/components/topology/DeviceNode';
import { TrafficEdge } from '@/components/topology/TrafficEdge';
import { DeviceDrawer } from '@/components/DeviceDrawer';
import { LinkManager } from '@/components/topology/LinkManager';
import { edgeSpeed, fmtSpeed, REDUCED_MOTION } from '@/lib/format';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Tag, Tags, ArrowLeftRight, Cable } from 'lucide-react';

const nodeTypes = { device: DeviceNode };
const edgeTypes = { traffic: TrafficEdge };

// strip the left-side handle prefix ("L::eth0" -> "eth0")
const normHandle = (h) => (h && h.startsWith('L::') ? h.slice(3) : h);

function Legend() {
  const items = [
    ['Active traffic', 'hsl(var(--traffic-active))'],
    ['High load', 'hsl(var(--status-warn))'],
    ['Congested', 'hsl(var(--status-crit))'],
    ['Idle / down', 'hsl(var(--muted-foreground))'],
  ];
  return (
    <div className="absolute bottom-4 left-4 z-10 rounded-xl bg-card/90 border border-primary/15 px-3 py-2.5 backdrop-blur">
      <div className="hud-label !text-[10px] mb-1.5">Link Traffic</div>
      <div className="space-y-1">
        {items.map(([l, c]) => (
          <div key={l} className="flex items-center gap-2 text-[11px] font-mono">
            <span className="inline-block w-4 h-0.5 rounded" style={{ background: c }} />{l}
          </div>
        ))}
      </div>
    </div>
  );
}

function ConnectConfirm({ pending, nodeMap, onClose, onCreated }) {
  const [label, setLabel] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  React.useEffect(() => { setLabel(''); }, [pending]);
  if (!pending) return null;

  const a = nodeMap[pending.a_device] || {};
  const b = nodeMap[pending.b_device] || {};
  const aPort = (a.ports || []).find((p) => p.name === pending.a_ifname);
  const speed = fmtSpeed(aPort?.speed_mbps);

  const create = async () => {
    setBusy(true);
    try {
      await api.post('/links', {
        a_device: pending.a_device, a_ifname: pending.a_ifname,
        b_device: pending.b_device, b_ifname: pending.b_ifname, label,
      });
      toast.success('Link created');
      onCreated?.();
      onClose();
    } catch {
      toast.error('Failed to create link');
    } finally { setBusy(false); }
  };

  return (
    <Dialog open={!!pending} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-card border-primary/20 max-w-md" data-testid="connect-confirm-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Cable size={17} className="text-primary" />Create Link</DialogTitle>
          <DialogDescription>Confirm this cable between two ports. Live traffic will drive the animated line.</DialogDescription>
        </DialogHeader>

        <div className="rounded-xl border border-primary/15 bg-white/[0.02] p-4">
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
            <div className="min-w-0">
              <div className="text-[13px] font-semibold truncate">{a.name || pending.a_device}</div>
              <div className="text-[11px] font-mono text-accent truncate">{pending.a_ifname}</div>
            </div>
            <ArrowLeftRight size={16} className="text-primary" />
            <div className="min-w-0">
              <div className="text-[13px] font-semibold truncate">{b.name || pending.b_device}</div>
              <div className="text-[11px] font-mono text-accent truncate">{pending.b_ifname}</div>
            </div>
          </div>
          {speed && (
            <div className="mt-3 flex items-center justify-center">
              <span className="hud-label">Detected speed:&nbsp;</span>
              <span className="text-[12px] font-mono text-accent" data-testid="connect-detected-speed">{speed}</span>
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Label (optional)</Label>
          <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. Ridge PtP"
                 data-testid="connect-link-label-input" autoFocus />
        </div>

        <DialogFooter>
          <Button variant="secondary" className="border border-border" onClick={onClose} data-testid="connect-cancel-button">Cancel</Button>
          <Button onClick={create} disabled={busy} className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary" data-testid="connect-create-button">
            <Cable size={15} className="mr-1.5" />{busy ? 'Creating…' : 'Create Link'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function TopologyInner() {
  const { data, refresh } = usePoll('/topology', 4000);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selected, setSelected] = React.useState(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [showLabels, setShowLabels] = React.useState(false);
  const [pending, setPending] = React.useState(null);

  const nodeMap = useMemo(
    () => Object.fromEntries((data?.nodes || []).map((n) => [n.id, n])),
    [data]
  );

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
        data: { ...e, speed: REDUCED_MOTION ? '0s' : edgeSpeed(e.util), showLabels },
      }))
    );
  }, [data, setNodes, setEdges, showLabels]);

  // keep edge label toggle live without waiting for the next poll
  useEffect(() => {
    setEdges((eds) => eds.map((e) => ({ ...e, data: { ...e.data, showLabels } })));
  }, [showLabels, setEdges]);

  const onNodeDragStop = useCallback((_e, node) => {
    api.patch(`/devices/${node.id}/position`, { x: node.position.x, y: node.position.y }).catch(() => {});
  }, []);

  const onNodeClick = useCallback((_e, node) => {
    setSelected(node.id);
    setDrawerOpen(true);
  }, []);

  const isValidConnection = useCallback((c) => c.source !== c.target, []);

  const onConnect = useCallback((c) => {
    const a_ifname = normHandle(c.sourceHandle);
    const b_ifname = normHandle(c.targetHandle);
    if (!c.source || !c.target || c.source === c.target) return;
    if (!a_ifname || !b_ifname) { toast.error('Drag between two specific ports'); return; }
    setPending({ a_device: c.source, a_ifname, b_device: c.target, b_ifname });
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
        onConnect={onConnect}
        isValidConnection={isValidConnection}
        connectionMode={ConnectionMode.Loose}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        nodesConnectable
        elementsSelectable
      >
        <Background variant={BackgroundVariant.Dots} gap={26} size={1} color="hsl(142 40% 40% / 0.14)" />
        <Controls showInteractive={false} />
      </ReactFlow>

      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <Button
          data-testid="toggle-link-labels-button"
          onClick={() => setShowLabels((v) => !v)}
          className={`backdrop-blur border ${showLabels
            ? 'bg-primary/15 border-primary/40 text-primary glow-primary'
            : 'bg-card/90 border-border text-foreground hover:bg-white/10'}`}
        >
          {showLabels ? <Tag size={16} className="mr-1.5" /> : <Tags size={16} className="mr-1.5" />}
          Link Labels
        </Button>
        <LinkManager onChange={refresh} />
      </div>

      <div className="absolute top-4 left-4 z-10 hud-label bg-card/70 border border-primary/15 rounded-lg px-2.5 py-1.5 backdrop-blur">
        Drag a port dot to another to connect · click a node for details
      </div>

      <Legend />
      <ConnectConfirm pending={pending} nodeMap={nodeMap} onClose={() => setPending(null)} onCreated={refresh} />
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
