#!/bin/bash

# Session start hook to activate A-mem MCP usage
# This runs at the start of every Claude Code session

cat << 'EOF'
⚠️ AGENTIC MEMORY SYSTEM ACTIVE ⚠️

You have PERSISTENT MEMORY via the a-mem MCP server.

🔴 SELF-COMMITMENT WORKFLOW:

BEFORE STARTING ANY TASK, say out loud:
  "Let me check my memory for relevant context..."
Then IMMEDIATELY call search_memories("<keywords>")

AFTER LEARNING SOMETHING NEW (used Read/Grep/Glob), say:
  "I learned something new - saving to memory..."
Then IMMEDIATELY call add_memory_note(content="<what you learned>")

⚠️ EXPLICIT TRIGGERS:
• User asks "how does X work?" → search("X")
• You're about to use Grep/Read → STOP, search memory first
• You just read files to answer a question → save what you learned
• You fixed a bug → save the solution

SKIP SAVING when memory already had the answer (nothing new learned).
EOF
