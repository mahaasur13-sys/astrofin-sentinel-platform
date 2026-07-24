"""
NetworkPartitioner — nftables/iptables DOCKER-USER chain injector.

Provides a clean interface for applying and rolling back network-level faults
on the Docker bridge (atom-net) without touching the host's iptables rules
permanently.

Usage (from host)
-----------------
    from chaos.partitioner import NetworkPartitioner

import logging
log = logging.getLogger(__name__)


    np = NetworkPartitioner(bridge="docker0")
    np.block_ip("172.28.1.10", "172.28.1.11")  # A → B
    np.partition_nodes(["172.28.1.10"], ["172.28.1.11", "172.28.1.12"])
    np.restore_all()

Usage (from container)
----------------------
    Use HostChaosAgent to inject rules via the host's iptables.
"""

from __future__ import annotations

import re
import subprocess


class NetworkPartitioner:
    """
    Manage network partition rules in iptables DOCKER-USER chain.

    The DOCKER-USER chain is evaluated before the main DOCKER filter rules,
    making it the ideal place to inject chaos rules that only affect containers
    without breaking the host's networking.

    Rules are appended with comment markers for clean identification and removal.
    """

    CHAIN = "DOCKER-USER"
    MARK_COMMENT_PREFIX = "CHAOS_RULE"

    def __init__(self, bridge: str = "docker0", dry_run: bool = False):
        self.bridge = bridge
        self.dry_run = dry_run
        self._applied_rules: list[str] = []

    # ── Core operations ─────────────────────────────────────────────────────

    def block_ip(self, src_ip: str, dst_ip: str, protocol: str = "all") -> bool:
        """
        Block all traffic from src_ip to dst_ip.

        Returns True if rule was added (or already exists).
        """
        comment = f"{self.MARK_COMMENT_PREFIX}:block:{src_ip}:{dst_ip}"
        rule = [
            "iptables",
            "-I", self.CHAIN,
            "-s", src_ip,
            "-d", dst_ip,
            "-j", "DROP",
            "-m", "comment",
            "--comment", comment,
        ]
        return self._add_rule(rule)

    def allow_ip(self, src_ip: str, dst_ip: str) -> bool:
        """Remove a previously added block rule for src→dst."""
        comment = f"{self.MARK_COMMENT_PREFIX}:block:{src_ip}:{dst_ip}"
        return self._remove_by_comment(comment)

    def block_protocol(
        self,
        src_ip: str,
        dst_ip: str,
        protocol: str,
        dst_port: int | None = None,
    ) -> bool:
        """Block traffic of a specific protocol (tcp/udp/icmp) to dst_ip:port."""
        rule = [
            "iptables", "-I", self.CHAIN,
            "-s", src_ip,
            "-d", dst_ip,
            "-p", protocol,
            "-j", "DROP",
        ]
        if dst_port:
            rule.extend(["--dport", str(dst_port)])
        comment = f"{self.MARK_COMMENT_PREFIX}:proto:{protocol}:{src_ip}:{dst_ip}"
        rule.extend(["-m", "comment", "--comment", comment])
        return self._add_rule(rule)

    def partition_nodes(self, isolated_ips: list[str], rest_ips: list[str]) -> int:
        """
        Isolate a set of IPs from the rest of the cluster.

        Applies bidirectional blocks between isolated_ips and rest_ips.

        Returns number of rules applied.
        """
        count = 0
        for src in isolated_ips:
            for dst in rest_ips:
                if self.block_ip(src, dst):
                    count += 1
                if self.block_ip(dst, src):
                    count += 1
        return count

    def restore_all(self) -> int:
        """
        Remove all CHAOS_RULE-marked rules from DOCKER-USER.

        Returns number of rules removed.
        In dry_run mode, no rules are ever added so this is a no-op returning 0.
        """
        if self.dry_run:
            self._applied_rules.clear()
            return 0

        removed = 0
        # List all CHAOS rules
        result = subprocess.run(
            ["iptables", "-L", self.CHAIN, "-n", "--line-numbers"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return 0

        # Parse line numbers in reverse to avoid index shift on deletion
        chaos_lines: list[tuple[str, str]] = []
        for line in result.stdout.splitlines():
            if self.MARK_COMMENT_PREFIX in line:
                parts = re.split(r"\s+", line.strip())
                if len(parts) >= 2:
                    num, policy = parts[0], parts[1]
                    chaos_lines.append((num, policy))

        for num, _ in reversed(chaos_lines):
            subprocess.run(
                ["iptables", "-D", self.CHAIN, num],
                capture_output=True,
            )
            removed += 1

        self._applied_rules.clear()
        return removed

    # ── Query ────────────────────────────────────────────────────────────────

    def list_rules(self) -> list[str]:
        """Return list of CHAOS rules currently in DOCKER-USER."""
        result = subprocess.run(
            ["iptables", "-L", self.CHAIN, "-n"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if self.MARK_COMMENT_PREFIX in line]

    # ── Helpers ────────────────────────────────────────────────────────────

    def _add_rule(self, rule: list[str]) -> bool:
        if self.dry_run:
            log.info(f"[DRY_RUN] {' '.join(rule)}")
            return True

        result = subprocess.run(rule, capture_output=True)
        if result.returncode == 0:
            self._applied_rules.append(" ".join(rule))
            return True
        return False

    def _remove_by_comment(self, comment_substring: str) -> bool:
        result = subprocess.run(
            ["iptables", "-L", self.CHAIN, "-n", "--line-numbers"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        for line in reversed(result.stdout.splitlines()):
            if comment_substring in line:
                parts = re.split(r"\s+", line.strip())
                if len(parts) >= 1:
                    num = parts[0]
                    subprocess.run(
                        ["iptables", "-D", self.CHAIN, num],
                        capture_output=True,
                    )
                    return True
        return False


class HostChaosAgent:
    """
    Agent that runs on the Docker host and injects iptables rules
    on behalf of chaos scenarios running inside containers.

    Since containers cannot directly manipulate iptables on the host,
    this agent exposes a simple HTTP endpoint that containers can call
    to request rule injection.

    Usage (on host):
        agent = HostChaosAgent(listen="0.0.0.0:8899")
        agent.start()  # blocks

    Usage (from container):
        import requests
        requests.post("http://host.docker.internal:8899/block",
                     json={"src": "172.28.1.10", "dst": "172.28.1.11"})
    """

    def __init__(self, listen: str = "0.0.0.0:8899"):
        self.listen = listen
        self._server = None
        self.partitioner = NetworkPartitioner()

    def start(self):
        """Start the HTTP control API (blocking)."""
        import http.server
        import json
        import socketserver

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                except Exception:
                    self.send_error(400, "invalid JSON")
                    return

                action = data.get("action", "")
                src = data.get("src", "")
                dst = data.get("dst", "")
                data.get("protocol", "all")
                data.get("port")

                ok = False
                detail = ""

                try:
                    if action == "block":
                        ok = self.server.partitioner.block_ip(src, dst)
                        detail = f"block {src}→{dst}"
                    elif action == "unblock":
                        ok = self.server.partitioner.allow_ip(src, dst)
                        detail = f"unblock {src}→{dst}"
                    elif action == "partition":
                        iso = data.get("isolated", [])
                        rest = data.get("rest", [])
                        count = self.server.partitioner.partition_nodes(iso, rest)
                        ok = True
                        detail = f"partitioned {count} rules"
                    elif action == "restore":
                        count = self.server.partitioner.restore_all()
                        ok = True
                        detail = f"restored {count} rules"
                    elif action == "list":
                        rules = self.server.partitioner.list_rules()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"rules": rules}).encode())
                        return
                    else:
                        self.send_error(400, f"unknown action: {action}")
                        return
                except Exception as e:
                    self.send_error(500, str(e))
                    return

                self.send_response(200 if ok else 500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok, "detail": detail}).encode())

            def log_message(self, format, *args):
                log.info(f"[CHAOS_AGENT] {args[0]}")

        class THTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            partitioner = self.partitioner
            allow_reuse_address = True

        self._server = THTTPServer((self.listen.split(":")[0], int(self.listen.split(":")[1])), Handler)
        log.info(f"[CHAOS_AGENT] listening on {self.listen}")
        self._server.serve_forever()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
