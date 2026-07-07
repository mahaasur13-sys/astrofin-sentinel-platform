# SSH Setup для GitHub (Workflow Scope Fix)

## 1. Почему возникает ошибка `workflow scope`

OAuth-токены (включая те, что использует `gh`) **запрещают** создание/изменение файлов в `.github/workflows/` без явно запрошенного scope `workflow`.

**Почему так?** GitHub защищает workflow-файлы от OAuth-приложений, чтобы вредоносные OAuth- apps не могли модифицировать CI/CD без ведома пользователя.

**SSH не имеет этого ограничения** — аутентификация по ключу позволяет работать с любыми файлами репозитория, включая workflow.

---

## 2. Ручная настройка SSH

### 2.1 Генерация SSH-ключа

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**Опции:**
- `-t ed25519` — современный алгоритм (быстрый, безопасный)
- `-C "email"` — комментарий для идентификации ключа
- При запросе **путь файла** — нажми `Enter` для默认值 (`~/.ssh/id_ed25519`) или укажи кастомный (например `~/.ssh/github_ed25519`)
- **Passphrase** — настоятельно рекомендуется (защита ключа), но можно оставить пустым

### 2.2 Добавление публичного ключа на GitHub

**1.** Выведи публичный ключ:

```bash
cat ~/.ssh/id_ed25519.pub
# или, если кастомный путь:
cat ~/.ssh/github_ed25519.pub
```

**2.** Перейди в GitHub:
→ https://github.com/settings/keys

**3.** Нажми **New SSH Key**

**4.** Заполни:
- **Title** — например `Home Cluster Lab` или `Zo Computer`
- **Key type** — `Authentication Key`
- **Key** — вставь содержимое из вывода `cat`

**5.** Нажми **Add SSH Key**

### 2.3 Проверка подключения

```bash
ssh -T git@github.com
```

**Ожидаемый ответ:**
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 2.4 Переключение remote URL на SSH

```bash
# Узнай текущий remote
git remote -v

# Смени URL на SSH
git remote set-url origin git@github.com:username/repo.git
# Пример: git remote set-url origin git@github.com:mahaasur13-sys/home-cluster-iac.git

# Проверь
git remote -v
```

### 2.5 Пуш

```bash
git push origin main
# или текущая ветка:
git push origin $(git branch --show-current)
```

---

## 3. Автоматический скрипт `setup_ssh.sh`

```bash
#!/usr/bin/env bash
# setup_ssh.sh — автоматическая настройка SSH для GitHub
# Usage: ./setup_ssh.sh [--repo /path/to/repo] [--push]

set -euo pipefail

GITHUB_HOST="github.com"
DEFAULT_KEY_FILE="${HOME}/.ssh/id_ed25519"
KEY_FILE=""
KEY_TYPE="ed25519"

# ─── Helpers ───────────────────────────────────────────────────
info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*"; exit 1; }

# ─── Parse args ────────────────────────────────────────────────
TARGET_REPO=""
DO_PUSH=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)  TARGET_REPO="$2"; shift 2 ;;
        --push)  DO_PUSH=true;     shift 1 ;;
        *)       echo "Unknown: $1"; shift ;;
    esac
done

# ─── 1. Find or create key ─────────────────────────────────────
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
        echo "Найден существующий ключ: $existing"
        read -p "Использовать его? [Y/n]: " -n 1 -r
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
    echo "Генерация нового SSH-ключа..."
    read -p "Email для ключа: " email
    [[ -z "$email" ]] && error "Email не указан"

    KEY_FILE="${HOME}/.ssh/github_ed25519"
    ssh-keygen -t ed25519 -C "$email" -f "$KEY_FILE" -N ""
    echo "Ключ создан: ${KEY_FILE}"
}

# ─── 2. Print public key + instructions ────────────────────────
show_key() {
    local pub="${KEY_FILE}.pub"
    [[ ! -f "$pub" ]] && error "Публичный ключ не найден: $pub"

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ПУБЛИЧНЫЙ КЛЮЧ (скопируй в буфер):"
    echo "═══════════════════════════════════════════════════════"
    cat "$pub"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "  1. Перейди: https://github.com/settings/keys"
    echo "  2. Нажми:   New SSH Key"
    echo "  3. Вставь ключ (см. выше) в поле 'Key'"
    echo "  4. Нажми:   Add SSH Key"
    echo ""
    read -p "Нажми ENTER после добавления ключа на GitHub... " -r
}

# ─── 3. Verify connection ──────────────────────────────────────
verify() {
    info "Проверка подключения к GitHub..."
    local out
    out="$(ssh -T git@github.com 2>&1 || true)"
    if echo "$out" | grep -qi "successfully authenticated"; then
        info "Подключение OK: $(echo "$out" | head -1)"
        return 0
    else
        warn "Подключение не подтверждено: $out"
        return 1
    fi
}

# ─── 4. Update repo remote ─────────────────────────────────────
update_remote() {
    local repo="${TARGET_REPO:-$(pwd)}"
    [[ ! -d "$repo/.git" ]] && error "Не git-репозиторий: $repo"

    local url current_url
    current_url="$(git remote get-url origin 2>/dev/null || true)"
    [[ -z "$current_url" ]] && error "remote 'origin' не найден"

    # Extract owner/repo from HTTPS URL
    local owner repo_name
    owner="$(echo "$current_url" | sed -E 's|https://github.com/([^/]+)/([^/]+)(\.git)?|\1|')"
    repo_name="$(echo "$current_url" | sed -E 's|https://github.com/([^/]+)/([^/]+)(\.git)?|\2|')"

    local new_url="git@github.com:${owner}/${repo_name}.git"

    git -C "$repo" remote set-url origin "$new_url"
    info "Remote обновлён: $new_url"

    if [[ "$DO_PUSH" == "true" ]]; then
        info "Push..."
        git -C "$repo" push origin HEAD
        info "Push OK"
    fi
}

# ─── Main ───────────────────────────────────────────────────────
main() {
    echo "=== SSH Setup для GitHub ==="

    if choose_key; then
        info "Используем существующий ключ"
    else
        generate_key
    fi

    show_key
    verify || { warn "Повтори проверку"; verify || warn "Соединение не работает"; }

    if [[ -n "$TARGET_REPO" ]] || [[ -d "$(pwd)/.git" ]]; then
        update_remote
    fi

    echo ""
    info "Готово! SSH настроен."
    echo "  Ключ: ${KEY_FILE}"
    echo "  Remote: git@github.com:..."
}

main
