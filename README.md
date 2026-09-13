# DAKSH · SNNS Local Intelligence

The working Phase 1 application is a private JARVIS-style second brain for macOS. It uses free local models through Ollama, local faster-whisper voice input, macOS speech, persistent SQLite memory, semantic document learning for PDF, TXT, Markdown, DOCX, CSV, and XLSX, and deterministic finance profiling. A governed connector control plane and allowlisted read-only Finance MCP are included; third-party connectors are never installed automatically.

```sh
./setup_mac.sh
ollama pull nomic-embed-text
.venv/bin/python -m local_workspace.server
```

Open <http://127.0.0.1:9001>. See [local_workspace/README.md](local_workspace/README.md) for the complete Phase 1 guide and [MCP_AND_SKILLS_REVIEW.md](MCP_AND_SKILLS_REVIEW.md) for connector decisions. The repository does not require a paid AI API.

## Legacy orchestration research

The older modules below are preserved as research inputs for later orchestrator phases. Some of their original architectural descriptions are aspirational and are not exposed as working Phase 1 capabilities.

# LLM Orchestrator: Three-Tier Hierarchical System

A sophisticated Large Language Model orchestration framework featuring:
- **Three-Level Hierarchy**: Commander → Manager → Worker
- **Skill-Based Task System**: Reusable, composable skills with no token overhead
- **MCP Integration**: Model Context Protocol for seamless tool integration
- **Graph-Based RAG**: Knowledge graph with document indexing as your "second brain"
- **Zero-Token Work Processing**: Skills executed locally without LLM API calls
- **Multi-Versioning**: Repeated work versions tracked and optimized

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         COMMANDER (Strategic Level)                 │
│  - Receives high-level objectives                   │
│  - Delegates to Managers                            │
│  - Synthesizes final results                        │
└──────────────┬──────────────────────────────────────┘
               │ (Tasks & Context)
       ┌───────┴────────┐
       │                │
┌──────▼────────┐  ┌────▼──────────┐
│   MANAGER 1   │  │   MANAGER 2   │
│ (Tactical)    │  │ (Tactical)    │
│ - Plan work   │  │ - Plan work   │
│ - Allocate    │  │ - Allocate    │
│ - Monitor     │  │ - Monitor     │
└──────┬────────┘  └────┬──────────┘
       │                │
    ┌──┴──┐          ┌──┴──┐
    │     │          │     │
┌───▼┐ ┌──▼──┐   ┌──▼──┐ ┌▼───┐
│W1  │ │W2   │   │W3   │ │W4  │
│    │ │     │   │     │ │    │
└────┘ └─────┘   └─────┘ └────┘
(Workers - Execute Skills)
```

## Key Features

### 1. Three-Level Hierarchy
- **Level 1 (Commander)**: Strategic planning, objective decomposition, result synthesis
- **Level 2 (Managers)**: Tactical planning, worker coordination, resource allocation
- **Level 3 (Workers)**: Skill execution, local processing, no API calls

### 2. Skill System
- **Reusable Skills**: Pre-built, composable work units
- **Zero Token Cost**: Skills run locally without LLM API overhead
- **Versioning**: Track multiple versions of repeated work
- **Skill Registry**: Centralized catalog of available skills

### 3. MCP (Model Context Protocol)
- Seamless integration with external tools and services
- Context-aware task execution
- Tool discovery and capability matching

### 4. Graph-Based RAG (Retrieval-Augmented Generation)
- **Knowledge Graph**: Documents indexed as interconnected nodes
- **Document Indexing**: Automatic extraction and linking
- **Query Resolution**: Graph traversal for context retrieval
- **Second Brain**: Persistent knowledge base for reference

### 5. Work Versioning
- Track multiple iterations of repeated work
- Compare versions and outcomes
- Learn from previous iterations

## Project Structure

```
build-llm-from-scratch/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── mcp_config.yaml
├── orchestrator/
│   ├── __init__.py
│   ├── commander.py          # Strategic level
│   ├── manager.py            # Tactical level
│   └── worker.py             # Execution level
├── skills/
│   ├── __init__.py
│   ├── skill_base.py         # Base skill class
│   ├── skill_registry.py     # Skill management
│   └── built_in/
│       ├── text_processing.py
│       ├── data_analysis.py
│       └── knowledge_retrieval.py
├── mcp/
│   ├── __init__.py
│   ├── mcp_server.py         # MCP server implementation
│   └── tools_registry.py     # Tool definitions
├── rag/
│   ├── __init__.py
│   ├── graph_builder.py      # Knowledge graph construction
│   ├── document_indexer.py   # Document processing
│   ├── graph_query.py        # Query resolution
│   └── storage/
│       └── knowledge_graph.db
├── work_management/
│   ├── __init__.py
│   ├── task.py               # Task definitions
│   ├── work_tracker.py       # Version tracking
│   └── execution_log.py      # Execution history
├── tests/
│   ├── __init__.py
│   ├── test_orchestrator.py
│   └── test_skills.py
└── examples/
    ├── basic_workflow.py
    └── advanced_scenario.py
```

## Quick Start

### Prerequisites
- Python 3.10+
- MacBook Air (tested on M1/M2)
- 8GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch.git
cd build-llm-from-scratch

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m orchestrator.setup
```

### Basic Usage

```python
from orchestrator.commander import Commander

# Initialize orchestrator
commander = Commander(
    name="Chief Commander",
    num_managers=2,
    workers_per_manager=2
)

# Define objective
objective = "Analyze user feedback and generate insights"

# Execute
result = commander.execute(objective)
print(result)
```

## Components

### Commander
Strategic-level orchestrator that:
- Receives high-level objectives
- Decomposes into manageable tasks
- Delegates to managers
- Synthesizes final output

### Manager
Tactical-level coordinator that:
- Plans work breakdown
- Allocates workers
- Monitors progress
- Handles failures and retries

### Worker
Execution-level processor that:
- Executes assigned skills
- Reports status
- No direct LLM calls (skill-based)

### Skill System
Modular, reusable work units:
- Pure functions or complex logic
- Version tracking
- Performance metrics
- No token overhead

### MCP Integration
- Tool discovery
- Context passing
- Result formatting
- Error handling

### Graph-Based RAG
- Document indexing
- Knowledge graph construction
- Semantic search
- Reference tracking

## Configuration

Edit `config/settings.py`:

```python
# LLM Settings
LLM_PROVIDER = "openai"  # or "local", "anthropic"
LLM_MODEL = "gpt-4"
LLM_TEMP = 0.7

# Orchestrator Settings
COMMANDER_THINK_TIME = 2.0
MANAGER_PARALLEL_WORKERS = 3
WORKER_SKILL_RETRY_LIMIT = 3

# RAG Settings
GRAPH_MAX_DEPTH = 5
RETRIEVE_TOP_K = 5

# Skill Settings
SKILL_CACHE_ENABLED = True
SKILL_VERSION_RETENTION = 10
```

## Use Cases

1. **Document Analysis & Summarization**: Parse documents with RAG, delegate to workers, synthesize insights
2. **Multi-Step Workflows**: Break complex tasks into skills executed by hierarchy
3. **Real-Time Knowledge Building**: RAG system continuously learns from processed documents
4. **Parallel Processing**: Managers distribute work to workers simultaneously
5. **Intelligent Caching**: Skills avoid redundant computation

## Development Roadmap

- [x] Commander implementation
- [x] Manager coordination system
- [x] Worker task execution
- [ ] Skill registry and versioning
- [ ] MCP server and tool integration
- [ ] Graph-based RAG engine
- [ ] Work tracking and versioning
- [ ] Web UI dashboard
- [ ] Persistence layer
- [ ] Performance optimization

## Contributing

This is a personal project. Feel free to fork and adapt for your needs!

## License

MIT

## Status

🚀 In Development

---

**This system acts as your second brain and second-in-command, handling complex work through a structured hierarchy.**
