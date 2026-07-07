#!/usr/bin/env bash
set -euo pipefail

REPO="mahaasur13-sys/home-cluster-iac"
WORKFLOW_DIR=".github/workflows"

echo "=== Home Cluster IaC CI Setup ==="

command -v gh >/dev/null 2>&1 || { echo "gh not found. Install: https://cli.github.com"; exit 1; }

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Введите Fine-grained PAT (с правами workflow):"
  read -s -r GH_TOKEN
fi

[[ -z "$GH_TOKEN" ]] && { echo "ERROR: TOKEN empty"; exit 1; }

cd "$(dirname "$0")/.."
git checkout -b ci-setup 2>/dev/null || git checkout ci-setup
mkdir -p "$WORKFLOW_DIR"

cat > "$WORKFLOW_DIR/infra-ci.yml" << 'YAMLEOF'
name: Infra CI

on:
  push:
    branches: [main, ci-setup]
    paths:
      - 'terraform/**'
      - 'ansible/**'
      - 'scripts/**'
      - 'k8s/**'
      - '.github/workflows/infra-ci.yml'
  pull_request:
    paths:
      - 'terraform/**'
      - 'ansible/**'
      - 'scripts/**'
      - 'k8s/**'

jobs:
  terraform-validate:
    name: Terraform Validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0
      - run: cd terraform && terraform init -upgrade
      - run: cd terraform && terraform validate
      - run: cd terraform && terraform fmt -check -recursive

  ansible-lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ansible-lint
      - run: ansible-lint ansible/playbook.yml

  shellcheck:
    name: ShellCheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: find scripts/ -name "*.sh" -exec shellcheck {} +
