import { memo } from "react";
import { Handle, NodeProps, Position } from "@xyflow/react";

export type EditorNodeKind = "source" | "node" | "sink";

export type EditorNodeData = {
  id: string;
  kind: EditorNodeKind;
  plugin: string;
  label: string;
};

function pluginShortName(plugin: string): string {
  const raw = String(plugin || "").trim();
  if (!raw) return "(plugin)";
  const lastDot = raw.lastIndexOf(".");
  const lastColon = raw.lastIndexOf(":");
  const cut = Math.max(lastDot, lastColon);
  if (cut >= 0 && cut + 1 < raw.length) {
    return raw.slice(cut + 1);
  }
  return raw;
}

const EditorNodeCard = memo(function EditorNodeCard({ data }: NodeProps) {
  const nodeData = (data ?? {}) as Partial<EditorNodeData>;
  const kind = nodeData.kind === "source" || nodeData.kind === "sink" ? nodeData.kind : "node";
  const kindClass = kind === "source" ? "source" : kind === "sink" ? "sink" : "node";
  const hasInput = kind !== "source";
  const hasOutput = kind !== "sink";
  const nodeId = String(nodeData.id ?? "(node)");
  const label = String(nodeData.label ?? "node");
  const plugin = String(nodeData.plugin ?? "");

  return (
    <div className={`editor-kind-node ${kindClass}`} data-kind={kind}>
      {hasInput ? <Handle type="target" position={Position.Left} id="in" /> : null}
      <div className="editor-kind-node-main">
        <div className="editor-kind-node-title">{nodeId}</div>
        <div className="editor-kind-node-kind">{label}</div>
        <div className="editor-kind-node-plugin">{pluginShortName(plugin)}</div>
      </div>
      {hasOutput ? <Handle type="source" position={Position.Right} id="out" /> : null}
    </div>
  );
});

export const editorNodeTypes = {
  source: EditorNodeCard,
  node: EditorNodeCard,
  sink: EditorNodeCard
};
