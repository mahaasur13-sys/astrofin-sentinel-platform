from typing import Any, Dict


class Reconciler:
    """
    Minimal reconciler required for tests + ATOMController wiring.

    Accepts the shared K8sClient so a real reconcile pass can read/refresh
    cluster state without having to construct another API client per loop.
    The historical in-memory ``state`` dict is preserved for unit tests
    that introspect ``reconciler.state["last"]``.
    """

    def __init__(self, k8s: Any | None = None):
        self.k8s = k8s
        self.state: Dict[str, Any] = {}

    def reconcile(self, obj: Any) -> Dict:
        return self.reconciler(obj)

    def reconciler(self, obj: Any) -> Dict:
        self.state["last"] = obj
        return {
            "status": "ok",
            "object": obj,
        }
