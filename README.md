# A-MEM: Self-evolving memory for coding agents

<p align="center">
  <a href="https://pypi.org/project/a-mem/"><img src="https://img.shields.io/pypi/v/a-mem" alt="PyPI version"></a>
  <a href="https://pypi.org/project/a-mem/"><img src="https://img.shields.io/pypi/dm/a-mem" alt="PyPI downloads"></a>
  <a href="https://registry.modelcontextprotocol.io/?q=io.github.DiaaAj%2Fa-mem-mcp"><img src="https://img.shields.io/badge/MCP-Registry-blue" alt="MCP Registry"></a>
</p>

**mcp-name: io.github.DiaaAj/a-mem-mcp**

A-MEM is a self-evolving memory system for coding agents. Unlike simple vector stores, A-MEM automatically organizes knowledge into a Zettelkasten-style graph with dynamic relationships. Memories don't just get stored—they evolve and connect over time.

Currently tested with **Claude Code**. Support for other MCP-compatible agents is planned.

<img src="/Figure/demo.gif">

## Quick Start

### Install

```bash
pip install a-mem
```

### Add to Claude Code

```bash
claude mcp add a-mem -s user -- a-mem-mcp \
  -e LLM_BACKEND=openai \
  -e LLM_MODEL=gpt-4o-mini \
  -e OPENAI_API_KEY=sk-...
```

That's it! A session-start hook installs automatically to remind Claude to use memory.

> **Note:** Memory is stored per-project in `./chroma_db`. For global memory across all projects, see [Memory Scope](#memory-scope).

### Uninstall

```bash
a-mem-uninstall-hook   # Remove hooks first
pip uninstall a-mem
```

## How It Works

```
t=0              t=1                t=2

                 ◉───◉             ◉───◉
 ◉               │                 ╱ │ ╲
                 ◉                ◉──┼──◉
                                     │
                                     ◉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶
            self-evolving memory
```

1. **Add a memory** → A-MEM extracts keywords, context, and tags via LLM
2. **Find neighbors** → Searches for semantically similar existing memories
3. **Evolve** → Decides whether to link, strengthen connections, or update related memories
4. **Store** → Persists to ChromaDB with full metadata and relationships

The result: a knowledge graph that grows smarter over time, not just bigger.

## Features

**Self-Evolving Memory**
Memories aren't static. When you add new knowledge, A-MEM automatically finds related memories and strengthens connections, updates context, and evolves tags.

**Semantic + Structural Search**
Combines vector similarity with graph traversal. Find memories by meaning, then explore their connections.

**Peek and Drill**
Start with breadth-first search to capture relevant memories via lightweight metadata (id, context, keywords, tags). Then drill depth-first into specific memories with `read_memory_note` for full content. This minimizes token usage while maximizing recall.

## MCP Tools

A-MEM exposes 8 tools to your coding agent:

| Tool | Description |
|------|-------------|
| `add_memory_note` | Store new knowledge (async, returns immediately) |
| `search_memories` | Semantic search across all memories |
| `search_memories_agentic` | Search + follow graph connections |
| `search_memories_by_time` | Search within a time range |
| `read_memory_note` | Get full details (supports bulk reads) |
| `update_memory_note` | Modify existing memory |
| `delete_memory_note` | Remove a memory |
| `check_task_status` | Check async task completion |

### Example Usage

```python
# The agent calls these automatically, but here's what happens:

# Store a memory (returns task_id immediately)
add_memory_note(content="Auth uses JWT in httpOnly cookies, validated by AuthMiddleware")

# Search later
search_memories(query="authentication flow", k=5)

# Deep search with connections
search_memories_agentic(query="security", k=5)
```

## Advanced Configuration

### JSON Config

For more control, edit `~/.claude/settings.json` (global) or `.claude/settings.local.json` (project):

```json
{
  "mcpServers": {
    "a-mem": {
      "command": "a-mem-mcp",
      "env": {
        "LLM_BACKEND": "openai",
        "LLM_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BACKEND` | `openai`, `ollama`, `sglang`, `openrouter` | `openai` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `CHROMA_DB_PATH` | Storage directory | `./chroma_db` |
| `EVO_THRESHOLD` | Evolution trigger threshold | `100` |

### Memory Scope

- **Project-specific** (default): Each project gets isolated memory in `./chroma_db`
- **Global**: Share across projects by setting `CHROMA_DB_PATH=~/.local/share/a-mem/chroma_db`

### Alternative Backends

**Ollama (local, free)**
```bash
claude mcp add a-mem -s user -- a-mem-mcp \
  -e LLM_BACKEND=ollama \
  -e LLM_MODEL=llama2
```

**OpenRouter (100+ models)**
```bash
claude mcp add a-mem -s user -- a-mem-mcp \
  -e LLM_BACKEND=openrouter \
  -e LLM_MODEL=anthropic/claude-3.5-sonnet \
  -e OPENROUTER_API_KEY=sk-or-...
```

### Hook Management (Claude Code)

The session-start hook reminds Claude to use memory tools. It installs automatically with Claude Code, but you can manage it manually:

```bash
a-mem-install-hook     # Install/reinstall hook
a-mem-uninstall-hook   # Remove hook completely
```

## Python API

Use A-MEM directly in Python (works with any agent or application):

```python
from agentic_memory.memory_system import AgenticMemorySystem

memory = AgenticMemorySystem(
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Add (auto-generates keywords, tags, context)
memory_id = memory.add_note("FastAPI app uses dependency injection for DB sessions")

# Search
results = memory.search("database patterns", k=5)

# Read full details
note = memory.read(memory_id)
print(note.keywords, note.tags, note.links)
```

## Research

A-MEM implements concepts from the paper:

> **A-MEM: Agentic Memory for LLM Agents**
> Xu et al., 2025
> [arXiv:2502.12110](https://arxiv.org/pdf/2502.12110)
