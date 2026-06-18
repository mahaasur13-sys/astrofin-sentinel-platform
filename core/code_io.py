from __future__ import annotations

import ast
import subprocess
import tempfile
from pathlib import Path


def is_valid_python(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"{e.msg} (line {e.lineno})"


def normalize_code(code: str) -> str:
    code = code.replace("\r\n", "\n").strip() + "\n"
    return code


def format_code_black(code: str) -> str:
    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        subprocess.run(
            ["black", tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        formatted = Path(tmp_path).read_text(encoding="utf-8")
        Path(tmp_path).unlink(missing_ok=True)
        return formatted
    except Exception:
        return code


def write_code_file(
    path: str,
    content: str,
    *,
    validate: bool = True,
    auto_format: bool = True,
) -> None:
    assert isinstance(content, str), "content must be str"
    assert len(content.strip()) > 0, "empty code"

    code = normalize_code(content)

    if validate:
        ok, err = is_valid_python(code)
        if not ok:
            raise ValueError(f"Invalid Python code: {err}")

    if auto_format:
        code = format_code_black(code)

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    tmp = p.with_suffix(".tmp")
    tmp.write_text(code, encoding="utf-8")
    tmp.replace(p)


def safe_write_code_file(path: str, content: str) -> bool:
    try:
        write_code_file(path, content)
        return True
    except Exception as e:
        print(f"[CODE WRITE ERROR] {e}")
        return False
