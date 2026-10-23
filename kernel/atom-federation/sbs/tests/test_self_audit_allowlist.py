"""Regression: self-audit must honour its own allowlist, and only that.

``apply_mutation`` in a module listed in ``_ALLOWED_MUTATION_MODULES`` is a
mutation point, not a bypass.  Anything else that defines or calls it is still
a bypass — the allowlist must not have widened the detector.
"""

from pathlib import Path

from core.runtime.self_audit import SelfAudit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _audit(path: Path):
    audit = SelfAudit()
    return audit._audit_file(path, REPO_ROOT)


def _write(tmp_path: Path, name: str, body: str) -> Path:
    target = tmp_path / name
    target.write_text(body, encoding="utf-8")
    return target


def test_v8_2b_apply_mutation_is_a_mutation_point_not_a_bypass():
    target = REPO_ROOT / "orchestration/v8_2b_controlled_autocorrection/mutation_executor.py"

    result = _audit(target)

    assert result["bypasses"] == []
    assert "orchestration.v8_2b_controlled_autocorrection.mutation_executor:apply_mutation" in (
        result["mutation_points"]
    )


def test_repo_audit_finds_no_bypass_paths():
    result = SelfAudit()._do_audit(REPO_ROOT)

    assert result.passed, result.error_message
    assert result.bypass_paths_detected == []


def test_defining_apply_mutation_outside_allowlist_is_still_a_bypass(tmp_path):
    rogue = _write(tmp_path, "rogue_loop.py", "def apply_mutation():\n    return None\n")

    result = _audit(rogue)

    assert len(result["bypasses"]) == 1
    assert result["bypasses"][0].bypass_type == "direct_call"
    assert result["mutation_points"] == {}


def test_calling_apply_mutation_from_outside_allowlist_is_still_a_bypass(tmp_path):
    rogue = _write(
        tmp_path,
        "rogue_loop.py",
        "def tick(executor):\n    executor.apply_mutation({})\n",
    )

    result = _audit(rogue)

    assert len(result["bypasses"]) == 1
    assert result["bypasses"][0].bypass_type == "direct_call"
