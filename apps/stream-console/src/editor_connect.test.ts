import { findSnapTargetInput, isConnectionAllowedHybrid, isDuplicateEdgeExact } from "./editor_connect";

describe("editor_connect", () => {
  it("allows valid connection in hybrid policy", () => {
    const gate = isConnectionAllowedHybrid({
      sourceId: "node_a",
      targetId: "node_b",
      sourceKind: "node",
      targetKind: "node",
      existingEdges: [],
      candidate: { src: "node_a", dst: "node_b" }
    });
    expect(gate).toEqual({ ok: true });
  });

  it("blocks sink outgoing and source incoming in hybrid policy", () => {
    const sinkBlocked = isConnectionAllowedHybrid({
      sourceId: "sink_1",
      targetId: "node_1",
      sourceKind: "sink",
      targetKind: "node",
      existingEdges: [],
      candidate: { src: "sink_1", dst: "node_1" }
    });
    expect(sinkBlocked).toEqual({ ok: false, reason: "sink_outgoing_blocked" });

    const sourceBlocked = isConnectionAllowedHybrid({
      sourceId: "node_1",
      targetId: "source_1",
      sourceKind: "node",
      targetKind: "source",
      existingEdges: [],
      candidate: { src: "node_1", dst: "source_1" }
    });
    expect(sourceBlocked).toEqual({ ok: false, reason: "source_incoming_blocked" });
  });

  it("blocks self-loop and exact duplicate", () => {
    const selfLoop = isConnectionAllowedHybrid({
      sourceId: "n1",
      targetId: "n1",
      sourceKind: "node",
      targetKind: "node",
      existingEdges: [],
      candidate: { src: "n1", dst: "n1" }
    });
    expect(selfLoop).toEqual({ ok: false, reason: "self_loop_blocked" });

    const existing = [{ src: "n1", dst: "n2", src_port: "out", dst_port: "in" }];
    expect(isDuplicateEdgeExact(existing, { src: "n1", dst: "n2", src_port: "out", dst_port: "in" })).toBe(true);
    const duplicate = isConnectionAllowedHybrid({
      sourceId: "n1",
      targetId: "n2",
      sourceKind: "node",
      targetKind: "node",
      existingEdges: existing,
      candidate: { src: "n1", dst: "n2", src_port: "out", dst_port: "in" }
    });
    expect(duplicate).toEqual({ ok: false, reason: "duplicate_edge_blocked" });
  });

  it("finds nearest valid snap target and excludes source/source-kind targets", () => {
    const target = findSnapTargetInput({
      flowPoint: { x: 103, y: 122 },
      sourceNodeId: "src",
      thresholdFlow: 42,
      nodes: [
        { id: "src", data: { kind: "source" }, position: { x: 100, y: 100 }, width: 200, height: 90 },
        { id: "source_like", data: { kind: "source" }, position: { x: 100, y: 100 }, width: 200, height: 90 },
        { id: "node_a", data: { kind: "node" }, position: { x: 100, y: 100 }, width: 200, height: 90 }
      ]
    });
    expect(target).toEqual({ nodeId: "node_a", handleId: "in" });
  });

  it("returns null when pointer is outside snap threshold", () => {
    const target = findSnapTargetInput({
      flowPoint: { x: 1000, y: 1000 },
      sourceNodeId: "src",
      thresholdFlow: 20,
      nodes: [{ id: "node_a", data: { kind: "node" }, position: { x: 0, y: 0 }, width: 120, height: 50 }]
    });
    expect(target).toBeNull();
  });
});
