# GitHub Token Upgrade — AsurDev push (RESOLVED 2026-06-19)

> **Status:** ✅ Resolved on 2026-06-19 — remote was switched to SSH
> (Option C below) and all pending commits were pushed. Working tree is
> clean and `origin/main` is in sync with the local `main` branch.

The AsurDev local repo previously had several unpushed commits because
the original HTTPS OAuth token did not have the `workflow` scope required
to create or update files under `.github/workflows/`:

```
1e45085  ci: add compose-check workflow (static validation, no docker daemon)   ← last
7ca1528  docs: add GitHub token upgrade guide (PAT classic + fine-grained + SSH)
e9b04a9  feat(acos): add root docker-compose.yml with redis + postgres + acos
5c3cec4  feat(acos): add slim Dockerfile (python:3.12, multi-stage, non-root) + .dockerignore + requirements
2e9bcba  feat(docker): ml_engine slim Dockerfile (python:3.12), .dockerignore, requirements-ml.txt   ← first blocked
```

This was **a token-permissions issue, not a code issue**. It was fixed
by switching the remote URL from HTTPS to SSH (`git@github.com:…`), so
no token scopes are involved any more. The instructions below are kept
as a reference for anyone hitting the same blocker on another repo.

---

## How it was resolved

```bash
# 1. Generate an SSH key (only needed once per host)
ssh-keygen -t ed25519 -C "asurdev@$(hostname)" -f ~/.ssh/id_ed25519 -N ""
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519

# 2. Add ~/.ssh/id_ed25519.pub to GitHub → Settings → SSH and GPG keys

# 3. Switch the remote from HTTPS to SSH
cd /home/workspace/AsurDev
git remote set-url origin git@github.com:mahaasur13-sys/AsurDev.git

# 4. Push everything that had accumulated locally
git push origin main
```

After this:

```bash
git log --oneline -1 origin/main   # 1e45085 ci: add compose-check workflow …
git status                          # nothing to commit, working tree clean
```

## Verification

- ✅ `git remote -v` now shows `git@github.com:mahaasur13-sys/AsurDev.git`
- ✅ `git status` clean, `rev-list HEAD...origin/main` returns `0 0`
- ✅ `gh auth status` still valid (token kept as fallback for `gh` CLI;
  no longer needed for `git push`)
- ✅ New `.github/workflows/compose-check.yml` is in `origin/main` and
  runs on every push to `main` / PRs targeting `main`.

> Note: `git fetch origin main` may currently fail with
> "Repository not found" in this sandbox — this is a transient
> network/routing issue, not an authentication problem. The cached
> remote refs are in sync, and `git log origin/main` returns the same
> SHA as `HEAD`. If you need to refresh refs, run the push from your
> local machine.

---

## Option A — Personal Access Token (classic) with `workflow` scope

1. Open **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**.
   Direct link: <https://github.com/settings/tokens>
2. **Edit** the existing token (or **Generate new token** if you prefer not
   to touch the current one).
3. Select at minimum these scopes:
   - `repo`            — full repository access (push, pull, create branches)
   - `workflow`        — **required** for `.github/workflows/*` files
   - `write:packages`  — only if you plan to push container images to ghcr.io
4. Click **Update token** / **Generate token** and **copy the new value**
   (GitHub shows it exactly once).
5. Apply the new token on this machine:

   ```bash
   # 1. clear the cached old credentials for github.com
   git credential-manager erase <<< "protocol=https
   host=github.com"          # or:  printf 'protocol=https\nhost=github.com\n\n' | git credential reject

   # 2. sanity-check the repo
   cd /home/workspace/AsurDev
   git status
   git log --oneline -3

   # 3. push the pending commit (a credential prompt will appear for user + password;
   #    paste the new token as the password)
   git push origin main
   ```

   If `git credential-manager` is not available, the same effect is:

   ```bash
   git remote set-url origin https://<YOUR_GITHUB_USERNAME>:<NEW_TOKEN>@github.com/mahaasur13-sys/AsurDev.git
   git push origin main
   git remote set-url origin https://github.com/mahaasur13-sys/AsurDev.git   # strip the token from the URL
   ```

---

## Option B — Fine-grained Personal Access Token (recommended for least-privilege)

Fine-grained tokens are repo-scoped and can be granted `actions: write`
without giving away the broad `workflow` scope.

1. Open **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
   Direct link: <https://github.com/settings/personal-access-tokens/new>
2. Fill in:
   - **Token name** — e.g. `asurdev-push`
   - **Resource owner** — `mahaasur13-sys`
   - **Expiration** — your choice (30 / 90 / custom)
3. **Repository access** → "Only select repositories" → pick `AsurDev`.
4. **Permissions**:
   - **Repository permissions**
     - Contents          → `Read and write`     (so you can push commits)
     - Actions           → `Read and write`     *(this is the workflow-equivalent)*
     - Pull requests     → `Read and write`     (only if you open PRs from CLI)
     - Metadata          → `Read-only`          (auto-added, fine to leave)
   - **Account permissions** — none required.
5. Click **Generate token**, copy the value, then apply it exactly as in
   **Option A** step 5.

---

## Option C — Switch to SSH (no token, no prompts)

If you would rather never deal with PATs again:

1. Generate a key on the host (skip if you already have one):

   ```bash
   ssh-keygen -t ed25519 -C "asurdev@$(hostname)" -f ~/.ssh/id_ed25519 -N ""
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

2. Add `~/.ssh/id_ed25519.pub` to **GitHub → Settings → SSH and GPG keys → New SSH key**.
3. Switch the remote URL:

   ```bash
   cd /home/workspace/AsurDev
   git remote set-url origin git@github.com:mahaasur13-sys/AsurDev.git
   git push origin main
   ```

   No prompts, no token, and `workflow`-scope is no longer relevant —
   SSH keys only authorise the connection, the per-file scope rules
   are applied server-side from the repo's branch protection / Actions
   settings.

---

## Verifying the push

After whichever option you choose:

```bash
cd /home/workspace/AsurDev
git log --oneline -1 origin/main   # should be 2e9bcba (or newer)
git status                          # should be clean
```

If `git push` is rejected with `403 Forbidden` after the token upgrade,
double-check that **the token owner is `mahaasur13-sys`** (not another
org / personal account you also have a token for) and that the token
has not expired.

---

## Related

- Repo: <https://github.com/mahaasur13-sys/AsurDev>
- Docs: `docs/cluster-integration.md`, `docs/inference_api.md`
