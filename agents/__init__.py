"""Agents package — all imports are lazy to avoid heavy deps (faiss, transformers)."""
# Lazy accessors only — no import-time side effects
# Use agents._impl.<agent> directly in code that needs specific agents
__all__: list[str] = []
