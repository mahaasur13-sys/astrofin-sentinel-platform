#!/usr/bin/env python3
"""Validate docker-compose.yml for P0 security requirements."""

import sys
from pathlib import Path

import yaml


def main():
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_path.exists():
        print(f"ERROR: {compose_path} not found")
        sys.exit(1)

    with open(compose_path) as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    errors = []

    # 1. Redis must require a password
    redis = services.get("redis", {})
    redis_cmd = redis.get("command", "")
    if "requirepass" not in str(redis_cmd) and "--requirepass" not in str(redis_cmd):
        errors.append("Redis: no --requirepass in command")

    # 2. Grafana must not use default admin/admin
    grafana = services.get("grafana", {})
    grafana_env = grafana.get("environment", {})
    if isinstance(grafana_env, list):
        grafana_env = {k: v for item in grafana_env for k, v in [item.split("=", 1)]}
    pass_val = grafana_env.get("GF_SECURITY_ADMIN_PASSWORD", "admin")
    if pass_val == "admin" or "${GRAFANA_ADMIN_PASSWORD:-admin}" in str(grafana.get("environment", "")):
        errors.append("Grafana: default password 'admin' is still configured")

    # 3. sslmode=disable anywhere (in environment or command)
    compose_str = yaml.dump(data)
    if "sslmode=disable" in compose_str:
        errors.append("PostgreSQL connections: sslmode=disable found (should be require)")

    # 4. Monitoring ports should bind to 127.0.0.1
    for svc_name, svc in services.items():
        ports = svc.get("ports", [])
        for port_map in ports:
            port_str = str(port_map)
            if (
                "9090" in port_str
                or "3001" in port_str
                or "16686" in port_str
                or "9187" in port_str
                or "9121" in port_str
            ):
                if not port_str.startswith("127.0.0.1:"):
                    errors.append(f"{svc_name}: port {port_str} is not bound to 127.0.0.1")

    # 5. Services must drop all capabilities and disable privilege escalation
    for svc_name, svc in services.items():
        sec_opt = svc.get("security_opt", [])
        cap_drop = svc.get("cap_drop", [])
        if "no-new-privileges:true" not in sec_opt:
            errors.append(f"{svc_name}: missing security_opt: no-new-privileges:true")
        if "ALL" not in cap_drop:
            errors.append(f"{svc_name}: missing cap_drop: ALL")

    if errors:
        print("ERROR: Docker security issues found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("OK: All Docker security checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
