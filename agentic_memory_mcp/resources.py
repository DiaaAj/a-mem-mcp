"""MCP resources for browsing memory state."""

import json
from typing import Any
from mcp.server import Server
from mcp.types import Resource, TextContent


def register_resources(server: Server, memory_system: Any) -> None:
    """Register memory resources with the MCP server.

    Args:
        server: MCP server instance
        memory_system: AgenticMemorySystem instance
    """

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List all available memory resources."""
        return [
            Resource(
                uri="memory://usage-guide",
                name="Memory System Usage Guide",
                mimeType="text/markdown",
                description="Guide for AI agents on when and how to use the agentic memory system proactively"
            ),
            Resource(
                uri="memory://all",
                name="All Memories",
                mimeType="application/json",
                description="View all memories in the system (with truncated content for overview)"
            ),
            Resource(
                uri="memory://stats",
                name="Memory Statistics",
                mimeType="application/json",
                description="View memory system statistics (total count, evolution count, tag distribution)"
            ),
            Resource(
                uri="memory://by-tag/{tag}",
                name="Memories by Tag",
                mimeType="application/json",
                description="View memories filtered by a specific tag"
            )
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a memory resource.

        Args:
            uri: Resource URI to read

        Returns:
            JSON string with resource contents
        """
        try:
            if uri == "memory://usage-guide":
                # Return usage guide for AI agents
                guide = """# Agentic Memory System - Usage Guide for AI Agents

## What is this?

This is a **persistent, cross-session knowledge base** that stores memories permanently. Unlike conversation context which resets each session, memories stored here persist forever and can be retrieved in any future session.

## When to Store Memories (PROACTIVELY)

### Always store memories when you:

1. **Learn about codebase architecture**
   - Component structure and relationships
   - Design patterns and conventions
   - How different parts of the system work together

2. **Solve problems or debug issues**
   - Solutions to bugs and how you fixed them
   - Error patterns and their resolutions
   - Workarounds for limitations

3. **Discover important context**
   - API usage patterns
   - Configuration requirements
   - Dependencies and their purposes
   - Environment-specific quirks

4. **Complete significant tasks**
   - Implementation approaches that worked well
   - Key decisions made and why
   - Lessons learned from the implementation

5. **Explore code or documentation**
   - Understanding of how specific modules work
   - Purpose of specific files or functions
   - Documentation insights

## When to Search Memories (BEFORE ACTING)

### Search BEFORE you:

1. **Start working on a codebase**
   - Search for past learnings about this project
   - Check if you've explored similar code before

2. **Encounter a problem**
   - Search if you've solved something similar
   - Look for related debugging experiences

3. **Need context**
   - Search for specific topics, components, or patterns
   - Find accumulated knowledge instead of re-exploring

## Best Practices

### Good Memory Content
✅ Specific and detailed: "The authentication flow in this app uses JWT tokens stored in httpOnly cookies. The AuthMiddleware validates tokens on every API request by checking the signature against the SECRET_KEY environment variable."

❌ Too vague: "This app uses authentication"

### Memory Granularity
- Store one coherent concept per memory
- Break complex topics into multiple related memories
- Let the evolution system link related memories automatically

### Memory Evolution
The system automatically:
- Links related memories together
- Updates tags and context as new memories are added
- Builds a knowledge graph of interconnected concepts

## Tool Usage

- **add_memory_note**: Store new learnings (use proactively!)
- **search_memories**: Find relevant past knowledge (use before starting work!)
- **search_memories_agentic**: Deep search including linked memories
- **read_memory_note**: Get full details of a specific memory
- **update_memory_note**: Refine memories with new information
- **delete_memory_note**: Remove incorrect/obsolete memories

## Example Workflow

1. User: "Help me understand the authentication system"
2. **FIRST**: Search for existing memories about authentication
3. If found: Use that knowledge as starting point
4. If not found: Explore the code
5. **AFTER exploring**: Store your findings as memories
6. Continue with the task using accumulated knowledge

## Remember

This is YOUR long-term memory. Use it actively to build up knowledge over time. Each memory makes future sessions more effective!
"""
                return guide

            elif uri == "memory://all":
                # Return all memories with truncated content
                all_memories = []
                for mem_id, memory in memory_system.memories.items():
                    # Truncate long content
                    content = memory.content
                    if len(content) > 200:
                        content = content[:200] + "..."

                    mem_dict = {
                        "id": memory.id,
                        "content": content,
                        "keywords": memory.keywords,
                        "tags": memory.tags,
                        "context": memory.context,
                        "timestamp": memory.timestamp,
                        "retrieval_count": memory.retrieval_count
                    }
                    all_memories.append(mem_dict)

                result = {
                    "total_memories": len(all_memories),
                    "memories": all_memories
                }
                return json.dumps(result, indent=2)

            elif uri == "memory://stats":
                # Return statistics
                total = len(memory_system.memories)

                # Count tag distribution
                tag_counts = {}
                for memory in memory_system.memories.values():
                    for tag in memory.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

                result = {
                    "total_memories": total,
                    "evolution_count": memory_system.evo_cnt,
                    "evolution_threshold": memory_system.evo_threshold,
                    "tag_distribution": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))
                }
                return json.dumps(result, indent=2)

            elif uri.startswith("memory://by-tag/"):
                # Extract tag from URI
                tag = uri.split("/")[-1]

                # Filter memories by tag
                matching = []
                for memory in memory_system.memories.values():
                    if tag in memory.tags:
                        # Truncate long content
                        content = memory.content
                        if len(content) > 200:
                            content = content[:200] + "..."

                        matching.append({
                            "id": memory.id,
                            "content": content,
                            "keywords": memory.keywords,
                            "tags": memory.tags,
                            "context": memory.context,
                            "timestamp": memory.timestamp
                        })

                result = {
                    "tag": tag,
                    "count": len(matching),
                    "memories": matching
                }
                return json.dumps(result, indent=2)

            else:
                return json.dumps({
                    "error": f"Unknown resource URI: {uri}"
                })

        except Exception as e:
            return json.dumps({
                "error": f"Resource read error: {str(e)}"
            })
