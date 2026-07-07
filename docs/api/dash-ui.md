# Dash UI — Human reference

The Dash app in `web/app.py` is not a REST service: it serves an HTML dashboard
and exchanges state via Dash callbacks, not HTTP endpoints. This file documents
the user-visible tabs and their data flow for engineers who need to extend
the UI.

| Tab id            | Label        | Source of data                                    |
|-------------------|--------------|---------------------------------------------------|
| `tab-dashboard`   | 📊 Dashboard | `web/callbacks.py` → live engine metrics         |
| `tab-evolution`   | ▶ Evolution  | `web/components/evolution.py` → strategy history  |
| `tab-sessions`    | 📋 Sessions  | `web/sessions_callbacks.py` → sessions table     |
| `tab-explorer`    | 🔬 Explorer  | `knowledge/rag_retriever.py` → RAG search        |
| `tab-live`        | 📡 Live      | `meta_rl/persistence.py` → live agent feed       |

The Flask server that backs Dash also hosts the `data_room` blueprint
(`/data-room/conflicts`) and the routes from `web/wsgi.py`. These are
documented in `openapi.yaml`.

The OpenAPI specification does not describe Dash callbacks because they
are not a contract — the contract is the Python function signature in
`web/callbacks.py`. Update that file when changing tab behavior.
