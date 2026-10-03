"""Fail-closed contract tests for the DSH MCP bridges (`.dsh/mcp-servers/`).

Covers the tool allowlist and the ROMA credential resolution:

  1. an unknown tool is never permitted;
  2. a missing/blank allowlist means read-only, never allow-all;
  3. a read-only role cannot reach mutating/financial/destructive tools;
  4. an explicitly granted read-only tool still works;
  5. ROMA_API_KEY missing / empty / valid.

No network is touched: the deny gate and the key gate both run before any
request is issued.
"""
from __future__ import annotations

import asyncio
import importlib.util
import pathlib
import sys

import pytest

pytestmark = pytest.mark.unit

BRIDGE_DIR = pathlib.Path(__file__).resolve().parents[1] / ".dsh" / "mcp-servers"

if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

DUMMY_KEY = "test-key-not-a-secret"


def _load_bridge(name: str):
    spec = importlib.util.spec_from_file_location(f"dsh_bridge_{name}", BRIDGE_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def allowlist():
    return _load_bridge("tool_allowlist")


@pytest.fixture(scope="module")
def roma():
    return _load_bridge("roma_bridge")


@pytest.fixture(scope="module")
def zo():
    return _load_bridge("zo_bridge")


# 1. Unknown names are dropped, never granted.

def test_unknown_tool_is_not_allowed(allowlist, roma):
    resolved = allowlist.resolve_allowed_tools(
        roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, "get_usage,nonexistent_tool"
    )
    assert "nonexistent_tool" not in resolved
    assert allowlist.is_allowed("nonexistent_tool", resolved) is False
    assert allowlist.is_allowed("nonexistent_tool", allowed=frozenset()) is False


def test_unknown_tool_call_is_denied_at_the_bridge(roma):
    reply = asyncio.run(roma.call_tool("nonexistent_tool", {}))
    assert reply[0].text == "Tool not permitted: nonexistent_tool"


# 2. Missing/blank allowlist is read-only, never allow-all.

@pytest.mark.parametrize("raw", [None, "", "   ", ",", "undefined", "null", "NULL"])
def test_missing_or_blank_allowlist_is_read_only_not_allow_all(allowlist, roma, raw):
    resolved = allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, raw)
    assert resolved == frozenset(roma.READ_ONLY_TOOLS)
    assert resolved != frozenset(roma.READ_ONLY_TOOLS | roma.PRIVILEGED_TOOLS)
    assert "submit_job" not in resolved
    assert "cancel_job" not in resolved


def test_wildcard_is_refused_rather_than_expanded(allowlist, roma):
    for raw in ("*", "all", "ALL", "get_usage,*"):
        resolved = allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, raw)
        assert "submit_job" not in resolved
        assert "cancel_job" not in resolved
    assert allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, "*") == frozenset()


def test_default_allowlist_excludes_privileged_tools_in_bridge(roma, zo):
    assert "submit_job" not in roma.ALLOWED_TOOLS
    assert "cancel_job" not in roma.ALLOWED_TOOLS
    assert roma.PRIVILEGED_TOOLS.isdisjoint(roma.ALLOWED_TOOLS)
    assert zo.PRIVILEGED_TOOLS == frozenset()
    assert zo.ALLOWED_TOOLS == frozenset(zo.READ_ONLY_TOOLS)


# 3. Read-only role cannot reach mutating / financial / destructive tools.

def test_read_only_resolution_never_grants_privileged(allowlist, roma):
    read_only_only = ",".join(sorted(roma.READ_ONLY_TOOLS))
    resolved = allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, read_only_only)
    assert resolved == frozenset(roma.READ_ONLY_TOOLS)
    assert roma.PRIVILEGED_TOOLS.isdisjoint(resolved)


def test_mutating_and_financial_tools_are_not_advertised_by_default(roma):
    advertised = {tool.name for tool in asyncio.run(roma.list_tools())}
    assert advertised == set(roma.READ_ONLY_TOOLS)
    assert "submit_job" not in advertised
    assert "cancel_job" not in advertised


def test_privileged_tool_is_denied_even_when_it_exists_in_the_registry(roma):
    assert "submit_job" in roma.PRIVILEGED_TOOLS
    reply = asyncio.run(roma.call_tool("submit_job", {"task": "noop"}))
    assert reply[0].text == "Tool not permitted: submit_job"


def test_privileged_tool_requires_explicit_naming(allowlist, roma):
    resolved = allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, "submit_job")
    assert resolved == frozenset({"submit_job"})
    assert "cancel_job" not in resolved
    assert "get_usage" not in resolved


# 4. An explicitly granted read-only tool keeps working.

def test_explicitly_allowed_read_only_tool_is_permitted(allowlist, roma):
    resolved = allowlist.resolve_allowed_tools(roma.READ_ONLY_TOOLS, roma.PRIVILEGED_TOOLS, "get_usage")
    assert resolved == frozenset({"get_usage"})
    assert allowlist.is_allowed("get_usage", resolved) is True
    assert allowlist.is_allowed("submit_job", resolved) is False


def test_explicitly_allowed_read_only_tool_is_advertised(roma, monkeypatch):
    monkeypatch.setattr(roma, "ALLOWED_TOOLS", frozenset({"get_usage"}))
    advertised = {tool.name for tool in asyncio.run(roma.list_tools())}
    assert advertised == {"get_usage"}


# 5. ROMA_API_KEY: missing / empty / valid.

@pytest.mark.parametrize("raw", [None, "", "   ", "undefined", "null", "NULL"])
def test_roma_api_key_missing_or_empty_is_config_error(roma, raw):
    with pytest.raises(roma.ConfigError) as excinfo:
        roma.resolve_api_key(raw)
    assert "ROMA_API_KEY" in str(excinfo.value)


def test_roma_api_key_valid_is_returned(roma):
    assert roma.resolve_api_key(DUMMY_KEY) == DUMMY_KEY
    assert roma.resolve_api_key(f"  {DUMMY_KEY}  ") == DUMMY_KEY


def test_roma_request_without_key_fails_closed_before_any_http(roma, monkeypatch):
    monkeypatch.delenv("ROMA_API_KEY", raising=False)
    with pytest.raises(roma.ConfigError):
        asyncio.run(roma._roma_request("GET", "/health"))


def test_roma_api_key_error_message_does_not_leak_a_value(roma):
    with pytest.raises(roma.ConfigError) as excinfo:
        roma.resolve_api_key("")
    assert DUMMY_KEY not in str(excinfo.value)


# Regression guard: commands are argument vectors, never shell strings.

def test_zo_bridge_has_no_shell_true_and_executes_argv(zo):
    source = (BRIDGE_DIR / "zo_bridge.py").read_text(encoding="utf-8")
    assert "shell=True" not in source
    assert zo._run_cmd(["echo", "allowlist-probe"])["stdout"] == "allowlist-probe"
    assert zo._run_cmd(["uptime"])["success"] is True


# 6. Denied privileged tools are never executed: no HTTP is attempted.

@pytest.mark.parametrize("tool", ["submit_job", "cancel_job"])
def test_denied_privileged_tool_is_never_executed(roma, monkeypatch, tool):
    attempts: list = []

    async def _spy(*args, **kwargs):
        attempts.append((args, kwargs))
        raise AssertionError(f"{tool} must not issue an HTTP request")

    monkeypatch.setattr(roma, "_roma_request", _spy)

    assert tool not in roma.ALLOWED_TOOLS
    assert tool not in {t.name for t in asyncio.run(roma.list_tools())}

    reply = asyncio.run(roma.call_tool(tool, {"task": "noop"}))
    assert reply[0].text == f"Tool not permitted: {tool}"
    assert attempts == []
