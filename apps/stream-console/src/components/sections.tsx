import { FormEvent } from "react";

import { PresetItem } from "../app_types";

type DashboardSectionProps = {
  busy: boolean;
  health: Record<string, unknown> | null;
  fleetStatus: Record<string, unknown> | null;
  monitorSnapshot: Record<string, unknown> | null;
  onRefresh: () => void;
};

export function DashboardSection({ busy, health, fleetStatus, monitorSnapshot, onRefresh }: DashboardSectionProps) {
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
          <button disabled={busy} onClick={onRefresh}>
            Refresh
          </button>
        </div>
        <p className="hint">Monitor shows fleet log/PID streams only. Preset run output is a one-shot session result.</p>
        <pre>{JSON.stringify({ health, fleetStatus, monitorSnapshot }, null, 2)}</pre>
      </article>
    </section>
  );
}

type PresetsSectionProps = {
  busy: boolean;
  showExperimental: boolean;
  onToggleExperimental: (value: boolean) => void;
  onReload: () => void;
  presetId: string;
  onPresetIdChange: (value: string) => void;
  presets: PresetItem[];
  presetInputPath: string;
  onPresetInputPathChange: (value: string) => void;
  presetCameraIndex: string;
  onPresetCameraIndexChange: (value: string) => void;
  presetDevice: string;
  onPresetDeviceChange: (value: string) => void;
  presetModelPath: string;
  onPresetModelPathChange: (value: string) => void;
  presetYoloConf: string;
  onPresetYoloConfChange: (value: string) => void;
  presetYoloIou: string;
  onPresetYoloIouChange: (value: string) => void;
  presetYoloMaxDet: string;
  onPresetYoloMaxDetChange: (value: string) => void;
  presetLoop: string;
  onPresetLoopChange: (value: string) => void;
  presetMaxEvents: string;
  onPresetMaxEventsChange: (value: string) => void;
  onValidate: () => void;
  onRun: () => void;
  currentPreset: PresetItem | undefined;
  presetSessionOutput: string;
};

export function PresetsSection({
  busy,
  showExperimental,
  onToggleExperimental,
  onReload,
  presetId,
  onPresetIdChange,
  presets,
  presetInputPath,
  onPresetInputPathChange,
  presetCameraIndex,
  onPresetCameraIndexChange,
  presetDevice,
  onPresetDeviceChange,
  presetModelPath,
  onPresetModelPathChange,
  presetYoloConf,
  onPresetYoloConfChange,
  presetYoloIou,
  onPresetYoloIouChange,
  presetYoloMaxDet,
  onPresetYoloMaxDetChange,
  presetLoop,
  onPresetLoopChange,
  presetMaxEvents,
  onPresetMaxEventsChange,
  onValidate,
  onRun,
  currentPreset,
  presetSessionOutput
}: PresetsSectionProps) {
  return (
    <section className="panel-grid">
      <article className="card wide">
        <div className="row between wrap">
          <h3>Preset Catalog</h3>
          <label className="checkbox">
            <input type="checkbox" checked={showExperimental} onChange={(e) => onToggleExperimental(e.target.checked)} />
            experimental
          </label>
        </div>
        <div className="row wrap">
          <button disabled={busy} onClick={onReload}>
            Reload Presets
          </button>
          <select value={presetId} onChange={(e) => onPresetIdChange(e.target.value)}>
            {presets.map((preset) => (
              <option key={preset.preset_id} value={preset.preset_id}>
                {preset.preset_id}
              </option>
            ))}
          </select>
          <input value={presetInputPath} onChange={(e) => onPresetInputPathChange(e.target.value)} placeholder="input path" />
          <input value={presetCameraIndex} onChange={(e) => onPresetCameraIndexChange(e.target.value)} placeholder="camera index" />
          <input value={presetDevice} onChange={(e) => onPresetDeviceChange(e.target.value)} placeholder="device (cpu|0)" />
          <input value={presetModelPath} onChange={(e) => onPresetModelPathChange(e.target.value)} placeholder="model path" />
          <input value={presetYoloConf} onChange={(e) => onPresetYoloConfChange(e.target.value)} placeholder="yolo conf (0..1)" />
          <input value={presetYoloIou} onChange={(e) => onPresetYoloIouChange(e.target.value)} placeholder="yolo iou (0..1)" />
          <input value={presetYoloMaxDet} onChange={(e) => onPresetYoloMaxDetChange(e.target.value)} placeholder="yolo max det" />
          <input value={presetLoop} onChange={(e) => onPresetLoopChange(e.target.value)} placeholder="loop true|false" />
          <input value={presetMaxEvents} onChange={(e) => onPresetMaxEventsChange(e.target.value)} placeholder="max events" />
          <button disabled={busy} onClick={onValidate}>
            Validate
          </button>
          <button disabled={busy} onClick={onRun}>
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

type FleetSectionProps = {
  busy: boolean;
  fleetConfig: string;
  onFleetConfigChange: (value: string) => void;
  fleetGraphTemplate: string;
  onFleetGraphTemplateChange: (value: string) => void;
  fleetLogDir: string;
  onFleetLogDirChange: (value: string) => void;
  fleetStreams: string;
  onFleetStreamsChange: (value: string) => void;
  fleetExtraArgs: string;
  onFleetExtraArgsChange: (value: string) => void;
  onStart: () => void;
  onStop: () => void;
  onStatus: () => void;
  fleetStatus: Record<string, unknown> | null;
};

export function FleetSection({
  busy,
  fleetConfig,
  onFleetConfigChange,
  fleetGraphTemplate,
  onFleetGraphTemplateChange,
  fleetLogDir,
  onFleetLogDirChange,
  fleetStreams,
  onFleetStreamsChange,
  fleetExtraArgs,
  onFleetExtraArgsChange,
  onStart,
  onStop,
  onStatus,
  fleetStatus
}: FleetSectionProps) {
  return (
    <section className="panel-grid">
      <article className="card wide">
        <h3>Fleet Control</h3>
        <form
          className="column"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            onStart();
          }}
        >
          <div className="row wrap">
            <input value={fleetConfig} onChange={(e) => onFleetConfigChange(e.target.value)} placeholder="config path" />
            <input value={fleetGraphTemplate} onChange={(e) => onFleetGraphTemplateChange(e.target.value)} placeholder="graph template" />
            <input value={fleetLogDir} onChange={(e) => onFleetLogDirChange(e.target.value)} placeholder="log dir (optional)" />
            <input value={fleetStreams} onChange={(e) => onFleetStreamsChange(e.target.value)} placeholder="stream ids csv" />
            <input value={fleetExtraArgs} onChange={(e) => onFleetExtraArgsChange(e.target.value)} placeholder="extra args" />
          </div>
          <div className="row wrap">
            <button type="submit" disabled={busy}>
              Start
            </button>
            <button type="button" disabled={busy} onClick={onStop}>
              Stop
            </button>
            <button type="button" disabled={busy} onClick={onStatus}>
              Status
            </button>
          </div>
        </form>
        <pre>{JSON.stringify(fleetStatus, null, 2)}</pre>
      </article>
    </section>
  );
}

type MonitorSectionProps = {
  busy: boolean;
  monitorSnapshot: Record<string, unknown> | null;
  onRefresh: () => void;
};

export function MonitorSection({ busy, monitorSnapshot, onRefresh }: MonitorSectionProps) {
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
          <button disabled={busy} onClick={onRefresh}>
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

type GovernanceSectionProps = {
  busy: boolean;
  auditLimit: string;
  onAuditLimitChange: (value: string) => void;
  onRefresh: () => void;
  policySnapshot: Record<string, unknown> | null;
  auditRows: Record<string, unknown>[];
};

export function GovernanceSection({
  busy,
  auditLimit,
  onAuditLimitChange,
  onRefresh,
  policySnapshot,
  auditRows
}: GovernanceSectionProps) {
  return (
    <section className="panel-grid">
      <article className="card wide">
        <div className="row wrap between">
          <h3>Governance Snapshot</h3>
          <div className="row wrap">
            <input value={auditLimit} onChange={(e) => onAuditLimitChange(e.target.value)} placeholder="audit limit" />
            <button disabled={busy} onClick={onRefresh}>
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
