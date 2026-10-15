#!/usr/bin/env python3
"""
Zo Computer — MCP Server (stdio transport).
Exposes Zo host capabilities as MCP tools for DeepSeek Harness.

Provides: health checks, service status, system diagnostics.
This is a READ-ONLY bridge — no destructive operations.

Commands are executed as argument vectors with shell=False; no argument is ever
interpolated into a shell string. The tool allowlist is fail-closed (see
tool_allowlist.py) and defaults to this bridge's read-only set.
"""
import asyncio
import json
import os
import re
import subprocess

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tool_allowlist import is_allowed, resolve_allowed_tools, warn

server = Server("zo-computer")

# ── Tool registry ──────────────────────────────────────────────────────────
# This bridge is read-only by design: `privileged` stays empty. It exists so the
# classification is explicit and so a future mutating tool cannot be added
# without being named here.

READ_ONLY_TOOLS = frozenset({
    "check_health",
    "list_services",
    "get_service_logs",
    "check_port",
    "get_disk_usage",
    "get_memory_usage",
    "list_processes",
})
PRIVILEGED_TOOLS: frozenset[str] = frozenset()

ALLOWED_TOOLS = resolve_allowed_tools(
    READ_ONLY_TOOLS, PRIVILEGED_TOOLS, os.environ.get("ZO_BRIDGE_ALLOWED_TOOLS")
)

SERVICE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
MAX_STDOUT = 2000
MAX_STDERR = 500


def _run_cmd(argv: list[str], timeout: int = 10) -> dict:
    """Run a command as an argument vector (no shell) and return structured output."""
    try:
        result = subprocess.run(
            argv, shell=False, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[:MAX_STDOUT],
            "stderr": result.stderr.strip()[:MAX_STDERR],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def _with_stdout(result: dict, text: str) -> dict:
    """Return a copy of a command result with stdout replaced (still length-capped)."""
    updated = dict(result)
    updated["stdout"] = text.strip()[:MAX_STDOUT]
    return updated


def _as_int(value, low: int, high: int):
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if low <= value <= high:
        return value
    return None


def _valid_service_name(value) -> str | None:
    if not isinstance(value, str) or not SERVICE_NAME_RE.fullmatch(value):
        return None
    if ".." in value:
        return None
    return value


@server.list_tools()
async def list_tools() -> list[Tool]:
    tools = [
        Tool(
            name="check_health",
            description="Check Zo host health: CPU, memory, disk, uptime",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="list_services",
            description="List all Zo user services and their status",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_service_logs",
            description="Get recent logs for a Zo service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name (e.g. astrofin-prod-strategy)"},
                    "lines": {"type": "integer", "description": "Number of log lines", "default": 20},
                },
                "required": ["service_name"],
            },
        ),
        Tool(
            name="check_port",
            description="Check if a port is open on the Zo host",
            inputSchema={
                "type": "object",
                "properties": {"port": {"type": "integer", "description": "Port number"}},
                "required": ["port"],
            },
        ),
        Tool(
            name="get_disk_usage",
            description="Get disk usage for the Zo workspace",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_memory_usage",
            description="Get RAM usage",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="list_processes",
            description="List running Python and Node processes on Zo",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]
    return [tool for tool in tools if is_allowed(tool.name, ALLOWED_TOOLS)]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if not is_allowed(name, ALLOWED_TOOLS):
        warn(f"denied tool call: {name!r}")
        return [TextContent(type="text", text=f"Tool not permitted: {name}")]

    try:
        if name == "check_health":
            uptime = _run_cmd(["uptime"])
            top = _run_cmd(["top", "-bn1"])
            cpu_head = "\n".join(top["stdout"].splitlines()[:5])
            return [TextContent(type="text", text=json.dumps({
                "uptime": uptime,
                "cpu_top": _with_stdout(top, cpu_head),
            }, indent=2))]

        elif name == "list_services":
            result = _run_cmd(["find", "/dev/shm", "-name", "*.log", "-type", "f"], timeout=5)
            names = sorted({
                line.strip()[len("/dev/shm/"):][: -len(".log")]
                for line in result["stdout"].splitlines()
                if line.strip().startswith("/dev/shm/") and line.strip().endswith(".log")
            })
            return [TextContent(type="text", text=json.dumps(
                _with_stdout(result, "\n".join(names)), indent=2))]

        elif name == "get_service_logs":
            svc = _valid_service_name(arguments.get("service_name"))
            if svc is None:
                return [TextContent(type="text", text="Invalid service_name")]
            lines = _as_int(arguments.get("lines", 20), 1, 1000)
            if lines is None:
                return [TextContent(type="text", text="Invalid lines")]
            log_path = f"/dev/shm/{svc}.log"
            if not os.path.isfile(log_path):
                return [TextContent(type="text", text="No log file found")]
            result = _run_cmd(["tail", "-n", str(lines), log_path])
            return [TextContent(type="text", text=result["stdout"] if result["success"] else result["stderr"])]

        elif name == "check_port":
            port = _as_int(arguments.get("port"), 1, 65535)
            if port is None:
                return [TextContent(type="text", text="Invalid port")]
            result = _run_cmd(["ss", "-tlnp"])
            matching = [line for line in result["stdout"].splitlines() if f":{port} " in line]
            text = "\n".join(matching) if matching else f"Port {port} not open"
            return [TextContent(type="text", text=text)]

        elif name == "get_disk_usage":
            result = _run_cmd(["df", "-h", "/home/workspace"])
            return [TextContent(type="text", text=result["stdout"])]

        elif name == "get_memory_usage":
            result = _run_cmd(["free", "-h"])
            return [TextContent(type="text", text=result["stdout"])]

        elif name == "list_processes":
            result = _run_cmd(["ps", "aux"])
            rows = []
            for line in result["stdout"].splitlines()[1:]:
                if "python" not in line and "node" not in line:
                    continue
                if "grep" in line:
                    continue
                fields = line.split()
                if len(fields) < 11:
                    continue
                rows.append(" ".join([fields[1], fields[2], fields[3], fields[10]]))
                if len(rows) == 20:
                    break
            return [TextContent(type="text", text="\n".join(rows))]

        else:
            return [TextContent(type="text", text=f"Tool not permitted: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
