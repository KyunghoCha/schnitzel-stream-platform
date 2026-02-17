import { GraphSpecInput } from "./api";
import { EditorNodeKind } from "./editor_nodes";
import { EditorValidationSummary, NodePos } from "./app_types";

export function defaultPosition(index: number): NodePos {
  return {
    x: 100 + (index % 4) * 250,
    y: 80 + Math.floor(index / 4) * 180
  };
}

export function defaultSpec(): GraphSpecInput {
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

export function defaultNodeTemplate(kind: "source" | "node" | "sink", id: string) {
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

export function nextNodeId(base: string, spec: GraphSpecInput): string {
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

export function normalizeKind(kind: string): EditorNodeKind {
  const raw = kind.trim().toLowerCase();
  if (raw === "source") return "source";
  if (raw === "sink") return "sink";
  return "node";
}

export function edgeIdentity(
  edge: { src: string; dst: string; src_port?: string; dst_port?: string },
  index: number
): string {
  return `${edge.src}|${edge.dst}|${edge.src_port ?? "*"}|${edge.dst_port ?? "*"}|${index}`;
}

export function parseEditorValidationSummary(raw: unknown): EditorValidationSummary | null {
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

export function toNumber(value: string): number | undefined {
  const txt = value.trim();
  if (!txt) return undefined;
  const n = Number(txt);
  if (!Number.isFinite(n)) return undefined;
  return n;
}

export function toBoolText(value: string): "" | "true" | "false" {
  const lower = value.trim().toLowerCase();
  if (lower === "true" || lower === "false") {
    return lower;
  }
  return "";
}

export function connectionErrorMessage(reason: string): string {
  if (reason === "sink_outgoing_blocked") {
    return "sink cannot have outgoing edges";
  }
  if (reason === "source_incoming_blocked") {
    return "source cannot have incoming edges";
  }
  if (reason === "self_loop_blocked") {
    return "self-loop is blocked in editor";
  }
  if (reason === "duplicate_edge_blocked") {
    return "duplicate edge";
  }
  return reason;
}
