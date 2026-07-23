#!/bin/bash
# Validate all configs in the repo

set -euo pipefail

ERRORS=0

echo "🔍 Validating Home Cluster IaC configs..."
echo ""

# Terraform syntax check
if command -v terraform >/dev/null 2>&1; then
  echo "  ✓ Terraform found"
  for dir in terraform/sites/*/; do
    echo "  Checking $(basename $dir)..."
    (cd "$dir" && terraform init -backend=false >/dev/null 2>&1 && \
      terraform validate >/dev/null 2>&1) && \
      echo "    ✓ $dir" || { echo "    ❌ $dir"; ((ERRORS++)); }
  done
else
  echo "  ⚠️  Terraform not found — skipping TF validation"
fi

# Ansible syntax check
if command -v ansible-playbook >/dev/null 2>&1; then
  echo ""
  echo "  ✓ Ansible found"
  ansible-playbook ansible/playbook.yml --syntax-check 2>/dev/null && \
    echo "    ✓ playbook.yml valid" || { echo "    ❌ playbook.yml"; ((ERRORS++)); }
else
  echo "  ⚠️  Ansible not found — skipping Ansible validation"
fi

# ShellCheck Day scripts
if command -v shellcheck >/dev/null 2>&1; then
  echo ""
  echo "  ✓ ShellCheck found"
  for script in scripts/day*.sh; do
    shellcheck "$script" >/dev/null 2>&1 && \
      echo "    ✓ $script" || { echo "    ❌ $script"; ((ERRORS++)); }
  done
else
  echo "  ⚠️  ShellCheck not found — skipping shell validation"
fi

echo ""
if [[ $ERRORS -eq 0 ]]; then
  echo "✅ All validations passed"
  exit 0
else
  echo "❌ $ERRORS validation(s) failed"
  exit 1
fi
