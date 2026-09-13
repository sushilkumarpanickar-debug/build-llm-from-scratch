# Getting Started with LLM Orchestrator

## Quick Start (5 minutes)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch.git
cd build-llm-from-scratch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data .cache
```

### 2. Run the Example

```bash
python examples/basic_example.py
```

You should see output like:
```
╔════════════════════════════════════════════════════════════════════════════╗
║        LLM Orchestrator: Three-Tier Hierarchical System Examples          ║
║                                                                            ║
║  Features:                                                                 ║
║  • Zero-Token Execution (No LLM API calls)                                ║
║  • Unlimited Credits Mode                                                 ║
║  • OmniRoute-Style Skill Routing                                          ║
║  • Graph-Based RAG (Second Brain)                                         ║
║  • Work Versioning & Tracking                                             ║
║  • MCP Integration                                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OrchestratorSystem (Main)                    │
│                   Your Second Brain & Command                   │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ├─ Commander (Strategic Level)
       │   ├─ Receives objectives
       │   ├─ Decomposes into tasks
       │   └─ Coordinates Managers
       │
       ├─ SkillRouter (OmniRoute Engine)
       │   ├─ Intelligent routing
       │   ├─ Zero-token execution
       │   └─ Skill chaining
       │
       ├─ KnowledgeGraph (Second Brain / RAG)
       │   ├─ Document indexing
       │   ├─ Semantic search
       │   └─ Graph traversal
       │
       ├─ MCPServer (Tool Integration)
       │   ├─ Tool discovery
       │   ├─ Context management
       │   └─ Chain execution
       │
       └─ WorkTracker (Version Management)
           ├─ Work versioning
           ├─ Execution history
           └─ Performance tracking
```

## Core Components

### 1. Commander (Strategic Level)

```python
from orchestrator.commander import Commander

commander = Commander(
    name="Chief Commander",
    num_managers=2,
    workers_per_manager=2
)

result = commander.execute("Analyze customer feedback")
```

**Responsibilities:**
- Receive high-level objectives
- Decompose into manageable tasks
- Delegate to managers
- Synthesize final results

### 2. Managers & Workers (Tactical & Execution Levels)

Automatically managed by Commander. The hierarchy coordinates work delegation.

**Manager responsibilities:**
- Plan work breakdown
- Allocate workers to tasks
- Monitor execution progress
- Handle failures and retries

**Worker responsibilities:**
- Execute assigned skills
- No direct LLM API calls
- Track skill execution
- Report results

### 3. Skills System (Zero-Token Execution)

Reusable, composable work units that execute without LLM API calls.

```python
from skills.skill_base import Skill, SkillInput, SkillType

class CustomSkill(Skill):
    def __init__(self):
        super().__init__(
            name="My Custom Skill",
            skill_type=SkillType.TRANSFORMATION,
            description="Does something useful",
        )
    
    def execute(self, skill_input: SkillInput):
        # Your logic here - NO LLM CALLS
        output = SkillOutput()
        output.output_data = {"processed": True}
        return output
    
    def can_handle(self, task_description: str) -> bool:
        return "keyword" in task_description.lower()
```

**Built-in Skills:**
- `TextProcessingSkill`: Clean, extract, and transform text
- `DataAnalysisSkill`: Analyze data and extract insights
- `KnowledgeRetrievalSkill`: Query the knowledge graph
- `SynthesisSkill`: Combine and format results

### 4. OmniRoute-Style Skill Router

Intelligent routing system that chains skills together.

```python
from skills.skill_router import SkillRouter, RoutingRule, RoutingStrategy

router = SkillRouter()

# Register skills
router.register_skill(text_skill)
router.register_skill(analysis_skill)

# Define routing rules
router.register_routing_rule(
    RoutingRule(
        source_skill=text_skill.id,
        target_skill=analysis_skill.id,
        condition="success:true",
        strategy=RoutingStrategy.SEQUENTIAL,
    )
)

# Execute path
result = router.execute_path(text_skill.id, input_data)
```

**Features:**
- Sequential execution
- Parallel execution
- Conditional routing
- Fallback mechanisms
- Zero-token operation

### 5. Knowledge Graph (Your Second Brain)

Graph-based RAG system for persistent knowledge management.

```python
from rag.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# Add knowledge
doc = kg.add_document(
    title="My Document",
    content="The content...",
    source="my_source"
)

# Query knowledge
results = kg.query("What is...?", top_k=5)

# Traverse graph
traversal = kg.traverse_graph(node_id, max_depth=3)
```

**Features:**
- Automatic document chunking
- Entity extraction
- Semantic search
- Graph traversal
- Zero-token retrieval

### 6. MCP Server (Tool Integration)

Model Context Protocol server for seamless tool integration.

```python
from mcp.mcp_server import MCPServer, MCPTool, ToolType

mcp = MCPServer()

# Create and register tools
tool = MCPTool(
    name="My Tool",
    tool_type=ToolType.TEXT_PROCESSING,
    description="Does something",
    handler=my_handler_function
)

mcp.register_tool(tool)

# Discover tools
tools = mcp.discover_tools("text")

# Execute tool chain
results = mcp.execute_tool_chain(tool_ids, context, inputs)
```

### 7. Work Tracker (Version Management)

Track and version work items across multiple iterations.

```python
from work_management.work_tracker import WorkTracker

tracker = WorkTracker()

# Create work item
work = tracker.create_work(
    name="My Task",
    description="Task description",
    work_type="skill_execution"
)

# Add version
version = tracker.add_version(
    work_id=work.id,
    input_data={...},
    output_data={...},
    skills_used=["skill1"],
    execution_time_ms=1000.0,
    status="completed"
)

# Compare versions
comparison = tracker.compare_versions(work.id, 1, 2)

# Get statistics
stats = tracker.get_work_stats(work.id)
```

## Integration: Using Everything Together

```python
from orchestrator.integration import OrchestratorSystem, SystemConfig

# Initialize the complete system
config = SystemConfig(
    num_managers=2,
    workers_per_manager=2,
    enable_rag=True,          # Enable knowledge graph
    enable_mcp=True,          # Enable MCP
    enable_work_tracking=True, # Enable work versioning
    zero_token_mode=True       # ALWAYS True
)

system = OrchestratorSystem(config)

# Execute objective through entire pipeline
result = system.execute_objective(
    objective="Analyze and summarize reports",
    use_rag=True  # Retrieve context from knowledge graph
)

# Add knowledge to system's brain
system.add_knowledge(
    title="Important Info",
    content="The content...",
    source="my_docs"
)

# Query the knowledge base
kg_result = system.query_knowledge("What is...?")

# Get system status
status = system.get_system_status()
print(f"System Status: {status}")
```

## Configuration

Edit `config/settings.py` to customize behavior:

```python
# LLM Settings (for strategic planning only)
LLM_PROVIDER = "openai"  # or "local", "anthropic"
LLM_MODEL = "gpt-4"
LLM_TEMPERATURE = 0.7

# Orchestrator Settings
NUM_MANAGERS = 2
WORKERS_PER_MANAGER = 2
COMMANDER_THINK_TIME = 2.0
MANAGER_PARALLEL_WORKERS = 3

# Skill Settings
SKILL_CACHE_ENABLED = True
SKILL_CACHE_TTL_SECONDS = 3600
SKILLS_ZERO_TOKEN_MODE = True  # ALWAYS enabled

# RAG Settings
GRAPH_MAX_DEPTH = 5
RAG_RETRIEVE_TOP_K = 5
RAG_CHUNK_SIZE = 512

# MCP Settings
MCP_SERVER_HOST = "localhost"
MCP_SERVER_PORT = 8000

# Work Management
WORK_VERSIONING_ENABLED = True
WORK_VERSION_HISTORY_SIZE = 50
```

## Token/Credit Usage

**ZERO-TOKEN MODE: ALWAYS ENABLED**

All components operate in zero-token mode:
- ✅ Skills execute locally without LLM API calls
- ✅ Work processing consumes 0 tokens
- ✅ RAG retrieval consumes 0 tokens
- ✅ Skill caching prevents redundant computation
- ✅ Unlimited credits mode active

**Tokens Used:** Always 0
**Credits Used:** Unlimited

## Performance Tips

1. **Skill Caching**: Enabled by default. Identical inputs return cached results.
2. **Parallel Execution**: Manager can execute multiple workers simultaneously.
3. **Graph Traversal**: Limit `GRAPH_MAX_DEPTH` for faster queries.
4. **Chunking**: Adjust `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP` for your data.
5. **Work Versioning**: Set `WORK_VERSION_HISTORY_SIZE` to balance memory vs. history.

## Troubleshooting

### Skills not executing?
1. Check `config/settings.py` has correct skill cache settings
2. Verify skill `can_handle()` returns True for your task
3. Check logs in `logs/orchestrator.log`

### Knowledge graph slow?
1. Reduce `GRAPH_MAX_DEPTH`
2. Decrease `RAG_RETRIEVE_TOP_K`
3. Adjust `RAG_CHUNK_SIZE` for your data

### High memory usage?
1. Reduce `WORK_VERSION_HISTORY_SIZE`
2. Disable RAG if not needed: `enable_rag=False`
3. Clear cache periodically

## Examples

### Example 1: Basic Objective

```bash
python examples/basic_example.py
```

### Example 2: Custom Skill

```python
from skills.skill_base import Skill, SkillInput, SkillOutput, SkillType

class MySkill(Skill):
    def __init__(self):
        super().__init__(
            name="My Skill",
            skill_type=SkillType.TRANSFORMATION,
        )
    
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        output = SkillOutput()
        data = skill_input.data
        output.output_data = {"result": process(data)}
        return output
    
    def can_handle(self, task: str) -> bool:
        return "keyword" in task.lower()
```

## Next Steps

1. **Read the README**: Full architecture overview
2. **Explore Examples**: `examples/` directory
3. **Check Logs**: `logs/orchestrator.log` for detailed info
4. **Build Skills**: Create custom skills in `skills/built_in/`
5. **Populate Knowledge**: Use `system.add_knowledge()` to build your second brain
6. **Monitor**: Use `system.get_system_status()` to track performance

## Support

- **Issues**: Create an issue on GitHub
- **Documentation**: See README.md
- **Logs**: Check `logs/orchestrator.log`
- **Configuration**: Edit `config/settings.py`

---

**Remember:** This system is your second brain and second-in-command. It handles complex work through structured hierarchy and intelligent routing, all without consuming LLM tokens or credits.
