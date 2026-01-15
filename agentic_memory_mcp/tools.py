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
    """Arguments for reading one or more memory notes."""
    memory_id: str | None = Field(default=None, description="The ID of the memory to read (for single read)")
    memory_ids: list[str] | None = Field(default=None, description="List of memory IDs to read (for bulk read)")


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


class SearchByTimeArgs(BaseModel):
    """Arguments for time-based memory search."""
    time_from: str | None = Field(
        default=None,
        description="Start time in YYYYMMDDHHMM format (inclusive)"
    )
    time_to: str | None = Field(
        default=None,
        description="End time in YYYYMMDDHHMM format (inclusive)"
    )
    query: str | None = Field(
        default=None,
        description="Optional semantic query to combine with time filter"
    )
    k: int = Field(default=10, description="Maximum results to return")


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
                description="""Save learnings to persistent memory. This builds cross-session knowledge.

**SELF-COMMITMENT:** After exploring code or completing research, say: "I learned something new - saving to memory..." then IMMEDIATELY call this tool. This verbal commitment ensures you don't forget to save.

**EXPLICIT TRIGGERS - Save memory when you just:**
• Used Read tool to understand a file → save what you learned about it
• Used Grep/Glob to find code patterns → save the pattern location
• Fixed a bug or solved an error → save the solution
• Discovered how components connect → save the architecture insight
• Found configuration requirements → save them for next time

**WHAT TO SAVE:**
• Architecture: "Auth flow: JWT in cookie → AuthMiddleware → req.user"
• Locations: "API routes defined in src/api/, use FastAPI"
• Solutions: "ENOENT error? Run npm install first"
• Patterns: "All components use React Query for data fetching"

**SKIP SAVING when:**
• Memory search already had the answer (nothing new learned)
• Information is trivial or obvious
• You only read a file without gaining reusable insight

**ASYNC:** Returns immediately. Processing happens in background.

⚠️ **REMEMBER:** If you used search_memories at the start but then explored code to find the answer, you MUST save what you discovered.""",
                inputSchema=AddNoteArgs.model_json_schema()
            ),
            Tool(
                name="read_memory_note",
                description="""Read full details of one or more memories by ID.

**WHEN TO USE:**
• After search returns memory IDs - read full details to get complete context
• To see evolution history showing how the memory has been refined over time
• To view linked memories (related concepts the system connected automatically)
• To check retrieval_count and last_accessed metadata

**USAGE:**
• Single read: provide `memory_id` - returns the note directly
• Bulk read: provide `memory_ids` list - returns dict mapping each ID to its note

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

**SELF-COMMITMENT:** When you receive a task, FIRST say: "Let me check my memory for relevant context..." then IMMEDIATELY call this tool. This verbal commitment ensures you don't skip the search.

**EXPLICIT TRIGGERS - Search memory when:**
• User asks "how does X work?" → search("X architecture")
• User asks to fix/debug something → search("error X solution")
• User asks about a file/component → search("component-name")
• User asks to implement something → search("similar feature patterns")
• You're about to use Grep/Glob/Read to explore → STOP, search memory first

**SEARCH STRATEGY:**
• Use specific terms: component names, tech stack, error messages, feature names
• Try multiple searches if first yields no results (different keywords)
• Search returns top-k most semantically similar memories from ALL past sessions

**RETURNS:** Metadata only (id, context, keywords, tags, score) - NO full content. Use read_memory_note(memory_id) to get full content for relevant memories.

⚠️ **AFTER COMPLETING WORK:** If you explored code, read files, or discovered anything NEW beyond what memory returned, call add_memory_note() to save it. If memory already had the answer and no new exploration was needed, saving is not required.""",
                inputSchema=SearchArgs.model_json_schema()
            ),
            Tool(
                name="search_memories_agentic",
                description="""Advanced memory search that follows the knowledge graph - returns semantically similar memories PLUS their linked neighbors.

**WHEN TO USE THIS INSTEAD OF search_memories:**
• Complex architectural questions spanning multiple components
• Need to understand relationships between concepts
• Simple search_memories gave limited results but you need more context

**HOW IT WORKS:**
1. Finds semantically similar memories (like search_memories)
2. ALSO retrieves linked memories through the knowledge graph
3. Returns expanded result set showing knowledge clusters

**RETURNS:** Metadata only (id, context, keywords, tags, timestamp, category, is_neighbor, score) - NO full content. Use read_memory_note(memory_id) to get full content.

⚠️ **AFTER COMPLETING WORK:** If you explored code or discovered anything NEW beyond what memory returned, call add_memory_note() to save it.""",
                inputSchema=SearchArgs.model_json_schema()
            ),
            Tool(
                name="search_memories_by_time",
                description="""Search memories within a specific time period.

**IMPORTANT:** You must convert natural language time expressions to YYYYMMDDHHMM format before calling.
Use your knowledge of today's date to calculate the correct timestamps.

**Examples of conversion (assuming today is 2026-01-14):**
• "yesterday" → time_from="202601130000", time_to="202601132359"
• "last week" → time_from="202601070000", time_to="202601132359"
• "last Wednesday" → Calculate that date, e.g. time_from="202601080000", time_to="202601082359"
• "past 3 hours" → time_from=3 hours ago from now, time_to=now
• "this month" → time_from="202601010000", time_to=now
• "December 15th" → time_from="202512150000", time_to="202512152359"

**Parameters:**
• time_from: Start time in YYYYMMDDHHMM format (inclusive)
• time_to: End time in YYYYMMDDHHMM format (inclusive, defaults to now if omitted)
• query: Optional semantic query to filter within the time range
• k: Maximum results (default 10)

**RETURNS:** Memories sorted by recency (newest first). If query is provided, sorted by semantic similarity instead.

**USE CASES:**
• "What did we do yesterday?" → search_memories_by_time(time_from="...", time_to="...")
• "Show me architecture notes from last week" → search_memories_by_time(time_from="...", time_to="...", query="architecture")""",
                inputSchema=SearchByTimeArgs.model_json_schema()
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

                # Determine if single or bulk read
                if args.memory_ids is not None:
                    # Bulk read
                    notes_map = memory_system.read_multiple(args.memory_ids)
                    result = {"status": "success", "notes": {}}

                    for memory_id, note in notes_map.items():
                        if note is None:
                            result["notes"][memory_id] = None
                        else:
                            result["notes"][memory_id] = {
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
                elif args.memory_id is not None:
                    # Single read (existing behavior)
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
                else:
                    result = {
                        "status": "error",
                        "message": "Must provide either memory_id or memory_ids"
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

            elif name == "search_memories_by_time":
                args = SearchByTimeArgs(**arguments)

                # Require at least one time constraint
                if not args.time_from and not args.time_to:
                    result = {
                        "status": "error",
                        "message": "Must provide at least one of time_from or time_to"
                    }
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                # Execute search
                results = memory_system.search_by_time(
                    time_from=args.time_from,
                    time_to=args.time_to,
                    query=args.query,
                    k=args.k
                )

                result = {
                    "status": "success",
                    "count": len(results),
                    "time_range": {
                        "from": args.time_from,
                        "to": args.time_to
                    },
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
