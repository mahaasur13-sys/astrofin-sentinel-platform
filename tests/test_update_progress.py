from __future__ import annotations

import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "tools" / "update_progress.sh"

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@test.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@test.com",
}


@pytest.mark.unit
def test_update_progress_script_exists():
    assert SCRIPT.exists(), "tools/update_progress.sh not found"


@pytest.mark.unit
def test_generates_progress_file(tmp_path):
    # NOTE: this test MUST run against an isolated copy of the script in a
    # throwaway directory. A previous version did `os.chdir(ROOT)`, `git init`
    # and `rm -rf .git` in the REAL repository root, which destroyed the
    # working repo's .git during a test run. The script derives its own root
    # from `dirname $0/..`, so copying it into `tmp_path/tools/` makes it
    # operate entirely inside tmp_path.
    env = {**os.environ, **_GIT_ENV}

    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    shutil.copy(SCRIPT, tools_dir / "update_progress.sh")

    subprocess.run(["git", "init"], cwd=tmp_path, check=False)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=False)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=False)

    (tmp_path / "test_temp.txt").write_text("test")
    subprocess.run(["git", "add", "test_temp.txt"], cwd=tmp_path, check=False)
    subprocess.run(
        ["git", "commit", "-m", "Test commit for progress"],
        cwd=tmp_path,
        check=False,
        env=env,
    )

    subprocess.run(
        ["bash", str(tools_dir / "update_progress.sh")],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
    )

    progress_file = tmp_path / "progress.md"
    assert progress_file.exists(), "progress.md was not created"
    content = progress_file.read_text()
    today = date.today().isoformat()
    assert today in content, "progress.md does not contain today's date"
    assert "Test commit for progress" in content, "progress.md does not contain commit message"
    # tmp_path is auto-removed by pytest — no manual cleanup, no real .git touched.
