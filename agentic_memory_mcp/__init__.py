"""MCP (Model Context Protocol) wrapper for Agentic Memory System.

This package provides an MCP server that exposes the A-MEM memory system
to coding agents and LLM applications via standardized tools, resources, and prompts.
"""

from .server import MCPMemoryServer
from .config import MCPConfig

__version__ = "0.1.0"
__all__ = ["MCPMemoryServer", "MCPConfig"]
