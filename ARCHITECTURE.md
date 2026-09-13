# Architecture Deep Dive

## Three-Tier Hierarchy

The LLM Orchestrator implements a hierarchical command structure inspired by military and organizational management:

### Level 1: Commander (Strategic)
```
Responsibility: Vision and Decomposition
- Receive high-level objectives from user
- Analyze and understand requirements
- Decompose into strategic tasks
- Plan resource allocation
- Coordinate with managers
- Synthesize final output

Thinking Time: Configurable (default: 2s)
LLM Usage: Strategic planning only (can be offline)
Token Cost: Minimal (can be zero)
```

### Level 2: Managers (Tactical)
```
Responsibility: Planning and Coordination
- Receive tasks from Commander
- Create detailed execution plans
- Allocate work to workers
- Monitor progress
- Handle failures and retries
- Report status to Commander

Parallel Workers: Configurable (default: 3 per manager)
LLM Usage: None (pure orchestration)
Token Cost: Zero
```

### Level 3: Workers (Execution)
```
Responsibility: Work Execution
- Execute assigned skills
- Process data locally
- Track execution metrics
- Return results to manager

Skills Available: Text Processing, Analysis, Retrieval, Synthesis
LLM Usage: None (skill-based only)
Token Cost: Zero
```

## Skill System Architecture

### Skill Lifecycle

```
1. Registration
   ├─ Skill created with type and routing rules
   ├─ Added to SkillRouter
   └─ Made available for execution

2. Preparation
   ├─ Input validation
   ├─ Cache lookup (if enabled)
   └─ Context setup

3. Execution
   ├─ Core skill logic runs
   ├─ Output generated
   └─ Time tracked

4. Routing
   ├─ Evaluate routing rules
   ├─ Determine next skill(s)
   └─ Set up chaining

5. Caching
   ├─ Store result in cache
   ├─ Expire old entries
   └─ Ready for next call
```

### Skill Types

```
Transformation Skill
├─ Input: Raw data
├─ Process: Clean, format, convert
└─ Output: Structured data

Extraction Skill
├─ Input: Unstructured content
├─ Process: Pattern matching, NER
└─ Output: Extracted entities

Analysis Skill
├─ Input: Data to analyze
├─ Process: Statistical analysis
└─ Output: Insights and patterns

Synthesis Skill
├─ Input: Multiple data sources
├─ Process: Combine and format
└─ Output: Unified result

Retrieval Skill
├─ Input: Query
├─ Process: Graph search
└─ Output: Relevant context
```

## OmniRoute Routing Strategy

### Sequential Routing
```
Skill A → Skill B → Skill C → Output

Example: Text → Analysis → Synthesis
```

### Parallel Routing
```
        ┌→ Skill B ┐
Skill A─┤→ Skill C ├→ Output
        └→ Skill D ┘

Example: Process multiple data sources
```

### Conditional Routing
```
Skill A ─→ [Success?] ─→ Skill B
           [Failure?] ─→ Fallback Skill

Example: Attempt primary, fallback on error
```

### Loop Routing
```
       ┌─────────┐
       │         ▼
Skill A → [Condition?] → Repeat
       │         │
       └─ Success ─→ Next

Example: Retry until success
```

## Knowledge Graph (RAG) Architecture

### Graph Structure

```
Document Node
├─ Title
├─ Chunks (multiple)
│  └─ Chunk nodes linked to document
├─ Entities (multiple)
│  └─ Entity nodes linked to document
└─ Metadata

Edge Types:
- document → chunk: "contains_chunk"
- document → entity: "mentions"
- entity → entity: "relates_to"
```

### Query Pipeline

```
1. Input: User query
   ↓
2. Entity Extraction
   ├─ Extract capitalized phrases
   ├─ Extract technical terms
   └─ Build query entity list
   ↓
3. Node Search
   ├─ Find relevant nodes
   ├─ Score by relevance
   └─ Rank by score
   ↓
4. Context Retrieval
   ├─ Get connected nodes
   ├─ Build context graph
   └─ Format for output
   ↓
5. Output: Ranked results with context
```

### Chunking Strategy

```
Document: "A B C D E F G H I J K L M N O P Q R S T"

Chunk Size: 5 words
Overlap: 2 words

Chunk 1: A B C D E
Chunk 2:     D E F G H
Chunk 3:         G H I J K
Chunk 4:             J K L M N
...
```

## MCP Server Architecture

### Tool Registration

```
1. Tool Definition
   ├─ Name and type
   ├─ Input/output schema
   ├─ Handler function
   └─ Metadata

2. Registration
   ├─ Add to tool registry
   ├─ Index by name and type
   └─ Make discoverable

3. Discovery
   ├─ Query by name/type
   ├─ Filter by capability
   └─ Return matching tools
```

### Context Management

```
Context Stack
├─ Context 1 (User message 1)
│  ├─ Session data
│  ├─ Previous outputs
│  └─ Metadata
├─ Context 2 (User message 2)
│  └─ ...
└─ Context N (Current)

Passed to all tools for:
- State management
- Cross-tool communication
- Session tracking
```

## Work Tracking & Versioning

### Version History

```
Work: "Customer Analysis"
├─ Version 1 (2024-01-01)
│  ├─ Input: Raw feedback
│  ├─ Skills: [TextProcess, Analysis]
│  ├─ Output: Initial insights
│  ├─ Time: 2000ms
│  └─ Status: Completed
├─ Version 2 (2024-01-02)
│  ├─ Input: More feedback
│  ├─ Skills: [TextProcess, Analysis, Synthesis]
│  ├─ Output: Enhanced insights
│  ├─ Time: 1500ms (10% faster)
│  └─ Status: Completed
└─ Version 3 (Current)
   └─ ...
```

### Comparison

```
Compare V1 vs V2:
├─ Status: Same (Completed)
├─ Time: 2000ms → 1500ms (-25%)
├─ Skills: Added Synthesis
├─ Quality: Better insights
└─ Recommendation: Use V2 approach
```

## Data Flow: End-to-End

### Complete Objective Execution

```
User Input
    ↓
[Commander]
├─ Analyze objective
├─ Query RAG for context
└─ Decompose into tasks
    ↓
[Managers] (Parallel)
├─ Plan task execution
├─ Allocate to workers
└─ Coordinate timing
    ↓
[Workers] (Parallel)
├─ Select skills
├─ Route through skills
│  └─ Skill 1 → Skill 2 → Skill 3
├─ Execute locally
└─ Return results
    ↓
[Manager]
├─ Collect results
├─ Track versions
└─ Report to Commander
    ↓
[Commander]
├─ Synthesize outputs
├─ Store in RAG
└─ Return to user
    ↓
Final Output
```

## Performance Characteristics

### Execution Time
```
Small task:     100-500ms
Medium task:    500ms-2s
Large task:     2-10s

Limited by:
- Skill execution time (local processing)
- Graph traversal depth
- Number of workers/parallelism
```

### Memory Usage
```
Base system:         ~50MB
Per skill:          ~5-10MB
RAG (1000 docs):    ~100-200MB
Work history:       ~10MB per 1000 versions

Optimizations:
- Skill caching reduces redundant processing
- Version trimming limits history size
- Chunk overlap balances redundancy vs efficiency
```

### Scalability
```
Dimensions:
├─ Managers: Linear (2-10 recommended)
├─ Workers per Manager: Linear (2-5 recommended)
├─ Skills: Linear (10-100 practical)
├─ Documents: Exponential (1K-100K feasible)
└─ Versions per work: Linear (50-500 practical)

Bottlenecks:
- RAG graph traversal at high depth
- Skill cache memory at high hit rates
- Version history at high execution counts
```

---

**Key Principle**: All execution is local with zero LLM token consumption. The Commander handles strategic planning but workers execute skills without external API calls.
