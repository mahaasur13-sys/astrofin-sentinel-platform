# conftest.py — SBS isolation layer for atom-federation-os
#
# Problem: tests import modules that transitively import atomos_pkg/atomos/core/execution_loop
# which has `import time, random, uuid` at module level, causing nondeterminism.
#
# Solution:
#   1. Mock atomos modules at the earliest possible moment (before any imports)
#   2. Provide deterministic stub ExecutionLoop
#   3. Set PYTHONHASHSEED=0 for deterministic hash
#   4. Suppress DeprecationWarning from legacy atomos code

import os
import sys
import types
from pathlib import Path

# ── Deterministic env (must be first) ──────────────────────────────────
os.environ.setdefault('PYTHONHASHSEED', '0')
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')

_ROOT = Path(__file__).parent


# ── Mock classes ─────────────────────────────────────────────────────

class _MockExecutionLoop:
    def __init__(self, policy_kernel=None, federation_layer=None):
        self.pk = policy_kernel
        self.federation = federation_layer
        self._trace = []
        self._executed_plans = {}
        self._layer_refs = {'drl': lambda: {}, 'ccl': lambda: {}, 'f2': lambda: {}, 'desc': lambda: {}}

    def execute(self, intent, context=None):
        return self.execute.__wrapped__(self, intent, context) if hasattr(self.execute, '__wrapped__') else self._execute_impl(intent)

    def _execute_impl(self, intent, context=None):
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
        # Mock SBS enforcement: raise InvariantViolation for split-brain state
        drl_state = self._layer_refs['drl']() if callable(self._layer_refs['drl']) else self._layer_refs['drl']
        if drl_state.get('partitions', 0) >= 2:
            from sbs.runtime import InvariantViolation
            raise InvariantViolation("execute_with_sbs", ["SPLIT_BRAIN"], drl_state)
        plan = self._execute_impl(intent)
        return plan, None

    def set_layers(self, drl_state_getter=None, ccl_state_getter=None, f2_state_getter=None, desc_state_getter=None):
        if drl_state_getter is not None:
            self._layer_refs['drl'] = drl_state_getter
        if ccl_state_getter is not None:
            self._layer_refs['ccl'] = ccl_state_getter
        if f2_state_getter is not None:
            self._layer_refs['f2'] = f2_state_getter
        if desc_state_getter is not None:
            self._layer_refs['desc'] = desc_state_getter

    def collect_state(self):
        return {
            'drl': self._layer_refs['drl']() if callable(self._layer_refs['drl']) else self._layer_refs['drl'],
            'ccl': self._layer_refs['ccl']() if callable(self._layer_refs['ccl']) else self._layer_refs['ccl'],
            'f2': self._layer_refs['f2']() if callable(self._layer_refs['f2']) else self._layer_refs['f2'],
            'desc': self._layer_refs['desc']() if callable(self._layer_refs['desc']) else self._layer_refs['desc'],
        }

    @staticmethod
    def sbs_is_available():
        return True

    @staticmethod
    def get_sbs_mode_enum():
        class _MockSBSMode:
            OFF = 0
            AUDIT = 1
            ENFORCED = 2
        return _MockSBSMode()


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
        return {'step_id': step.get('id', '?'), 'status': 'done', 'output': {}}

    async def execute_intent(self, intent, loop_component):
        plan = loop_component.execute(intent)
        return {'plan_id': plan.plan_id, 'steps': [], 'is_safe': plan.is_safe}


# ── Inject stubs into sys.modules BEFORE any test code runs ────────────

def _make_stub(name: str):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)

# atomos.core.execution_loop
_make_stub('atomos')
_make_stub('atomos.core')
_exec_stub = _make_stub('atomos.core.execution_loop')
sys.modules['atomos.core.execution_loop'] = types.ModuleType('atomos.core.execution_loop')
exec_mod = sys.modules['atomos.core.execution_loop']
exec_mod.ExecutionLoop = _MockExecutionLoop
exec_mod.SBSRuntimeEnforcer = type('MockSBSEnforcer', (), {})
exec_mod.ExecutionPlan = type('ExecutionPlan', (), {})
exec_mod.SimulatedStep = type('SimulatedStep', (), {})
exec_mod.RiskProfile = type('RiskProfile', (), {})

# atomos.swarm.swarm_engine
_make_stub('atomos.swarm')
sys.modules['atomos.swarm.swarm_engine'] = types.ModuleType('atomos.swarm.swarm_engine')
swarm_mod = sys.modules['atomos.swarm.swarm_engine']
swarm_mod.register = lambda *a, **k: (lambda f: f)
swarm_mod.SwarmEngine = _MockSwarmEngine

# atomos.runtime.async_runtime
_make_stub('atomos.runtime')
sys.modules['atomos.runtime.async_runtime'] = types.ModuleType('atomos.runtime.async_runtime')
async_mod = sys.modules['atomos.runtime.async_runtime']
async_mod.AsyncExecutionEngine = _MockAsyncExecutionEngine

# atomos.core.service_registry
_make_stub('atomos.core.service_registry')
sys.modules['atomos.core.service_registry'].register = lambda *a, **k: (lambda f: f)


# ── Add paths for real packages when available ───────────────────────
_ATOMOS_PKG = _ROOT.parent / 'atomos_pkg'
if _ATOMOS_PKG.exists():
    if str(_ATOMOS_PKG) not in sys.path:
        sys.path.insert(0, str(_ATOMOS_PKG))

# Local atom_operator
sys.path.insert(0, str(_ROOT / 'kubernetes'))

# ── Suppress deprecation warnings ────────────────────────────────────
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning, module='atomos.*')
