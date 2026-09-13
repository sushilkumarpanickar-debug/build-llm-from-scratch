"""
Configuration settings for LLM providers and DAKSH
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        """Allow the local, dependency-free runtime path to use OS environment."""
        return False

load_dotenv()

# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================

# Primary LLM Provider (default)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")  # openai, anthropic, azure, perplexity, local
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Local LLM (Ollama)
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:3b")

# ============================================================================
# ROUTING CONFIGURATION
# ============================================================================

# Enable intelligent routing (prefers skills over LLM)
ENABLE_INTELLIGENT_ROUTING = os.getenv("ENABLE_INTELLIGENT_ROUTING", "true").lower() == "true"

# Maximum cost per request (in USD)
MAX_COST_PER_REQUEST = float(os.getenv("MAX_COST_PER_REQUEST", "0.1"))

# Prefer cheaper providers
PREFER_CHEAPER = os.getenv("PREFER_CHEAPER", "true").lower() == "true"

# Local is always preferred. Cloud providers are registered only when this is
# explicitly enabled, allowing a gradual transition to local-only operation.
CLOUD_FALLBACK_ENABLED = os.getenv("CLOUD_FALLBACK_ENABLED", "false").lower() == "true"

# ============================================================================
# DAKSH CONFIGURATION
# ============================================================================

# Voice settings
DAKSH_VOICE_ENABLED = os.getenv("DAKSH_VOICE_ENABLED", "true").lower() == "true"
DAKSH_VOICE_PROFILE = os.getenv("DAKSH_VOICE_PROFILE", "neutral")  # neutral, british, american, indian
DAKSH_LISTEN_TIMEOUT = float(os.getenv("DAKSH_LISTEN_TIMEOUT", "10.0"))
DAKSH_RESPONSE_SPEED = float(os.getenv("DAKSH_RESPONSE_SPEED", "1.0"))  # 0.5x to 2.0x

# Interface settings
DAKSH_VISUAL_EFFECTS = os.getenv("DAKSH_VISUAL_EFFECTS", "true").lower() == "true"
DAKSH_PERSONALITY = os.getenv("DAKSH_PERSONALITY", "professional")  # professional, friendly, casual
DAKSH_AUTO_EXECUTE = os.getenv("DAKSH_AUTO_EXECUTE", "false").lower() == "true"

# Web dashboard
DAKSH_WEB_PORT = int(os.getenv("DAKSH_WEB_PORT", "9000"))
DAKSH_WEB_HOST = os.getenv("DAKSH_WEB_HOST", "localhost")
DAKSH_DATA_DIR = Path(
    os.getenv(
        "DAKSH_DATA_DIR",
        "~/Library/Mobile Documents/com~apple~CloudDocs/DAKSH",
    )
).expanduser()

# OpenCode coding agent: local Ollama only, restricted to this repository.
DAKSH_OPENCODE_TIMEOUT_SECONDS = int(os.getenv("DAKSH_OPENCODE_TIMEOUT_SECONDS", "300"))
DAKSH_OPENCODE_MAX_OUTPUT_BYTES = int(os.getenv("DAKSH_OPENCODE_MAX_OUTPUT_BYTES", str(64 * 1024)))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_CHAT_ID = os.getenv("TELEGRAM_ALLOWED_CHAT_ID")
DAKSH_TELEGRAM_APPROVAL_EXPIRY_SECONDS = int(os.getenv("DAKSH_TELEGRAM_APPROVAL_EXPIRY_SECONDS", "900"))
DAKSH_TELEGRAM_REQUEST_TIMEOUT_SECONDS = float(os.getenv("DAKSH_TELEGRAM_REQUEST_TIMEOUT_SECONDS", "10"))

# ============================================================================
# ORCHESTRATOR CONFIGURATION
# ============================================================================

# Commander settings
COMMANDER_NAME = os.getenv("COMMANDER_NAME", "Chief Commander")
COMMANDER_THINK_TIME = float(os.getenv("COMMANDER_THINK_TIME", "2.0"))
NUM_MANAGERS = int(os.getenv("NUM_MANAGERS", "2"))
WORKERS_PER_MANAGER = int(os.getenv("WORKERS_PER_MANAGER", "2"))
COMMANDER_MAX_OBJECTIVES = int(os.getenv("COMMANDER_MAX_OBJECTIVES", "50"))
COMMANDER_WORKER_TIMEOUT = int(os.getenv("COMMANDER_WORKER_TIMEOUT", "300"))  # seconds

# Manager and worker settings
MANAGER_PLAN_TIME = float(os.getenv("MANAGER_PLAN_TIME", "1.0"))
MANAGER_RETRY_LIMIT = int(os.getenv("MANAGER_RETRY_LIMIT", "3"))
WORKER_EXECUTE_TIME = float(os.getenv("WORKER_EXECUTE_TIME", "0.5"))
SKILLS_ZERO_TOKEN_MODE = os.getenv("SKILLS_ZERO_TOKEN_MODE", "true").lower() == "true"

# Knowledge base settings
KNOWLEDGE_BASE_TYPE = os.getenv("KNOWLEDGE_BASE_TYPE", "vector")  # vector, sql, hybrid
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")  # faiss, pinecone, weaviate

# RAG settings
GRAPH_MAX_DEPTH = int(os.getenv("GRAPH_MAX_DEPTH", "5"))
RAG_RETRIEVE_TOP_K = int(os.getenv("RAG_RETRIEVE_TOP_K", "5"))
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "512"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# MCP settings
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
MCP_AUTO_DISCOVER_TOOLS = os.getenv("MCP_AUTO_DISCOVER_TOOLS", "true").lower() == "true"
MCP_TOOL_TIMEOUT = int(os.getenv("MCP_TOOL_TIMEOUT", "30"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/daksh.log")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

# Caching
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds
SKILL_CACHE_ENABLED = os.getenv("SKILL_CACHE_ENABLED", "true").lower() == "true"
SKILL_CACHE_TTL_SECONDS = int(os.getenv("SKILL_CACHE_TTL_SECONDS", "3600"))
SKILL_VERSION_RETENTION = int(os.getenv("SKILL_VERSION_RETENTION", "10"))

# Work tracking
WORK_VERSIONING_ENABLED = os.getenv("WORK_VERSIONING_ENABLED", "true").lower() == "true"
WORK_VERSION_HISTORY_SIZE = int(os.getenv("WORK_VERSION_HISTORY_SIZE", "50"))
EXECUTION_LOG_RETENTION_DAYS = int(os.getenv("EXECUTION_LOG_RETENTION_DAYS", "30"))

# Rate limiting
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
