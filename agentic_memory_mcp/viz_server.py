"""Live memory graph visualization server with WebSocket updates."""

import argparse
import asyncio
import html
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from aiohttp import web, WSMsgType

from agentic_memory.memory_system import AgenticMemorySystem, MemoryNote
from .config import MCPConfig


class MemoryGraphServer:
    """WebSocket server for live memory graph visualization."""

    def __init__(
        self,
        storage_path: str,
        host: str = "localhost",
        port: int = 8765,
        poll_interval: float = 2.0
    ):
        """Initialize the server.

        Args:
            storage_path: Path to ChromaDB storage
            host: Host to bind to
            port: Port to bind to
            poll_interval: Seconds between polling for changes
        """
        self.storage_path = storage_path
        self.host = host
        self.port = port
        self.poll_interval = poll_interval

        self.memory_system: Optional[AgenticMemorySystem] = None
        self.known_ids: Set[str] = set()
        self.known_data: Dict[str, Dict] = {}  # id -> node data for change detection
        self.websockets: Set[web.WebSocketResponse] = set()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Set up HTTP routes."""
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_get("/ws", self._handle_websocket)

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serve the HTML page."""
        template_path = Path(__file__).parent / "templates" / "graph_live.html"
        if template_path.exists():
            return web.Response(
                text=template_path.read_text(),
                content_type="text/html"
            )
        return web.Response(text="Template not found", status=404)

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)

        print(f"WebSocket client connected. Total clients: {len(self.websockets)}")

        try:
            # Send initial graph data
            graph_data = self._get_full_graph()
            await ws.send_json({
                "type": "initial",
                "nodes": graph_data["nodes"],
                "edges": graph_data["edges"]
            })

            # Keep connection alive
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
                    break
                # Client can send ping/pong or requests here if needed

        finally:
            self.websockets.discard(ws)
            print(f"WebSocket client disconnected. Total clients: {len(self.websockets)}")

        return ws

    def _init_memory_system(self):
        """Initialize the memory system."""
        if self.memory_system is None:
            config = MCPConfig.from_env()
            self.memory_system = AgenticMemorySystem(
                storage_path=self.storage_path,
                model_name=config.embedding_model,
                llm_backend=config.llm_backend,
                llm_model=config.llm_model,
                api_key=config.api_key,
                evo_threshold=config.evo_threshold
            )

    def _get_full_graph(self) -> Dict[str, Any]:
        """Get complete graph data."""
        self._init_memory_system()

        all_ids = self.memory_system.retriever.get_all_ids()
        memories = self.memory_system.read_multiple(all_ids)

        nodes = []
        edges = []
        seen_edges: Set[tuple] = set()
        self.known_ids = set()
        self.known_data = {}

        for memory_id, note in memories.items():
            if note is None:
                continue

            self.known_ids.add(memory_id)
            node_data = self._build_node(memory_id, note)
            nodes.append(node_data)
            self.known_data[memory_id] = node_data

        # Build edges
        for memory_id, note in memories.items():
            if note is None:
                continue
            for link_id in (note.links or []):
                if link_id in self.known_ids:
                    edge_key = tuple(sorted([memory_id, link_id]))
                    if edge_key not in seen_edges:
                        edges.append({"from": memory_id, "to": link_id})
                        seen_edges.add(edge_key)

        return {"nodes": nodes, "edges": edges}

    def _build_node(self, memory_id: str, note: MemoryNote) -> Dict[str, Any]:
        """Build node data for a memory."""
        return {
            "id": memory_id,
            "label": self._truncate(note.context or "No context", 35),
            "title": self._build_hover_html(note),
            "group": note.category or "Uncategorized",
            "data": {
                "content": note.content,
                "keywords": note.keywords or [],
                "tags": note.tags or [],
                "context": note.context,
                "category": note.category,
                "timestamp": note.timestamp,
                "last_accessed": note.last_accessed,
                "retrieval_count": note.retrieval_count,
                "links": note.links or [],
                "evolution_history": note.evolution_history or []
            }
        }

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    def _build_hover_html(self, note: MemoryNote) -> str:
        """Build HTML tooltip for node hover."""
        parts = [f"<b>{html.escape(note.context or 'No context')}</b>"]
        if note.keywords:
            keywords_str = ", ".join(note.keywords[:5])
            if len(note.keywords) > 5:
                keywords_str += "..."
            parts.append(f"<br><i>Keywords:</i> {html.escape(keywords_str)}")
        return "".join(parts)

    async def _poll_for_changes(self):
        """Background task to poll for database changes."""
        print(f"Starting change detection (polling every {self.poll_interval}s)")

        while True:
            try:
                await asyncio.sleep(self.poll_interval)

                if not self.websockets:
                    continue  # No clients, skip polling

                self._init_memory_system()
                # Only get IDs - lightweight operation
                current_ids = set(self.memory_system.retriever.get_all_ids())

                added_ids = current_ids - self.known_ids
                removed_ids = self.known_ids - current_ids

                if added_ids or removed_ids:
                    await self._broadcast_changes(added_ids, removed_ids)

            except Exception as e:
                print(f"Error during polling: {e}")

    async def _broadcast_changes(self, added_ids: Set[str], removed_ids: Set[str]):
        """Broadcast changes to all connected clients."""
        if removed_ids:
            # Send removal message
            msg = {
                "type": "remove",
                "nodeIds": list(removed_ids)
            }
            await self._broadcast(msg)
            for rid in removed_ids:
                self.known_ids.discard(rid)
                self.known_data.pop(rid, None)
            print(f"Broadcast removal of {len(removed_ids)} nodes")

        if added_ids:
            # Load new memories
            memories = self.memory_system.read_multiple(list(added_ids))

            new_nodes = []
            new_edges = []
            seen_edges: Set[tuple] = set()

            for memory_id, note in memories.items():
                if note is None:
                    continue

                self.known_ids.add(memory_id)
                node_data = self._build_node(memory_id, note)
                new_nodes.append(node_data)
                self.known_data[memory_id] = node_data

                # Build edges for new node
                for link_id in (note.links or []):
                    if link_id in self.known_ids:
                        edge_key = tuple(sorted([memory_id, link_id]))
                        if edge_key not in seen_edges:
                            new_edges.append({"from": memory_id, "to": link_id})
                            seen_edges.add(edge_key)

            if new_nodes:
                msg = {
                    "type": "add",
                    "nodes": new_nodes,
                    "edges": new_edges
                }
                await self._broadcast(msg)
                print(f"Broadcast addition of {len(new_nodes)} nodes, {len(new_edges)} edges")

    async def _broadcast(self, msg: Dict[str, Any]):
        """Send message to all connected WebSocket clients."""
        if not self.websockets:
            return

        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_json(msg)
            except Exception:
                dead_sockets.add(ws)

        self.websockets -= dead_sockets

    async def start(self, open_browser: bool = True):
        """Start the server."""
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        url = f"http://{self.host}:{self.port}"
        print(f"Live visualization server running at {url}")
        print("Press Ctrl+C to stop")

        if open_browser:
            webbrowser.open(url)

        # Start polling task
        poll_task = asyncio.create_task(self._poll_for_changes())

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass
            await runner.cleanup()


def main():
    """CLI entry point for a-mem-live."""
    parser = argparse.ArgumentParser(
        description="Start live memory graph visualization server",
        prog="a-mem-live"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open browser automatically"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between polling for changes (default: 2.0)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="ChromaDB path (default: from CHROMA_DB_PATH env or ./chroma_db)"
    )

    args = parser.parse_args()

    config = MCPConfig.from_env()
    storage_path = args.db_path or config.storage_path

    print(f"Using database: {storage_path}")

    server = MemoryGraphServer(
        storage_path=storage_path,
        host=args.host,
        port=args.port,
        poll_interval=args.poll_interval
    )

    try:
        asyncio.run(server.start(open_browser=not args.no_open))
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
