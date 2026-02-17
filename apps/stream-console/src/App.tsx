import { FormEvent, memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Background,
  Connection,
  Controls,
  Edge,
  EdgeChange,
  MiniMap,
  Node,
  NodeChange,
  NodeTypes,
  ReactFlowInstance,
  ReactFlow
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import YAML from "yaml";

import {
  apiRequest,
  defaultApiBase,
  GraphFromProfileOverrides,
  GraphSpecInput,
  normalizeGraphSpecInput
} from "./api";
import { alignNodePositions, computeAutoLayout } from "./editor_layout";
import { editorNodeTypes, EditorNodeKind } from "./editor_nodes";

type TabId = "dashboard" | "presets" | "fleet" | "monitor" | "editor" | "governance";

type PresetItem = {
  preset_id: string;
  experimental: boolean;
  graph: string;
  description: string;
};

type GraphProfileItem = {
  profile_id: string;
  experimental: boolean;
  template: string;
  description: string;
};

type NodePos = { x: number; y: number };

type EditorValidationSummary = {
  status: "ok" | "error";
  nodeCount: number;
  edgeCount: number;
  message: string;
};

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "presets", label: "Presets" },
  { id: "fleet", label: "Fleet" },
  { id: "monitor", label: "Monitor" },
  { id: "editor", label: "Editor" },
  { id: "governance", label: "Governance" }
];

function defaultPosition(index: number): NodePos {
  return {
    x: 100 + (index % 4) * 250,
    y: 80 + Math.floor(index / 4) * 180
  };
}

function defaultSpec(): GraphSpecInput {
  return {
    version: 2,
    nodes: [
      {
        id: "src",
        kind: "source",
        plugin: "schnitzel_stream.nodes.dev:StaticSource",
        config: {
          packets: [
            {
              kind: "demo",
              source_id: "editor_demo",
              payload: { message: "hello from block editor" }
            }
          ]
        }
      },
      {
        id: "out",
        kind: "sink",
        plugin: "schnitzel_stream.nodes.dev:PrintSink",
        config: {
          prefix: "EDITOR "
        }
      }
    ],
    edges: [{ src: "src", dst: "out" }],
    config: {}
  };
}

function defaultNodeTemplate(kind: "source" | "node" | "sink", id: string) {
  if (kind === "source") {
    return {
      id,
      kind,
      plugin: "schnitzel_stream.nodes.dev:StaticSource",
      config: {
        packets: [
          {
            kind: "demo",
            source_id: id,
            payload: { value: id }
          }
        ]
      }
    };
  }
  if (kind === "sink") {
    return {
      id,
      kind,
      plugin: "schnitzel_stream.nodes.dev:PrintSink",
      config: { prefix: `${id.toUpperCase()} ` }
    };
  }
  return {
    id,
    kind,
    plugin: "schnitzel_stream.nodes.dev:Identity",
    config: {}
  };
}

function nextNodeId(base: string, spec: GraphSpecInput): string {
  const normalized = base.trim() || "node";
  if (!spec.nodes.some((node) => node.id === normalized)) {
    return normalized;
  }
  let n = 2;
  while (spec.nodes.some((node) => node.id === `${normalized}_${n}`)) {
    n += 1;
  }
  return `${normalized}_${n}`;
}

function normalizeKind(kind: string): EditorNodeKind {
  const raw = kind.trim().toLowerCase();
  if (raw === "source") return "source";
  if (raw === "sink") return "sink";
  return "node";
}

function edgeIdentity(edge: { src: string; dst: string; src_port?: string; dst_port?: string }, index: number): string {
  return `${edge.src}|${edge.dst}|${edge.src_port ?? "*"}|${edge.dst_port ?? "*"}|${index}`;
}

function parseEditorValidationSummary(raw: unknown): EditorValidationSummary | null {
  if (!raw || typeof raw !== "object") return null;
  const row = raw as Record<string, unknown>;
  const ok = Boolean(row.ok);
  const nodeCount = Number(row.node_count ?? row.nodeCount ?? 0);
  const edgeCount = Number(row.edge_count ?? row.edgeCount ?? 0);
  const errorText = String(row.error ?? row.reason ?? "").trim();
  return {
    status: ok ? "ok" : "error",
    nodeCount: Number.isFinite(nodeCount) ? nodeCount : 0,
    edgeCount: Number.isFinite(edgeCount) ? edgeCount : 0,
    message: ok ? "graph validation passed" : errorText || "graph validation failed"
  };
}

function toNumber(value: string): number | undefined {
  const txt = value.trim();
  if (!txt) return undefined;
  const n = Number(txt);
  if (!Number.isFinite(n)) return undefined;
  return n;
}

function toBoolText(value: string): "" | "true" | "false" {
  const lower = value.trim().toLowerCase();
  if (lower === "true" || lower === "false") {
    return lower;
  }
  return "";
}

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

const EditorCanvas = memo(function EditorCanvas({
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
      onNodesChange={onLocalNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
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

export function App() {
  const [tab, setTab] = useState<TabId>("dashboard");
  const [apiBase, setApiBase] = useState<string>(defaultApiBase());
  const [token, setToken] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [fleetStatus, setFleetStatus] = useState<Record<string, unknown> | null>(null);
  const [monitorSnapshot, setMonitorSnapshot] = useState<Record<string, unknown> | null>(null);

  const [presets, setPresets] = useState<PresetItem[]>([]);
  const [showExperimental, setShowExperimental] = useState<boolean>(false);
  const [presetId, setPresetId] = useState<string>("inproc_demo");
  const [presetInputPath, setPresetInputPath] = useState<string>("");
  const [presetCameraIndex, setPresetCameraIndex] = useState<string>("0");
  const [presetDevice, setPresetDevice] = useState<string>("cpu");
  const [presetModelPath, setPresetModelPath] = useState<string>("");
  const [presetYoloConf, setPresetYoloConf] = useState<string>("");
  const [presetYoloIou, setPresetYoloIou] = useState<string>("");
  const [presetYoloMaxDet, setPresetYoloMaxDet] = useState<string>("");
  const [presetLoop, setPresetLoop] = useState<string>("");
  const [presetMaxEvents, setPresetMaxEvents] = useState<string>("");

  const [fleetConfig, setFleetConfig] = useState<string>("configs/fleet.yaml");
  const [fleetGraphTemplate, setFleetGraphTemplate] = useState<string>("configs/graphs/dev_stream_template_v2.yaml");
  const [fleetLogDir, setFleetLogDir] = useState<string>("");
  const [fleetStreams, setFleetStreams] = useState<string>("");
  const [fleetExtraArgs, setFleetExtraArgs] = useState<string>("");

  const [auditLimit, setAuditLimit] = useState<string>("50");
  const [policySnapshot, setPolicySnapshot] = useState<Record<string, unknown> | null>(null);
  const [auditRows, setAuditRows] = useState<Record<string, unknown>[]>([]);
  const [presetSessionOutput, setPresetSessionOutput] = useState<string>("(no preset session output yet)");

  const [editorSpec, setEditorSpec] = useState<GraphSpecInput>(() => defaultSpec());
  const [editorPositions, setEditorPositions] = useState<Record<string, NodePos>>({
    src: { x: 100, y: 100 },
    out: { x: 420, y: 100 }
  });
  const [editorYaml, setEditorYaml] = useState<string>(() => YAML.stringify(defaultSpec()));
  const [editorActionLog, setEditorActionLog] = useState<string>("(no local editor action yet)");
  const [editorApiOutput, setEditorApiOutput] = useState<string>("(no editor API output yet)");
  const [editorValidationSummary, setEditorValidationSummary] = useState<EditorValidationSummary | null>(null);
  const [editorProfiles, setEditorProfiles] = useState<GraphProfileItem[]>([]);
  const [editorProfileId, setEditorProfileId] = useState<string>("inproc_demo");
  const [editorAllowExperimental, setEditorAllowExperimental] = useState<boolean>(false);
  const [editorInputPath, setEditorInputPath] = useState<string>("");
  const [editorCameraIndex, setEditorCameraIndex] = useState<string>("");
  const [editorDevice, setEditorDevice] = useState<string>("cpu");
  const [editorModelPath, setEditorModelPath] = useState<string>("");
  const [editorLoop, setEditorLoop] = useState<string>("");
  const [editorMaxEvents, setEditorMaxEvents] = useState<string>("30");
  const [editorSelectedNode, setEditorSelectedNode] = useState<string>("src");
  const [editorNodeId, setEditorNodeId] = useState<string>("src");
  const [editorNodeKind, setEditorNodeKind] = useState<string>("source");
  const [editorNodePlugin, setEditorNodePlugin] = useState<string>("schnitzel_stream.nodes.dev:StaticSource");
  const [editorNodeConfig, setEditorNodeConfig] = useState<string>(
    JSON.stringify(defaultSpec().nodes[0].config, null, 2)
  );
  const [editorNodePosX, setEditorNodePosX] = useState<string>("100");
  const [editorNodePosY, setEditorNodePosY] = useState<string>("100");
  const [editorEdgeSrc, setEditorEdgeSrc] = useState<string>("src");
  const [editorEdgeDst, setEditorEdgeDst] = useState<string>("out");

  const [output, setOutput] = useState<string>("Ready");
  const [flowInstance, setFlowInstance] = useState<ReactFlowInstance<any, any> | null>(null);
  const currentPreset = useMemo(() => presets.find((x) => x.preset_id === presetId), [presets, presetId]);
  const currentEditorProfile = useMemo(
    () => editorProfiles.find((item) => item.profile_id === editorProfileId),
    [editorProfiles, editorProfileId]
  );

  const flowNodes = useMemo(() => {
    return editorSpec.nodes.map((node, idx) => {
      const kind = normalizeKind(node.kind);
      const pos = editorPositions[node.id] ?? defaultPosition(idx);
      return {
        id: node.id,
        type: kind,
        position: { x: pos.x, y: pos.y },
        selected: node.id === editorSelectedNode,
        data: {
          id: node.id,
          kind,
          plugin: node.plugin,
          label: kind
        }
      };
    });
  }, [editorPositions, editorSelectedNode, editorSpec.nodes]);

  const flowEdges = useMemo(() => {
    return editorSpec.edges.map((edge, idx) => ({
      id: edgeIdentity(edge, idx),
      source: edge.src,
      target: edge.dst,
      sourceHandle: edge.src_port,
      targetHandle: edge.dst_port,
      label: edge.src_port || edge.dst_port ? `${edge.src_port ?? "*"} -> ${edge.dst_port ?? "*"}` : undefined
    }));
  }, [editorSpec.edges]);

  function syncEditorYaml(spec: GraphSpecInput) {
    setEditorYaml(YAML.stringify(spec));
  }

  function selectEditorNode(nodeId: string, spec: GraphSpecInput = editorSpec, positions: Record<string, NodePos> = editorPositions) {
    const node = spec.nodes.find((item) => item.id === nodeId);
    if (!node) {
      return;
    }
    setEditorSelectedNode(node.id);
    setEditorNodeId(node.id);
    setEditorNodeKind(node.kind);
    setEditorNodePlugin(node.plugin);
    setEditorNodeConfig(JSON.stringify(node.config ?? {}, null, 2));
    const idx = spec.nodes.findIndex((item) => item.id === node.id);
    const pos = positions[node.id] ?? defaultPosition(Math.max(0, idx));
    setEditorNodePosX(String(Math.round(pos.x)));
    setEditorNodePosY(String(Math.round(pos.y)));
  }

  function applyEditorSpec(spec: GraphSpecInput, positions: Record<string, NodePos>) {
    setEditorSpec(spec);
    setEditorPositions(positions);
    syncEditorYaml(spec);
    setEditorValidationSummary(null);

    if (!spec.nodes.length) {
      setEditorSelectedNode("");
      setEditorNodeId("");
      setEditorNodeKind("node");
      setEditorNodePlugin("schnitzel_stream.nodes.dev:Identity");
      setEditorNodeConfig("{}");
      setEditorNodePosX("0");
      setEditorNodePosY("0");
      setEditorEdgeSrc("");
      setEditorEdgeDst("");
      return;
    }

    const selected =
      spec.nodes.find((node) => node.id === editorSelectedNode)?.id ??
      spec.nodes[0].id;
    const src = spec.nodes.find((node) => node.id === editorEdgeSrc)?.id ?? spec.nodes[0].id;
    const dst = spec.nodes.find((node) => node.id === editorEdgeDst)?.id ?? spec.nodes[Math.min(1, spec.nodes.length - 1)].id;

    setEditorEdgeSrc(src);
    setEditorEdgeDst(dst);
    selectEditorNode(selected, spec, positions);
  }

  function writeEditorAction(payload: unknown): void {
    setEditorActionLog(JSON.stringify(payload, null, 2));
  }

  function writeEditorApi(payload: unknown): void {
    setEditorApiOutput(JSON.stringify(payload, null, 2));
  }

  const onFlowEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      const nextFlowEdges = applyEdgeChanges(changes, flowEdges as Edge[]);
      const nextEdges = nextFlowEdges.map((edge) => {
        const out: GraphSpecInput["edges"][number] = {
          src: edge.source,
          dst: edge.target
        };
        if (edge.sourceHandle) out.src_port = edge.sourceHandle;
        if (edge.targetHandle) out.dst_port = edge.targetHandle;
        return out;
      });

      const currentSignatures = editorSpec.edges.map((edge, idx) => edgeIdentity(edge, idx));
      const nextSignatures = nextEdges.map((edge, idx) => edgeIdentity(edge, idx));
      const structuralChange =
        currentSignatures.length !== nextSignatures.length ||
        currentSignatures.some((sig, idx) => sig !== nextSignatures[idx]);
      if (!structuralChange) {
        return;
      }

      applyEditorSpec(
        {
          ...editorSpec,
          edges: nextEdges
        },
        editorPositions
      );
      writeEditorAction({
        action: "editor.edge.sync.canvas",
        edges: nextEdges.length
      });
    },
    [editorPositions, editorSpec, flowEdges]
  );

  const onCanvasNodesRemoved = useCallback(
    (nodeIds: string[]) => {
      if (nodeIds.length === 0) {
        return;
      }
      const removedSet = new Set(nodeIds);
      const nextNodes = editorSpec.nodes.filter((node) => !removedSet.has(node.id));
      const nextEdges = editorSpec.edges.filter((edge) => !removedSet.has(edge.src) && !removedSet.has(edge.dst));
      const nextPositions = { ...editorPositions };
      for (const id of nodeIds) {
        delete nextPositions[id];
      }
      applyEditorSpec(
        {
          ...editorSpec,
          nodes: nextNodes,
          edges: nextEdges
        },
        nextPositions
      );
      writeEditorAction({
        action: "editor.node.remove.canvas",
        node_ids: nodeIds
      });
    },
    [editorPositions, editorSpec]
  );

  const onCanvasPositionsCommit = useCallback(
    (nextPositions: Record<string, NodePos>) => {
      applyEditorPositions(nextPositions);
      writeEditorAction({
        action: "editor.node.position.commit",
        nodes: Object.keys(nextPositions).length
      });
    },
    [editorSelectedNode]
  );

  const onCanvasNodeSelect = useCallback(
    (nodeId: string) => {
      setEditorSelectedNode(nodeId);
      selectEditorNode(nodeId);
    },
    [editorPositions, editorSpec]
  );

  const onFlowConnect = useCallback(
    (connection: Connection) => {
      const src = String(connection.source ?? "").trim();
      const dst = String(connection.target ?? "").trim();
      if (!src || !dst) {
        setOutput("[ERROR] editor.edge.connect: source/target are required");
        return;
      }

      const srcNode = editorSpec.nodes.find((node) => node.id === src);
      const dstNode = editorSpec.nodes.find((node) => node.id === dst);
      if (!srcNode || !dstNode) {
        setOutput("[ERROR] editor.edge.connect: source/target must refer to existing nodes");
        return;
      }
      if (normalizeKind(srcNode.kind) === "sink") {
        setOutput("[ERROR] editor.edge.connect: sink cannot have outgoing edges");
        return;
      }
      if (normalizeKind(dstNode.kind) === "source") {
        setOutput("[ERROR] editor.edge.connect: source cannot have incoming edges");
        return;
      }

      const nextFlowEdges = addEdge(
        {
          source: src,
          target: dst,
          sourceHandle: connection.sourceHandle ?? null,
          targetHandle: connection.targetHandle ?? null
        },
        flowEdges as Edge[]
      );
      const nextEdges = nextFlowEdges.map((edge) => {
        const out: GraphSpecInput["edges"][number] = { src: edge.source, dst: edge.target };
        if (edge.sourceHandle) out.src_port = edge.sourceHandle;
        if (edge.targetHandle) out.dst_port = edge.targetHandle;
        return out;
      });

      const duplicateCount = nextEdges.filter(
        (edge) =>
          edge.src === src &&
          edge.dst === dst &&
          (edge.src_port ?? "") === (connection.sourceHandle ?? "") &&
          (edge.dst_port ?? "") === (connection.targetHandle ?? "")
      ).length;
      if (duplicateCount > 1) {
        setOutput("[ERROR] editor.edge.connect: duplicate edge");
        return;
      }

      applyEditorSpec(
        {
          ...editorSpec,
          edges: nextEdges
        },
        editorPositions
      );
      writeEditorAction({
        action: "editor.edge.connect.canvas",
        src,
        dst,
        src_port: connection.sourceHandle ?? "",
        dst_port: connection.targetHandle ?? ""
      });
    },
    [editorPositions, editorSpec, flowEdges]
  );

  function applyEditorPositions(nextPositions: Record<string, NodePos>): void {
    setEditorPositions(nextPositions);
    if (editorSelectedNode && nextPositions[editorSelectedNode]) {
      setEditorNodePosX(String(Math.round(nextPositions[editorSelectedNode].x)));
      setEditorNodePosY(String(Math.round(nextPositions[editorSelectedNode].y)));
    }
  }

  function autoLayoutEditor(): void {
    const nextPositions = computeAutoLayout(editorSpec.nodes, editorSpec.edges);
    applyEditorPositions(nextPositions);
    writeEditorAction({
      action: "editor.layout.auto",
      nodes: editorSpec.nodes.length
    });
    flowInstance?.fitView({ padding: 0.2, duration: 250 });
  }

  function alignEditor(axis: "horizontal" | "vertical"): void {
    const nodeIds = editorSpec.nodes.map((node) => node.id);
    const nextPositions = alignNodePositions(editorPositions, nodeIds, axis);
    applyEditorPositions(nextPositions);
    writeEditorAction({
      action: `editor.layout.align.${axis}`,
      nodes: nodeIds.length
    });
    flowInstance?.fitView({ padding: 0.2, duration: 250 });
  }

  function fitEditorView(): void {
    flowInstance?.fitView({ padding: 0.2, duration: 250 });
  }

  async function runAction(label: string, fn: () => Promise<void>) {
    setBusy(true);
    try {
      await fn();
      setOutput(`[OK] ${label}`);
    } catch (err) {
      setOutput(`[ERROR] ${label}: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function loadDashboard() {
    await runAction("dashboard.refresh", async () => {
      const [healthResp, fleetResp, monitorResp] = await Promise.all([
        apiRequest<{ [k: string]: unknown }>("/api/v1/health", { baseUrl: apiBase, token }),
        apiRequest<{ [k: string]: unknown }>("/api/v1/fleet/status", { baseUrl: apiBase, token }),
        apiRequest<{ [k: string]: unknown }>("/api/v1/monitor/snapshot", { baseUrl: apiBase, token })
      ]);
      setHealth(healthResp.data);
      setFleetStatus(fleetResp.data);
      setMonitorSnapshot(monitorResp.data);
    });
  }

  async function loadPresets() {
    await runAction("presets.list", async () => {
      const resp = await apiRequest<{ presets?: PresetItem[] }>(
        `/api/v1/presets?experimental=${showExperimental ? "true" : "false"}`,
        { baseUrl: apiBase, token }
      );
      const rows = Array.isArray(resp.data.presets) ? resp.data.presets : [];
      setPresets(rows);
      if (!rows.some((row) => row.preset_id === presetId) && rows.length > 0) {
        setPresetId(rows[0].preset_id);
      }
    });
  }

  async function runPreset(validateOnly: boolean) {
    await runAction(validateOnly ? "preset.validate" : "preset.run", async () => {
      const body: Record<string, unknown> = {
        experimental: showExperimental,
        device: presetDevice
      };
      if (presetInputPath.trim()) body.input_path = presetInputPath.trim();
      if (presetLoop.trim()) body.loop = presetLoop.trim();
      if (presetCameraIndex.trim()) body.camera_index = Number(presetCameraIndex);
      if (presetMaxEvents.trim()) body.max_events = Number(presetMaxEvents);
      if (presetModelPath.trim()) body.model_path = presetModelPath.trim();
      if (presetYoloConf.trim()) body.yolo_conf = Number(presetYoloConf);
      if (presetYoloIou.trim()) body.yolo_iou = Number(presetYoloIou);
      if (presetYoloMaxDet.trim()) body.yolo_max_det = Number(presetYoloMaxDet);

      const route = validateOnly ? `/api/v1/presets/${presetId}/validate` : `/api/v1/presets/${presetId}/run`;
      const resp = await apiRequest<{ [k: string]: unknown }>(route, {
        baseUrl: apiBase,
        token,
        method: "POST",
        body
      });
      setPresetSessionOutput(JSON.stringify(resp, null, 2));
      setOutput(JSON.stringify(resp, null, 2));
    });
  }

  async function fleetStart() {
    await runAction("fleet.start", async () => {
      const body: Record<string, unknown> = {
        config: fleetConfig,
        graph_template: fleetGraphTemplate,
        streams: fleetStreams,
        extra_args: fleetExtraArgs
      };
      if (fleetLogDir.trim()) body.log_dir = fleetLogDir.trim();
      const resp = await apiRequest<{ [k: string]: unknown }>("/api/v1/fleet/start", {
        baseUrl: apiBase,
        token,
        method: "POST",
        body
      });
      setOutput(JSON.stringify(resp, null, 2));
    });
  }

  async function fleetStop() {
    await runAction("fleet.stop", async () => {
      const body: Record<string, unknown> = {};
      if (fleetLogDir.trim()) body.log_dir = fleetLogDir.trim();
      const resp = await apiRequest<{ [k: string]: unknown }>("/api/v1/fleet/stop", {
        baseUrl: apiBase,
        token,
        method: "POST",
        body
      });
      setOutput(JSON.stringify(resp, null, 2));
    });
  }

  async function fleetQueryStatus() {
    await runAction("fleet.status", async () => {
      const path = fleetLogDir.trim() ? `/api/v1/fleet/status?log_dir=${encodeURIComponent(fleetLogDir.trim())}` : "/api/v1/fleet/status";
      const resp = await apiRequest<{ [k: string]: unknown }>(path, { baseUrl: apiBase, token });
      setFleetStatus(resp.data);
      setOutput(JSON.stringify(resp, null, 2));
    });
  }

  async function monitorQuerySnapshot() {
    await runAction("monitor.snapshot", async () => {
      const path = fleetLogDir.trim()
        ? `/api/v1/monitor/snapshot?log_dir=${encodeURIComponent(fleetLogDir.trim())}`
        : "/api/v1/monitor/snapshot";
      const resp = await apiRequest<{ snapshot?: Record<string, unknown> }>(path, { baseUrl: apiBase, token });
      setMonitorSnapshot(resp.data.snapshot ?? null);
      setOutput(JSON.stringify(resp, null, 2));
    });
  }

  async function loadGovernance() {
    await runAction("governance.refresh", async () => {
      const policyResp = await apiRequest<{ [k: string]: unknown }>("/api/v1/governance/policy-snapshot", {
        baseUrl: apiBase,
        token
      });
      const limit = Number(auditLimit) > 0 ? Number(auditLimit) : 50;
      const auditResp = await apiRequest<{ events?: Record<string, unknown>[] }>(
        `/api/v1/governance/audit?limit=${limit}`,
        { baseUrl: apiBase, token }
      );
      setPolicySnapshot(policyResp.data);
      setAuditRows(Array.isArray(auditResp.data.events) ? auditResp.data.events : []);
    });
  }

  async function loadEditorProfiles() {
    await runAction("graph.profiles", async () => {
      const resp = await apiRequest<{ profiles?: GraphProfileItem[] }>(
        `/api/v1/graph/profiles?experimental=${editorAllowExperimental ? "true" : "false"}`,
        { baseUrl: apiBase, token }
      );
      const rows = Array.isArray(resp.data.profiles) ? resp.data.profiles : [];
      setEditorProfiles(rows);
      if (rows.length > 0 && !rows.some((row) => row.profile_id === editorProfileId)) {
        setEditorProfileId(rows[0].profile_id);
      }
      writeEditorApi(resp);
      setEditorValidationSummary(null);
    });
  }

  function buildProfileOverrides(): GraphFromProfileOverrides {
    const ov: GraphFromProfileOverrides = {};
    if (editorInputPath.trim()) ov.input_path = editorInputPath.trim();
    const camera = toNumber(editorCameraIndex);
    if (camera !== undefined) ov.camera_index = camera;
    if (editorDevice.trim()) ov.device = editorDevice.trim();
    if (editorModelPath.trim()) ov.model_path = editorModelPath.trim();
    const loop = toBoolText(editorLoop);
    if (loop) ov.loop = loop;
    const maxEvents = toNumber(editorMaxEvents);
    if (maxEvents !== undefined && maxEvents > 0) ov.max_events = maxEvents;
    return ov;
  }

  async function editorLoadFromProfile() {
    await runAction("graph.from_profile", async () => {
      if (!editorProfileId.trim()) {
        throw new Error("profile_id is required");
      }
      const resp = await apiRequest<{ spec?: unknown; profile_id?: string; overrides?: Record<string, string> }>(
        "/api/v1/graph/from-profile",
        {
          baseUrl: apiBase,
          token,
          method: "POST",
          body: {
            profile_id: editorProfileId.trim(),
            experimental: editorAllowExperimental,
            overrides: buildProfileOverrides()
          }
        }
      );
      const spec = normalizeGraphSpecInput(resp.data.spec ?? {});
      const positions: Record<string, NodePos> = {};
      spec.nodes.forEach((node, idx) => {
        positions[node.id] = defaultPosition(idx);
      });
      applyEditorSpec(spec, positions);
      writeEditorApi(resp);
      setEditorValidationSummary(parseEditorValidationSummary((resp.data as Record<string, unknown>).validation));
    });
  }

  async function editorValidate() {
    await runAction("graph.validate", async () => {
      const resp = await apiRequest<{ validation?: Record<string, unknown> }>("/api/v1/graph/validate", {
        baseUrl: apiBase,
        token,
        method: "POST",
        body: {
          spec: editorSpec
        }
      });
      writeEditorApi(resp);
      setEditorValidationSummary(parseEditorValidationSummary(resp.data.validation));
    });
  }

  async function editorRun() {
    await runAction("graph.run", async () => {
      const maxEvents = toNumber(editorMaxEvents) ?? 30;
      const resp = await apiRequest<{ returncode?: number; command?: string; temp_spec_path?: string }>(
        "/api/v1/graph/run",
        {
          baseUrl: apiBase,
          token,
          method: "POST",
          body: {
            spec: editorSpec,
            max_events: maxEvents
          }
        }
      );
      writeEditorApi(resp);
    });
  }

  function addEditorNode(kind: "source" | "node" | "sink") {
    const base = kind === "source" ? "source" : kind === "sink" ? "sink" : "node";
    const nodeId = nextNodeId(base, editorSpec);
    const nextNode = defaultNodeTemplate(kind, nodeId);
    const nextSpec: GraphSpecInput = {
      ...editorSpec,
      nodes: [...editorSpec.nodes, nextNode]
    };
    const nextPositions = {
      ...editorPositions,
      [nodeId]: defaultPosition(nextSpec.nodes.length - 1)
    };
    applyEditorSpec(nextSpec, nextPositions);
  }

  function saveSelectedNode() {
    if (!editorSelectedNode.trim()) return;

    let config: Record<string, unknown> = {};
    try {
      const parsed = JSON.parse(editorNodeConfig || "{}");
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("node config must be JSON object");
      }
      config = parsed as Record<string, unknown>;
    } catch (err) {
      setOutput(`[ERROR] editor.node.save: invalid node config json (${String(err)})`);
      return;
    }

    const targetId = editorSelectedNode.trim();
    const nextIdRaw = editorNodeId.trim();
    if (!nextIdRaw) {
      setOutput("[ERROR] editor.node.save: node id is required");
      return;
    }
    if (nextIdRaw !== targetId && editorSpec.nodes.some((node) => node.id === nextIdRaw)) {
      setOutput(`[ERROR] editor.node.save: node id already exists (${nextIdRaw})`);
      return;
    }
    const nextX = toNumber(editorNodePosX);
    const nextY = toNumber(editorNodePosY);
    if (nextX === undefined || nextY === undefined) {
      setOutput("[ERROR] editor.node.save: x/y must be valid numbers");
      return;
    }

    const nextNodes = editorSpec.nodes.map((node) => {
      if (node.id !== targetId) return node;
      return {
        ...node,
        id: nextIdRaw,
        kind: editorNodeKind.trim() || "node",
        plugin: editorNodePlugin.trim(),
        config
      };
    });
    const nextEdges = editorSpec.edges.map((edge) => ({
      ...edge,
      src: edge.src === targetId ? nextIdRaw : edge.src,
      dst: edge.dst === targetId ? nextIdRaw : edge.dst
    }));
    const nextPositions = { ...editorPositions };
    const oldPos = nextPositions[targetId] ?? { x: nextX, y: nextY };
    delete nextPositions[targetId];
    nextPositions[nextIdRaw] = { x: nextX, y: nextY };

    applyEditorSpec(
      {
        ...editorSpec,
        nodes: nextNodes,
        edges: nextEdges
      },
      {
        ...nextPositions,
        [nextIdRaw]: { x: nextX, y: nextY },
        ...(nextIdRaw === targetId ? { [nextIdRaw]: { x: nextX, y: nextY } } : {})
      }
    );
    setEditorSelectedNode(nextIdRaw);
    setEditorEdgeSrc((prev) => (prev === targetId ? nextIdRaw : prev));
    setEditorEdgeDst((prev) => (prev === targetId ? nextIdRaw : prev));
    writeEditorAction({
      action: "editor.node.save",
      node_id: nextIdRaw,
      position: { x: nextX, y: nextY },
      previous_position: oldPos
    });
  }

  function removeSelectedNode() {
    const target = editorSelectedNode.trim();
    if (!target) return;
    const nextNodes = editorSpec.nodes.filter((node) => node.id !== target);
    const nextEdges = editorSpec.edges.filter((edge) => edge.src !== target && edge.dst !== target);
    const nextPositions = { ...editorPositions };
    delete nextPositions[target];
    applyEditorSpec({ ...editorSpec, nodes: nextNodes, edges: nextEdges }, nextPositions);
    writeEditorAction({ action: "editor.node.remove", node_id: target });
  }

  function addEditorEdge() {
    const src = editorEdgeSrc.trim();
    const dst = editorEdgeDst.trim();
    if (!src || !dst) {
      setOutput("[ERROR] editor.edge.add: src and dst are required");
      return;
    }
    if (!editorSpec.nodes.some((node) => node.id === src) || !editorSpec.nodes.some((node) => node.id === dst)) {
      setOutput("[ERROR] editor.edge.add: src/dst must refer to existing nodes");
      return;
    }
    if (editorSpec.edges.some((edge) => edge.src === src && edge.dst === dst)) {
      setOutput("[ERROR] editor.edge.add: duplicate edge");
      return;
    }
    const nextSpec: GraphSpecInput = {
      ...editorSpec,
      edges: [...editorSpec.edges, { src, dst }]
    };
    applyEditorSpec(nextSpec, editorPositions);
    writeEditorAction({ action: "editor.edge.add", src, dst });
  }

  function removeEditorEdge(index: number) {
    if (index < 0 || index >= editorSpec.edges.length) return;
    const removed = editorSpec.edges[index];
    const nextEdges = editorSpec.edges.filter((_, idx) => idx !== index);
    applyEditorSpec({ ...editorSpec, edges: nextEdges }, editorPositions);
    writeEditorAction({
      action: "editor.edge.remove",
      edge: removed
    });
  }

  function exportYaml() {
    syncEditorYaml(editorSpec);
    writeEditorAction({
      action: "editor.yaml.export",
      nodes: editorSpec.nodes.length,
      edges: editorSpec.edges.length
    });
  }

  function importYaml() {
    try {
      const raw = YAML.parse(editorYaml);
      const normalized = normalizeGraphSpecInput(raw);
      const nextPositions: Record<string, NodePos> = {};
      normalized.nodes.forEach((node, idx) => {
        nextPositions[node.id] = editorPositions[node.id] ?? defaultPosition(idx);
      });
      applyEditorSpec(normalized, nextPositions);
      writeEditorAction({
        action: "editor.yaml.import",
        nodes: normalized.nodes.length,
        edges: normalized.edges.length
      });
    } catch (err) {
      setOutput(`[ERROR] editor.yaml.import: ${String(err)}`);
    }
  }

  function handleTabClick(nextTab: TabId) {
    setTab(nextTab);
    if (nextTab === "dashboard") void loadDashboard();
    if (nextTab === "presets") void loadPresets();
    if (nextTab === "fleet") void fleetQueryStatus();
    if (nextTab === "monitor") void monitorQuerySnapshot();
    if (nextTab === "editor") void loadEditorProfiles();
    if (nextTab === "governance") void loadGovernance();
  }

  function renderDashboard() {
    const runningCount = Number(fleetStatus?.running ?? 0);
    const streamTotal = Number((monitorSnapshot?.snapshot as Record<string, unknown> | undefined)?.streams_total ?? 0);
    return (
      <section className="panel-grid">
        <article className="card accent-a">
          <h3>Service Health</h3>
          <p className="metric">{String(health?.service ?? "-")}</p>
          <p className="hint">security: {String(health?.security_mode ?? "-")}</p>
        </article>
        <article className="card accent-b">
          <h3>Fleet Running</h3>
          <p className="metric">{runningCount}</p>
          <p className="hint">active worker processes</p>
        </article>
        <article className="card accent-c">
          <h3>Monitor Streams</h3>
          <p className="metric">{streamTotal}</p>
          <p className="hint">discovered pid/log streams</p>
        </article>
        <article className="card wide">
          <div className="row between">
            <h3>Quick Actions</h3>
            <button disabled={busy} onClick={() => void loadDashboard()}>
              Refresh
            </button>
          </div>
          <p className="hint">Monitor shows fleet log/PID streams only. Preset run output is a one-shot session result.</p>
          <pre>{JSON.stringify({ health, fleetStatus, monitorSnapshot }, null, 2)}</pre>
        </article>
      </section>
    );
  }

  function renderPresets() {
    return (
      <section className="panel-grid">
        <article className="card wide">
          <div className="row between wrap">
            <h3>Preset Catalog</h3>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={showExperimental}
                onChange={(e) => {
                  setShowExperimental(e.target.checked);
                  void loadPresets();
                }}
              />
              experimental
            </label>
          </div>
          <div className="row wrap">
            <button disabled={busy} onClick={() => void loadPresets()}>
              Reload Presets
            </button>
            <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
              {presets.map((preset) => (
                <option key={preset.preset_id} value={preset.preset_id}>
                  {preset.preset_id}
                </option>
              ))}
            </select>
            <input value={presetInputPath} onChange={(e) => setPresetInputPath(e.target.value)} placeholder="input path" />
            <input value={presetCameraIndex} onChange={(e) => setPresetCameraIndex(e.target.value)} placeholder="camera index" />
            <input value={presetDevice} onChange={(e) => setPresetDevice(e.target.value)} placeholder="device (cpu|0)" />
            <input value={presetModelPath} onChange={(e) => setPresetModelPath(e.target.value)} placeholder="model path" />
            <input value={presetYoloConf} onChange={(e) => setPresetYoloConf(e.target.value)} placeholder="yolo conf (0..1)" />
            <input value={presetYoloIou} onChange={(e) => setPresetYoloIou(e.target.value)} placeholder="yolo iou (0..1)" />
            <input value={presetYoloMaxDet} onChange={(e) => setPresetYoloMaxDet(e.target.value)} placeholder="yolo max det" />
            <input value={presetLoop} onChange={(e) => setPresetLoop(e.target.value)} placeholder="loop true|false" />
            <input value={presetMaxEvents} onChange={(e) => setPresetMaxEvents(e.target.value)} placeholder="max events" />
            <button disabled={busy} onClick={() => void runPreset(true)}>
              Validate
            </button>
            <button disabled={busy} onClick={() => void runPreset(false)}>
              Run
            </button>
          </div>
          <p className="hint">
            selected: {currentPreset?.preset_id ?? "-"} {currentPreset?.experimental ? "(experimental)" : ""}
          </p>
          <h4>Preset Session Output (One-shot)</h4>
          <p className="hint">This output is not a fleet monitor stream.</p>
          <pre>{presetSessionOutput}</pre>
          <h4>Preset Catalog Payload</h4>
          <pre>{JSON.stringify(presets, null, 2)}</pre>
        </article>
      </section>
    );
  }

  function renderFleet() {
    return (
      <section className="panel-grid">
        <article className="card wide">
          <h3>Fleet Control</h3>
          <form
            className="column"
            onSubmit={(e: FormEvent) => {
              e.preventDefault();
              void fleetStart();
            }}
          >
            <div className="row wrap">
              <input value={fleetConfig} onChange={(e) => setFleetConfig(e.target.value)} placeholder="config path" />
              <input
                value={fleetGraphTemplate}
                onChange={(e) => setFleetGraphTemplate(e.target.value)}
                placeholder="graph template"
              />
              <input value={fleetLogDir} onChange={(e) => setFleetLogDir(e.target.value)} placeholder="log dir (optional)" />
              <input value={fleetStreams} onChange={(e) => setFleetStreams(e.target.value)} placeholder="stream ids csv" />
              <input value={fleetExtraArgs} onChange={(e) => setFleetExtraArgs(e.target.value)} placeholder="extra args" />
            </div>
            <div className="row wrap">
              <button type="submit" disabled={busy}>
                Start
              </button>
              <button type="button" disabled={busy} onClick={() => void fleetStop()}>
                Stop
              </button>
              <button type="button" disabled={busy} onClick={() => void fleetQueryStatus()}>
                Status
              </button>
            </div>
          </form>
          <pre>{JSON.stringify(fleetStatus, null, 2)}</pre>
        </article>
      </section>
    );
  }

  function renderMonitor() {
    const rows =
      (monitorSnapshot?.snapshot as Record<string, unknown> | undefined)?.streams &&
      Array.isArray((monitorSnapshot?.snapshot as Record<string, unknown>).streams)
        ? ((monitorSnapshot?.snapshot as Record<string, unknown>).streams as Record<string, unknown>[])
        : [];

    return (
      <section className="panel-grid">
        <article className="card wide">
          <div className="row between">
            <h3>Monitor Snapshot</h3>
            <button disabled={busy} onClick={() => void monitorQuerySnapshot()}>
              Refresh
            </button>
          </div>
          <p className="hint">Monitor tracks fleet logs/PIDs only. Use Fleet Start to populate stream rows.</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>stream_id</th>
                  <th>status</th>
                  <th>pid</th>
                  <th>events_total</th>
                  <th>eps_window</th>
                  <th>last_error_tail</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={`${String(row.stream_id)}-${index}`}>
                    <td>{String(row.stream_id ?? "-")}</td>
                    <td>{String(row.status ?? "-")}</td>
                    <td>{String(row.pid ?? "-")}</td>
                    <td>{String(row.events_total ?? "-")}</td>
                    <td>{String(row.eps_window ?? "-")}</td>
                    <td>{String(row.last_error_tail ?? "-")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    );
  }

  function renderEditor() {
    return (
      <section className="panel-grid">
        <article className="card wide">
          <div className="row between wrap">
            <h3>Block Editor MVP</h3>
            <p className="hint">Graph run is a one-shot session action and not part of Fleet monitor rows.</p>
          </div>

          <div className="row wrap">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={editorAllowExperimental}
                onChange={(e) => {
                  setEditorAllowExperimental(e.target.checked);
                  void loadEditorProfiles();
                }}
              />
              experimental profiles
            </label>
            <button disabled={busy} onClick={() => void loadEditorProfiles()}>
              Reload Profiles
            </button>
            <select value={editorProfileId} onChange={(e) => setEditorProfileId(e.target.value)}>
              {editorProfiles.map((item) => (
                <option key={item.profile_id} value={item.profile_id}>
                  {item.profile_id}
                </option>
              ))}
            </select>
            <button disabled={busy} onClick={() => void editorLoadFromProfile()}>
              Load Profile
            </button>
            <span className="hint">
              selected: {currentEditorProfile?.profile_id ?? "-"}
              {currentEditorProfile?.experimental ? " (experimental)" : ""}
            </span>
          </div>

          <div className="row wrap">
            <input value={editorInputPath} onChange={(e) => setEditorInputPath(e.target.value)} placeholder="override input path" />
            <input
              value={editorCameraIndex}
              onChange={(e) => setEditorCameraIndex(e.target.value)}
              placeholder="override camera index"
            />
            <input value={editorDevice} onChange={(e) => setEditorDevice(e.target.value)} placeholder="override device" />
            <input value={editorModelPath} onChange={(e) => setEditorModelPath(e.target.value)} placeholder="override model path" />
            <input value={editorLoop} onChange={(e) => setEditorLoop(e.target.value)} placeholder="override loop true|false" />
            <input value={editorMaxEvents} onChange={(e) => setEditorMaxEvents(e.target.value)} placeholder="max events" />
          </div>

          <div className="row wrap">
            <button disabled={busy} onClick={() => addEditorNode("source")}>
              Add Source
            </button>
            <button disabled={busy} onClick={() => addEditorNode("node")}>
              Add Node
            </button>
            <button disabled={busy} onClick={() => addEditorNode("sink")}>
              Add Sink
            </button>
            <select value={editorEdgeSrc} onChange={(e) => setEditorEdgeSrc(e.target.value)}>
              {editorSpec.nodes.map((node) => (
                <option key={`src-${node.id}`} value={node.id}>
                  {node.id}
                </option>
              ))}
            </select>
            <select value={editorEdgeDst} onChange={(e) => setEditorEdgeDst(e.target.value)}>
              {editorSpec.nodes.map((node) => (
                <option key={`dst-${node.id}`} value={node.id}>
                  {node.id}
                </option>
              ))}
            </select>
            <button disabled={busy} onClick={() => addEditorEdge()}>
              Add Edge
            </button>
            <button disabled={busy} onClick={() => autoLayoutEditor()}>
              Auto Layout
            </button>
            <button disabled={busy} onClick={() => alignEditor("horizontal")}>
              Align Horizontal
            </button>
            <button disabled={busy} onClick={() => alignEditor("vertical")}>
              Align Vertical
            </button>
            <button disabled={busy} onClick={() => fitEditorView()}>
              Fit View
            </button>
          </div>

          <div className="editor-canvas" data-testid="editor-canvas">
            <EditorCanvas
              nodes={flowNodes}
              edges={flowEdges}
              nodeTypes={editorNodeTypes}
              onNodesRemoved={onCanvasNodesRemoved}
              onPositionsCommit={onCanvasPositionsCommit}
              onEdgesChange={onFlowEdgesChange}
              onConnect={onFlowConnect}
              onInit={(instance) => setFlowInstance(instance)}
              onNodeSelect={onCanvasNodeSelect}
            />
          </div>

          <div className="editor-two-col">
            <section>
              <h4>Selected Node</h4>
              <div className="row wrap">
                <select
                  value={editorSelectedNode}
                  onChange={(e) => {
                    const next = e.target.value;
                    setEditorSelectedNode(next);
                    selectEditorNode(next);
                  }}
                >
                  {editorSpec.nodes.map((node) => (
                    <option key={`node-${node.id}`} value={node.id}>
                      {node.id}
                    </option>
                  ))}
                </select>
                <input value={editorNodeId} onChange={(e) => setEditorNodeId(e.target.value)} placeholder="node id" />
                <input value={editorNodeKind} onChange={(e) => setEditorNodeKind(e.target.value)} placeholder="kind" />
                <input value={editorNodePlugin} onChange={(e) => setEditorNodePlugin(e.target.value)} placeholder="plugin" />
                <input value={editorNodePosX} onChange={(e) => setEditorNodePosX(e.target.value)} placeholder="x" />
                <input value={editorNodePosY} onChange={(e) => setEditorNodePosY(e.target.value)} placeholder="y" />
                <button disabled={busy} onClick={() => saveSelectedNode()}>
                  Save Node
                </button>
                <button disabled={busy} onClick={() => removeSelectedNode()}>
                  Remove Node
                </button>
              </div>
              <textarea
                value={editorNodeConfig}
                onChange={(e) => setEditorNodeConfig(e.target.value)}
                rows={10}
                className="code-area"
              />
            </section>
            <section>
              <h4>Edges</h4>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>src</th>
                      <th>dst</th>
                      <th>src_port</th>
                      <th>dst_port</th>
                      <th>action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {editorSpec.edges.map((edge, idx) => (
                      <tr key={`edge-${idx}-${edge.src}-${edge.dst}`}>
                        <td>{edge.src}</td>
                        <td>{edge.dst}</td>
                        <td>{edge.src_port ?? ""}</td>
                        <td>{edge.dst_port ?? ""}</td>
                        <td>
                          <button disabled={busy} onClick={() => removeEditorEdge(idx)}>
                            remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <h4>YAML Import / Export</h4>
          <div className="row wrap">
            <button disabled={busy} onClick={() => exportYaml()}>
              Export YAML
            </button>
            <button disabled={busy} onClick={() => importYaml()}>
              Import YAML
            </button>
            <button disabled={busy} onClick={() => void editorValidate()}>
              Validate Graph
            </button>
            <button disabled={busy} onClick={() => void editorRun()}>
              Run Graph
            </button>
          </div>
          <textarea
            value={editorYaml}
            onChange={(e) => setEditorYaml(e.target.value)}
            rows={14}
            className="code-area"
            placeholder="version: 2"
          />

          <h4>Validation Summary</h4>
          <div className={`validation-badge ${editorValidationSummary?.status ?? "idle"}`}>
            {editorValidationSummary ? (
              <>
                <strong>{editorValidationSummary.status.toUpperCase()}</strong>
                <span>nodes={editorValidationSummary.nodeCount}</span>
                <span>edges={editorValidationSummary.edgeCount}</span>
                <span>{editorValidationSummary.message}</span>
              </>
            ) : (
              <span>No validation run yet.</span>
            )}
          </div>

          <h4>Editor Action Log</h4>
          <pre>{editorActionLog}</pre>

          <h4>Editor API Output</h4>
          <pre>{editorApiOutput}</pre>
        </article>
      </section>
    );
  }

  function renderGovernance() {
    return (
      <section className="panel-grid">
        <article className="card wide">
          <div className="row wrap between">
            <h3>Governance Snapshot</h3>
            <div className="row wrap">
              <input value={auditLimit} onChange={(e) => setAuditLimit(e.target.value)} placeholder="audit limit" />
              <button disabled={busy} onClick={() => void loadGovernance()}>
                Refresh
              </button>
            </div>
          </div>
          <h4>Policy Snapshot</h4>
          <pre>{JSON.stringify(policySnapshot, null, 2)}</pre>
          <h4>Audit Tail</h4>
          <pre>{JSON.stringify(auditRows, null, 2)}</pre>
        </article>
      </section>
    );
  }

  return (
    <div className="shell">
      <header className="topbar">
        <h1>Stream Console</h1>
        <p>Universal stream operations UI</p>
      </header>

      <section className="toolbar card">
        <div className="row wrap">
          <label>
            API Base
            <input value={apiBase} onChange={(e) => setApiBase(e.target.value)} placeholder="http://127.0.0.1:18700" />
          </label>
          <label>
            Bearer Token (optional)
            <input value={token} onChange={(e) => setToken(e.target.value)} type="password" placeholder="token" />
          </label>
          <button disabled={busy} onClick={() => void loadDashboard()}>
            Ping
          </button>
        </div>
        <p className="hint">{output}</p>
      </section>

      <nav className="tabs" aria-label="primary tabs">
        {TABS.map((item) => (
          <button
            key={item.id}
            className={tab === item.id ? "active" : ""}
            onClick={() => handleTabClick(item.id)}
            disabled={busy}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === "dashboard" && renderDashboard()}
        {tab === "presets" && renderPresets()}
        {tab === "fleet" && renderFleet()}
        {tab === "monitor" && renderMonitor()}
        {tab === "editor" && renderEditor()}
        {tab === "governance" && renderGovernance()}
      </main>
    </div>
  );
}
