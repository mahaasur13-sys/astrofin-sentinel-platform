"""ACOS Engine Contract — enforced execution engine interface."""
from typing import Protocol, Any

class ExecutionEngineContract(Protocol):
    """ENFORCED contract for execution engines."""
    
    def execute(self, dag: dict, context: dict) -> dict:
        """Execute compiled DAG. MUST return dict with 'results' and 'state'."""
        ...
    
    def get_state(self) -> dict:
        """Return current engine state."""
        ...

def validate_engine_contract(obj: Any) -> None:
    """FAIL FAST — raise if object violates ExecutionEngineContract."""
    required = ["execute", "get_state"]
    for method in required:
        if not hasattr(obj, method):
            raise RuntimeError(
                f"ExecutionEngine contract violation: missing method '{method}()'. "
                f"Object: {type(obj).__name__}"
            )
