# Installation Instructions

## Quick Start (Recommended)

Since you're on Arch Linux with an externally-managed Python environment, here's the easiest way to get started:

### Step 1: Create a Virtual Environment

```bash
cd /home/dia/workspace/a-mem-sys/A-mem-sys
python -m venv .venv
```

### Step 2: Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -e .
```

This will install the package and all dependencies in your virtual environment.

### Step 4: Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit and add your API key
nano .env
```

Make sure to set:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 5: Run the Server

Now you can run the server in three ways:

**Option A: Using the installed command (recommended)**
```bash
agentic-memory-mcp
```

**Option B: Using the standalone runner**
```bash
python run_mcp_server.py
```

**Option C: Using Python module**
```bash
python -m agentic_memory_mcp.server
```

## Alternative: Without Virtual Environment

If you prefer not to use a virtual environment, you can run the server directly:

### Step 1: Install Dependencies System-Wide (requires sudo)

```bash
# WARNING: This may conflict with system packages
pip install --break-system-packages -e .
```

### Step 2: Run with Python directly

```bash
python run_mcp_server.py
```

## Checking Installation

To verify everything is installed correctly:

```bash
# Activate venv first if you created one
source .venv/bin/activate

# Test import
python -c "from agentic_memory_mcp import MCPMemoryServer; print('✅ Success!')"

# Check that dependencies are installed
python -c "import mcp, pydantic; print('✅ MCP dependencies installed!')"
```

## Running the Server

Once installed, the server will:
1. Load configuration from `.env` file (or environment variables)
2. Initialize the AgenticMemorySystem
3. Start listening for MCP protocol messages on stdin/stdout

The server runs as a stdio-based MCP server, which means it communicates via standard input/output. This is how MCP clients (like Claude Code) connect to it.

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

## Next Steps

- See `SETUP.md` for configuration details
- See `agentic_memory_mcp/README.md` for API documentation
- Try the example: `python examples/mcp_server_example.py`
