import { memo, useCallback, useEffect, useRef, useState } from "react";
import {
  applyNodeChanges,
  Background,
  Connection,
  ConnectionLineType,
  Controls,
  Edge,
  EdgeChange,
  MarkerType,
  MiniMap,
  Node,
  NodeChange,
  NodeTypes,
  ReactFlow,
  ReactFlowInstance
} from "@xyflow/react";

import { findSnapTargetInput, type SnapNodeInput } from "../../editor_connect";
import { NodePos } from "../../app_types";

type EditorCanvasProps = {
  nodes: Node[];
  edges: Edge[];
  nodeTypes: NodeTypes;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  onInit: (instance: ReactFlowInstance<any, any>) => void;
  onNodeSelect: (nodeId: string) => void;
  onNodesRemoved: (nodeIds: string[]) => void;
  onPositionsCommit: (positions: Record<string, NodePos>) => void;
};

function eventClientPoint(evt: MouseEvent | TouchEvent): { x: number; y: number } | null {
  if ("clientX" in evt && typeof evt.clientX === "number") {
    return {
      x: evt.clientX,
      y: evt.clientY
    };
  }
  const touch = "changedTouches" in evt ? evt.changedTouches?.[0] ?? evt.touches?.[0] : null;
  if (!touch) {
    return null;
  }
  return {
    x: touch.clientX,
    y: touch.clientY
  };
}

const EDGE_COLOR = "#9cc3dd";
const EDGE_STYLE = {
  stroke: EDGE_COLOR,
  strokeWidth: 2.25
};

export const EditorCanvas = memo(function EditorCanvas({
  nodes,
  edges,
  nodeTypes,
  onEdgesChange,
  onConnect,
  onInit,
  onNodeSelect,
  onNodesRemoved,
  onPositionsCommit
}: EditorCanvasProps) {
  const [localNodes, setLocalNodes] = useState<Node[]>(nodes);
  const localNodesRef = useRef<Node[]>(nodes);
  const flowRef = useRef<ReactFlowInstance<any, any> | null>(null);
  const connectStartRef = useRef<{ sourceId: string; sourceHandle: string } | null>(null);
  const didConnectRef = useRef(false);

  useEffect(() => {
    setLocalNodes(nodes);
  }, [nodes]);

  useEffect(() => {
    localNodesRef.current = localNodes;
  }, [localNodes]);

  const commitPositions = useCallback(() => {
    const currentNodes = flowRef.current?.getNodes?.() ?? localNodesRef.current;
    const nextPositions: Record<string, NodePos> = {};
    for (const row of currentNodes) {
      nextPositions[String(row.id)] = {
        x: Number(row.position?.x ?? 0),
        y: Number(row.position?.y ?? 0)
      };
    }
    onPositionsCommit(nextPositions);
  }, [onPositionsCommit]);

  const onLocalNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setLocalNodes((prev) => applyNodeChanges(changes, prev as Node[]));
      const removed = changes.filter((change) => change.type === "remove").map((change) => String(change.id));
      if (removed.length > 0) {
        onNodesRemoved(removed);
      }
    },
    [onNodesRemoved]
  );

  const onNodeClick = useCallback(
    (_evt: unknown, node: Node) => {
      onNodeSelect(String(node.id));
    },
    [onNodeSelect]
  );

  const onLocalConnectStart = useCallback((_event: unknown, params: { nodeId?: string | null; handleId?: string | null }) => {
    didConnectRef.current = false;
    const sourceId = String(params?.nodeId ?? "").trim();
    if (!sourceId) {
      connectStartRef.current = null;
      return;
    }
    const sourceHandle = String(params?.handleId ?? "out");
    connectStartRef.current = { sourceId, sourceHandle };
  }, []);

  const onLocalConnect = useCallback(
    (connection: Connection) => {
      didConnectRef.current = true;
      onConnect(connection);
    },
    [onConnect]
  );

  const onLocalConnectEnd = useCallback(
    (event: MouseEvent | TouchEvent) => {
      const started = connectStartRef.current;
      connectStartRef.current = null;

      if (!started || didConnectRef.current) {
        return;
      }

      const flow = flowRef.current;
      if (!flow) {
        return;
      }
      const point = eventClientPoint(event);
      if (!point) {
        return;
      }
      const flowPoint = flow.screenToFlowPosition(point);
      const zoom = typeof flow.getZoom === "function" ? flow.getZoom() : 1;
      const thresholdFlow = 42 / Math.max(zoom, 0.001);
      const target = findSnapTargetInput({
        flowPoint,
        nodes: flow.getNodes() as unknown as SnapNodeInput[],
        sourceNodeId: started.sourceId,
        thresholdFlow
      });
      if (!target) {
        return;
      }
      onConnect({
        source: started.sourceId,
        sourceHandle: started.sourceHandle || "out",
        target: target.nodeId,
        targetHandle: target.handleId
      });
    },
    [onConnect]
  );

  return (
    <ReactFlow
      nodes={localNodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      elementsSelectable
      nodesDraggable
      nodesConnectable
      zoomOnDoubleClick={false}
      connectionRadius={42}
      connectOnClick
      connectionLineType={ConnectionLineType.Step}
      connectionLineStyle={EDGE_STYLE}
      defaultEdgeOptions={{
        type: "step",
        style: EDGE_STYLE,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: EDGE_COLOR,
          width: 20,
          height: 20
        }
      }}
      onNodesChange={onLocalNodesChange}
      onEdgesChange={onEdgesChange}
      onConnectStart={onLocalConnectStart}
      onConnect={onLocalConnect}
      onConnectEnd={onLocalConnectEnd}
      onNodeClick={onNodeClick}
      onNodeDragStop={commitPositions}
      onSelectionDragStop={commitPositions}
      onInit={(instance) => {
        flowRef.current = instance;
        onInit(instance);
      }}
    >
      <MiniMap />
      <Controls />
      <Background />
    </ReactFlow>
  );
});
