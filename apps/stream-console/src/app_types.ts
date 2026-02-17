export type TabId = "dashboard" | "presets" | "fleet" | "monitor" | "editor" | "governance";

export type PresetItem = {
  preset_id: string;
  experimental: boolean;
  graph: string;
  description: string;
};

export type GraphProfileItem = {
  profile_id: string;
  experimental: boolean;
  template: string;
  description: string;
};

export type NodePos = { x: number; y: number };

export type EditorValidationSummary = {
  status: "ok" | "error";
  nodeCount: number;
  edgeCount: number;
  message: string;
};
