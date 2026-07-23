#!/usr/bin/env python3
"""
sbs — CLI entry point wrapper.
Passes sys.argv to the Typer app so 'sbs --version' etc. work as [project.scripts].
"""
import sys

from sbs.cli import app

app(sys.argv[1:] if len(sys.argv) > 1 else ["--version"])
