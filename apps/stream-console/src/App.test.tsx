import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { App } from "./App";

vi.mock("@xyflow/react", () => ({
  ReactFlow: ({ children }: { children?: unknown }) => <div data-testid="react-flow">{children as any}</div>,
  Background: () => <div data-testid="flow-bg" />,
  Controls: () => <div data-testid="flow-controls" />,
  MiniMap: () => <div data-testid="flow-minimap" />
}));

const okEnvelope = {
  schema_version: 1,
  status: "ok",
  request_id: "r1",
  ts: new Date().toISOString(),
  data: {}
};

describe("Stream Console App", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.restoreAllMocks();
    fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/presets")) {
        return new Response(
          JSON.stringify({
            ...okEnvelope,
            data: {
              presets: [
                {
                  preset_id: "inproc_demo",
                  experimental: false,
                  graph: "configs/graphs/dev_inproc_demo_v2.yaml",
                  description: "demo"
                }
              ]
            }
          })
        );
      }
      if (url.includes("/api/v1/graph/profiles")) {
        return new Response(
          JSON.stringify({
            ...okEnvelope,
            data: {
              profiles: [
                {
                  profile_id: "inproc_demo",
                  experimental: false,
                  template: "configs/graphs/templates/inproc_demo_v2.template.yaml",
                  description: "editor demo"
                }
              ]
            }
          })
        );
      }
      if (url.includes("/api/v1/graph/from-profile")) {
        return new Response(
          JSON.stringify({
            ...okEnvelope,
            data: {
              profile_id: "inproc_demo",
              overrides: {},
              spec: {
                version: 2,
                nodes: [
                  {
                    id: "src",
                    kind: "source",
                    plugin: "schnitzel_stream.nodes.dev:StaticSource",
                    config: { packets: [] }
                  },
                  {
                    id: "out",
                    kind: "sink",
                    plugin: "schnitzel_stream.nodes.dev:PrintSink",
                    config: {}
                  }
                ],
                edges: [{ src: "src", dst: "out" }],
                config: {}
              },
              validation: { ok: true, error: "", node_count: 2, edge_count: 1 }
            }
          })
        );
      }
      if (url.includes("/api/v1/graph/validate")) {
        return new Response(
          JSON.stringify({
            ...okEnvelope,
            data: {
              validation: { ok: true, error: "", node_count: 2, edge_count: 1 }
            }
          })
        );
      }
      if (url.includes("/api/v1/graph/run")) {
        return new Response(
          JSON.stringify({
            ...okEnvelope,
            data: {
              returncode: 0,
              command: "python -m schnitzel_stream --graph outputs/tmp/editor.yaml --max-events 30",
              temp_spec_path: "outputs/tmp/editor.yaml"
            }
          })
        );
      }
      if (url.includes("/api/v1/fleet/status")) {
        return new Response(JSON.stringify({ ...okEnvelope, data: { running: 0, total: 0, lines: [] } }));
      }
      if (url.includes("/api/v1/monitor/snapshot")) {
        return new Response(JSON.stringify({ ...okEnvelope, data: { snapshot: { streams_total: 0, streams: [] } } }));
      }
      if (url.includes("/api/v1/health")) {
        return new Response(
          JSON.stringify({ ...okEnvelope, data: { service: "stream_control_api", security_mode: "local-only" } })
        );
      }
      if (url.includes("/api/v1/governance/policy-snapshot")) {
        return new Response(JSON.stringify({ ...okEnvelope, data: { security_mode: "local-only" } }));
      }
      if (url.includes("/api/v1/governance/audit")) {
        return new Response(JSON.stringify({ ...okEnvelope, data: { events: [] } }));
      }
      return new Response(JSON.stringify(okEnvelope));
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  it("renders shell and tabs", () => {
    render(<App />);
    expect(screen.getByText("Stream Console")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Presets" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Editor" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Governance" })).toBeInTheDocument();
    expect(screen.getByText(/Monitor shows fleet log\/PID streams only/i)).toBeInTheDocument();
  });

  it("loads presets when switching tab", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Presets" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("inproc_demo")).toBeInTheDocument();
    });
    expect(screen.getByText("Preset Session Output (One-shot)")).toBeInTheDocument();
    expect(screen.getByText(/not a fleet monitor stream/i)).toBeInTheDocument();
  });

  it("shows advanced yolo override fields in presets tab", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Presets" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("inproc_demo")).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText("model path")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("yolo conf (0..1)")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("yolo iou (0..1)")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("yolo max det")).toBeInTheDocument();
  });

  it("sends advanced override fields when running a preset", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Presets" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("inproc_demo")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText("model path"), { target: { value: "models/yolov8n.pt" } });
    fireEvent.change(screen.getByPlaceholderText("yolo conf (0..1)"), { target: { value: "0.4" } });
    fireEvent.change(screen.getByPlaceholderText("yolo iou (0..1)"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByPlaceholderText("yolo max det"), { target: { value: "77" } });

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    await waitFor(() => {
      const runCall = fetchMock.mock.calls.find((call) => String(call[0]).includes("/api/v1/presets/inproc_demo/run"));
      expect(runCall).toBeTruthy();
    });

    const runCall = fetchMock.mock.calls.find((call) => String(call[0]).includes("/api/v1/presets/inproc_demo/run"));
    expect(runCall).toBeTruthy();
    const init = (runCall?.[1] ?? {}) as RequestInit;
    const body = JSON.parse(String(init.body ?? "{}"));
    expect(body.model_path).toBe("models/yolov8n.pt");
    expect(body.yolo_conf).toBe(0.4);
    expect(body.yolo_iou).toBe(0.5);
    expect(body.yolo_max_det).toBe(77);
  });

  it("renders editor tab and validates graph spec", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Editor" }));

    await waitFor(() => {
      expect(screen.getByText("Block Editor MVP")).toBeInTheDocument();
    });
    expect(screen.getByTestId("react-flow")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Validate Graph" }));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find((entry) => String(entry[0]).includes("/api/v1/graph/validate"));
      expect(call).toBeTruthy();
    });
  });

  it("calls graph run endpoint from editor", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Editor" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run Graph" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Run Graph" }));

    await waitFor(() => {
      const runCall = fetchMock.mock.calls.find((call) => String(call[0]).includes("/api/v1/graph/run"));
      expect(runCall).toBeTruthy();
    });
  });

  it("runs dashboard refresh", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Ping" }));

    await waitFor(() => {
      expect(screen.getByText(/\[OK\] dashboard.refresh/i)).toBeInTheDocument();
    });
  });
});
