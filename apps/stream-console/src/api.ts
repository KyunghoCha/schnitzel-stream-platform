export type Envelope<T = Record<string, unknown>> = {
  schema_version: number;
  status: "ok" | "error";
  request_id: string;
  ts: string;
  data: T;
  error?: Record<string, unknown> | null;
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
