# AsurDev (subtree)

Embedded copy of `mahaasur13-sys/AsurDev` (ml_engine submodule) as a plain
directory after ADR-0001 migration from submodule to subtree (closes #100, #102).

This directory is a snapshot of `master@<commit>` at the time of migration.
For ongoing upstream development see
<https://github.com/mahaasur13-sys/AsurDev>.

## Original layout

- `ml_engine/Dockerfile` — empty placeholder retained for path compatibility
  with downstream tooling (e.g. `docker build -f AsurDev/ml_engine/Dockerfile`).

## Future updates

To pull new commits from upstream, re-run:

```bash
git subtree pull --prefix=AsurDev git@github.com:mahaasur13-sys/AsurDev.git master
```
