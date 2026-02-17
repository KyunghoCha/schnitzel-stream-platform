import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

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
        if (url.includes("/api/v1/fleet/status")) {
          return new Response(JSON.stringify({ ...okEnvelope, data: { running: 0, total: 0, lines: [] } }));
        }
        if (url.includes("/api/v1/monitor/snapshot")) {
          return new Response(JSON.stringify({ ...okEnvelope, data: { snapshot: { streams_total: 0, streams: [] } } }));
        }
        if (url.includes("/api/v1/health")) {
          return new Response(JSON.stringify({ ...okEnvelope, data: { service: "stream_control_api", security_mode: "local-only" } }));
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

  it("runs dashboard refresh", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Ping" }));

    await waitFor(() => {
      expect(screen.getByText(/\[OK\] dashboard.refresh/i)).toBeInTheDocument();
    });
  });
});
