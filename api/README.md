# API Documentation

This repository currently exposes a minimal HTTP surface.

## Discovered endpoint

- `GET /data-room/conflicts` — returns the parsed conflict journal as JSON

## OpenAPI

See `openapi.yaml` for the current OpenAPI 3.0 snippet.

## Notes

If the platform later exposes additional external HTTP APIs, extend `openapi.yaml`
and keep this directory in sync with the actual routes.
