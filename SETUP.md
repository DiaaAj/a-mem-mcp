# Quick Setup Guide for A-MEM MCP Server

This guide will get you up and running with the Agentic Memory MCP server in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (or access to another LLM backend)

## Installation

### 1. Install the Package

```bash
cd /home/dia/workspace/a-mem-sys/A-mem-sys
pip install -e .
```

This will install all dependencies including:
- The base `agentic_memory` package
- The MCP wrapper `agentic_memory_mcp`
- All required dependencies (mcp, pydantic, python-dotenv, etc.)

### 2. Configure Environment Variables

**Option A: Using .env file (Recommended)**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Edit these lines in `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

**Option B: Export environment variables**

```bash
export OPENAI_API_KEY=sk-your-actual-key-here
export LLM_BACKEND=openai
export LLM_MODEL=gpt-4o-mini
```

### 3. Test the Installation

Run a quick test to make sure everything is working:

```bash
# Test import
python -c "from agentic_memory_mcp import MCPMemoryServer, MCPConfig; print('✅ Installation successful!')"
```

### 4. Run the MCP Server

```bash
# Run via console script
agentic-memory-mcp
```

Or run the example:

```bash
python examples/mcp_server_example.py
```

The server will start and listen for MCP protocol messages via stdin/stdout.

## Connecting to Claude Code

To use this MCP server with Claude Code, add it to your MCP configuration:

**Location**: `~/.config/claude/mcp_config.json` (or your IDE's MCP config)

```json
{
  "mcpServers": {
    "agentic-memory": {
      "command": "agentic-memory-mcp",
      "args": [],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

Or if using `.env` file:

```json
{
  "mcpServers": {
    "agentic-memory": {
      "command": "agentic-memory-mcp",
      "args": []
    }
  }
}
```

## Verify It's Working

Once connected to Claude Code, you should see these MCP capabilities:

**Tools** (7):
- add_memory_note
- read_memory_note
- update_memory_note
- delete_memory_note
- search_memories
- search_memories_agentic
- find_related_memories

**Resources** (3):
- memory://all
- memory://stats
- memory://by-tag/{tag}

**Prompts** (3):
- recall-context
- similar-to
- memory-summary

## Basic Usage

### From Claude Code

Ask Claude to:
- "Add a memory about the authentication system we just built"
- "Search memories for information about database schemas"
- "Show me memory stats"
- "Recall context about the API endpoints"

### Programmatically (Python)

```python
from agentic_memory_mcp import MCPMemoryServer, MCPConfig

# Your code here - see examples/mcp_server_example.py
```

## Troubleshooting

### "Module not found" error

Make sure you installed with `-e .`:
```bash
pip install -e .
```

### "API key not found" error

Check your environment variables:
```bash
echo $OPENAI_API_KEY
```

Or verify `.env` file exists and contains your key:
```bash
cat .env | grep OPENAI_API_KEY
```

### MCP server not responding

Check logs (stderr output):
- Server initialization messages
- Configuration loaded
- Any error messages

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
agentic-memory-mcp
```

## Alternative LLM Backends

### Using Ollama (Free, Local)

```bash
# In .env or export
LLM_BACKEND=ollama
LLM_MODEL=llama2
# No API key needed!
```

### Using SGLang (Fast Local Inference)

```bash
# Terminal 1: Start SGLang server
python -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct

# Terminal 2: Configure and run MCP server
export LLM_BACKEND=sglang
export LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
agentic-memory-mcp
```

### Using OpenRouter (100+ Models)

```bash
# In .env or export
LLM_BACKEND=openrouter
LLM_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=sk-or-your-key-here
```

## Next Steps

- Read the full documentation in `agentic_memory_mcp/README.md`
- Explore examples in `examples/`
- Check the original A-MEM paper: https://arxiv.org/pdf/2502.12110
- Experiment with different search methods (basic, agentic, find_related)

## Getting Help

If you run into issues:
1. Check the logs (stderr output)
2. Verify your environment variables
3. Test with a simple example
4. Check the GitHub issues: https://github.com/agiresearch/A-mem/issues

Happy memory managing! 🧠
