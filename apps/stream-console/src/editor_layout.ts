export type LayoutNodeInput = {
  id: string;
};

export type LayoutEdgeInput = {
  src: string;
  dst: string;
};

export type LayoutPos = {
  x: number;
  y: number;
};

export type LayoutSize = {
  width: number;
  height: number;
};

function insertSorted(queue: string[], value: string): void {
  queue.push(value);
  queue.sort((a, b) => a.localeCompare(b));
}

function sizeForNode(id: string, sizes?: Record<string, LayoutSize | undefined>): LayoutSize {
  const width = Number(sizes?.[id]?.width ?? 200);
  const height = Number(sizes?.[id]?.height ?? 90);
  return {
    width: Number.isFinite(width) ? Math.max(20, width) : 200,
    height: Number.isFinite(height) ? Math.max(20, height) : 90
  };
}

// Intent: keep layout dependency-free and deterministic to avoid adding a heavy graph-layout package in P23.
export function computeAutoLayout(
  nodes: ReadonlyArray<LayoutNodeInput>,
  edges: ReadonlyArray<LayoutEdgeInput>,
  opts?: {
    marginX?: number;
    marginY?: number;
    gapX?: number;
    gapY?: number;
  }
): Record<string, LayoutPos> {
  const marginX = Number(opts?.marginX ?? 80);
  const marginY = Number(opts?.marginY ?? 80);
  const gapX = Number(opts?.gapX ?? 340);
  const gapY = Number(opts?.gapY ?? 180);

  const nodeIds = Array.from(new Set(nodes.map((node) => String(node.id).trim()).filter(Boolean))).sort((a, b) =>
    a.localeCompare(b)
  );
  const known = new Set(nodeIds);

  const indegree = new Map<string, number>();
  const out = new Map<string, string[]>();
  for (const id of nodeIds) {
    indegree.set(id, 0);
    out.set(id, []);
  }
  for (const edge of edges) {
    const src = String(edge.src || "").trim();
    const dst = String(edge.dst || "").trim();
    if (!known.has(src) || !known.has(dst)) continue;
    out.get(src)!.push(dst);
    indegree.set(dst, (indegree.get(dst) ?? 0) + 1);
  }
  for (const id of nodeIds) {
    out.get(id)!.sort((a, b) => a.localeCompare(b));
  }

  const layer = new Map<string, number>();
  const queue: string[] = [];
  for (const id of nodeIds) {
    if ((indegree.get(id) ?? 0) === 0) {
      queue.push(id);
      layer.set(id, 0);
    }
  }
  queue.sort((a, b) => a.localeCompare(b));

  const visited = new Set<string>();
  while (queue.length > 0) {
    const id = queue.shift()!;
    visited.add(id);
    const baseLayer = layer.get(id) ?? 0;
    for (const dst of out.get(id) ?? []) {
      const nextLayer = Math.max(layer.get(dst) ?? 0, baseLayer + 1);
      layer.set(dst, nextLayer);
      const nextIndegree = (indegree.get(dst) ?? 0) - 1;
      indegree.set(dst, nextIndegree);
      if (nextIndegree === 0) {
        insertSorted(queue, dst);
      }
    }
  }

  let maxLayer = 0;
  for (const val of layer.values()) {
    maxLayer = Math.max(maxLayer, val);
  }
  const unresolved = nodeIds.filter((id) => !visited.has(id));
  unresolved.forEach((id, idx) => {
    layer.set(id, maxLayer + 1 + Math.floor(idx / 6));
  });

  const byLayer = new Map<number, string[]>();
  for (const id of nodeIds) {
    const l = layer.get(id) ?? 0;
    if (!byLayer.has(l)) byLayer.set(l, []);
    byLayer.get(l)!.push(id);
  }
  for (const ids of byLayer.values()) {
    ids.sort((a, b) => a.localeCompare(b));
  }

  const result: Record<string, LayoutPos> = {};
  for (const [l, ids] of Array.from(byLayer.entries()).sort((a, b) => a[0] - b[0])) {
    ids.forEach((id, row) => {
      result[id] = {
        x: marginX + l * gapX,
        y: marginY + row * gapY
      };
    });
  }
  return result;
}

export function alignNodePositions(
  positions: Record<string, LayoutPos>,
  nodeIds: ReadonlyArray<string>,
  axis: "horizontal" | "vertical",
  opts?: {
    sizes?: Record<string, LayoutSize | undefined>;
    gap?: number;
  }
): Record<string, LayoutPos> {
  const ids = nodeIds.map((id) => String(id).trim()).filter((id) => !!positions[id]);
  if (ids.length === 0) {
    return { ...positions };
  }

  const gap = Number(opts?.gap ?? 36);
  const out: Record<string, LayoutPos> = { ...positions };
  if (axis === "horizontal") {
    const y = Math.min(...ids.map((id) => out[id].y));
    const ordered = ids
      .map((id) => ({ id, x: out[id].x, size: sizeForNode(id, opts?.sizes) }))
      .sort((a, b) => a.x - b.x || a.id.localeCompare(b.id));
    let cursor = ordered[0].x;
    for (let idx = 0; idx < ordered.length; idx += 1) {
      const row = ordered[idx];
      const x = idx === 0 ? row.x : Math.max(row.x, cursor);
      out[row.id] = { x, y };
      cursor = x + row.size.width + gap;
    }
    return out;
  }

  const x = Math.min(...ids.map((id) => out[id].x));
  const ordered = ids
    .map((id) => ({ id, y: out[id].y, size: sizeForNode(id, opts?.sizes) }))
    .sort((a, b) => a.y - b.y || a.id.localeCompare(b.id));
  let cursor = ordered[0].y;
  for (let idx = 0; idx < ordered.length; idx += 1) {
    const row = ordered[idx];
    const y = idx === 0 ? row.y : Math.max(row.y, cursor);
    out[row.id] = { x, y };
    cursor = y + row.size.height + gap;
  }
  return out;
}
