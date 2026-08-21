#!/usr/bin/env python3
"""
ROMA Execution Bridge — MCP Server (stdio transport).
Exposes ROMA API as MCP tools for DeepSeek Harness.

Architecture Principle:
  DeepSeek Harness = BRAIN (planning, reasoning, coding)
  ROMA Execution Bridge = HANDS (GPU/CPU execution, billing, workers)

All GPU/CPU/billing operations MUST go through this MCP server.
Harness NEVER accesses GPU rental APIs directly.
"""
import asyncio
import json
import os
import sys

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

ROMA_BASE = os.environ.get("ROMA_API_URL", "http://localhost:8900")
ROMA_API_KEY = os.environ.get("ROMA_API_KEY", "")

server = Server("roma-execution-bridge")


async def _roma_request(method: str, path: str, json_body: dict | None = None) -> dict:
    """Make an authenticated request to ROMA API."""
    headers = {"Content-Type": "application/json"}
    if ROMA_API_KEY:
        headers["X-API-Key"] = ROMA_API_KEY

    url = f"{ROMA_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "POST":
            resp = await client.post(url, headers=headers, json=json_body)
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        resp.raise_for_status()
        return resp.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="check_health",
            description="Check ROMA Execution Bridge health status",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="submit_job",
            description="Submit a GPU/CPU job to ROMA Execution Bridge. THE ONLY WAY to request GPU/CPU resources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description / command to run"},
                    "image": {"type": "string", "description": "Docker image (e.g. pytorch/pytorch:latest)"},
                    "gpu_required": {"type": "boolean", "description": "Whether GPU is needed", "default": False},
                    "priority": {"type": "integer", "description": "Priority 1-10", "default": 5, "minimum": 1, "maximum": 10},
                    "execution_mode": {"type": "string", "description": "Execution mode", "default": "k8s_job"},
                    "backend": {"type": "string", "description": "Backend: local, slurm, or ray", "default": "local"},
                    "instance_type": {"type": "string", "description": "GPU type: any, RTX 3060, A100, H100", "default": "any"},
                },
                "required": ["task"],
            },
        ),
        Tool(
            name="get_job_status",
            description="Get status of a submitted job",
            inputSchema={
                "type": "object",
                "properties": {"job_id": {"type": "string", "description": "Job ID"}},
                "required": ["job_id"],
            },
        ),
        Tool(
            name="cancel_job",
            description="Cancel a running/pending job",
            inputSchema={
                "type": "object",
                "properties": {"job_id": {"type": "string", "description": "Job ID"}},
                "required": ["job_id"],
            },
        ),
        Tool(
            name="list_jobs",
            description="List all jobs",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_workers",
            description="List all workers and their status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_worker_metrics",
            description="Get metrics for a specific worker",
            inputSchema={
                "type": "object",
                "properties": {"worker_id": {"type": "string", "description": "Worker ID"}},
                "required": ["worker_id"],
            },
        ),
        Tool(
            name="get_billing_balance",
            description="Get current billing balance",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_billing_ledger",
            description="Get billing ledger entries",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_billing_spend_cap",
            description="Get current spend cap",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_usage",
            description="Get current usage statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "check_health":
            result = await _roma_request("GET", "/health")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "submit_job":
            result = await _roma_request("POST", "/submit", json_body={
                "task": arguments["task"],
                "image": arguments.get("image"),
                "gpu_required": arguments.get("gpu_required", False),
                "priority": arguments.get("priority", 5),
                "execution_mode": arguments.get("execution_mode", "k8s_job"),
                "backend": arguments.get("backend", "local"),
                "instance_type": arguments.get("instance_type", "any"),
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_job_status":
            result = await _roma_request("GET", f"/status/{arguments['job_id']}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "cancel_job":
            result = await _roma_request("POST", f"/cancel/{arguments['job_id']}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_jobs":
            result = await _roma_request("GET", "/jobs")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_workers":
            result = await _roma_request("GET", "/workers")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_worker_metrics":
            result = await _roma_request("GET", f"/workers/{arguments['worker_id']}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_billing_balance":
            result = await _roma_request("GET", "/billing/balance")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_billing_ledger":
            result = await _roma_request("GET", "/billing/ledger")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_billing_spend_cap":
            result = await _roma_request("GET", "/billing/spend-cap")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_usage":
            result = await _roma_request("GET", "/usage")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"ROMA API error ({e.response.status_code}): {e.response.text[:500]}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
