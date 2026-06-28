#!/usr/bin/env python3
"""
check_installed.sh — сверка dpkg vs pop-os-setup stages
usage:
  python3 check_installed.py                    # live system
  python3 check_installed.py /path/to/dpkg.txt  # from file
"""
import sys
import subprocess
import re
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────
RED   = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW= '\033[1;33m'
CYAN  = '\033[0;36m'
BOLD  = '\033[1m'
RESET = '\033[0m'

SCRIPT_DIR = Path(__file__).parent.resolve()
STAGES_DIR = SCRIPT_DIR / "stages"

# ── collect packages from stages ────────────────────────────────────────────
def get_stages_packages():
    packages = set()
    for stage in sorted(STAGES_DIR.glob("stage*.sh")):
        text = stage.read_text()
        # Split by lines that start with apt (possibly indented)
        for line in text.splitlines():
            line = line.strip()
            if re.match(r'^\s*(sudo\s+)?apt install -y', line) and not line.startswith("#"):
                # Strip everything after 2>& | || 2>/dev/null tail |
                clean = re.sub(r'\s+(2>&\d?| \|{1,2}|\d>/dev/null| true)', '', line)
                m = re.search(r'apt install -y\s+(.+)', clean)
                if m:
                    FAKE = {"||", "|", "true", "false", "&&", "2>&1", "2>&2"}
                    for token in m.group(1).split():
                        t = token.strip()
                        if t and t not in FAKE and not t.startswith("-") and t not in ("\\", "|"):
                            packages.add(t)
    return packages

# ── read installed packages ──────────────────────────────────────────────────
def get_installed_packages(dpkg_path=None):
    if dpkg_path:
        with open(dpkg_path) as f:
            lines = f.readlines()
    else:
        result = subprocess.run(
            ["dpkg", "-l"],
            capture_output=True, text=True
        )
        lines = result.stdout.splitlines()

    installed = set()
    for line in lines:
        if line.startswith("ii "):
            parts = line.split(None, 4)
            if len(parts) >= 2:
                # Parse: "pkg-name:arch" -> pkg-name
                pkg = parts[1].rsplit("/", 1)[0].rsplit(":", 1)[0]
                installed.add(pkg)
    return installed

# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dpkg_path = sys.argv[1] if len(sys.argv) > 1 else None

    stages_pkgs = get_stages_packages()
    installed   = get_installed_packages(dpkg_path)

    matched = sorted(stages_pkgs & installed)
    missing = sorted(stages_pkgs - installed)

    print(f"{CYAN}{BOLD}▶ Сканирую stages...{RESET}")
    print(f"  Найдено пакетов в stages: {BOLD}{len(stages_pkgs)}{RESET}")
    print(f"  Прочитано из: {BOLD}{'файла: ' + dpkg_path if dpkg_path else 'dpkg -l (live)'}{RESET}")
    print()
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  {CYAN}ПОКРЫТИЕ:{RESET}  {GREEN}{len(matched)}{RESET} установлено  ·  {RED}{len(missing)}{RESET} отсутствует")  # noqa: E501
    print(f"{BOLD}{'═'*60}{RESET}")
    print()

    if missing:
        print(f"{YELLOW}{BOLD}⚠ отсутствуют ({len(missing)}):{RESET}")
        # Group by stage
        stage_map = {}
        for pkg in missing:
            for stage in sorted(STAGES_DIR.glob("stage*.sh")):
                if re.search(rf'\b{re.escape(pkg)}\b', stage.read_text()):
                    sname = stage.stem  # stage4_dev_tools
                    break
            else:
                sname = "unknown"
            stage_map.setdefault(sname, []).append(pkg)

        for sname, pkgs in sorted(stage_map.items()):
            print(f"  {CYAN}{sname}{RESET}:")
            for p in pkgs:
                print(f"    - {p}")
        print()
        install_cmd = "sudo apt install -y " + " ".join(missing)
        print(f"  {CYAN}→ Установить все:{RESET}")
        print(f"     {install_cmd}")
    else:
        print(f"{GREEN}✓ Все пакеты из stages уже установлены{RESET}")

    print()
    print(f"{BOLD}─── Покрытие по stages ───{RESET}")
    for stage in sorted(STAGES_DIR.glob("stage*.sh")):
        sname = stage.stem
        text = stage.read_text()

        # Extract packages for this stage
        stage_pkgs = set()
        for line in text.splitlines():
            line = line.strip()
            if re.match(r'^\s*(sudo\s+)?apt install -y', line) and not line.startswith("#"):
                clean = re.sub(r'\s+(2>&\d?| \|{1,2}|\d>/dev/null| true)', '', line)
                m = re.search(r'apt install -y\s+(.+)', clean)
                if m:
                    FAKE = {"||", "|", "true", "false", "&&", "2>&1", "2>&2"}
                    for token in m.group(1).split():
                        t = token.strip()
                        if t and t not in FAKE and not t.startswith("-") and t not in ("\\", "|"):
                            stage_pkgs.add(t)

        if not stage_pkgs:
            continue

        matched_count = len(stage_pkgs & installed)
        total = len(stage_pkgs)
        pct = int(matched_count * 100 / total)

        if pct == 100:   color, sym = GREEN, "✓"  # noqa: E701
        elif pct > 0:    color, sym = YELLOW, "◐"  # noqa: E701
        else:            color, sym = RED, "✖"  # noqa: E701

        print(f"  {color}{sym}{RESET} {sname:<30} {pct:3d}%  ({matched_count}/{total})")
