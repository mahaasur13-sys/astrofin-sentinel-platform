#!/usr/bin/env python3
"""
scripts/translate_comments.py
Безопасный перевод русских комментариев во всех .py-файлах проекта на английский.
Использует deep-translator (GoogleTranslate) – требуется интернет.
Строковые литералы и docstring не изменяются.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Tuple

try:
    from deep_translator import GoogleTranslator
except ImportError:
    sys.exit("Установите deep-translator: pip install deep-translator")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "dist", "build"}
CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
COMMENT_LINE_PATTERN = re.compile(r"^(\s*#)\s*(.*)$")  # строка, начинающаяся с # (возможно с отступом)


def extract_comment_text(line: str) -> Tuple[str, str, str] | None:
    """Если строка является однострочным комментарием с кириллицей,
    возвращает (отступ, '# ', текст комментария)."""
    match = COMMENT_LINE_PATTERN.match(line)
    if not match:
        return None
    prefix, text = match.group(1), match.group(2)
    if not CYRILLIC_PATTERN.search(text):
        return None
    return match.group(1), prefix + " ", text  # префикс с '# '


def translate_comment_text(text: str) -> str:
    """Переводит текст комментария на английский."""
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠ Ошибка перевода: {e}, оставляем оригинал")
        return text


def process_file(filepath: Path) -> bool:
    """Обрабатывает один .py файл, заменяет русские комментарии на английские.
    Возвращает True, если были изменения."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ Ошибка чтения {filepath}: {e}")
        return False

    changed = False
    new_lines = []
    for line in lines:
        if (res := extract_comment_text(line)) is not None:
            indent, hash_space, orig_text = res
            translated = translate_comment_text(orig_text)
            if translated != orig_text:
                new_line = f"{indent}{hash_space}{translated}\n"
                new_lines.append(new_line)
                changed = True
                print(f"  ✏ {filepath.name}: {orig_text.strip()[:60]}... → {translated.strip()[:60]}...")
                continue
        new_lines.append(line)

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


def main():
    py_files = [p for p in PROJECT_ROOT.rglob("*.py") if not any(part in EXCLUDE_DIRS for part in p.parts)]
    print(f"Найдено {len(py_files)} .py файлов")
    translated_files = 0
    for fp in sorted(py_files):
        if process_file(fp):
            translated_files += 1
    print(f"✅ Переведено файлов: {translated_files}")


if __name__ == "__main__":
    main()
