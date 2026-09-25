"""DAG per-node metrics collector."""

from __future__ import annotations

from dataclasses import dataclass

from core.dag.context import DAGContext


@dataclass
class DAGRunSummary:
    run_id: str
    name: str
    total_ms: float
    node_results: dict[str, "NodeResult"]  # noqa: F821
    ok_count: int
    fail_count: int

    @property
    def bottleneck_node(self) -> tuple[str, float]:
        """Узел с наибольшей длительностью (потенциальный bottleneck)."""
        if not self.node_results:
            return ("", 0.0)
        slowest = max(
            self.node_results.items(), key=lambda x: x[1].duration_ms
        )
        return slowest[0], slowest[1].duration_ms

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "name": self.name,
            "total_ms": round(self.total_ms, 1),
            "ok_count": self.ok_count,
            "fail_count": self.fail_count,
            "bottleneck_node": self.bottleneck_node[0],
            "bottleneck_ms": round(self.bottleneck_node[1], 1),
            "node_results": {
                nid: {
                    "ok": nr.ok,
                    "duration_ms": round(nr.duration_ms, 1),
                    "error": nr.error,
                    "retry_count": nr.retry_count,
                }
                for nid, nr in self.node_results.items()
            },
        }


def summarize_run(ctx: DAGContext, name: str = "") -> DAGRunSummary:
    from core.dag.context import NodeResult  # break cycle

    ok = sum(1 for r in ctx.results.values() if r.ok)
    return DAGRunSummary(
        run_id=ctx.run_id,
        name=name or "unknown",
        total_ms=ctx.elapsed_ms,
        node_results=dict(ctx.results),
        ok_count=ok,
        fail_count=len(ctx.results) - ok,
    )
