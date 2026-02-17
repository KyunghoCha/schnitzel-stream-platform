import { alignNodePositions, computeAutoLayout } from "./editor_layout";

describe("editor_layout", () => {
  it("computes deterministic positions for a DAG", () => {
    const nodes = [{ id: "src" }, { id: "mid" }, { id: "out" }];
    const edges = [
      { src: "src", dst: "mid" },
      { src: "mid", dst: "out" }
    ];

    const first = computeAutoLayout(nodes, edges);
    const second = computeAutoLayout(nodes, edges);
    expect(first).toEqual(second);
    expect(first.src.x).toBeLessThan(first.mid.x);
    expect(first.mid.x).toBeLessThan(first.out.x);
  });

  it("falls back safely when graph contains a cycle", () => {
    const nodes = [{ id: "a" }, { id: "b" }, { id: "c" }];
    const edges = [
      { src: "a", dst: "b" },
      { src: "b", dst: "a" }
    ];

    const pos = computeAutoLayout(nodes, edges);
    expect(Object.keys(pos).sort()).toEqual(["a", "b", "c"]);
    expect(Number.isFinite(pos.a.x)).toBe(true);
    expect(Number.isFinite(pos.b.y)).toBe(true);
    expect(Number.isFinite(pos.c.x)).toBe(true);
  });

  it("aligns positions with non-overlap packing on horizontal and vertical axes", () => {
    const base = {
      a: { x: 10, y: 10 },
      b: { x: 20, y: 50 },
      c: { x: 30, y: 90 }
    };
    const sizes = {
      a: { width: 120, height: 40 },
      b: { width: 120, height: 40 },
      c: { width: 120, height: 40 }
    };

    const horizontal = alignNodePositions(base, ["a", "b", "c"], "horizontal", { sizes, gap: 36 });
    expect(horizontal.a.y).toBe(horizontal.b.y);
    expect(horizontal.b.y).toBe(horizontal.c.y);
    expect(horizontal.b.x).toBeGreaterThanOrEqual(horizontal.a.x + 120 + 36);
    expect(horizontal.c.x).toBeGreaterThanOrEqual(horizontal.b.x + 120 + 36);

    const vertical = alignNodePositions(base, ["a", "b", "c"], "vertical", { sizes, gap: 36 });
    expect(vertical.a.x).toBe(vertical.b.x);
    expect(vertical.b.x).toBe(vertical.c.x);
    expect(vertical.b.y).toBeGreaterThanOrEqual(vertical.a.y + 40 + 36);
    expect(vertical.c.y).toBeGreaterThanOrEqual(vertical.b.y + 40 + 36);
  });
});
