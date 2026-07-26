# ALERT: MetaRLNightlyFail

## Severity: warning →

## What triggers
Nightly CI workflow `test-meta-rl` fails with exit code != 0. This means the Meta-RL training/checkpoint pipeline is broken.

## Immediate response

1. **Check CI logs**: Go to https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/workflows/nightly.yml, find the latest failed Meta-RL job.

2. **Identify root cause**:
   - `ImportError`: usually means deps changed. Run `uv sync` and re-trigger.
   - `S3 access denied`: check AWS credentials in CI secrets → `astrofin-ml-models` bucket policy.
   - `Checkpoint corrupted`: delete `data/meta_rl/gen_*_checkpoint.json` and trigger fresh run.
   - `OOM killed`: reduce `num_agents` in `meta_rl/evolution.py` to 20.

3. **Manual rerun**:
   ```bash
   gh workflow run nightly.yml --ref master
   ```

4. **If still failing after 2 attempts**: escalate to @felix, post in `#alerts-meta-rl` Slack channel.

## Recovery verification

- [ ] Nightly CI job passed → Slack `#alerts-meta-rl` receives ✅
- [ ] Check `data/meta_rl/sessions/` — new evolution JSONL file present
- [ ] Check Prometheus: `meta_rl_checkpoint_age_seconds < 86400`

## Post-mortem template

After resolution, fill in `docs/postmortems/meta-rl-YYYY-MM-DD.md`:
- Root cause
- Detection time
- Resolution time
- Action items
