#!/usr/bin/env python3
"""
Standalone runner for the MCP Memory Server.

This script can be run directly without installing the package.
Just make sure you have the dependencies installed in your environment.

Usage:
    python run_mcp_server.py

    Or with virtual environment:
    .venv/bin/python run_mcp_server.py
"""

import sys
import os

# Add current directory to path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the server
from agentic_memory_mcp.server import main

if __name__ == "__main__":
    main()
