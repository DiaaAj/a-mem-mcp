"""MCP tools for memory operations."""

import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field


class AddNoteArgs(BaseModel):
    """Arguments for adding a memory note."""
    content: str = Field(description="The content of the memory note")
    keywords: list[str] | None = Field(default=None, description="Keywords for the memory (optional, auto-generated if not provided)")
    tags: list[str] | None = Field(default=None, description="Tags for categorization (optional, auto-generated if not provided)")
    context: str | None = Field(default=None, description="Context description (optional, auto-generated if not provided)")
    timestamp: str | None = Field(default=None, description="Timestamp in format YYYYMMDDHHMM (optional, auto-generated if not provided)")


class ReadNoteArgs(BaseModel):
    """Arguments for reading a memory note."""
    memory_id: str = Field(description="The ID of the memory to read")


class UpdateNoteArgs(BaseModel):
    """Arguments for updating a memory note."""
    memory_id: str = Field(description="The ID of the memory to update")
    content: str | None = Field(default=None, description="New content (optional)")
    keywords: list[str] | None = Field(default=None, description="New keywords (optional)")
    tags: list[str] | None = Field(default=None, description="New tags (optional)")
    context: str | None = Field(default=None, description="New context (optional)")


class DeleteNoteArgs(BaseModel):
    """Arguments for deleting a memory note."""
    memory_id: str = Field(description="The ID of the memory to delete")


class SearchArgs(BaseModel):
    """Arguments for searching memories."""
    query: str = Field(description="Search query text")
    k: int = Field(default=5, description="Number of results to return (default: 5)")


def register_tools(server: Server, memory_system: Any) -> None:
    """Register all memory operation tools with the MCP server.

    Args:
        server: MCP server instance
        memory_system: AgenticMemorySystem instance
    """

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available memory tools."""
        return [
            Tool(
                name="add_memory_note",
                description="""Add a memory note to the persistent knowledge base. This memory persists across all sessions.

USE THIS PROACTIVELY when you:
- Learn something new about a codebase (architecture, patterns, how things work)
- Discover solutions to problems or debug issues
- Gain insights from exploring code or documentation
- Complete a significant task and want to remember key learnings
- Encounter important context that would be valuable later

The memory system auto-generates keywords, tags, and context via LLM if not provided. Memories are stored permanently and searchable across all future sessions.""",
                inputSchema=AddNoteArgs.model_json_schema()
            ),
            Tool(
                name="read_memory_note",
                description="Read a specific memory note by its ID. Use this when you have a memory ID from search results and want to see full details including links and evolution history.",
                inputSchema=ReadNoteArgs.model_json_schema()
            ),
            Tool(
                name="update_memory_note",
                description="Update an existing memory note's content or metadata. Use this when you discover new information that refines or corrects a previously stored memory.",
                inputSchema=UpdateNoteArgs.model_json_schema()
            ),
            Tool(
                name="delete_memory_note",
                description="Delete a memory note by its ID. Use this to remove incorrect or obsolete memories from the knowledge base.",
                inputSchema=DeleteNoteArgs.model_json_schema()
            ),
            Tool(
                name="search_memories",
                description="""Search the persistent memory knowledge base using semantic similarity.

USE THIS to recall information from previous sessions:
- Before starting work on a codebase, search for relevant past learnings
- When encountering a problem, check if you've solved something similar before
- To find context about specific topics, components, or patterns
- To leverage accumulated knowledge instead of re-exploring

Returns memories ranked by semantic similarity. For related memories with graph connections, use search_memories_agentic instead.""",
                inputSchema=SearchArgs.model_json_schema()
            ),
            Tool(
                name="search_memories_agentic",
                description="""Search memories and include their linked neighbors (expanded agentic search through the knowledge graph).

This returns not just semantically similar memories, but also memories that are connected through the evolution system's relationship graph. Use this when you want deeper context and related information beyond simple keyword matching.

Best for: Understanding complex topics with interconnected concepts, exploring knowledge clusters.""",
                inputSchema=SearchArgs.model_json_schema()
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls.

        Args:
            name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            if name == "add_memory_note":
                args = AddNoteArgs(**arguments)
                kwargs = {}
                if args.keywords is not None:
                    kwargs['keywords'] = args.keywords
                if args.tags is not None:
                    kwargs['tags'] = args.tags
                if args.context is not None:
                    kwargs['context'] = args.context
                if args.timestamp is not None:
                    kwargs['time'] = args.timestamp

                memory_id = memory_system.add_note(content=args.content, **kwargs)

                result = {
                    "status": "success",
                    "memory_id": memory_id,
                    "message": "Memory note added successfully"
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "read_memory_note":
                args = ReadNoteArgs(**arguments)
                note = memory_system.read(args.memory_id)

                if note is None:
                    result = {
                        "status": "error",
                        "message": f"Memory not found: {args.memory_id}"
                    }
                else:
                    result = {
                        "status": "success",
                        "note": {
                            "id": note.id,
                            "content": note.content,
                            "keywords": note.keywords,
                            "tags": note.tags,
                            "context": note.context,
                            "timestamp": note.timestamp,
                            "last_accessed": note.last_accessed,
                            "links": note.links,
                            "retrieval_count": note.retrieval_count,
                            "category": note.category,
                            "evolution_history": note.evolution_history
                        }
                    }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "update_memory_note":
                args = UpdateNoteArgs(**arguments)
                update_fields = {}
                if args.content is not None:
                    update_fields['content'] = args.content
                if args.keywords is not None:
                    update_fields['keywords'] = args.keywords
                if args.tags is not None:
                    update_fields['tags'] = args.tags
                if args.context is not None:
                    update_fields['context'] = args.context

                success = memory_system.update(args.memory_id, **update_fields)

                result = {
                    "status": "success" if success else "error",
                    "message": "Memory updated successfully" if success else f"Memory not found: {args.memory_id}"
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "delete_memory_note":
                args = DeleteNoteArgs(**arguments)
                success = memory_system.delete(args.memory_id)

                result = {
                    "status": "success" if success else "error",
                    "message": "Memory deleted successfully" if success else f"Memory not found: {args.memory_id}"
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "search_memories":
                args = SearchArgs(**arguments)
                results = memory_system.search(args.query, k=args.k)

                result = {
                    "status": "success",
                    "count": len(results),
                    "results": results
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "search_memories_agentic":
                args = SearchArgs(**arguments)
                results = memory_system.search_agentic(args.query, k=args.k)

                result = {
                    "status": "success",
                    "count": len(results),
                    "results": results
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            else:
                result = {
                    "status": "error",
                    "message": f"Unknown tool: {name}"
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            result = {
                "status": "error",
                "message": f"Tool execution error: {str(e)}"
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
