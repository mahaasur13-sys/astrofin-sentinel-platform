# AstroFin Sentinel Dashboard — Чёрный экран: Fix Plan

> **Статус:** Zo-окружение  ✅ (bootstrap fixed) | Ожидается проверка пользователем на Pop!_OS / Linux
> **Дата:** 2026-07-24

## Текущее состояние (Zo)

| Ресурс | Статус |
|--------|--------|
| sentinel-ui-v2 | ✅ 200 OK, Cache-Control: no-cache |
| astrofin-api | ✅ 200 OK |
| dist/index.html | ✅ index-BUAd4Lf8.js (latest) |
| Service Worker | ❌ удалён из dist (SW кэшировал старый билд) |
| Bootstrap instrumentation | ✅ логи [AstroFin] на каждом этапе |
| RootErrorBoundary | ✅ ловит все ошибки, показывает fallback + кнопка «Перезагрузить» |

## Что исправлено

### P0 — Bootstrap instrumentation (`src/main.tsx`)
- **Mount point check:** Перед `createRoot()` проверяется `document.getElementById('root')`. Если отсутствует — показывает fallback UI без React.
- **Feature Flags / Sentry / Web Vitals:** Каждый инициализируется в отдельном try/catch. Сбой одного не блокирует остальные.
- **Логи:** `[AstroFin] Phase 0 start` → `[AstroFin] Phase 0.1/0.2/0.3` → `[AstroFin] Phase 0 complete` → `[AstroFin] Bootstrap: mounting <App />` → `[AstroFin] Bootstrap: render() called`.

### P1 — Sentry Graceful Fallback
- `initSentry()` НЕ бросает исключений. Функция проверяет наличие DSN — если нет, просто логгирует и выходит.
- `lib/sentry.ts` использует `@sentry/browser` (ленивый импорт).

### P2 — Zustand shallow comparison (`src/App.tsx`)
- Добавлен `import { shallow } from 'zustand/shallow'`.
- Объектный селектор `useDashboardStore((s) => ({...}))` теперь использует `shallow` для предотвращения бесконечных ререндеров:
  ```tsx
  const { isMobile, ... } = useDashboardStore(
    (s) => ({ isMobile: s.isMobile, ... }),
    shallow
  );
  ```

### P3 — Service Worker отключён
- `dist/sw.js` / `dist/registerSW.js` удалены из production-сборки.
- Причина: SW кэшировал старый билд с багом (React #185). Новые версии не подгружались.

### P4 — RootErrorBoundary
- `src/main.tsx`: Классовый компонент с `componentDidCatch()`.
- При ошибке рендера показывает: ⚠ эмодзи, сообщение об ошибке, стек, кнопку «Перезагрузить».
- Кнопка делает `this.setState({ hasError: false })` + `window.location.reload()`.

## Как проверить на локальной машине

```bash
cd ~/Projects/astrofin-sentinel-platform/web-react

# 1. Убедиться, что актуальный код на месте
git pull origin main

# 2. Установка зависимостей (если нужно)
npm install

# 3. Production build
npm run build

# 4. Запустить локальный сервер
python3 -m http.server 4200 -d dist &

# 5. Открыть браузер: http://localhost:4200
# 6. F12 → Console — проверить логи [AstroFin]
```

## Что ожидать

### Успешный сценарий
1. Загружается страница с тёмным фоном
2. Виден Header (AstroFin Sentinel), Sidebar (Overview, Agents, ...), StatusBar
3. В Console: `[AstroFin] Phase 0 complete`, затем данные SSE

### Сценарий с ошибкой
1. RootErrorBoundary показывает фиолетово-чёрный экран с сообщением об ошибке
2. В Console: `[AstroFin] Root render error: ...`
3. **Нажать «Перезагрузить»** — это сбросит SW-кэш и перезагрузит страницу

### Сценарий «пустая консоль»
1. Если в Console НЕТ логов `[AstroFin]` — проблема до выполнения JS (HTML, CSP, Vite build)
2. Проверить, что dist/index.html содержит `<script ... src="/assets/index-*.js">`

### Сценарий «React #185: Maximum update depth exceeded»
1. Наиболее вероятная причина — `useDashboardSSE` в бесконечном цикле
2. Отключить SSE: закомментировать `useDashboardSSE()` в App.tsx → rebuild
3. Если без SSE работает → проблема в хуке SSE → добавить защиту от повторных вызовов

## Emergency Rollback

```bash
# Вернуться к предыдущему коммиту
cd ~/Projects/astrofin-sentinel-platform/web-react
git stash
git checkout HEAD~1 -- src/App.tsx src/main.tsx
npm run build
```

---

> **TL;DR:** Bootstrap instrumentation + RootErrorBoundary + shallow + SW removal = dashboard должен загружаться. Если чёрный экран сохраняется — проблема в SSE-хуке или конкретном компоненте. Пришли скриншот консоли (F12 → Console) для точной диагностики.
