#!/usr/bin/env python3
"""
Zo Computer — MCP Server (stdio transport).
Exposes Zo host capabilities as MCP tools for DeepSeek Harness.

Provides: health checks, service status, system diagnostics.
This is a READ-ONLY bridge — no destructive operations.
"""
import asyncio
import json
import os
import subprocess

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("zo-computer")


def _run_cmd(cmd: str, timeout: int = 10) -> dict:
    """Run a shell command and return structured output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[:2000],
            "stderr": result.stderr.strip()[:500],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
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


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "check_health":
            uptime = _run_cmd("uptime")
            cpu = _run_cmd("top -bn1 | head -5")
            return [TextContent(type="text", text=json.dumps({
                "uptime": uptime,
                "cpu_top": cpu,
            }, indent=2))]

        elif name == "list_services":
            result = _run_cmd(
                "find /dev/shm -name '*.log' -type f | sed 's|/dev/shm/||' | sed 's|.log||' | sort -u",
                timeout=5,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_service_logs":
            svc = arguments["service_name"]
            lines = arguments.get("lines", 20)
            log_path = f"/dev/shm/{svc}.log"
            result = _run_cmd(f"tail -{lines} {log_path} 2>/dev/null || echo 'No log file found'")
            return [TextContent(type="text", text=result["stdout"] if result["success"] else result["stderr"])]

        elif name == "check_port":
            port = arguments["port"]
            result = _run_cmd(f"ss -tlnp | grep ':{port} ' || echo 'Port {port} not open'")
            return [TextContent(type="text", text=result["stdout"])]

        elif name == "get_disk_usage":
            result = _run_cmd("df -h /home/workspace")
            return [TextContent(type="text", text=result["stdout"])]

        elif name == "get_memory_usage":
            result = _run_cmd("free -h")
            return [TextContent(type="text", text=result["stdout"])]

        elif name == "list_processes":
            result = _run_cmd(
                "ps aux | grep -E 'python|node' | grep -v grep | awk '{print $2, $3, $4, $11}' | head -20"
            )
            return [TextContent(type="text", text=result["stdout"])]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
