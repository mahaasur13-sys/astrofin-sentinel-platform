# tests/conftest.py — SBS isolation for atom-federation-os tests
#
# Isolates tests from atomos_pkg dependency by mocking:
#   - atomos.core.execution_loop (ExecutionLoop → mock)
#   - atomos.swarm.swarm_engine (SwarmEngine → mock)
#   - atomos.runtime.async_runtime (AsyncExecutionEngine → mock)
#
# This allows tests to run even if atomos_pkg is not installed,
# and ensures deterministic execution by mocking random/time/uuid usage.

import os
import sys
import types
from pathlib import Path

# Deterministic environment — MUST be set before any other import
os.environ.setdefault('PYTHONHASHSEED', '0')
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')

_ROOT = Path(__file__).parent.parent


# ── Mock stubs ────────────────────────────────────────────────────────

class _MockExecutionLoop:
    def __init__(self, policy_kernel=None, federation_layer=None):
        self.pk = policy_kernel
        self.federation = federation_layer
        self._trace = []
        self._executed_plans = {}

    def execute(self, intent, context=None):
        import warnings
        warnings.warn(
            'ExecutionLoop.execute() is deprecated. Use ExecutionGateway.execute() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        import hashlib
        plan_id = hashlib.sha256(f'{intent}mock'.encode()).hexdigest()[:16]
        from dataclasses import dataclass
        @dataclass
        class MockPlan:
            plan_id: str
            intent: str
            steps: list
            total_risk_score: float = 0.0
            is_safe: bool = False
            blocked_at_step: str = ''
            blocked_reason: str = ''
            federation_hint: str = ''
            verification_hash: str = ''
        return MockPlan(plan_id=plan_id, intent=intent, steps=[])

    def execute_with_sbs(self, intent, context=None, sbs_enforcer=None, sbs_mode=None):
        plan = self.execute(intent, context)
        return plan, None

    def set_layers(self, *args, **kwargs):
        pass

    def collect_state(self):
        return {'drl': {}, 'ccl': {}, 'f2': {}, 'desc': {}}

    @staticmethod
    def sbs_is_available():
        return False

    @staticmethod
    def get_sbs_mode_enum():
        return None


class _MockSwarmEngine:
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

    def init(self) -> None:
        pass

    def get_strategy(self, task: str) -> str:
        t = task.lower()
        if any(kw in t for kw in ['search all', 'scan all', 'find all', 'audit']):
            return 'fan_out'
        if any(kw in t for kw in ['parallel', 'concurrent']):
            return 'concurrent'
        return 'sequential'

    def get_num_workers(self, task: str) -> int:
        return self.max_workers

    def run(self, task: str, num_workers: int | None = None, strategy: str = 'sequential') -> dict:
        workers = num_workers or self.max_workers
        return {
            'task': task,
            'strategy': strategy,
            'workers': workers,
            'subtasks': [],
            'merged_result': '[MOCK] Use real TAAR v14+ for actual execution',
        }

    def health(self) -> dict:
        return {'max_workers': self.max_workers, 'strategy': 'sequential'}


class _MockAsyncExecutionEngine:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self._active_tasks: dict = {}

    async def run(self, execution_graph):
        results = []
        for step in execution_graph:
            result = await self._execute_step(step)
            results.append(result)
        return results

    async def _execute_step(self, step):
        import asyncio
        await asyncio.sleep(0)  # no actual delay in mock
        return {'step_id': step.get('id', '?'), 'status': 'done', 'output': {}}

    async def execute_intent(self, intent, loop_component):
        plan = loop_component.execute(intent)
        return {'plan_id': plan.plan_id, 'steps': [], 'is_safe': plan.is_safe}


# ── Inject mocks into sys.modules BEFORE any test imports ─────────────

def _inject_mocks():
    # Stub module factories
    def make_stub(name):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    modules_to_mock = {
        'atomos': None,
        'atomos.core': None,
        'atomos.core.execution_loop': _MockExecutionLoop,
        'atomos.core.service_registry': None,
        'atomos.swarm': None,
        'atomos.swarm.swarm_engine': _MockSwarmEngine,
        'atomos.runtime': None,
        'atomos.runtime.async_runtime': _MockAsyncExecutionEngine,
    }

    for name, cls in modules_to_mock.items():
        make_stub(name)
        if cls is not None:
            setattr(sys.modules[name.split('.')[0]] if '.' in name else sys.modules[name],
                    name.split('.')[-1], cls)
        # For nested modules, also attach to parent
        parts = name.split('.')
        if len(parts) >= 2:
            parent_name = parts[0]
            attr = parts[1]
            if parent_name in sys.modules and not hasattr(sys.modules[parent_name], attr):
                setattr(sys.modules[parent_name], attr, sys.modules[name])


# Inject before any test code runs
_inject_mocks()

# Override specific modules with our mocks
sys.modules['atomos.core.execution_loop'] = types.ModuleType('atomos.core.execution_loop')
sys.modules['atomos.core.execution_loop'].ExecutionLoop = _MockExecutionLoop
sys.modules['atomos.core.execution_loop'].SBSRuntimeEnforcer = type('MockSBSEnforcer', (), {})
sys.modules['atomos.core.execution_loop'].ExecutionPlan = type('ExecutionPlan', (), {})
sys.modules['atomos.core.execution_loop'].SimulatedStep = type('SimulatedStep', (), {})
sys.modules['atomos.core.execution_loop'].RiskProfile = type('RiskProfile', (), {})

sys.modules['atomos.swarm.swarm_engine'] = types.ModuleType('atomos.swarm.swarm_engine')
sys.modules['atomos.swarm.swarm_engine'].register = lambda *a, **k: (lambda f: f)
sys.modules['atomos.swarm.swarm_engine'].SwarmEngine = _MockSwarmEngine

sys.modules['atomos.runtime.async_runtime'] = types.ModuleType('atomos.runtime.async_runtime')
sys.modules['atomos.runtime.async_runtime'].AsyncExecutionEngine = _MockAsyncExecutionEngine

sys.modules['atomos.core.service_registry'] = types.ModuleType('atomos.core.service_registry')
sys.modules['atomos.core.service_registry'].register = lambda *a, **k: (lambda f: f)

# ── Add paths for real packages when available ───────────────────────
_ATOMOS_PKG = _ROOT.parent / 'atomos_pkg'
if _ATOMOS_PKG.exists():
    if str(_ATOMOS_PKG) not in sys.path:
        sys.path.insert(0, str(_ATOMOS_PKG))

sys.path.insert(0, str(_ROOT / 'kubernetes'))

# ── Suppress deprecation warnings ────────────────────────────────────
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning, module='atomos.*')
