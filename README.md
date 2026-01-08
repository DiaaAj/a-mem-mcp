# Agentic Memory

A persistent memory system for LLM agents with automatic knowledge organization, semantic linking, and intelligent evolution powered by ChromaDB and LLM-driven metadata generation.

## Installation

```bash
pip install agentic-memory
```

Configure your environment:
```bash
# Create .env file or set environment variables
export LLM_BACKEND=openai
export LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=sk-...
export EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Quick Start

### As MCP Server (with Claude Code)

Add to your `.claude/settings.local.json`:
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

### As Python Library

```python
from agentic_memory.memory_system import AgenticMemorySystem

# Initialize
memory = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Add memories (auto-generates keywords, tags, context via LLM)
memory_id = memory.add_note("Neural networks process data through layers")

# Search semantically
results = memory.search("machine learning", k=5)

# Update and delete
memory.update(memory_id, content="Updated content")
memory.delete(memory_id)
```

## MCP Tools

When used as an MCP server, provides 6 tools to Claude:

| Tool | Description |
|------|-------------|
| `add_memory_note` | Store new knowledge with auto-generated metadata |
| `search_memories` | Semantic vector search through memories |
| `search_memories_agentic` | Graph-traversal search following memory links |
| `read_memory_note` | Retrieve full memory by ID |
| `update_memory_note` | Modify existing memories |
| `delete_memory_note` | Remove memories |

## Key Features

**Automatic Metadata Generation**
- LLM analyzes content to extract keywords, tags, and context
- No manual categorization required
- Supports partial metadata provision

**Intelligent Memory Evolution**
- Automatically links related memories
- Updates tags and context based on relationships
- Builds interconnected knowledge graphs

**Enhanced Semantic Search**
- Vector embeddings using content + metadata
- ChromaDB for fast similarity search
- Multiple search modes (basic, agentic with graph traversal)

**Flexible LLM Backends**
- OpenAI (GPT-4, GPT-4o-mini)
- Ollama (local deployment)
- SGLang (fast local inference)
- OpenRouter (100+ models)

**Persistent Storage**
- ChromaDB for vector storage
- Configurable storage path
- Project-specific or global memory scopes

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BACKEND` | LLM backend: openai, ollama, sglang, openrouter | openai |
| `LLM_MODEL` | Model name | gpt-4o-mini |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |
| `CHROMA_DB_PATH` | Storage directory path | ./chroma_db |
| `EVO_THRESHOLD` | Memory evolution threshold | 100 |
| `SGLANG_HOST` | SGLang server host | http://localhost |
| `SGLANG_PORT` | SGLang server port | 30000 |

### Memory Scope

**Project-Specific** (default):
```bash
export CHROMA_DB_PATH=./chroma_db
```
Each project gets isolated memory storage.

**Global** (shared across projects):
```bash
export CHROMA_DB_PATH=/home/user/.local/share/agentic-memory/chroma_db
```
All projects share the same memory database.

## LLM Backend Examples

### OpenAI
```python
memory = AgenticMemorySystem(
    llm_backend="openai",
    llm_model="gpt-4o-mini",
    model_name="all-MiniLM-L6-v2"
)
```

### Ollama (Local)
```python
memory = AgenticMemorySystem(
    llm_backend="ollama",
    llm_model="llama2",
    model_name="all-MiniLM-L6-v2"
)
```

### SGLang (Fast Local)
```bash
# Start server
python -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct
```
```python
memory = AgenticMemorySystem(
    llm_backend="sglang",
    llm_model="meta-llama/Llama-3.1-8B-Instruct",
    sglang_host="http://localhost",
    sglang_port=30000,
    model_name="all-MiniLM-L6-v2"
)
```

### OpenRouter (Multi-Provider)
```python
memory = AgenticMemorySystem(
    llm_backend="openrouter",
    llm_model="openai/gpt-4o-mini",
    api_key="sk-or-...",
    model_name="all-MiniLM-L6-v2"
)
```

## How It Works

1. **Add Memory**: Content is analyzed by LLM to generate keywords, tags, and context
2. **Enhanced Embedding**: Vector embeddings include both content and metadata
3. **Storage**: Memories stored in ChromaDB with rich semantic information
4. **Evolution**: System finds related memories and creates bidirectional links
5. **Search**: Semantic search uses enhanced embeddings for superior retrieval

## Research Paper

For more details, see our paper: [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110)

To reproduce research results, visit: [https://github.com/WujiangXu/AgenticMemory](https://github.com/WujiangXu/AgenticMemory)

## Citation

```bibtex
@article{xu2025mem,
  title={A-mem: Agentic memory for llm agents},
  author={Xu, Wujiang and Liang, Zujie and Mei, Kai and Gao, Hang and Tan, Juntao and Zhang, Yongfeng},
  journal={arXiv preprint arXiv:2502.12110},
  year={2025}
}
```

## License

MIT License - See LICENSE for details.
