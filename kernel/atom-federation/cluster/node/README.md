# Cluster Node — Container Image

Production container for a single ATOM Federation OS cluster node
(gRPC server + DRL bridge + SBS enforcer + health graph). Same standard
as `AsurDev/acos/Dockerfile`: multi-stage, slim, non-root, tini PID 1,
pinned deps, real liveness probe.

## What lives here

```
cluster/node/
├── Dockerfile          # 2-stage, python:3.12-slim, non-root, tini, healthcheck
├── requirements.txt    # pinned: grpcio==1.80.0, protobuf==6.33.6
├── healthcheck.py      # standalone liveness probe (3-layer: imports / gRPC / TCP)
├── entrypoint.py       # reads NODE_ID/PEERS/NODE_PORT from env, starts node
├── node.py             # ClusterNode — full node runtime (RPC + DRL + SBS)
└── health.py           # ClusterHealthGraph, NodeState (used by node.py)
```

The Dockerfile `COPY cluster/ ./cluster/` so the whole tree lands in
the image; the `entrypoint.py` lives one level above `shared/` and
imports `cluster.shared.runtime_bootstrap.BootstrapNode`.

## Build

```bash
# from repo root
docker build -t atom-node:local -f cluster/node/Dockerfile .

# 3-node cluster via compose
docker compose up -d

# single node (for ad-hoc smoke)
docker run --rm \
  -e NODE_ID=node-a \
  -e PEERS=node-b,node-c \
  -e NODE_PORT=50051 \
  atom-node:local
```

## Liveness

The Dockerfile `HEALTHCHECK` (and the `healthcheck:` block in
`docker-compose.yml`) both invoke:

```bash
python -m cluster.node.healthcheck
```

The probe runs **three layered checks** and exits 0 if any of them
succeeds, 1 if all fail. This is deliberately not just `import grpc`
(an import succeeds even when the runtime is broken) and not just
`/proc/net/tcp` (a port in `LISTEN` does not prove gRPC works):

| Layer | What it checks | When it passes |
|---|---|---|
| 1. Module imports | `grpc`, `google.protobuf`, `cluster.node.health`, `cluster.shared.*` | All imports succeed |
| 2. gRPC channel state | `grpc.secure_channel` / `insecure_channel` reachability via `_connectivity_state` | `READY` (or `IDLE` + port LISTEN) |
| 3. `/proc/net/tcp` | `NODE_PORT` hex in LISTEN state (`0A`) | Port is bound by some process |

If `NODE_PORT` is unset (e.g. `docker exec` smoke), layer 3 falls
back to "any TCP LISTEN" so the probe still works in single-shot mode.

Inspect live status:

```bash
docker inspect --format='{{json .State.Health}}' atom-node-a
```

## Configuration

All configuration is environment-driven (no mounted config files):

| Env var | Required | Default | Purpose |
|---|---|---|---|
| `NODE_ID` | yes | `unknown` | Unique node identifier (`node-a`/`b`/`c` in compose) |
| `PEERS` | yes | empty | Comma-separated peer IDs (used for RPC mesh + DRL) |
| `NODE_PORT` | yes | unset | gRPC listen port — MUST match `PORT_MAP` in `cluster/shared/rpc_server.py` |
| `PYTHONUNBUFFERED` | no | `1` | Stdout flush on every write (for log shipping) |
| `PYTHONPATH` | no | `/app` | Python import root |

## Differences from `AsurDev/acos/Dockerfile`

| | acos | cluster/node |
|---|---|---|
| Base | `python:3.12-slim` | `python:3.12-slim` (parity) |
| User | `acos` uid 1001 | `atom` uid 1001 |
| Entrypoint | `python -m acos_cli invariants` | `python cluster/node/entrypoint.py` |
| Healthcheck | `python -m acos_cli invariants` | `python -m cluster.node.healthcheck` |
| Deps | stdlib-only (empty pinned file) | `grpcio==1.80.0`, `protobuf==6.33.6` |
| Working dir | `/app` | `/app` |
| Exposed ports | `8080` (HTTP, reserved) | none (gRPC port is per-node via env) |

The asymmetry in `Exposed ports` is intentional: acos is expected to
expose a future HTTP `/metrics` endpoint; cluster nodes speak gRPC
on a port that varies per node (`50051`/`50052`/`50053`), so we do
not pin `EXPOSE` here.

## CI

`hadolint cluster/node/Dockerfile` runs as part of the Docker
container CI. Current state: 2 `DL3008` warnings (apt version
pinning) — same warnings as the acos reference Dockerfile (drift
parity is preserved; both will be fixed together in a future lint
parity sweep).

## Troubleshooting

**Container restarts immediately**

Check `docker logs atom-node-a`. The most common cause is a missing
or wrong `PEERS` (the node will exit if it cannot initialise the
gRPC mesh).

**`unhealthy` but logs look fine**

Run the probe manually:

```bash
docker exec atom-node-a python -m cluster.node.healthcheck
```

The output names the failing layer (`unhealthy — port 50051 NOT in
LISTEN` vs. `channel-fail: ...` vs. `imports failed: ...`).

**gRPC channel stays `IDLE` even when port is up**

This is normal on first start. The probe treats `IDLE` + `LISTEN` as
healthy because the channel only transitions to `READY` after the
first RPC. If you want a stricter probe, call any peer — the
channel will then enter `READY` state.
