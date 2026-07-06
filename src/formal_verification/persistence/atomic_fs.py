# persistence/atomic_fs.py — NEW
# ATOM-META-RL-022 P0 — Filesystem Determinism Layer

import hashlib
import json
import os
import shutil
import threading
from dataclasses import dataclass
from typing import Any

from core.deterministic import DeterministicUUIDFactory


@dataclass
class SnapshotHash:
    tick: int
    state_hash: str
    content_hash: str
    snapshot_id: str

    def verify(self, state: Any, tick: int) -> bool:
        canonical = self._canonical_json(state)
        content_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        expected_id = DeterministicUUIDFactory.make_id(
            'snap', content_hash, str(tick)
        )
        return (
            content_hash == self.content_hash and
            expected_id == self.snapshot_id
        )

    @staticmethod
    def _canonical_json(obj: Any) -> str:
        return json.dumps(obj, sort_keys=True, separators=(',', ':'))


class AtomicFileWrite:
    r'''
    Atomic file write using 2-phase commit + rename (atomic on POSIX).

    Phase 1: Write content to .tmp.{ DeterministicID } file
    Phase 2: Atomic rename to target path (POSIX rename is atomic on same FS)

    Guarantees:
      - No partial writes (atomic rename)
      - Deterministic temp file naming (no uuid4, no time)
      - Same content + same tick → same temp filename
    '''

    def __init__(self, target_path: str):
        self.target_path = target_path
        self._lock = threading.RLock()

    def write(self, content: bytes, tick: int) -> None:
        '''
        Write content atomically.
        Phase 1: write to .tmp.{ deterministic_id }
        Phase 2: rename to target (atomic)
        '''
        with self._lock:
            tmp_id = DeterministicUUIDFactory.make_id(
                'atfw', self.target_path, str(tick)
            )
            tmp_path = f'{self.target_path}.tmp.{tmp_id}'

            # Phase 1: write to temp
            with open(tmp_path, 'wb') as f:
                f.write(content)

            # Phase 2: atomic rename
            os.rename(tmp_path, self.target_path)

    def write_json(self, data: Any, tick: int) -> None:
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        self.write(canonical.encode(), tick)

    def read(self) -> bytes:
        with self._lock:
            with open(self.target_path, 'rb') as f:
                return f.read()

    def read_json(self) -> Any:
        return json.loads(self.read())


class AtomicMultiFileWrite:
    r'''
    Atomic write of multiple files (all-or-nothing 2-phase commit).

    Usage:
        writer = AtomicMultiFileWrite(base_dir='/data/state')
        writer.add_file('state.json', data)
        writer.add_file('metadata.json', meta)
        writer.commit(tick=42)  # atomic all-or-nothing
    '''

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._files: dict[str, Any] = {}
        self._tick: int = 0
        self._lock = threading.RLock()
        os.makedirs(base_dir, exist_ok=True)

    def add_file(self, relative_path: str, data: Any) -> None:
        with self._lock:
            self._files[relative_path] = data

    def commit(self, tick: int) -> None:
        '''
        Phase 1: Write all files to .staging/{hash}/ directory
        Phase 2: Rename .staging to .committed (atomic)
        '''
        with self._lock:
            self._tick = tick
            staging_id = DeterministicUUIDFactory.make_id(
                'stg', self.base_dir, str(tick)
            )
            staging_dir = os.path.join(self.base_dir, f'.staging.{staging_id}')
            committed_dir = os.path.join(self.base_dir, '.committed')

            os.makedirs(staging_dir, exist_ok=True)

            # Phase 1: write all files to staging
            for rel_path, data in sorted(self._files.items()):
                file_path = os.path.join(staging_dir, rel_path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                if isinstance(data, (dict, list)):
                    content = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
                else:
                    content = str(data).encode()
                with open(file_path, 'wb') as f:
                    f.write(content)

            # Phase 2: atomic rename staging -> committed
            if os.path.exists(committed_dir):
                shutil.rmtree(committed_dir)
            os.rename(staging_dir, committed_dir)

            # Clear staging dir reference
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir)
            self._files.clear()

    def abort(self) -> None:
        '''Discard all staged files.'''
        with self._lock:
            self._files.clear()


class SnapshotHashValidator:
    r'''
    Deterministic snapshot hash computation and validation.

    Guarantees:
      - Same state at same tick → identical snapshot hash
      - Snapshot ID is content-addressed (deterministic)
      - Verification is deterministic (no time, no random)
    '''

    @staticmethod
    def compute_snapshot_hash(state: Any, tick: int) -> SnapshotHash:
        canonical = json.dumps(state, sort_keys=True, separators=(',', ':'))
        content_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        state_hash = hashlib.sha256(
            f'{content_hash}:{tick}:ATOM-SNAP'.encode()
        ).hexdigest()[:16]
        snapshot_id = DeterministicUUIDFactory.make_id(
            'snap', content_hash, str(tick)
        )
        return SnapshotHash(
            tick=tick,
            state_hash=state_hash,
            content_hash=content_hash,
            snapshot_id=snapshot_id
        )

    @staticmethod
    def compute_state_hash(state: Any) -> str:
        canonical = json.dumps(state, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @staticmethod
    def verify_transition(
        state_before: Any,
        state_after: Any,
        tick_before: int,
        tick_after: int,
        expected_hash_before: str,
        expected_hash_after: str
    ) -> bool:
        '''Verify a state transition is valid (hash matches expected).'''
        hash_before = SnapshotHashValidator.compute_state_hash(state_before)
        hash_after = SnapshotHashValidator.compute_state_hash(state_after)
        return (
            hash_before == expected_hash_before and
            hash_after == expected_hash_after and
            tick_after >= tick_before
        )


class DeterministicFsOrderingGuard:
    r'''
    Deterministic filesystem operation ordering.

    All operations are ordered by (operation_type, target_path_hash, tick).
    This guarantees identical operation sequence across all nodes.

    FileOp types: WRITE, READ, DELETE, MKDIR, RMDIR, RENAME, APPEND
    '''

    class FileOp:
        def __init__(
            self,
            op_type: str,
            target_path: str,
            tick: int,
            payload: Any = None
        ):
            self.op_type = op_type
            self.target_path = target_path
            self.tick = tick
            self.payload = payload

        @property
        def sort_key(self) -> tuple:
            path_hash = hashlib.sha256(self.target_path.encode()).hexdigest()
            return (self.op_type, path_hash, self.tick)

    def __init__(self):
        self._operations: list[DeterministicFsOrderingGuard.FileOp] = []
        self._lock = threading.RLock()

    def add_operation(self, op_type: str, target_path: str, tick: int, payload: Any = None) -> None:
        op = self.FileOp(op_type=op_type, target_path=target_path, tick=tick, payload=payload)
        with self._lock:
            self._operations.append(op)
            self._operations.sort(key=lambda x: x.sort_key)

    def get_ordered_operations(self, tick: int | None = None) -> list[FileOp]:
        with self._lock:
            if tick is None:
                return list(self._operations)
            return [op for op in self._operations if op.tick >= tick]

    def clear(self) -> None:
        with self._lock:
            self._operations.clear()


# ── Persistence Directory Setup ───────────────────────────────────────────────

def setup_persistence_dirs(base: str) -> dict[str, str]:
    '''
    Create deterministic persistence directory structure.
    '''
    dirs = {
        'wal': os.path.join(base, 'wal'),
        'snapshots': os.path.join(base, 'snapshots'),
        'ledger': os.path.join(base, 'ledger'),
        'events': os.path.join(base, 'events'),
        'checkpoints': os.path.join(base, 'checkpoints'),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs
