# ADR-0001: Submodule → Subtree Migration

**Status:** ✅ Accepted (2026-07-08)  
**Issue:** #100 (plan), #102 (dry-run)  
**Author:** Felix (with Zo Computer assistance)  
**Sprint:** Sprint 1, Phase 4

## Context

`astrofin-sentinel-platform` originally declared **6 submodules** in `.gitmodules`:

| Path | URL | Status |
|------|-----|--------|
| `AsurDev` | `git@github.com:mahaasur13-sys/AsurDev.git` | ✅ Real (1 subdir) |
| `home-cluster-iac` | `git@github.com:mahaasur13-sys/home-cluster-iac.git` | ❌ Ghost (empty, not in tree) |
| `roma-execution-bridge` | `git@github.com:mahaasur13-sys/roma-execution-bridge.git` | ❌ Ghost (empty, not in tree) |
| `astrofin-sentinel-v5` | `git@github.com:mahaasur13-sys/astrofin-sentinel-v5.git` | 🔶 Embedded in master (real files in repo, no submodule entry in tree) |
| `atom-federation-os` | `git@github.com:mahaasur13-sys/atom-federation-os.git` | 🔶 Embedded in master |
| `integrations/gitagent` | `git@github.com:mahaasur13-sys/integrations-gitagent.git` | 🔶 Embedded in master |

### Pain Points
- Submodules pin to a specific commit; updates require explicit `git submodule update --remote`.
- Ghost entries (home-cluster-iac, roma-execution-bridge) confuse newcomers: `.gitmodules` references paths that don't exist in the working tree.
- New contributors forget to run `git submodule update --init --recursive` and see broken imports.
- CI runs `git submodule status` and reports `-` (uninitialized) for ghost entries, masking the real state.

## Decision

**Migrate all submodule references to git subtrees** for the canonical sources we own, and **remove ghost entries** entirely from `.gitmodules`.

### Scope of this PR (#142, closes #100 + #102)

1. **AsurDev** — real submodule at `AsurDev/` is now a subtree with the full history from `mahaasur13-sys/AsurDev@master`.
2. **Embedded code** (`astrofin-sentinel-v5`, `atom-federation-os`, `integrations/gitagent`) — these are not submodules in the working tree; they live as plain directories. The `.gitmodules` references to them are **stale and must be deleted**.
3. **Ghost entries** (`home-cluster-iac`, `roma-execution-bridge`) — **removed** entirely; if needed later, add as proper subtree with explicit `git subtree add`.

### Migration method
```bash
# For AsurDev (the only real submodule in the working tree):
git rm --cached AsurDev
git subtree add --prefix=AsurDev \
  https://github.com/mahaasur13-sys/AsurDev.git master \
  --squash
```

For the others (no working-tree presence), we simply **edit `.gitmodules` to remove them**, then delete the file if empty.

## Consequences

### Positive
- Single `git clone` — no `submodule update --init --recursive` step.
- New contributors see a complete, working tree.
- CI no longer reports uninitialized submodules.
- Ghost references eliminated.

### Negative
- `git subtree pull --prefix=AsurDev` is the new update flow (more verbose than `submodule update`).
- History of `AsurDev` is **squashed** into a single commit at the merge boundary; pre-existing commit history is preserved inside the subtree object, but linear log is condensed.
- Anyone relying on the exact submodule SHA pins must update their tooling.

## Rollback Plan
If subtree migration causes issues, the previous `.gitmodules` is preserved at `.gitmodules.bak-pre-subtree-2026-07-08`. To rollback:
```bash
git checkout master
git checkout .gitmodules.bak-pre-subtree-2026-07-08 -- .gitmodules
git submodule sync && git submodule update --init --recursive
```

## References
- Issue #100: "P0-03: Submodule→subtree migration plan"
- Issue #102: "P0-03.b: Dry-run submodule migration"
- KNOWN_ISSUES.md KI-019 (Phantom Submodule)
- KNOWN_ISSUES.md KI-021 (Docker security waiver — separate concern)
