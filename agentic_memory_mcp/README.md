# Agentic Memory MCP Server

MCP (Model Context Protocol) wrapper for the A-MEM Agentic Memory System. This package exposes the memory system to coding agents and LLM applications via standardized MCP tools, resources, and prompts.

## Features

- **7 MCP Tools**: CRUD operations + 3 types of semantic search
- **3 MCP Resources**: Browse memory state (all, stats, by-tag)
- **3 MCP Prompts**: Memory-aware prompt templates
- **Zero modifications**: Wraps existing `agentic_memory` package without changes
- **Flexible configuration**: Environment variables or code-based config

## Installation

```bash
# Install with MCP dependencies
pip install -e .[mcp]

# Or install all dependencies
pip install mcp pydantic
```

## Quick Start

### Option 1: Using .env File (Recommended)

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Edit .env and add your API key
# LLM_BACKEND=openai
# LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=sk-your-actual-key-here
# EMBEDDING_MODEL=all-MiniLM-L6-v2
# EVO_THRESHOLD=100

# 3. Run the server (automatically loads .env)
agentic-memory-mcp
```

### Option 2: Using Environment Variables

```bash
# Set environment variables
export LLM_BACKEND=openai
export LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-...
export EMBEDDING_MODEL=all-MiniLM-L6-v2

# Run the server
agentic-memory-mcp
```

### Option 3: Python Code

```python
import asyncio
from agentic_memory_mcp import MCPMemoryServer, MCPConfig

async def main():
    # Create config
    config = MCPConfig(
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        api_key="sk-...",  # Or set OPENAI_API_KEY env var
        embedding_model="all-MiniLM-L6-v2",
        evo_threshold=100
    )

    # Run server
    server = MCPMemoryServer(config)
    await server.run()

asyncio.run(main())
```

### Option 4: Load from Environment

```python
from agentic_memory_mcp import MCPMemoryServer, MCPConfig

# Loads from environment variables
config = MCPConfig.from_env()
server = MCPMemoryServer(config)
await server.run()
```

## Available Tools

### CRUD Operations

1. **add_memory_note** - Add new memory (auto-generates metadata via LLM)
   - `content` (required): Memory content
   - `keywords`, `tags`, `context` (optional): Will be auto-generated if not provided

2. **read_memory_note** - Read memory by ID
   - `memory_id` (required): Memory UUID

3. **update_memory_note** - Update memory fields
   - `memory_id` (required): Memory UUID
   - `content`, `keywords`, `tags`, `context` (optional): Fields to update

4. **delete_memory_note** - Delete memory
   - `memory_id` (required): Memory UUID

### Search Operations

5. **search_memories** - Basic semantic search
   - `query` (required): Search query
   - `k` (optional, default=5): Number of results
   - Returns: Direct ChromaDB vector similarity matches

6. **search_memories_agentic** - Expanded search with links
   - `query` (required): Search query
   - `k` (optional, default=5): Number of results
   - Returns: Matches + their linked neighbor memories

7. **find_related_memories** - Formatted for LLM consumption
   - `query` (required): Search query
   - `k` (optional, default=5): Number of results
   - Returns: Tab-separated formatted string + memory IDs

## Available Resources

Access these URIs to browse memory state:

- **memory://all** - View all memories (truncated content)
- **memory://stats** - Statistics (count, evolution, tags)
- **memory://by-tag/{tag}** - Filter by specific tag

## Available Prompts

Memory-aware prompt templates:

1. **recall-context** - Search and format context about a topic
   - Parameter: `topic`

2. **similar-to** - Find and summarize similar memories
   - Parameter: `description`

3. **memory-summary** - Overview of memories
   - Parameter: `tag` (optional)

## Configuration

### Environment Variables

- `LLM_BACKEND` - LLM backend: "openai", "ollama", "sglang", "openrouter" (default: openai)
- `LLM_MODEL` - Model name (default: gpt-4o-mini)
- `OPENAI_API_KEY` - OpenAI API key (for openai backend)
- `OPENROUTER_API_KEY` - OpenRouter API key (for openrouter backend)
- `EMBEDDING_MODEL` - Sentence transformer model (default: all-MiniLM-L6-v2)
- `EVO_THRESHOLD` - Memory evolution threshold (default: 100)
- `SGLANG_HOST` - SGLang host (default: http://localhost)
- `SGLANG_PORT` - SGLang port (default: 30000)

### Supported LLM Backends

1. **OpenAI** (default)
   ```bash
   export LLM_BACKEND=openai
   export LLM_MODEL=gpt-4o-mini
   export OPENAI_API_KEY=sk-...
   ```

2. **Ollama** (local)
   ```bash
   export LLM_BACKEND=ollama
   export LLM_MODEL=llama2
   ```

3. **SGLang** (fast local inference)
   ```bash
   # Start SGLang server first
   python -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct

   export LLM_BACKEND=sglang
   export LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
   export SGLANG_HOST=http://localhost
   export SGLANG_PORT=30000
   ```

4. **OpenRouter** (100+ models)
   ```bash
   export LLM_BACKEND=openrouter
   export LLM_MODEL=openai/gpt-4o-mini
   export OPENROUTER_API_KEY=sk-...
   ```

## Connecting from Coding Agents

### Claude Code

Add to your MCP settings:

```json
{
  "mcpServers": {
    "agentic-memory": {
      "command": "agentic-memory-mcp",
      "env": {
        "LLM_BACKEND": "openai",
        "LLM_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Other MCP Clients

Any MCP-compatible client can connect to the server via stdio transport.

## Usage Flow

1. **Connect** - Agent connects via stdio
2. **Discover** - Agent lists tools, resources, prompts
3. **Add Memories** - Call `add_memory_note` during work
4. **Search** - Use `search_memories*` to recall information
5. **Browse** - Access `memory://stats` for overview
6. **Use Prompts** - Invoke prompts for formatted context

## Architecture

```
agentic_memory_mcp/
├── __init__.py          # Package exports
├── config.py            # Configuration & env loading
├── server.py            # Main MCP server
├── tools.py             # 7 MCP tools
├── resources.py         # 3 MCP resources
└── prompts.py           # 3 MCP prompts
```

The MCP layer is a clean wrapper around the existing `agentic_memory` package with zero modifications to the base implementation.

## License

MIT License - Same as parent A-MEM project
