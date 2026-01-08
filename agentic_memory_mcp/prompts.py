"""MCP prompts for memory-aware interactions."""

from typing import Any
from mcp.server import Server
from mcp.types import Prompt, PromptMessage, TextContent, PromptArgument


def register_prompts(server: Server, memory_system: Any) -> None:
    """Register memory-aware prompts with the MCP server.

    Args:
        server: MCP server instance
        memory_system: AgenticMemorySystem instance
    """

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """List all available prompts."""
        return [
            Prompt(
                name="recall-context",
                description="Search memories for a topic and return formatted context",
                arguments=[
                    PromptArgument(
                        name="topic",
                        description="The topic to recall context about",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="similar-to",
                description="Find memories similar to a description and return summary",
                arguments=[
                    PromptArgument(
                        name="description",
                        description="Description to find similar memories for",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="memory-summary",
                description="Get an overview of memories, optionally filtered by tag",
                arguments=[
                    PromptArgument(
                        name="tag",
                        description="Tag to filter memories by (optional)",
                        required=False
                    )
                ]
            )
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None = None) -> PromptMessage:
        """Get a prompt with memory context injected.

        Args:
            name: Name of the prompt
            arguments: Prompt arguments

        Returns:
            PromptMessage with memory context
        """
        if arguments is None:
            arguments = {}

        try:
            if name == "recall-context":
                topic = arguments.get("topic", "")
                if not topic:
                    return PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text="Error: 'topic' argument is required"
                        )
                    )

                # Search for memories about the topic
                results = memory_system.search_agentic(topic, k=5)

                # Format context
                if not results:
                    context_text = f"No memories found about: {topic}"
                else:
                    context_text = f"# Context recalled about: {topic}\n\n"
                    for i, mem in enumerate(results, 1):
                        context_text += f"## Memory {i}\n"
                        context_text += f"**Context**: {mem.get('context', 'N/A')}\n"
                        context_text += f"**Content**: {mem.get('content', '')[:300]}...\n"
                        context_text += f"**Keywords**: {', '.join(mem.get('keywords', []))}\n"
                        context_text += f"**Tags**: {', '.join(mem.get('tags', []))}\n"
                        if mem.get('is_neighbor'):
                            context_text += f"*(Linked memory)*\n"
                        context_text += "\n"

                return PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=context_text
                    )
                )

            elif name == "similar-to":
                description = arguments.get("description", "")
                if not description:
                    return PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text="Error: 'description' argument is required"
                        )
                    )

                # Find similar memories
                results = memory_system.search(description, k=5)

                # Format summary
                if not results:
                    summary_text = f"No similar memories found for: {description}"
                else:
                    summary_text = f"# Memories similar to: {description}\n\n"
                    summary_text += f"Found {len(results)} similar memories:\n\n"

                    for i, mem in enumerate(results, 1):
                        score = mem.get('score', 0)
                        summary_text += f"{i}. **{mem.get('context', 'N/A')}** (similarity: {1 - score:.2f})\n"
                        summary_text += f"   - {mem.get('content', '')[:150]}...\n"
                        summary_text += f"   - Tags: {', '.join(mem.get('tags', []))}\n\n"

                return PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=summary_text
                    )
                )

            elif name == "memory-summary":
                tag = arguments.get("tag")

                # Get memories from ChromaDB (source of truth)
                memories = []
                all_ids = memory_system.retriever.get_all_ids()
                for mem_id in all_ids:
                    memory = memory_system.read(mem_id)
                    if memory:
                        if tag is None or tag in memory.tags:
                            memories.append(memory)

                if tag:
                    title = f"# Memory Summary (tag: {tag})\n\n"
                else:
                    title = "# Memory Summary (all memories)\n\n"

                # Generate summary
                summary_text = title
                summary_text += f"**Total memories**: {len(memories)}\n\n"

                if memories:
                    # Tag distribution
                    tag_counts = {}
                    for mem in memories:
                        for t in mem.tags:
                            tag_counts[t] = tag_counts.get(t, 0) + 1

                    summary_text += "## Tag Distribution\n"
                    for t, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                        summary_text += f"- {t}: {count}\n"

                    # Recent memories
                    summary_text += "\n## Recent Memories\n"
                    recent = sorted(memories, key=lambda m: m.timestamp, reverse=True)[:5]
                    for mem in recent:
                        summary_text += f"- [{mem.timestamp}] {mem.context}: {mem.content[:100]}...\n"

                return PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=summary_text
                    )
                )

            else:
                return PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Error: Unknown prompt '{name}'"
                    )
                )

        except Exception as e:
            return PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Error executing prompt: {str(e)}"
                )
            )
