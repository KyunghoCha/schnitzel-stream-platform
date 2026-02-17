export type Envelope<T = Record<string, unknown>> = {
  schema_version: number;
  status: "ok" | "error";
  request_id: string;
  ts: string;
  data: T;
  error?: Record<string, unknown> | null;
};

export type GraphNodeInput = {
  id: string;
  kind: string;
  plugin: string;
  config: Record<string, unknown>;
};

export type GraphEdgeInput = {
  src: string;
  dst: string;
  src_port?: string;
  dst_port?: string;
};

export type GraphSpecInput = {
  version: 2;
  nodes: GraphNodeInput[];
  edges: GraphEdgeInput[];
  config: Record<string, unknown>;
};

export type GraphFromProfileOverrides = {
  input_path?: string;
  camera_index?: number;
  device?: string;
  model_path?: string;
  loop?: "" | "true" | "false";
  max_events?: number;
};

const DEFAULT_BASE = "http://127.0.0.1:18700";

function buildUrl(base: string, path: string): string {
  const normalizedBase = base.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export async function apiRequest<TData extends Record<string, unknown>>(
  path: string,
  opts: {
    baseUrl: string;
    token: string;
    method?: "GET" | "POST";
    body?: Record<string, unknown>;
  }
): Promise<Envelope<TData>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };
  if (opts.token.trim()) {
    headers.Authorization = `Bearer ${opts.token.trim()}`;
  }

  const resp = await fetch(buildUrl(opts.baseUrl || DEFAULT_BASE, path), {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined
  });

  const text = await resp.text();
  let parsed: unknown = {};
  if (text.trim()) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = { schema_version: 1, status: "error", request_id: "", ts: "", data: {}, error: { detail: text } };
    }
  }

  if (!resp.ok) {
    const errEnvelope = parsed as Envelope<TData>;
    throw new Error(
      `HTTP ${resp.status}: ${JSON.stringify(errEnvelope.error ?? errEnvelope.data ?? { detail: resp.statusText })}`
    );
  }

  return parsed as Envelope<TData>;
}

export function defaultApiBase(): string {
  const envValue = import.meta.env.VITE_API_BASE;
  return typeof envValue === "string" && envValue.trim() ? envValue : DEFAULT_BASE;
}

function asNumber(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return undefined;
  }
  return n;
}

function asText(value: unknown): string {
  return String(value ?? "").trim();
}

export function normalizeGraphSpecInput(input: unknown): GraphSpecInput {
  if (!input || typeof input !== "object") {
    throw new Error("graph spec must be a mapping");
  }
  const obj = input as Record<string, unknown>;
  const nodesRaw = Array.isArray(obj.nodes) ? obj.nodes : [];
  const edgesRaw = Array.isArray(obj.edges) ? obj.edges : [];
  const configRaw = obj.config && typeof obj.config === "object" ? (obj.config as Record<string, unknown>) : {};

  const nodes: GraphNodeInput[] = nodesRaw.map((row, idx) => {
    if (!row || typeof row !== "object") {
      throw new Error(`nodes[${idx}] must be a mapping`);
    }
    const node = row as Record<string, unknown>;
    const id = asText(node.id ?? node.node_id);
    const kind = asText(node.kind || "node") || "node";
    const plugin = asText(node.plugin);
    if (!id) {
      throw new Error(`nodes[${idx}].id is required`);
    }
    if (!plugin) {
      throw new Error(`nodes[${idx}].plugin is required`);
    }
    const cfg = node.config && typeof node.config === "object" ? (node.config as Record<string, unknown>) : {};
    return {
      id,
      kind,
      plugin,
      config: { ...cfg }
    };
  });

  const edges: GraphEdgeInput[] = edgesRaw.map((row, idx) => {
    if (!row || typeof row !== "object") {
      throw new Error(`edges[${idx}] must be a mapping`);
    }
    const edge = row as Record<string, unknown>;
    const src = asText(edge.src ?? edge.from);
    const dst = asText(edge.dst ?? edge.to);
    if (!src || !dst) {
      throw new Error(`edges[${idx}] requires src/dst`);
    }
    const srcPort = asText(edge.src_port ?? edge.from_port);
    const dstPort = asText(edge.dst_port ?? edge.to_port);
    const out: GraphEdgeInput = { src, dst };
    if (srcPort) out.src_port = srcPort;
    if (dstPort) out.dst_port = dstPort;
    return out;
  });

  const versionNum = asNumber(obj.version);
  if (versionNum !== undefined && versionNum !== 2) {
    throw new Error("spec.version must be 2");
  }

  return {
    version: 2,
    nodes,
    edges,
    config: { ...configRaw }
  };
}
