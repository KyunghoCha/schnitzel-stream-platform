import { FormEvent, useMemo, useState } from "react";
import { apiRequest, defaultApiBase } from "./api";

type TabId = "dashboard" | "presets" | "fleet" | "monitor" | "governance";

type PresetItem = {
  preset_id: string;
  experimental: boolean;
  graph: string;
  description: string;
};

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "presets", label: "Presets" },
  { id: "fleet", label: "Fleet" },
  { id: "monitor", label: "Monitor" },
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

  const [output, setOutput] = useState<string>("Ready");
  const currentPreset = useMemo(() => presets.find((x) => x.preset_id === presetId), [presets, presetId]);

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

  function handleTabClick(nextTab: TabId) {
    setTab(nextTab);
    if (nextTab === "dashboard") void loadDashboard();
    if (nextTab === "presets") void loadPresets();
    if (nextTab === "fleet") void fleetQueryStatus();
    if (nextTab === "monitor") void monitorQuerySnapshot();
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
        {tab === "governance" && renderGovernance()}
      </main>
    </div>
  );
}
