import { Connection, Edge, EdgeChange, Node, ReactFlowInstance } from "@xyflow/react";

import { GraphProfileItem, EditorValidationSummary } from "../../app_types";
import { GraphSpecInput } from "../../api";
import { editorNodeTypes } from "../../editor_nodes";
import { EditorCanvas } from "./EditorCanvas";

type EditorTabProps = {
  busy: boolean;
  editorAllowExperimental: boolean;
  onEditorAllowExperimentalChange: (value: boolean) => void;
  onReloadProfiles: () => void;
  editorProfileId: string;
  onEditorProfileIdChange: (value: string) => void;
  editorProfiles: GraphProfileItem[];
  onLoadProfile: () => void;
  currentEditorProfile: GraphProfileItem | undefined;

  editorInputPath: string;
  onEditorInputPathChange: (value: string) => void;
  editorCameraIndex: string;
  onEditorCameraIndexChange: (value: string) => void;
  editorDevice: string;
  onEditorDeviceChange: (value: string) => void;
  editorModelPath: string;
  onEditorModelPathChange: (value: string) => void;
  editorLoop: string;
  onEditorLoopChange: (value: string) => void;
  editorMaxEvents: string;
  onEditorMaxEventsChange: (value: string) => void;

  onAddNode: (kind: "source" | "node" | "sink") => void;
  editorEdgeSrc: string;
  onEditorEdgeSrcChange: (value: string) => void;
  editorEdgeDst: string;
  onEditorEdgeDstChange: (value: string) => void;
  onAddEdge: () => void;
  onAutoLayout: () => void;
  onAlignHorizontal: () => void;
  onAlignVertical: () => void;
  onFitView: () => void;

  flowNodes: Node[];
  flowEdges: Edge[];
  onCanvasNodesRemoved: (nodeIds: string[]) => void;
  onCanvasPositionsCommit: (positions: Record<string, { x: number; y: number }>) => void;
  onFlowEdgesChange: (changes: EdgeChange[]) => void;
  onFlowConnect: (connection: Connection) => void;
  onFlowInit: (instance: ReactFlowInstance<any, any>) => void;
  onCanvasNodeSelect: (nodeId: string) => void;

  editorSpec: GraphSpecInput;
  editorSelectedNode: string;
  onEditorSelectedNodeChange: (value: string) => void;
  onSelectEditorNode: (nodeId: string) => void;
  editorNodeId: string;
  onEditorNodeIdChange: (value: string) => void;
  editorNodeKind: string;
  onEditorNodeKindChange: (value: string) => void;
  editorNodePlugin: string;
  onEditorNodePluginChange: (value: string) => void;
  editorNodePosX: string;
  onEditorNodePosXChange: (value: string) => void;
  editorNodePosY: string;
  onEditorNodePosYChange: (value: string) => void;
  onSaveNode: () => void;
  onRemoveNode: () => void;
  editorNodeConfig: string;
  onEditorNodeConfigChange: (value: string) => void;

  onRemoveEditorEdge: (index: number) => void;

  onExportYaml: () => void;
  onImportYaml: () => void;
  onValidateGraph: () => void;
  onRunGraph: () => void;
  editorYaml: string;
  onEditorYamlChange: (value: string) => void;

  editorValidationSummary: EditorValidationSummary | null;
  editorActionLog: string;
  editorApiOutput: string;
};

export function EditorTab({
  busy,
  editorAllowExperimental,
  onEditorAllowExperimentalChange,
  onReloadProfiles,
  editorProfileId,
  onEditorProfileIdChange,
  editorProfiles,
  onLoadProfile,
  currentEditorProfile,
  editorInputPath,
  onEditorInputPathChange,
  editorCameraIndex,
  onEditorCameraIndexChange,
  editorDevice,
  onEditorDeviceChange,
  editorModelPath,
  onEditorModelPathChange,
  editorLoop,
  onEditorLoopChange,
  editorMaxEvents,
  onEditorMaxEventsChange,
  onAddNode,
  editorEdgeSrc,
  onEditorEdgeSrcChange,
  editorEdgeDst,
  onEditorEdgeDstChange,
  onAddEdge,
  onAutoLayout,
  onAlignHorizontal,
  onAlignVertical,
  onFitView,
  flowNodes,
  flowEdges,
  onCanvasNodesRemoved,
  onCanvasPositionsCommit,
  onFlowEdgesChange,
  onFlowConnect,
  onFlowInit,
  onCanvasNodeSelect,
  editorSpec,
  editorSelectedNode,
  onEditorSelectedNodeChange,
  onSelectEditorNode,
  editorNodeId,
  onEditorNodeIdChange,
  editorNodeKind,
  onEditorNodeKindChange,
  editorNodePlugin,
  onEditorNodePluginChange,
  editorNodePosX,
  onEditorNodePosXChange,
  editorNodePosY,
  onEditorNodePosYChange,
  onSaveNode,
  onRemoveNode,
  editorNodeConfig,
  onEditorNodeConfigChange,
  onRemoveEditorEdge,
  onExportYaml,
  onImportYaml,
  onValidateGraph,
  onRunGraph,
  editorYaml,
  onEditorYamlChange,
  editorValidationSummary,
  editorActionLog,
  editorApiOutput
}: EditorTabProps) {
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
              onChange={(e) => onEditorAllowExperimentalChange(e.target.checked)}
            />
            experimental profiles
          </label>
          <button disabled={busy} onClick={onReloadProfiles}>
            Reload Profiles
          </button>
          <select value={editorProfileId} onChange={(e) => onEditorProfileIdChange(e.target.value)}>
            {editorProfiles.map((item) => (
              <option key={item.profile_id} value={item.profile_id}>
                {item.profile_id}
              </option>
            ))}
          </select>
          <button disabled={busy} onClick={onLoadProfile}>
            Load Profile
          </button>
          <span className="hint">
            selected: {currentEditorProfile?.profile_id ?? "-"}
            {currentEditorProfile?.experimental ? " (experimental)" : ""}
          </span>
        </div>

        <div className="row wrap">
          <input value={editorInputPath} onChange={(e) => onEditorInputPathChange(e.target.value)} placeholder="override input path" />
          <input value={editorCameraIndex} onChange={(e) => onEditorCameraIndexChange(e.target.value)} placeholder="override camera index" />
          <input value={editorDevice} onChange={(e) => onEditorDeviceChange(e.target.value)} placeholder="override device" />
          <input value={editorModelPath} onChange={(e) => onEditorModelPathChange(e.target.value)} placeholder="override model path" />
          <input value={editorLoop} onChange={(e) => onEditorLoopChange(e.target.value)} placeholder="override loop true|false" />
          <input value={editorMaxEvents} onChange={(e) => onEditorMaxEventsChange(e.target.value)} placeholder="max events" />
        </div>

        <div className="row wrap">
          <button disabled={busy} onClick={() => onAddNode("source")}>
            Add Source
          </button>
          <button disabled={busy} onClick={() => onAddNode("node")}>
            Add Node
          </button>
          <button disabled={busy} onClick={() => onAddNode("sink")}>
            Add Sink
          </button>
          <select value={editorEdgeSrc} onChange={(e) => onEditorEdgeSrcChange(e.target.value)}>
            {editorSpec.nodes.map((node) => (
              <option key={`src-${node.id}`} value={node.id}>
                {node.id}
              </option>
            ))}
          </select>
          <select value={editorEdgeDst} onChange={(e) => onEditorEdgeDstChange(e.target.value)}>
            {editorSpec.nodes.map((node) => (
              <option key={`dst-${node.id}`} value={node.id}>
                {node.id}
              </option>
            ))}
          </select>
          <button disabled={busy} onClick={onAddEdge}>
            Add Edge
          </button>
          <button disabled={busy} onClick={onAutoLayout}>
            Auto Layout
          </button>
          <button disabled={busy} onClick={onAlignHorizontal}>
            Align Horizontal
          </button>
          <button disabled={busy} onClick={onAlignVertical}>
            Align Vertical
          </button>
          <button disabled={busy} onClick={onFitView}>
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
            onInit={onFlowInit}
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
                  onEditorSelectedNodeChange(next);
                  onSelectEditorNode(next);
                }}
              >
                {editorSpec.nodes.map((node) => (
                  <option key={`node-${node.id}`} value={node.id}>
                    {node.id}
                  </option>
                ))}
              </select>
              <input value={editorNodeId} onChange={(e) => onEditorNodeIdChange(e.target.value)} placeholder="node id" />
              <input value={editorNodeKind} onChange={(e) => onEditorNodeKindChange(e.target.value)} placeholder="kind" />
              <input value={editorNodePlugin} onChange={(e) => onEditorNodePluginChange(e.target.value)} placeholder="plugin" />
              <input value={editorNodePosX} onChange={(e) => onEditorNodePosXChange(e.target.value)} placeholder="x" />
              <input value={editorNodePosY} onChange={(e) => onEditorNodePosYChange(e.target.value)} placeholder="y" />
              <button disabled={busy} onClick={onSaveNode}>
                Save Node
              </button>
              <button disabled={busy} onClick={onRemoveNode}>
                Remove Node
              </button>
            </div>
            <textarea value={editorNodeConfig} onChange={(e) => onEditorNodeConfigChange(e.target.value)} rows={10} className="code-area" />
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
                        <button disabled={busy} onClick={() => onRemoveEditorEdge(idx)}>
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
          <button disabled={busy} onClick={onExportYaml}>
            Export YAML
          </button>
          <button disabled={busy} onClick={onImportYaml}>
            Import YAML
          </button>
          <button disabled={busy} onClick={onValidateGraph}>
            Validate Graph
          </button>
          <button disabled={busy} onClick={onRunGraph}>
            Run Graph
          </button>
        </div>
        <textarea value={editorYaml} onChange={(e) => onEditorYamlChange(e.target.value)} rows={14} className="code-area" placeholder="version: 2" />

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
