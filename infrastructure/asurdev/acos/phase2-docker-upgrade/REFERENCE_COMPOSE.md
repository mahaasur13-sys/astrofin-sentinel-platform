# Reference Compose — Phase-2 Standard

Canonical `docker-compose.yml` shape for the Phase-2 standard.
Like [REFERENCE_DOCKERFILE.md](./REFERENCE_DOCKERFILE.md), this is
**a template, not a copy-paste target** — adapt the service name,
build context, env vars, and port mappings to your service.

Both reference deployments follow this pattern:

- `AsurDev/docker-compose.yml` — acos + redis + postgres, single host.
- `atom-federation-os/docker-compose.yml` — 3-node cluster
  (`atom-node-a`, `atom-node-b`, `atom-node-c`).

---

## Single-service compose (acos pattern)

```yaml
services:
  <service>:
    build:
      context: .                          # repo root, NOT the Dockerfile dir
      dockerfile: <path/to/Dockerfile>
    image: <registry>/<service>:<tag>
    container_name: <service>
    restart: unless-stopped
    user: "1001:1001"                     # matches Dockerfile non-root user
    read_only: true                       # image is immutable at runtime
    tmpfs:
      - /tmp:size=64M                     # /tmp is the only writable scratch
    environment:
      PYTHONUNBUFFERED: "1"
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      # service-specific env vars go here
    volumes:
      - <service>-data:/app/data          # named volume, owned by 1001:1001
    networks:
      - <service>-net
    healthcheck:
      test: ["CMD", "python", "-m", "<service>.healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  <service>-data:

networks:
  <service>-net:
    driver: bridge
```

## 3-node cluster compose (atom-federation-os pattern)

```yaml
version: "3.9"

services:
  node-a:
    build:
      context: .
      dockerfile: cluster/node/Dockerfile
    image: acos/cluster-node:phase2
    container_name: atom-node-a
    hostname: atom-node-a
    environment:
      NODE_ID: node-a
      PEERS: node-b,node-c
      NODE_PORT: "50051"
    networks:
      atom-net:
        ipv4_address: 172.28.1.10
    volumes:
      - shared-data:/app/shared_data
    healthcheck:
      test: ["CMD", "python", "-m", "cluster.node.healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  node-b:
    # mirror of node-a with: NODE_ID=node-b, PEERS=node-a,node-c,
    # NODE_PORT=50052, ipv4_address=172.28.1.11

  node-c:
    # mirror of node-a with: NODE_ID=node-c, PEERS=node-a,node-b,
    # NODE_PORT=50053, ipv4_address=172.28.1.12

volumes:
  shared-data:

networks:
  atom-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.1.0/24
```

---

## Why each block is the way it is

### `build.context: .`

The build context is the **repo root**, not the directory
containing the Dockerfile. This is what lets `COPY cluster/`
in the Dockerfile resolve correctly: the Dockerfile lives at
`cluster/node/Dockerfile`, but the paths inside it are
**relative to the build context**, not to the Dockerfile.

```yaml
# ❌ wrong — context is too narrow, COPY cluster/ would fail
build:
  context: ./cluster/node
  dockerfile: Dockerfile

# ✅ right — context is repo root, COPY cluster/ resolves
build:
  context: .
  dockerfile: cluster/node/Dockerfile
```

### `user: "1001:1001"` + `read_only: true`

Two security primitives that are easy to skip:

- `user: "1001:1001"` — guarantees that even if a process in the
  container manages to escalate, it's still running as the
  non-root user. Matches the `USER` directive in the Dockerfile.
- `read_only: true` — makes the container's filesystem
  immutable at runtime. The container can ONLY write to
  `tmpfs` and explicitly mounted volumes. This catches a
  whole class of "container wrote to /etc/passwd" attacks.

### `tmpfs: /tmp:size=64M`

`read_only: true` breaks a lot of Python apps that write to
`/tmp`. The `tmpfs` entry re-enables `/tmp` as a 64 MB in-memory
filesystem — fast, ephemeral, and isolated.

If your service needs more tmp space (large numpy caches, model
downloads), bump the size or add additional tmpfs paths.

### `healthcheck` mirrors Dockerfile HEALTHCHECK

The compose-level `healthcheck:` MUST call the same module as
the Dockerfile's `HEALTHCHECK CMD`. If they differ:

- `docker ps` (which uses compose) shows one verdict.
- `docker inspect` (which uses the Dockerfile) shows another.

This was the original Phase-1 bug — the acos compose used
`python -c "import sys; sys.exit(0)"` while the Dockerfile used
`python -m acos_cli invariants`. They gave different verdicts.

### `deploy.resources`

Sets **soft and hard** CPU/memory limits:

- `limits` — Docker kills the container if it exceeds these.
- `reservations` — Docker guarantees at least this much is
  available (used by orchestrators for scheduling).

Without these, a single container can OOM-kill its host.

### `logging.driver: json-file`

Default Docker logging driver is `json-file` with **unbounded
size**. In production, a chatty service will fill the disk
within hours. `max-size: 10m` + `max-file: 3` keeps the last
30 MB of logs per container and rotates the rest.

For Loki/Grafana or similar log shipping, replace `driver`
with the appropriate plugin — but keep the rotation limits.

### `restart: unless-stopped`

Only restart if the container exited because of a crash, not
because someone ran `docker compose stop`. This is the correct
restart policy for **stateful** services that should survive
host reboots but not operator intervention.

For stateless batch jobs, use `restart: no`.

---

## Anti-patterns

❌ `image: myservice:latest` — never tag `:latest` in compose.
   Use a specific tag or a build hash.

❌ `build: .` with `image:` unset — leaves no stable handle to
   the built image. Always set `image:` even if you don't push
   it — it makes `docker compose down --rmi all` work correctly.

❌ `ports: ["50051:50051"]` for gRPC clusters — exposes the
   gRPC port on the host, where it will collide between nodes
   (node-a, node-b, node-c all want 50051). Use `expose:` (not
   `ports:`) for inter-container traffic; reserve `ports:` for
   host-visible services.

❌ `networks: default` — implicit network name. Always declare
   a named network so the service can be moved to a different
   compose project without losing connectivity.

❌ `environment: NODE_ID=node-a` (no quotes around the value) —
   YAML interprets `true`, `false`, `null`, and bare numbers as
   types. `NODE_PORT: "50051"` keeps it as a string. Compose
   is forgiving but downstream apps (gRPC, JSON env) are not.

❌ `volumes: - ./host/path:/container/path` for production data
   — host paths don't survive `docker compose down` and create
   permission mismatches between host uid and container uid 1001.
   Use **named volumes** (`- cluster-data:/app/data`).

❌ No `healthcheck:` block — without it, `docker compose ps`
   always shows `Up` even when the service is broken. Health
   gates are how orchestrators decide when to send traffic.
