# sbs/tests/conftest.py — SBS test integration boundary
# Ensures pip-installed atomos_pkg is on sys.path BEFORE root-level atomos/ is resolved.
import sys
from pathlib import Path

# Parent of atom-federation-os is /home/workspace/
_ATOMOS_PKG = Path(__file__).resolve().parents[2] / "atomos_pkg"
if _ATOMOS_PKG.exists():
    sys.path.insert(0, str(_ATOMOS_PKG))
