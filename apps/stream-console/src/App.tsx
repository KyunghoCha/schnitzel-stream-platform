import { useCallback, useMemo, useState } from "react";
import { applyEdgeChanges, Connection, Edge, EdgeChange, ReactFlowInstance } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import YAML from "yaml";

import {
  apiRequest,
  defaultApiBase,
  GraphFromProfileOverrides,
  GraphSpecInput,
  normalizeGraphSpecInput
} from "./api";
import { EditorValidationSummary, GraphProfileItem, NodePos, PresetItem, TabId } from "./app_types";
import { isConnectionAllowedHybrid } from "./editor_connect";
import { alignNodePositions, computeAutoLayout, type LayoutSize } from "./editor_layout";
import {
  connectionErrorMessage,
  defaultNodeTemplate,
  defaultPosition,
  defaultSpec,
  edgeIdentity,
  nextNodeId,
  normalizeKind,
  parseEditorValidationSummary,
  toBoolText,
  toNumber
} from "./editor_utils";
import { EditorTab } from "./components/editor/EditorTab";
import {
  DashboardSection,
  FleetSection,
  GovernanceSection,
  MonitorSection,
  PresetsSection
} from "./components/sections";

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "presets", label: "Presets" },
  { id: "fleet", label: "Fleet" },
  { id: "monitor", label: "Monitor" },
  { id: "editor", label: "Editor" },
  { id: "governance", label: "Governance" }
];

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

  function selectEditorNode(
    nodeId: string,
    spec: GraphSpecInput = editorSpec,
    positions: Record<string, NodePos> = editorPositions
  ) {
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

    const selected = spec.nodes.find((node) => node.id === editorSelectedNode)?.id ?? spec.nodes[0].id;
    const src = spec.nodes.find((node) => node.id === editorEdgeSrc)?.id ?? spec.nodes[0].id;
    const dst =
      spec.nodes.find((node) => node.id === editorEdgeDst)?.id ?? spec.nodes[Math.min(1, spec.nodes.length - 1)].id;

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

      const candidate: GraphSpecInput["edges"][number] = {
        src,
        dst
      };
      if (connection.sourceHandle) {
        candidate.src_port = connection.sourceHandle;
      }
      if (connection.targetHandle) {
        candidate.dst_port = connection.targetHandle;
      }
      const gate = isConnectionAllowedHybrid({
        sourceId: src,
        targetId: dst,
        sourceKind: srcNode.kind,
        targetKind: dstNode.kind,
        existingEdges: editorSpec.edges,
        candidate
      });
      if (!gate.ok) {
        setOutput(`[ERROR] editor.edge.connect: ${connectionErrorMessage(gate.reason)}`);
        return;
      }

      applyEditorSpec(
        {
          ...editorSpec,
          edges: [...editorSpec.edges, candidate]
        },
        editorPositions
      );
      writeEditorAction({
        action: "editor.edge.connect.canvas",
        src,
        dst,
        src_port: candidate.src_port ?? "",
        dst_port: candidate.dst_port ?? ""
      });
    },
    [editorPositions, editorSpec]
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

  function alignTargetNodeIds(): string[] {
    const selected = flowInstance?.getNodes?.().filter((node) => node.selected).map((node) => String(node.id)) ?? [];
    if (selected.length >= 2) {
      return selected;
    }
    return editorSpec.nodes.map((node) => node.id);
  }

  function measuredNodeSizes(): Record<string, LayoutSize> {
    const rows = flowInstance?.getNodes?.() ?? [];
    const out: Record<string, LayoutSize> = {};
    for (const node of rows) {
      const width = Number(node.measured?.width ?? node.width ?? 200);
      const height = Number(node.measured?.height ?? node.height ?? 90);
      out[String(node.id)] = {
        width: Number.isFinite(width) ? Math.max(20, width) : 200,
        height: Number.isFinite(height) ? Math.max(20, height) : 90
      };
    }
    return out;
  }

  function alignEditor(axis: "horizontal" | "vertical"): void {
    const nodeIds = alignTargetNodeIds();
    const nextPositions = alignNodePositions(editorPositions, nodeIds, axis, {
      sizes: measuredNodeSizes(),
      gap: 36
    });
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
      const path = fleetLogDir.trim()
        ? `/api/v1/fleet/status?log_dir=${encodeURIComponent(fleetLogDir.trim())}`
        : "/api/v1/fleet/status";
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
    const srcNode = editorSpec.nodes.find((node) => node.id === src);
    const dstNode = editorSpec.nodes.find((node) => node.id === dst);
    if (!srcNode || !dstNode) {
      setOutput("[ERROR] editor.edge.add: src/dst must refer to existing nodes");
      return;
    }
    const candidate: GraphSpecInput["edges"][number] = { src, dst };
    const gate = isConnectionAllowedHybrid({
      sourceId: src,
      targetId: dst,
      sourceKind: srcNode.kind,
      targetKind: dstNode.kind,
      existingEdges: editorSpec.edges,
      candidate
    });
    if (!gate.ok) {
      setOutput(`[ERROR] editor.edge.add: ${connectionErrorMessage(gate.reason)}`);
      return;
    }
    const nextSpec: GraphSpecInput = {
      ...editorSpec,
      edges: [...editorSpec.edges, candidate]
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
          <button key={item.id} className={tab === item.id ? "active" : ""} onClick={() => handleTabClick(item.id)} disabled={busy}>
            {item.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === "dashboard" && (
          <DashboardSection
            busy={busy}
            health={health}
            fleetStatus={fleetStatus}
            monitorSnapshot={monitorSnapshot}
            onRefresh={() => void loadDashboard()}
          />
        )}

        {tab === "presets" && (
          <PresetsSection
            busy={busy}
            showExperimental={showExperimental}
            onToggleExperimental={(value) => {
              setShowExperimental(value);
              void loadPresets();
            }}
            onReload={() => void loadPresets()}
            presetId={presetId}
            onPresetIdChange={setPresetId}
            presets={presets}
            presetInputPath={presetInputPath}
            onPresetInputPathChange={setPresetInputPath}
            presetCameraIndex={presetCameraIndex}
            onPresetCameraIndexChange={setPresetCameraIndex}
            presetDevice={presetDevice}
            onPresetDeviceChange={setPresetDevice}
            presetModelPath={presetModelPath}
            onPresetModelPathChange={setPresetModelPath}
            presetYoloConf={presetYoloConf}
            onPresetYoloConfChange={setPresetYoloConf}
            presetYoloIou={presetYoloIou}
            onPresetYoloIouChange={setPresetYoloIou}
            presetYoloMaxDet={presetYoloMaxDet}
            onPresetYoloMaxDetChange={setPresetYoloMaxDet}
            presetLoop={presetLoop}
            onPresetLoopChange={setPresetLoop}
            presetMaxEvents={presetMaxEvents}
            onPresetMaxEventsChange={setPresetMaxEvents}
            onValidate={() => void runPreset(true)}
            onRun={() => void runPreset(false)}
            currentPreset={currentPreset}
            presetSessionOutput={presetSessionOutput}
          />
        )}

        {tab === "fleet" && (
          <FleetSection
            busy={busy}
            fleetConfig={fleetConfig}
            onFleetConfigChange={setFleetConfig}
            fleetGraphTemplate={fleetGraphTemplate}
            onFleetGraphTemplateChange={setFleetGraphTemplate}
            fleetLogDir={fleetLogDir}
            onFleetLogDirChange={setFleetLogDir}
            fleetStreams={fleetStreams}
            onFleetStreamsChange={setFleetStreams}
            fleetExtraArgs={fleetExtraArgs}
            onFleetExtraArgsChange={setFleetExtraArgs}
            onStart={() => void fleetStart()}
            onStop={() => void fleetStop()}
            onStatus={() => void fleetQueryStatus()}
            fleetStatus={fleetStatus}
          />
        )}

        {tab === "monitor" && (
          <MonitorSection
            busy={busy}
            monitorSnapshot={monitorSnapshot}
            onRefresh={() => void monitorQuerySnapshot()}
          />
        )}

        {tab === "editor" && (
          <EditorTab
            busy={busy}
            editorAllowExperimental={editorAllowExperimental}
            onEditorAllowExperimentalChange={(value) => {
              setEditorAllowExperimental(value);
              void loadEditorProfiles();
            }}
            onReloadProfiles={() => void loadEditorProfiles()}
            editorProfileId={editorProfileId}
            onEditorProfileIdChange={setEditorProfileId}
            editorProfiles={editorProfiles}
            onLoadProfile={() => void editorLoadFromProfile()}
            currentEditorProfile={currentEditorProfile}
            editorInputPath={editorInputPath}
            onEditorInputPathChange={setEditorInputPath}
            editorCameraIndex={editorCameraIndex}
            onEditorCameraIndexChange={setEditorCameraIndex}
            editorDevice={editorDevice}
            onEditorDeviceChange={setEditorDevice}
            editorModelPath={editorModelPath}
            onEditorModelPathChange={setEditorModelPath}
            editorLoop={editorLoop}
            onEditorLoopChange={setEditorLoop}
            editorMaxEvents={editorMaxEvents}
            onEditorMaxEventsChange={setEditorMaxEvents}
            onAddNode={addEditorNode}
            editorEdgeSrc={editorEdgeSrc}
            onEditorEdgeSrcChange={setEditorEdgeSrc}
            editorEdgeDst={editorEdgeDst}
            onEditorEdgeDstChange={setEditorEdgeDst}
            onAddEdge={addEditorEdge}
            onAutoLayout={autoLayoutEditor}
            onAlignHorizontal={() => alignEditor("horizontal")}
            onAlignVertical={() => alignEditor("vertical")}
            onFitView={fitEditorView}
            flowNodes={flowNodes}
            flowEdges={flowEdges}
            onCanvasNodesRemoved={onCanvasNodesRemoved}
            onCanvasPositionsCommit={onCanvasPositionsCommit}
            onFlowEdgesChange={onFlowEdgesChange}
            onFlowConnect={onFlowConnect}
            onFlowInit={(instance) => setFlowInstance(instance)}
            onCanvasNodeSelect={onCanvasNodeSelect}
            editorSpec={editorSpec}
            editorSelectedNode={editorSelectedNode}
            onEditorSelectedNodeChange={setEditorSelectedNode}
            onSelectEditorNode={selectEditorNode}
            editorNodeId={editorNodeId}
            onEditorNodeIdChange={setEditorNodeId}
            editorNodeKind={editorNodeKind}
            onEditorNodeKindChange={setEditorNodeKind}
            editorNodePlugin={editorNodePlugin}
            onEditorNodePluginChange={setEditorNodePlugin}
            editorNodePosX={editorNodePosX}
            onEditorNodePosXChange={setEditorNodePosX}
            editorNodePosY={editorNodePosY}
            onEditorNodePosYChange={setEditorNodePosY}
            onSaveNode={saveSelectedNode}
            onRemoveNode={removeSelectedNode}
            editorNodeConfig={editorNodeConfig}
            onEditorNodeConfigChange={setEditorNodeConfig}
            onRemoveEditorEdge={removeEditorEdge}
            onExportYaml={exportYaml}
            onImportYaml={importYaml}
            onValidateGraph={() => void editorValidate()}
            onRunGraph={() => void editorRun()}
            editorYaml={editorYaml}
            onEditorYamlChange={setEditorYaml}
            editorValidationSummary={editorValidationSummary}
            editorActionLog={editorActionLog}
            editorApiOutput={editorApiOutput}
          />
        )}

        {tab === "governance" && (
          <GovernanceSection
            busy={busy}
            auditLimit={auditLimit}
            onAuditLimitChange={setAuditLimit}
            onRefresh={() => void loadGovernance()}
            policySnapshot={policySnapshot}
            auditRows={auditRows}
          />
        )}
      </main>
    </div>
  );
}
