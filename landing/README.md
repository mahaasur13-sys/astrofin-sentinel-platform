# DecisionOS Landing Page

Статический лендинг для DecisionOS v1.0.0 — enterprise multi-tenant SaaS decision infrastructure.

## 📁 Структура

```
landing/
├── index.html       # Главная: hero, features, code demo, AI chat, метрики
├── pricing.html     # Тарифы: Start ($49), Pro ($199), Enterprise (Custom)
├── docs.html        # Документация: REST API, Policy Engine, webhooks, ошибки
├── dashboard.html   # Макет админ-панели: решения, инвойсы, кошельки, тенанты
├── css/style.css    # Тёмная тема, CSS-переменные, адаптивность
└── README.md        # Этот файл
```

## 🚀 Деплой

### Vercel

```bash
npm i -g vercel
cd landing
vercel --prod
```

Vercel автоматически определит статический сайт (HTML + CSS).

### Netlify

```bash
npm i -g netlify-cli
cd landing
netlify deploy --prod --dir=.
```

Или drag-and-drop папку `landing/` на https://app.netlify.com/drop.

### GitHub Pages

1. Запушь содержимое `landing/` в ветку `gh-pages`:

```bash
git subtree push --prefix=landing origin gh-pages
```

2. В Settings → Pages выбери source: `gh-pages` branch.

### Любой статический хостинг

Скопируй содержимое `landing/` на сервер — это чистый HTML + CSS, без зависимостей.

## 🎨 Дизайн

- Тёмная тема с CSS-переменными
- Адаптивная вёрстка (мобильные + десктоп)
- Tailwind-подобные utility-классы (но без самого Tailwind — zero deps)
- Вдохновлено Stripe / Vercel

## 🔗 Продакшен

- **DecisionOS repo:** `roma-execution-bridge/`
- **Стратегический отчёт:** `docs/STRATEGIC-REPORT-DECISIONOS-v1.0.0.md`
- **Тесты:** 32/32 ✅

---

v1.0.0 · 2026-08-19
