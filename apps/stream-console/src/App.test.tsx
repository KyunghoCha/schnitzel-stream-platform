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
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
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
      })
    );
  });

  it("renders shell and tabs", () => {
    render(<App />);
    expect(screen.getByText("Stream Console")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Presets" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Governance" })).toBeInTheDocument();
  });

  it("loads presets when switching tab", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Presets" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("inproc_demo")).toBeInTheDocument();
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
