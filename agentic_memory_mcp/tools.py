"""MCP tools for memory operations."""

import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from .background import task_tracker, process_memory_task


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


class CheckTaskStatusArgs(BaseModel):
    """Arguments for checking task status."""
    task_id: str = Field(description="The task ID returned from add_memory_note")


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

**ASYNC BEHAVIOR:** This tool returns immediately (~1ms). Memory processing (LLM analysis, evolution, storage) happens in the background. The response includes a task_id which can be used to check completion status via check_task_status if needed (optional).

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

**RETURN VALUE:**
Returns immediately with:
- status: "queued" (memory will be processed in background)
- task_id: Unique identifier to check task status (optional, only if you need verification)

The system auto-generates keywords/tags via LLM if not provided. Memories persist permanently across ALL future sessions - this builds your long-term knowledge of this codebase.""",
                inputSchema=AddNoteArgs.model_json_schema()
            ),
            Tool(
                name="read_memory_note",
                description="""Read full details of a specific memory by ID.

**WHEN TO USE:**
• After search returns memory IDs - read full details to get complete context
• To see evolution history showing how the memory has been refined over time
• To view linked memories (related concepts the system connected automatically)
• To check retrieval_count and last_accessed metadata

**RETURNS:** Complete memory with content, keywords, tags, context, links, and evolution history.

Use this as a follow-up to search_memories() when you need comprehensive details beyond the search preview.""",
                inputSchema=ReadNoteArgs.model_json_schema()
            ),
            Tool(
                name="update_memory_note",
                description="""Update existing memory when you learn more or need to correct information.

**USE THIS PROACTIVELY WHEN:**
• You discover additional details about something already in memory (e.g., "I stored info about the auth flow, but now found it also handles rate limiting")
• Initial understanding was incomplete or partially incorrect
• You learn edge cases or exceptions to a previously stored pattern
• Context changes (e.g., a dependency was updated, changing how something works)

**IMPORTANT:** Keep memories accurate! Update rather than creating duplicate memories when you learn more about an existing topic.

**WORKFLOW:**
1. Search for existing memory on a topic
2. If found and needs refinement, update it
3. If topic is different enough, create new memory with add_memory_note instead

You can update: content, keywords, tags, or context. Other fields (timestamp, links) are managed automatically.""",
                inputSchema=UpdateNoteArgs.model_json_schema()
            ),
            Tool(
                name="delete_memory_note",
                description="""Delete incorrect or obsolete memories from the knowledge base.

**WHEN TO DELETE:**
• Memory contains completely wrong information that can't be fixed with update
• Information is obsolete (e.g., "Feature X uses deprecated API Y" but Feature X was removed)
• Duplicate memory that serves no purpose (prefer update_memory_note if consolidating)
• Testing/placeholder memory created by accident

**CAUTION:** Prefer update_memory_note over delete when information just needs correction. Only delete when the memory has no salvageable value.

The memory system evolves connections automatically, so removing a memory may affect the knowledge graph.""",
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
            ),
            Tool(
                name="check_task_status",
                description="""Check the status of a background memory task.

**USE THIS ONLY IF:**
• You need to verify that a critical memory has been stored before proceeding with dependent work
• Debugging why a memory might not be appearing in search results yet

**MOST OF THE TIME:** You should fire-and-forget without checking status. The background processing will complete shortly.

**RETURNS:**
- status: "queued" | "processing" | "completed" | "failed"
- task_id: The task identifier
- memory_id: Available when status="completed"
- error: Error message if status="failed"
- created_at, updated_at: Timestamps

Tasks are retained for 1 hour after completion, then automatically cleaned up.""",
                inputSchema=CheckTaskStatusArgs.model_json_schema()
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

                # Create task and return immediately
                task_id = await task_tracker.create_task(args.content, **kwargs)

                # Schedule background processing (fire-and-forget)
                asyncio.create_task(
                    process_memory_task(
                        memory_system,
                        task_id,
                        args.content,
                        **kwargs
                    )
                )

                result = {
                    "status": "queued",
                    "task_id": task_id,
                    "message": "Memory queued for background processing"
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

            elif name == "check_task_status":
                args = CheckTaskStatusArgs(**arguments)
                task = await task_tracker.get_task(args.task_id)

                if task is None:
                    result = {
                        "status": "error",
                        "message": f"Task not found: {args.task_id} (may have expired)"
                    }
                else:
                    result = {
                        "status": task.status,
                        "task_id": task.task_id,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    }
                    if task.memory_id:
                        result["memory_id"] = task.memory_id
                    if task.error:
                        result["error"] = task.error

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
