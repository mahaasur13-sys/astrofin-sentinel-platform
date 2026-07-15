"""ACOS Scheduler Contract — enforced scheduler interface."""
from typing import Protocol, Any

class SchedulerContract(Protocol):
    """ENFORCED contract for all Scheduler implementations."""
    
    def schedule(self, dag: dict, context: dict) -> dict:
        """Compile DAG into executable schedule. MUST return dict with 'nodes'."""
        ...
    
    def route(self, job: dict) -> str:
        """Route job to appropriate executor. MUST return executor name."""
        ...

def validate_scheduler_contract(obj: Any) -> None:
    """FAIL FAST — raise if object violates SchedulerContract."""
    required = ["schedule", "route"]
    for method in required:
        if not hasattr(obj, method):
            raise RuntimeError(
                f"Scheduler contract violation: missing method '{method}()'. "
                f"Object: {type(obj).__name__}"
            )
