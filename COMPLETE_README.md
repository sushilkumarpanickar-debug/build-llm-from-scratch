# LLM Orchestrator - Three-Tier Hierarchical System

## What is This?

A complete LLM orchestration framework that:
- ✅ **Never uses LLM tokens** for work execution (skills run locally)
- ✅ **Operates with unlimited credits** (no token counting)
- ✅ **Implements three-tier hierarchy**: Commander → Managers → Workers
- ✅ **Routes work through skills** using OmniRoute-style intelligent routing
- ✅ **Includes Graph-Based RAG** (your "second brain")
- ✅ **Tracks work versions** for iteration improvement
- ✅ **Integrates MCP** for seamless tool management

## Key Features

### 1. Zero-Token Execution
All skills execute locally without LLM API calls. Only strategic planning (Commander's thinking) uses optional LLM.

### 2. Three-Level Hierarchy
```
Commander (Strategic)      - Receives objectives, decomposes tasks
  ↓
Managers (Tactical)        - Plans execution, coordinates workers  
  ↓
Workers (Execution)        - Executes skills with zero token cost
```

### 3. OmniRoute-Style Skill Routing
Intelligent routing system that chains skills together with:
- Sequential execution
- Parallel execution
- Conditional routing
- Fallback mechanisms

### 4. Knowledge Graph (RAG)
Your "second brain" that:
- Indexes documents automatically
- Extracts entities
- Performs semantic search
- Builds knowledge relationships
- Zero-token retrieval

### 5. Work Versioning
Track and compare iterations:
- Version history
- Performance comparison
- Improvement tracking
- Execution logging

### 6. MCP Integration
Seamless tool integration with:
- Tool discovery
- Context management
- Tool chaining
- Zero-token execution

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run example
python examples/basic_example.py

# See getting started
cat GETTING_STARTED.md
```

## System Architecture

```
┌─────────────────────────────────────────────┐
│     OrchestratorSystem (Integration Layer)   │
│      Your Second Brain & Second-in-Command  │
└────────────────────────────────────────────┐
│                                            │
├─ Commander (Strategic Level)               │
│  ├─ Objective analysis                    │
│  ├─ Task decomposition                    │
│  └─ Result synthesis                      │
│                                            │
├─ SkillRouter (OmniRoute Engine)           │
│  ├─ Intelligent routing                   │
│  ├─ Skill chaining                        │
│  └─ Zero-token execution                  │
│                                            │
├─ KnowledgeGraph (RAG System)              │
│  ├─ Document indexing                     │
│  ├─ Semantic search                       │
│  └─ Graph traversal                       │
│                                            │
├─ MCPServer (Tool Management)              │
│  ├─ Tool discovery                        │
│  ├─ Context passing                       │
│  └─ Chain execution                       │
│                                            │
└─ WorkTracker (Version Management)         │
   ├─ Work versioning                       │
   ├─ Execution history                     │
   └─ Performance tracking                  │
```

## Core Concepts

### Skills
Reusable, composable work units that execute without LLM calls:
- Text Processing: Clean, extract, transform
- Data Analysis: Statistics, patterns, insights
- Knowledge Retrieval: Query the knowledge graph
- Synthesis: Combine and format results
- Custom: Create your own

### Routing
Intelligent skill chaining:
```python
Text → Analysis → Synthesis  # Sequential
Query → [Parallel: A, B, C]  # Parallel
Attempt → [Success? → Next] : [Fallback] # Conditional
```

### Knowledge Graph
Persistent knowledge store:
- Automatic chunking and indexing
- Entity extraction and linking
- Semantic search over documents
- Graph traversal for exploration
- Your "second brain"

### Work Tracking
Version management for iterations:
- Track multiple versions of work
- Compare performance metrics
- Learn from improvements
- Maintain full execution history

## Token/Credit Usage

**ZERO-TOKEN MODE: ALWAYS ENABLED**

- ✅ Skills: 0 tokens (local execution)
- ✅ Work processing: 0 tokens (local)
- ✅ RAG retrieval: 0 tokens (local)
- ✅ Total overhead: 0 tokens
- ✅ Credits: Unlimited

**Only optional LLM use:** Commander's strategic thinking (configurable, can be offline)

## File Structure

```
build-llm-from-scratch/
├── README.md                    # This file
├── GETTING_STARTED.md           # Quick start guide
├── ARCHITECTURE.md              # Deep dive
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
│
├── config/
│   └── settings.py              # All configuration
│
├── orchestrator/
│   ├── commander.py             # Strategic level
│   ├── manager.py               # Tactical level
│   ├── worker.py                # Execution level
│   └── integration.py            # Complete system
│
├── skills/
│   ├── skill_base.py            # Base class
│   ├── skill_router.py          # OmniRoute engine
│   └── built_in/
│       ├── text_processing.py
│       ├── data_analysis.py
│       ├── knowledge_retrieval.py
│       └── synthesis.py
│
├── rag/
│   └── knowledge_graph.py       # Graph-based RAG
│
├── mcp/
│   └── mcp_server.py            # MCP server
│
├── work_management/
│   └── work_tracker.py          # Version tracking
│
├── examples/
│   └── basic_example.py         # Complete example
│
and logs/ data/ directories
```

## Usage Examples

### 1. Execute Objective
```python
from orchestrator.integration import OrchestratorSystem

system = OrchestratorSystem()
result = system.execute_objective(
    "Analyze customer feedback and generate insights"
)
print(result['synthesis'])
```

### 2. Use Skills
```python
from skills.built_in.text_processing import TextProcessingSkill
from skills.skill_base import SkillInput

skill = TextProcessingSkill()
input_data = SkillInput(data={"text": "Hello world", "action": "clean"})
output = skill.run(input_data)
print(output.output_data)
```

### 3. Query Knowledge
```python
system.add_knowledge(
    title="My Document",
    content="Important information..."
)
results = system.query_knowledge("What is...?")
```

### 4. Track Work
```python
from work_management.work_tracker import WorkTracker

tracker = WorkTracker()
work = tracker.create_work("My Task", "Description")
tracker.add_version(work.id, input_data, output_data, skills, time_ms)
```

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings:
- `LLM_PROVIDER`: Which LLM to use (optional)
- `NUM_MANAGERS`: Number of manager instances
- `WORKERS_PER_MANAGER`: Workers per manager
- `SKILL_CACHE_ENABLED`: Enable skill caching
- `GRAPH_MAX_DEPTH`: RAG traversal depth
- All settings have sensible defaults

## Running Examples

```bash
# Run all examples
python examples/basic_example.py

# Check logs
tail -f logs/orchestrator.log
```

## Performance

- **Small task**: 100-500ms
- **Medium task**: 500ms-2s  
- **Large task**: 2-10s
- **Memory**: ~50MB base + skills + RAG
- **Scalability**: 2-10 managers, 2-5 workers each

## Troubleshooting

**Q: Skills not executing?**
A: Check `can_handle()` method and logs in `logs/orchestrator.log`

**Q: RAG slow?**
A: Reduce `GRAPH_MAX_DEPTH` and `RAG_RETRIEVE_TOP_K` in settings

**Q: High memory?**
A: Reduce `WORK_VERSION_HISTORY_SIZE` and disable RAG if unused

## Next Steps

1. Read [GETTING_STARTED.md](GETTING_STARTED.md) for detailed guide
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for deep dive
3. Run [examples/basic_example.py](examples/basic_example.py)
4. Create custom skills in `skills/built_in/`
5. Build your knowledge base with `system.add_knowledge()`

## Status

🚀 **Complete Implementation**
- ✅ Three-tier orchestrator
- ✅ Skill system with routing
- ✅ Graph-based RAG
- ✅ MCP integration
- ✅ Work versioning
- ✅ Examples and documentation

## License

MIT

---

**Your complete second brain and second-in-command for intelligent task orchestration with zero token overhead.**
