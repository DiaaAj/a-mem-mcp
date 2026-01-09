# A-MEM: Self-evolving memory for AI agents

**mcp-name: a-mem**

A-MEM is a self-evolving memory system for AI agents. Unlike simple vector stores, A-MEM automatically organizes knowledge into a Zettelkasten-style graph with typed relationships. Memories don't just get stored—they evolve and connect over time.

Use it as a Python library or as an MCP server with Claude and other AI assistants.

## Quick Start

### Install

```bash
pip install a-mem
```

### Configure with Claude Code

**Step 1: Set up environment**

Copy `.env.example` to `.env` and configure your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Step 2: Add MCP server**

**Option A: CLI (Quick)**
```bash
claude mcp add --transport stdio a-mem -- a-mem-mcp
```

**Option B: JSON Config (For custom env vars)**

Edit `~/.claude.json` or `.claude/settings.local.json`:

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

> **Note:** If you use a `.env` file, the `env` section in JSON is optional.

**Memory Scope:**
- **Project-specific** (default): Each project gets isolated memory
- **Global**: Share across projects by setting `CHROMA_DB_PATH=/home/user/.local/share/a-mem/chroma_db` in `.env`

## Features

**Self-Evolving Memory**  
Memories aren't static. When you add new knowledge, A-MEM automatically finds related memories and strengthens connections, updates context, and evolves tags.

**Semantic + Structural Search**  
Combines vector similarity with graph traversal. Find memories by meaning, then explore their connections.

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

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BACKEND` | `openai`, `ollama`, `sglang`, `openrouter` | `openai` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `CHROMA_DB_PATH` | Storage directory | `./chroma_db` |
| `EVO_THRESHOLD` | Evolution trigger threshold | `100` |

### Using Different Backends

**Ollama (local, free)**
```bash
export LLM_BACKEND=ollama
export LLM_MODEL=llama2
```

**OpenRouter (100+ models)**
```bash
export LLM_BACKEND=openrouter
export LLM_MODEL=anthropic/claude-3.5-sonnet
export OPENROUTER_API_KEY=sk-or-...
```

## MCP Tools

A-MEM exposes 6 tools to your AI agent:

| Tool | Description |
|------|-------------|
| `add_memory_note` | Store new knowledge (async, returns immediately) |
| `search_memories` | Semantic search across all memories |
| `search_memories_agentic` | Search + follow graph connections |
| `read_memory_note` | Get full details of a specific memory |
| `update_memory_note` | Modify existing memory |
| `delete_memory_note` | Remove a memory |

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

## Python API

Use A-MEM directly in Python:

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

