"""meta_rl/versions_storage.py -- ATOM-META-RL-012: Versioned Elite Storage + A/B Testing API"""
from __future__ import annotations

import json as _json
from pathlib import Path as _Path


def _data_dir():
    root = _Path(__file__).parent.parent
    d = root / "data" / "meta_rl"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _vdir():
    d = _data_dir() / "versions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _vpath(tag):
    return _vdir() / f"version_{tag}.json"


def _vindex_path():
    return _vdir() / "versions_index.json"


def _load_index():
    try:
        return _json.loads(_vindex_path().read_text())
    except Exception:
        return {"versions": [], "by_tag": {}}


def _save_index(idx):
    _vindex_path().write_text(_json.dumps(idx, indent=2))


class VersionedEliteStorage:
    def save_elite_version(self, elites, tag, session_id=""):
        idx = _load_index()
        records = []
        for e in elites or []:
            ev = getattr(e, "evaluation", None)
            chrom = getattr(getattr(e, "strategy", None), "chromosome", {}) if hasattr(e, "strategy") else {}
            records.append(
                {
                    "id": getattr(e, "id", ""),
                    "generation": getattr(e, "generation", 0),
                    "chromosome": chrom,
                    "reward": getattr(e, "reward", 0.0),
                    "risk_adjusted_pnl": getattr(ev, "risk_adjusted_pnl", 0.0) if ev else 0.0,
                    "session_id": session_id,
                }
            )
        vpath = _vpath(str(tag))
        vpath.write_text(_json.dumps(records, indent=2))
        if tag not in idx.get("versions", []):
            idx["versions"] = idx.get("versions", [])
            idx["versions"].append(str(tag))
        idx["by_tag"] = idx.get("by_tag", {})
        idx["by_tag"][str(tag)] = dict(tag=str(tag), session_id=session_id, n=len(records))
        _save_index(idx)
        print(f"[META-RL-VERSION] Saved {tag}: {len(records)} elites")
        return True

    def load_elite_version(self, tag):
        vpath = _vpath(str(tag))
        if not vpath.exists():
            print(f"[META-RL-VERSION] Version not found: {tag}")
            return []
        try:
            return _json.loads(vpath.read_text()) or []
        except Exception as e:
            print(f"[META-RL-VERSION] Load error {tag}: {e}")
            return []

    def list_versions(self):
        idx = _load_index()
        tags = idx.get("versions", [])
        print(f"[META-RL-VERSION] Versions: {tags}")
        return tags

    def compare_versions(self, tag_a, tag_b):
        recs_a = self.load_elite_version(tag_a)
        recs_b = self.load_elite_version(tag_b)
        if not recs_a or not recs_b:
            return dict(error="version not found", a=tag_a, b=tag_b)

        def stats(recs, tag):
            pnls = [r.get("risk_adjusted_pnl", r.get("reward", 0.0)) for r in recs]
            return dict(
                tag=tag,
                n=len(recs),
                mean_pnl=sum(pnls) / max(len(pnls), 1),
                max_pnl=max(pnls) if pnls else 0,
            )

        return dict(version_a=stats(recs_a, tag_a), version_b=stats(recs_b, tag_b))


# Singleton
_versioned_storage = None


def get_versioned_storage():
    global _versioned_storage
    if _versioned_storage is None:
        _versioned_storage = VersionedEliteStorage()
    return _versioned_storage
