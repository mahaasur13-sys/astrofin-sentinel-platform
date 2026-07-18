# Best Practices — Reference Implementations

This directory contains exemplar implementations demonstrating patterns
that should be replicated across the AstroFin Sentinel Platform codebase.

## Exemplars

| File | Pattern | Why Exemplar |
|------|---------|-------------|
| `llm_router_exemplar.py` | Lazy init, audit trail, TTL cache | Clean separation of concerns, graceful degradation, JSONL observability |
| `rtk_slice_exemplar.ts` | Redux Toolkit slice + thunk | Typed state, discriminated unions, proper async lifecycle |

## Usage

When creating new modules, use these as templates:

```bash
# New Python service — follow llm_router_pattern:
# 1. Lazy globals via _get_*() factories
# 2. JSONL logging for observability
# 3. TTL cache for expensive operations
# 4. Explicit error messages for config

# New Redux feature — follow rtk_slice pattern:
# 1. Typed state interface
# 2. createSlice with granular reducers
# 3. createAsyncThunk with lifecycle dispatch
# 4. No dispatch in JSX components
```
