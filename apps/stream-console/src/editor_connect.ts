import { GraphEdgeInput } from "./api";

type Point = {
  x: number;
  y: number;
};

type Size = {
  width: number;
  height: number;
};

export type SnapNodeInput = {
  id: string;
  type?: string;
  data?: Record<string, unknown>;
  position?: Point;
  positionAbsolute?: Point;
  width?: number;
  height?: number;
  measured?: {
    width?: number;
    height?: number;
  };
};

function normalizeNodeKind(raw: unknown): "source" | "node" | "sink" {
  const txt = String(raw ?? "")
    .trim()
    .toLowerCase();
  if (txt === "source") return "source";
  if (txt === "sink") return "sink";
  return "node";
}

function nodeSize(node: SnapNodeInput): Size {
  const width = Number(node.measured?.width ?? node.width ?? 200);
  const height = Number(node.measured?.height ?? node.height ?? 90);
  return {
    width: Number.isFinite(width) ? Math.max(20, width) : 200,
    height: Number.isFinite(height) ? Math.max(20, height) : 90
  };
}

function distancePointToRect(point: Point, rect: { x: number; y: number; width: number; height: number }): number {
  const dx =
    point.x < rect.x ? rect.x - point.x : point.x > rect.x + rect.width ? point.x - (rect.x + rect.width) : 0;
  const dy =
    point.y < rect.y ? rect.y - point.y : point.y > rect.y + rect.height ? point.y - (rect.y + rect.height) : 0;
  return Math.hypot(dx, dy);
}

export function isDuplicateEdgeExact(existingEdges: ReadonlyArray<GraphEdgeInput>, candidate: GraphEdgeInput): boolean {
  return existingEdges.some(
    (edge) =>
      edge.src === candidate.src &&
      edge.dst === candidate.dst &&
      (edge.src_port ?? "") === (candidate.src_port ?? "") &&
      (edge.dst_port ?? "") === (candidate.dst_port ?? "")
  );
}

export function isConnectionAllowedHybrid(params: {
  sourceId: string;
  targetId: string;
  sourceKind: string;
  targetKind: string;
  existingEdges: ReadonlyArray<GraphEdgeInput>;
  candidate: GraphEdgeInput;
}): { ok: true } | { ok: false; reason: string } {
  const sourceId = String(params.sourceId ?? "").trim();
  const targetId = String(params.targetId ?? "").trim();
  if (!sourceId || !targetId) {
    return { ok: false, reason: "source_target_required" };
  }
  if (sourceId === targetId) {
    return { ok: false, reason: "self_loop_blocked" };
  }
  if (normalizeNodeKind(params.sourceKind) === "sink") {
    return { ok: false, reason: "sink_outgoing_blocked" };
  }
  if (normalizeNodeKind(params.targetKind) === "source") {
    return { ok: false, reason: "source_incoming_blocked" };
  }
  if (isDuplicateEdgeExact(params.existingEdges, params.candidate)) {
    return { ok: false, reason: "duplicate_edge_blocked" };
  }
  return { ok: true };
}

export function findSnapTargetInput(params: {
  flowPoint: Point;
  nodes: ReadonlyArray<SnapNodeInput>;
  sourceNodeId: string;
  thresholdFlow: number;
}): { nodeId: string; handleId: string } | null {
  const sourceNodeId = String(params.sourceNodeId ?? "").trim();
  if (!sourceNodeId || params.nodes.length === 0) {
    return null;
  }

  let best: { nodeId: string; score: number } | null = null;
  for (const row of params.nodes) {
    const nodeId = String(row.id ?? "").trim();
    if (!nodeId || nodeId === sourceNodeId) {
      continue;
    }

    const kind = normalizeNodeKind(row.data?.kind ?? row.type);
    if (kind === "source") {
      continue;
    }

    const pos = row.positionAbsolute ?? row.position ?? { x: 0, y: 0 };
    const size = nodeSize(row);
    const rectDistance = distancePointToRect(params.flowPoint, {
      x: pos.x,
      y: pos.y,
      width: size.width,
      height: size.height
    });
    if (rectDistance <= params.thresholdFlow) {
      const score = rectDistance;
      if (!best || score < best.score) {
        best = { nodeId, score };
      }
      continue;
    }

    const inHandlePoint = { x: pos.x, y: pos.y + size.height / 2 };
    const handleDistance = Math.hypot(params.flowPoint.x - inHandlePoint.x, params.flowPoint.y - inHandlePoint.y);
    if (handleDistance <= params.thresholdFlow) {
      const score = handleDistance + 0.25;
      if (!best || score < best.score) {
        best = { nodeId, score };
      }
    }
  }

  if (!best) {
    return null;
  }
  return {
    nodeId: best.nodeId,
    handleId: "in"
  };
}
