# CI_CD_SETUP.md — Home Cluster IaC

## Описание
Документ описывает полную настройку CI/CD для репозитория `home-cluster-iac`: PAT с `workflow` scope, GitHub Actions workflows, self-hosted runner, и скрипт автоматической настройки.

---

## 1. Создание Fine-grained PAT

### Пошаговая инструкция

1. Перейти в **Settings → Developer settings → Fine-grained tokens**
2. Нажать **Generate new token**
3. Заполнить:
   - **Token name**: `home-cluster-iac CI`
   - **Expiration**: 90 дней (или 1 год)
   - **Resource owner**: `mahaasur13-sys`
   - **Repository access**: Only select repositories → `mahaasur13-sys/home-cluster-iac`
4. **Repository permissions**:
   - `Contents`: **Read and write**
   - `Workflows`: **Read and write**
   - `Metadata`: **Read-only** (по умолчанию)
5. Нажать **Generate token** и **скопировать токен**

> ⚠️ Сохраните токен — он отображается только один раз.

---

## 2. Настройка remote и push с PAT

```bash
# 1. Установить токен в gh
gh auth logout 2>/dev/null || true
echo "ВСТАВЬТЕ_ТОКЕН_СЮДА" | gh auth login --hostname github.com --with-token

# ИЛИ вручную:
gh auth login --hostname github.com -p https

# 2. Переключить remote на HTTPS с токеном
cd /home/workspace/home-cluster-iac

git remote set-url origin https://mahaasur13-sys:ТОКЕН@github.com/mahaasur13-sys/home-cluster-iac.git

# 3. Проверить
git remote -v

# 4. Создать CI-ветку
git checkout -b ci-setup

# 5. Добавить workflow и запушить
mkdir -p .github/workflows
```

### Если используете SSH (рекомендуется для local runner)

```bash
# PAT всё равно нужен для workflow-файлов
# SSH не работает для OAuth — только HTTPS с токеном в URL
git remote set-url origin https://mahaasur13-sys:ТОКЕН@github.com/mahaasur13-sys/home-cluster-iac.git
```

---

## 3. `.github/workflows/infra-ci.yml` (только проверки, без deploy)

```yaml
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
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0

      - name: Terraform Init
        run: cd terraform && terraform init -upgrade

      - name: Terraform Validate
        run: cd terraform && terraform validate

      - name: Terraform Format Check
        run: cd terraform && terraform fmt -check -recursive

  ansible-lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install ansible-lint
        run: pip install ansible-lint

      - name: Run ansible-lint
        run: ansible-lint ansible/playbook.yml

  shellcheck-scripts:
    name: ShellCheck (scripts)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run ShellCheck
        run: |
          find scripts/ -name "*.sh" -exec shellcheck {} +

  k8s-manifests:
    name: K8s Manifests (kubeval)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: kubeval
        run: |
          docker run --rm -t -v "$PWD/k8s:/data" ghcr.io/wbittman/kubeval:latest --strict
        continue-on-error: true
```

---

## 4. `.github/workflows/deploy.yml` (self-hosted runner, ручной)

```yaml
name: Deploy Cluster

on:
  workflow_dispatch:
    inputs:
      target:
        description: 'Target (day1|day2|day3|day4|day5|day6|day7|apply)'
        required: true
        default: 'day7'
  push:
    tags:
      - 'deploy-*'

jobs:
  deploy:
    name: Deploy to Home Cluster
    runs-on: self-hosted
    steps:
      - name: Checkout latest
        run: |
          cd /opt/home-cluster-iac
          git pull origin main

      - name: Run target
        env:
          TARGET: ${{ inputs.target || 'day7' }}
        run: |
          cd /opt/home-cluster-iac
          make $TARGET

      - name: Notify
        if: always()
        run: |
          echo "Deploy completed: ${{ job.status }}"
          # Telegram notification (optional)
          curl -s -X POST "https://api.telegram.org/bot${{ secrets.TG_BOT_TOKEN }}/sendMessage" \
            -d "chat_id=${{ secrets.TG_CHAT_ID }}" \
            -d "text=Deploy $TARGET: ${{ job.status }}" || true
```

---

## 5. Регистрация Self-Hosted Runner

### На управляющем узле (RTX 3060)

1. Перейти: **GitHub repo → Settings → Actions → Runners → New self-hosted runner**
2. Выбрать: **Linux** (x64)
3. Скопировать команды установки:

```bash
# Скачать
mkdir -p actions-runner && cd actions-runner
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.316.0/actions-runner-linux-x64-2.316.0.tar.gz
tar xzf actions-runner.tar.gz

# Настроить (заменить TOKEN и URL)
./config.sh --url https://github.com/mahaasur13-sys/home-cluster-iac --token ВАШ_ТОКЕН

# Установить как службу
./svc.sh install
./svc.sh start

# Или вручную (если не root):
./run.sh &
```

4. Убедиться, что runner появился в **Settings → Actions → Runners** со статусом **Idle**

### Дополнительные зависимости на runner

```bash
# Для Terraform jobs
sudo apt install -y terraform

# Для Ansible jobs
pip install ansible ansible-lint

# Для shellcheck
sudo apt install -y shellcheck

# Для K8s jobs
# (опционально) kubectl, kubeval
```

---

## 6. `scripts/setup_ci.sh` — автоматическая настройка

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="mahaasur13-sys/home-cluster-iac"
WORKFLOW_DIR=".github/workflows"
TOKEN_FILE="/tmp/gh_token.txt"

echo "=== Home Cluster IaC CI Setup ==="

# 1. Проверка инструментов
command -v gh >/dev/null 2>&1 || { echo "gh not found. Install: https://cli.github.com"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq not found. Run: sudo apt install -y jq"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "git not found."; exit 1; }

# 2. PAT через gh (интерактивно или переменная)
if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Введите Fine-grained PAT (с правами workflow):"
  read -s -r GH_TOKEN
fi

if [[ -z "$GH_TOKEN" ]]; then
  echo "ERROR: TOKEN is empty"
  exit 1
fi

# 3. Настройка remote
cd "$(dirname "$0")/.."
gh auth login --hostname github.com --with-token <<< "$GH_TOKEN" || true
git remote set-url origin "https://mahaasur13-sys:${GH_TOKEN}@github.com/${REPO}.git"
echo "Remote updated: $(git remote get-url origin)"

# 4. Создание CI-ветки
git checkout -b ci-setup 2>/dev/null || git checkout ci-setup
mkdir -p "$WORKFLOW_DIR"

# 5. Запись infra-ci.yml
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
YAMLEOF

echo "Created $WORKFLOW_DIR/infra-ci.yml"

# 6. Commit и push
git add "$WORKFLOW_DIR/"
git commit -m "feat: add GitHub Actions CI (terraform, ansible, shellcheck)"
git push -u origin ci-setup

# 7. Создание PR
gh pr create \
  --title "feat: add CI/CD pipeline" \
  --body "## Что добавлено\n\n- Terraform validate + fmt check\n- Ansible lint\n- ShellCheck for all scripts\n- Self-hosted runner deploy workflow (manual)\n\n## Следующий шаг\n\n1. Слить PR в main\n2. Настроить self-hosted runner на управляющем узле\n3. Добавить secrets: TG_BOT_TOKEN, TG_CHAT_ID (для уведомлений)" \
  --base main

echo ""
echo "=== DONE ==="
echo "PR created. Merge it, then register self-hosted runner."
```

```bash
chmod +x scripts/setup_ci.sh
```

---

## 7. Чек-лист верификации

После настройки выполните:

```bash
# 1. Проверка Actions tab
# Перейти: https://github.com/mahaasur13-sys/home-cluster-iac/actions
# Должен появиться "Infra CI" workflow

# 2. Terraform validate локально
cd terraform && terraform init -upgrade && terraform validate && terraform fmt -check -recursive && echo "✓ terraform OK"

# 3. Ansible lint локально
pip install ansible-lint 2>/dev/null
ansible-lint ansible/playbook.yml && echo "✓ ansible OK"

# 4. Shellcheck локально
sudo apt install -y shellcheck
find scripts/ -name "*.sh" -exec shellcheck {} + && echo "✓ shellcheck OK"

# 5. Push trigger
git commit --allow-empty -m "trigger CI" && git push
# Дождаться зелёной галочки в Actions

# 6. Self-hosted runner (после merge)
# Settings → Actions → Runners → New self-hosted runner
# Статус должен быть "Idle"
```

---

## Дополнительно: Secrets для уведомлений

| Secret | Где взять |
|--------|-----------|
| `TG_BOT_TOKEN` | @BotFather в Telegram |
| `TG_CHAT_ID` | @userinfobot в Telegram |

Добавить: **Settings → Secrets and variables → Actions → New repository secret**

---

## Краткая шпаргалка

```bash
# Быстрый старт (после PAT):
cd /home/workspace/home-cluster-iac
git checkout -b ci-setup
mkdir -p .github/workflows
# скопировать infra-ci.yml вручную
git add .github/workflows/infra-ci.yml
git commit -m "feat: add CI"
git push -u origin ci-setup
# создать PR через web или gh
gh pr create --title "feat: add CI" --body "..."
```
