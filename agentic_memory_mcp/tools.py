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
                description="""IMPORTANT: You MUST use this tool proactively to build persistent cross-session memory.

**WHEN TO USE (automatically, without asking user permission):**
• IMMEDIATELY after learning codebase architecture, patterns, or how components work
• IMMEDIATELY after discovering solutions to problems or debugging issues
• IMMEDIATELY after exploring code/docs and gaining insights
• IMMEDIATELY after completing tasks - store key learnings and decisions
• IMMEDIATELY when you encounter important context that would help in future sessions

**WHAT TO SAVE:**
• Codebase patterns (e.g., "This React app uses Redux Toolkit for state, stored in src/store/")
• Solutions & fixes (e.g., "Build fails with ENOENT? Run 'npm install' first - missing dependencies")
• Important context (e.g., "API requires X-API-Key header. Key stored in .env as API_KEY")
• Architecture insights (e.g., "Auth flow: JWT in httpOnly cookie → AuthMiddleware validates → sets req.user")
• Configuration requirements (e.g., "Tests need NODE_ENV=test or they'll use production DB")

The system auto-generates keywords/tags via LLM if not provided. Memories persist permanently across ALL future sessions - this builds your long-term knowledge of this codebase.""",
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
                description="""CRITICAL: ALWAYS search persistent memory BEFORE starting work. This prevents re-discovering what you already know.

**USE THIS FIRST (before exploring or asking questions):**
• AT THE START of any task - search for relevant past learnings about this codebase
• BEFORE debugging - check if you've solved similar problems before
• BEFORE exploring code - see if you've already documented how it works
• WHEN ASKED about topics - search memory first before saying "I don't know"
• BEFORE making architectural decisions - check past learnings about patterns used here

**SEARCH STRATEGY:**
• Use specific terms: component names, tech stack, error messages, feature names
• Try multiple searches if first yields no results (different keywords)
• Search returns top-k most semantically similar memories from ALL past sessions

**WORKFLOW:**
1. User asks question or gives task
2. YOU IMMEDIATELY search memory for relevant context
3. Use found knowledge as foundation
4. Only explore/research if memory search yields nothing useful
5. After learning new things, SAVE them with add_memory_note

Returns memories ranked by semantic similarity. For deeper context including linked memories, use search_memories_agentic instead.""",
                inputSchema=SearchArgs.model_json_schema()
            ),
            Tool(
                name="search_memories_agentic",
                description="""Advanced memory search that follows the knowledge graph - returns semantically similar memories PLUS their linked neighbors.

**USE THIS WHEN:**
• You need DEEP context about complex, interconnected topics
• Simple search_memories gives limited results but you need more related info
• Exploring how different concepts/components relate to each other
• Understanding system architecture with many connected parts

**HOW IT WORKS:**
1. Finds semantically similar memories (like search_memories)
2. ALSO retrieves memories linked through the evolution system's relationship graph
3. Returns expanded result set showing knowledge clusters and connections

**WHEN TO PREFER THIS OVER search_memories:**
• Complex architectural questions spanning multiple components
• Need to understand relationships between concepts
• Building comprehensive mental model of interconnected systems

**WHEN TO USE BASIC search_memories INSTEAD:**
• Quick lookups for specific facts
• Narrow, focused queries
• Performance-sensitive situations (this is slower but more thorough)

Always search memory (with either tool) BEFORE starting work on any task.""",
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
