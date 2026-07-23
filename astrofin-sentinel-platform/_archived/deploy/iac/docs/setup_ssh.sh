#!/usr/bin/env bash
# setup_ssh.sh — автоматическая настройка SSH для GitHub
# Usage: ./setup_ssh.sh [--repo /path/to/repo] [--push]

set -euo pipefail

GITHUB_HOST="github.com"
DEFAULT_KEY_FILE="${HOME}/.ssh/id_ed25519"
KEY_FILE=""
KEY_TYPE="ed25519"

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*"; exit 1; }

TARGET_REPO=""
DO_PUSH=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)  TARGET_REPO="$2"; shift 2 ;;
        --push)  DO_PUSH=true;     shift 1 ;;
        *)       echo "Unknown: $1"; shift ;;
    esac
done

find_key() {
    for f in "${HOME}/.ssh/id_ed25519.pub" "${HOME}/.ssh/github_ed25519.pub"; do
        [[ -f "$f" ]] && echo "$f" && return 0
    done
    return 1
}

choose_key() {
    local existing
    existing="$(find_key)" || true
    if [[ -n "$existing" ]]; then
        echo "Found existing key: $existing"
        read -p "Use it? [Y/n]: " -n 1 -r
        echo
        if [[ "$REPLY" =~ ^[Nn]$ ]]; then
            KEY_FILE=""
            return 1
        fi
        KEY_FILE="${existing%.pub}"
        return 0
    fi
    return 1
}

generate_key() {
    local email
    echo "Generating new SSH key..."
    read -p "Email for key: " email
    [[ -z "$email" ]] && error "Email required"
    KEY_FILE="${HOME}/.ssh/github_ed25519"
    ssh-keygen -t ed25519 -C "$email" -f "$KEY_FILE" -N ""
    echo "Key created: ${KEY_FILE}"
}

show_key() {
    local pub="${KEY_FILE}.pub"
    [[ ! -f "$pub" ]] && error "Public key not found: $pub"
    echo ""
    echo "============================================================"
    echo "  PUBLIC KEY (copy to clipboard):"
    echo "============================================================"
    cat "$pub"
    echo "============================================================"
    echo ""
    echo "  1. Go to: https://github.com/settings/keys"
    echo "  2. Click: New SSH Key"
    echo "  3. Paste key above into 'Key' field"
    echo "  4. Click: Add SSH Key"
    echo ""
    read -p "Press ENTER after adding key on GitHub... " -r
}

verify() {
    info "Verifying GitHub connection..."
    local out
    out="$(ssh -T git@github.com 2>&1 || true)"
    if echo "$out" | grep -qi "successfully authenticated"; then
        info "OK: $(echo "$out" | head -1)"
        return 0
    else
        warn "Not verified: $out"
        return 1
    fi
}

update_remote() {
    local repo="${TARGET_REPO:-$(pwd)}"
    [[ ! -d "$repo/.git" ]] && error "Not a git repo: $repo"
    local current_url
    current_url="$(git remote get-url origin 2>/dev/null || true)"
    [[ -z "$current_url" ]] && error "remote 'origin' not found"
    local owner repo_name
    owner="$(echo "$current_url" | sed -E 's|https://github.com/([^/]+)/([^/]+)(\.git)?|\1|')"
    repo_name="$(echo "$current_url" | sed -E 's|https://github.com/([^/]+)/([^/]+)(\.git)?|\2|')"
    local new_url="git@github.com:${owner}/${repo_name}.git"
    git -C "$repo" remote set-url origin "$new_url"
    info "Remote updated: $new_url"
    if [[ "$DO_PUSH" == "true" ]]; then
        git -C "$repo" push origin HEAD && info "Push OK"
    fi
}

main() {
    echo "=== SSH Setup for GitHub ==="
    if choose_key; then
        info "Using existing key"
    else
        generate_key
    fi
    show_key
    verify || { warn "Retry verify"; verify || warn "Connection failed"; }
    if [[ -n "$TARGET_REPO" ]] || [[ -d "$(pwd)/.git" ]]; then
        update_remote
    fi
    echo ""
    info "Done! SSH configured."
    echo "  Key: ${KEY_FILE}"
    echo "  Remote: git@github.com:..."
}

main
