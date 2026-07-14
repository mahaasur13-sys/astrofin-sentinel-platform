"""
sbs/version.py — Single Source of Truth для версии пакета.

ВСЕ источники версии (pyproject.toml dynamic, __init__.__version__,
setup.py, documentation) читают отсюда.

При релизе: обновить ТОЛЬКО этот файл.
"""

__version__ = "0.6.0"
__version_info__ = (0, 6, 0)
__version_tuple__ = __version_info__

VERSION = __version__
VERSION_INFO = __version_info__
VERSION_DATE = "2026-04-24"
BUILD = "release"
