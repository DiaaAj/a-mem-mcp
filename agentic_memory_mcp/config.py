"""Configuration for MCP Memory Server."""

from dataclasses import dataclass, field
from typing import Optional, Literal
import os

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use existing environment variables


@dataclass
class MCPConfig:
    """Configuration for MCP server and memory system.

    Attributes:
        llm_backend: LLM backend to use ("openai", "ollama", "sglang", "openrouter")
        llm_model: Name of the LLM model (e.g., "gpt-4o-mini")
        api_key: API key for the LLM service (optional, can use env var)
        embedding_model: Sentence transformer model for embeddings
        evo_threshold: Number of memories before triggering evolution
        server_name: Name of the MCP server
        sglang_host: Host URL for SGLang backend
        sglang_port: Port for SGLang backend
        storage_path: Directory path for persistent ChromaDB storage
    """

    llm_backend: str = "openai"
    llm_model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    evo_threshold: int = 100
    server_name: str = "agentic-memory"
    sglang_host: str = "http://localhost"
    sglang_port: int = 30000
    storage_path: str = "./chroma_db"

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables.

        Environment variables:
            LLM_BACKEND: LLM backend (default: openai)
            LLM_MODEL: LLM model name (default: gpt-4o-mini)
            OPENAI_API_KEY: OpenAI API key
            OPENROUTER_API_KEY: OpenRouter API key
            EMBEDDING_MODEL: Embedding model (default: all-MiniLM-L6-v2)
            EVO_THRESHOLD: Evolution threshold (default: 100)
            SGLANG_HOST: SGLang host (default: http://localhost)
            SGLANG_PORT: SGLang port (default: 30000)
            CHROMA_DB_PATH: ChromaDB storage path (default: ./chroma_db)

        Returns:
            MCPConfig instance populated from environment variables
        """
        llm_backend = os.getenv("LLM_BACKEND", "openai")

        # Determine API key based on backend
        api_key = None
        if llm_backend == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif llm_backend == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")

        return cls(
            llm_backend=llm_backend,
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=api_key,
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            evo_threshold=int(os.getenv("EVO_THRESHOLD", "100")),
            sglang_host=os.getenv("SGLANG_HOST", "http://localhost"),
            sglang_port=int(os.getenv("SGLANG_PORT", "30000")),
            storage_path=os.getenv("CHROMA_DB_PATH", "./chroma_db")
        )

    def to_dict(self) -> dict:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of config
        """
        return {
            "llm_backend": self.llm_backend,
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "evo_threshold": self.evo_threshold,
            "server_name": self.server_name,
            "sglang_host": self.sglang_host,
            "sglang_port": self.sglang_port,
            "storage_path": self.storage_path
        }
