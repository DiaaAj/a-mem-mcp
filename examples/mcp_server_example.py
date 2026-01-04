"""Example usage of the MCP Memory Server.

This script demonstrates how to configure and run the MCP server
for the Agentic Memory System.
"""

import asyncio
from agentic_memory_mcp import MCPMemoryServer, MCPConfig


async def run_with_explicit_config():
    """Run server with explicit configuration."""
    print("Running MCP server with explicit configuration...")

    config = MCPConfig(
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        embedding_model="all-MiniLM-L6-v2",
        evo_threshold=100,
        server_name="agentic-memory"
    )

    server = MCPMemoryServer(config)
    await server.run()


async def run_with_env_config():
    """Run server with environment-based configuration.

    Set these environment variables before running:
        export LLM_BACKEND=openai
        export LLM_MODEL=gpt-4o-mini
        export OPENAI_API_KEY=sk-...
        export EMBEDDING_MODEL=all-MiniLM-L6-v2
        export EVO_THRESHOLD=100
    """
    print("Running MCP server with environment configuration...")

    config = MCPConfig.from_env()
    print(f"Loaded config: {config.to_dict()}")

    server = MCPMemoryServer(config)
    await server.run()


def main():
    """Main entry point.

    Choose which configuration method to use.
    """
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--env":
        # Load from environment
        asyncio.run(run_with_env_config())
    else:
        # Use explicit config (requires OPENAI_API_KEY in environment)
        asyncio.run(run_with_explicit_config())


if __name__ == "__main__":
    """
    Usage:
        # With explicit config (still needs OPENAI_API_KEY in env):
        python examples/mcp_server_example.py

        # With environment config:
        export LLM_BACKEND=openai
        export LLM_MODEL=gpt-4o-mini
        export OPENAI_API_KEY=sk-...
        python examples/mcp_server_example.py --env

        # Or use the installed console script:
        agentic-memory-mcp
    """
    main()
