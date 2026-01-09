"""Main MCP server for Agentic Memory System."""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server

from agentic_memory.memory_system import AgenticMemorySystem
from .config import MCPConfig
from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts
from .background import task_tracker


logger = logging.getLogger(__name__)


class MCPMemoryServer:
    """MCP server wrapper for Agentic Memory System.

    Exposes the memory system via MCP tools, resources, and prompts.
    """

    def __init__(self, config: MCPConfig | None = None):
        """Initialize MCP memory server.

        Args:
            config: Server configuration. If None, loads from environment.
        """
        self.config = config or MCPConfig.from_env()
        self.server = Server(self.config.server_name)
        self.memory_system = self._init_memory_system()

        # Register all MCP components
        register_tools(self.server, self.memory_system)
        register_resources(self.server, self.memory_system)
        register_prompts(self.server, self.memory_system)

        # Background task tracking
        self._cleanup_task = None

        logger.info(f"MCP Memory Server initialized with config: {self.config.to_dict()}")

    def _init_memory_system(self) -> AgenticMemorySystem:
        """Initialize the memory system with configuration.

        Returns:
            Configured AgenticMemorySystem instance
        """
        return AgenticMemorySystem(
            model_name=self.config.embedding_model,
            llm_backend=self.config.llm_backend,
            llm_model=self.config.llm_model,
            evo_threshold=self.config.evo_threshold,
            api_key=self.config.api_key,
            sglang_host=self.config.sglang_host,
            sglang_port=self.config.sglang_port,
            storage_path=self.config.storage_path
        )

    async def run(self) -> None:
        """Run the MCP server via stdio transport.

        This method starts the server and listens for MCP protocol messages
        over stdin/stdout. Also starts background task cleanup.
        """
        logger.info("Starting MCP server via stdio transport...")

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(task_tracker.cleanup_old_tasks())
        logger.info("Started background task cleanup")

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        finally:
            # Cancel cleanup task on shutdown
            if self._cleanup_task:
                logger.info("Shutting down background task cleanup")
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    logger.info("Background cleanup task cancelled successfully")
                    pass


def main():
    """Main entry point for running the MCP server.

    This function can be used as a console script entry point.
    """
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Log to stderr to avoid interfering with stdio transport
    )

    # Auto-install session-start hook on first run
    try:
        from .install_hook import install_hook
        install_hook()
    except Exception as e:
        # Don't fail server startup if hook install fails
        logger.warning(f"Failed to auto-install session-start hook: {e}")

    # Create and run server
    try:
        config = MCPConfig.from_env()
        server = MCPMemoryServer(config)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
