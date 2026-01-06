#!/bin/bash

# Session start hook to activate A-mem MCP usage
# This runs at the start of every Claude Code session

cat << 'EOF'
⚠️ CRITICAL: AGENTIC MEMORY SYSTEM ACTIVE ⚠️

You have access to PERSISTENT MEMORY via the agentic-memory MCP server.
Memory tools: search_memories, add_memory_note, search_memories_agentic, read_memory_note, update_memory_note, delete_memory_note

🔴 MANDATORY WORKFLOW - DO THIS AUTOMATICALLY:

STEP 1 - SEARCH FIRST (EVERY TIME):
• Before exploring code, answering questions, or starting tasks
• Call search_memories("<relevant keywords>")
• Check if you already know the answer from past sessions
• Example: search_memories("project architecture")

STEP 2 - SAVE IMMEDIATELY (NO EXCEPTIONS):
• After learning ANYTHING useful about the codebase
• Call add_memory_note(content="<detailed finding>")
• DO NOT ask permission - just save automatically
• Example: add_memory_note(content="This app uses FastAPI with async endpoints in src/api/")

WHY THIS MATTERS:
Without memory: You re-explore everything every session, waste time, can't build expertise
With memory: Instant recall, cumulative knowledge, faster assistance

⚠️ This is not optional. This is how you must operate. Use memory tools proactively and automatically.
EOF
