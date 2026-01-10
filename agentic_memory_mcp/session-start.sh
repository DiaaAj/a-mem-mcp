#!/bin/bash

# Session start hook to activate A-mem MCP usage
# This runs at the start of every Claude Code session

cat << 'EOF'
⚠️ AGENTIC MEMORY SYSTEM ACTIVE ⚠️

You have access to PERSISTENT MEMORY via MCP tools (prefix: mcp__a-mem__).

Available MCP tools:
• mcp__a-mem__search_memories - Search before exploring code
• mcp__a-mem__add_memory_note - Save learnings immediately
• mcp__a-mem__search_memories_agentic - Deep search with graph connections
• mcp__a-mem__read_memory_note - Read full memory details
• mcp__a-mem__update_memory_note - Update existing memories
• mcp__a-mem__delete_memory_note - Remove memories

🔴 MANDATORY WORKFLOW:

1. SEARCH FIRST: Before exploring code or answering questions, call:
   mcp__a-mem__search_memories(query="<relevant keywords>")

2. SAVE LEARNINGS: After discovering anything useful, call:
   mcp__a-mem__add_memory_note(content="<what you learned>")

Do this automatically without asking permission.
EOF
