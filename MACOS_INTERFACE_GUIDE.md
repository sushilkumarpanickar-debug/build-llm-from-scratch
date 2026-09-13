# macOS Compatibility & Interface Guide

## ✅ macOS Compatibility

### System Requirements

**Minimum:**
- macOS 10.14+
- Python 3.8+
- 2GB RAM
- 500MB disk space

**Recommended:**
- macOS 12.0+ (Monterey or newer)
- Python 3.10+
- 4GB+ RAM
- 2GB disk space

### Installation on macBook

#### 1. Install Python (if not already installed)

```bash
# Using Homebrew (recommended)
brew install python@3.11

# Or download from python.org
# https://www.python.org/downloads/macos/

# Verify installation
python3 --version
```

#### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch.git
cd build-llm-from-scratch

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data .cache
```

#### 3. Run on macBook

```bash
# Run CLI interface
python3 run_cli.py

# Or run web interface
python3 run_web.py
# Then visit: http://localhost:8080

# Or run example
python3 examples/basic_example.py
```

### Common macOS Issues & Solutions

**Issue: "python3: command not found"**
```bash
# Solution: Install Python via Homebrew
brew install python@3.11
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Issue: Permission denied**
```bash
# Solution: Fix permissions
chmod +x run_cli.py run_web.py
```

**Issue: Module not found**
```bash
# Solution: Ensure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: Port 8000/8080 already in use**
```bash
# Solution: Change port in config
export MCP_SERVER_PORT=8001
python3 run_web.py
```

---

## 🖥️ Interface Options

### 1. CLI Interface (Command Line)

**Best for:** Quick testing, automation, scripts

```bash
python3 run_cli.py
```

**Features:**
- Text-based menu system
- Progress indicators
- Color-coded output
- Keyboard shortcuts
- Command history

**Example Output:**
```
╔════════════════════════════════════════════════════════════════════════════╗
║          LLM Orchestrator - Command Line Interface (macOS)                  ║
║                                                                              ║
║  Zero-Token Execution | Unlimited Credits | Hierarchical Orchestration    ║
╚════════════════════════════════════════════════════════════════════════════╝

[1] Execute Objective
[2] Query Knowledge Base
[3] Add Knowledge
[4] View System Status
[5] Manage Skills
[6] Work History
[7] Settings
[8] Exit

Enter choice: 
```

**Navigation:**
- Use number keys to select options
- Press 'q' to go back
- Press '?' for help
- Arrow keys for menu navigation

### 2. Web Interface (Browser)

**Best for:** Interactive exploration, visual monitoring, casual use

```bash
python3 run_web.py
# Opens http://localhost:8080
```

**Features:**
- Beautiful dashboard
- Real-time status monitoring
- Knowledge graph visualization
- Execution history charts
- Work version comparison
- Responsive design (mobile-friendly)
- Dark/Light theme

**Dashboard Pages:**

#### Home Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ System Status                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Objectives Executed: 12      |  Tokens Used: 0 (ZERO)     │
│  Tasks Completed: 48          |  Credits Used: ∞ (UNLIMITED)│
│  Work Versions: 156           |  Uptime: 2h 34m             │
│                                                              │
│  [Execute Objective] [Query KB] [Add Knowledge] [Settings]  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Objective Execution
```
┌─────────────────────────────────────────────────────────────┐
│ Execute New Objective                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Objective: ┌──────────────────────────────────────────┐  │
│            │ Enter your objective here...             │  │
│            └──────────────────────────────────────────┘  │
│                                                              │
│  Context (Optional):                                         │
│            ┌──────────────────────────────────────────┐  │
│            │ Add context or constraints              │  │
│            └──────────────────────────────────────────┘  │
│                                                              │
│            [ Execute ]  [ Clear ]  [ Recent Objectives ]   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Knowledge Base
```
┌─────────────────────────────────────────────────────────────┐
│ Knowledge Base                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Search: ┌──────────────────────────────────────────┐     │
│         │ Search your knowledge base...            │     │
│         └──────────────────────────────────────────┘     │
│                                                              │
│  [Add Document] [Graph View] [Statistics] [Export]         │
│                                                              │
│  Recent Documents:                                          │
│  • LLM Orchestrator Architecture (12 chunks, 8 entities)   │
│  • Skill System Guide (6 chunks, 4 entities)               │
│  • Configuration Reference (20 chunks, 15 entities)        │
│                                                              │
│  [View All]                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Work History
```
┌─────────────────────────────────────────────────────────────┐
│ Work Tracking & Versions                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Work Item: Customer Analysis                               │
│  ├─ Version 1  [2024-01-01] - 2000ms - 12/12 ✓ Complete   │
│  ├─ Version 2  [2024-01-02] - 1500ms - 12/12 ✓ Complete   │
│  ├─ Version 3  [2024-01-03] - 1200ms - 12/12 ✓ Complete   │
│  └─ Version 4  [2024-01-04] - 1100ms - 12/12 ✓ Complete   │
│                                                              │
│  Performance: -45% ⬇️ (V1→V4)                              │
│  Success Rate: 100%                                         │
│                                                              │
│  [Compare Versions] [Export] [Delete]                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### System Monitor
```
┌─────────────────────────────────────────────────────────────┐
│ System Performance Monitor                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CPU Usage:        [████████░░] 42%                         │
│  Memory Usage:     [██████░░░░] 28% (0.7GB / 2.5GB)        │
│  Disk Usage:       [███░░░░░░░] 8% (1.2GB / 15GB)          │
│                                                              │
│  Active Managers:  2 / 2                                    │
│  Active Workers:   4 / 4                                    │
│  Skill Cache Hit:  78%                                      │
│  Knowledge Graph:  156 nodes, 243 edges                    │
│                                                              │
│  Last Execution:   2m 34s ago                               │
│  Avg Execution:    1.2s                                     │
│  Total Tokens:     0 (ZERO-TOKEN MODE)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3. Jupyter Notebook Interface

**Best for:** Development, experimentation, learning

```bash
jupyter notebook
# Creates interactive notebooks for exploration
```

**Example Notebook:**
```python
from orchestrator.integration import OrchestratorSystem, SystemConfig

# Initialize system
system = OrchestratorSystem()

# Execute objective
result = system.execute_objective("Analyze customer feedback")

# Query knowledge
kg_result = system.query_knowledge("What insights were found?")

# Check status
status = system.get_system_status()

# Visualize results
import matplotlib.pyplot as plt
plt.plot(status['execution_times'])
plt.show()
```

### 4. API/REST Interface

**Best for:** Integration, automation, remote access

```bash
python3 run_api.py
# Runs FastAPI server at http://localhost:8000
```

**API Endpoints:**

```
POST /api/execute
Body: {"objective": "...", "context": {...}}
Response: {"result": {...}, "execution_time_ms": 1234}

GET /api/status
Response: {"system_status": {...}, "uptime": "2h 34m"}

GET /api/knowledge/search?query=...
Response: {"results": [...], "matched_nodes": 5}

POST /api/knowledge/add
Body: {"title": "...", "content": "...", "source": "..."}
Response: {"document_id": "...", "chunks": 5}

GET /api/work/{work_id}/history
Response: {"versions": [...], "stats": {...}}

GET /api/work/{work_id}/compare?v1=1&v2=2
Response: {"differences": {...}, "improvement": "25%"}
```

**Example cURL:**
```bash
# Execute objective
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"objective": "Analyze data"}'

# Query knowledge
curl -X GET "http://localhost:8000/api/knowledge/search?query=orchestrator"

# Get system status
curl -X GET http://localhost:8000/api/status
```

### 5. Python Library Interface

**Best for:** Programmatic usage, integration with other code

```python
from orchestrator.integration import OrchestratorSystem, SystemConfig
from skills.skill_base import SkillInput

# Initialize
system = OrchestratorSystem()

# Use as library
result = system.execute_objective("Your objective")
kg_results = system.query_knowledge("Your query")
system.add_knowledge("Title", "Content")
status = system.get_system_status()
```

---

## 🎯 Recommended Interface by Use Case

| Use Case | Best Interface | Why |
|----------|---|---|
| **Quick Testing** | CLI | Fast, no overhead, immediate feedback |
| **Visual Monitoring** | Web Dashboard | Real-time status, charts, intuitive |
| **Development** | Jupyter | Experimental, interactive exploration |
| **Production** | REST API | Scalable, remote access, integrations |
| **Automation** | Python Library | Direct programmatic control |
| **Learning** | Web + CLI | Best of both worlds for beginners |

---

## 🔧 Setting Up Your Preferred Interface

### Step 1: Choose Your Interface

Decide which interface(s) you want:
- **CLI only**: No additional setup needed
- **Web**: Install Flask/Streamlit
- **API**: Install FastAPI
- **Jupyter**: Install Jupyter

### Step 2: Install Requirements

```bash
# For CLI only (already included)
pip install -r requirements.txt

# For Web interface
pip install flask flask-cors python-dotenv

# For API interface
pip install fastapi uvicorn

# For Jupyter
pip install jupyter matplotlib

# For all interfaces
pip install -r requirements-all.txt
```

### Step 3: Create Interface Runner

**Create `run_cli.py`:**
```python
from cli.interface import CLIInterface

if __name__ == "__main__":
    cli = CLIInterface()
    cli.run()
```

**Create `run_web.py`:**
```python
from web.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host='localhost', port=8080, debug=False)
```

**Create `run_api.py`:**
```python
from api.server import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
```

### Step 4: Run Your Interface

```bash
# CLI
python3 run_cli.py

# Web
python3 run_web.py
# Visit: http://localhost:8080

# API
python3 run_api.py
# Visit: http://localhost:8000/docs
```

---

## 📱 macBook-Specific Tips

### Keyboard Shortcuts (All Interfaces)

```
CLI:
  Cmd+C      Exit
  Cmd+V      Paste (Terminal)
  Ctrl+R     Search history
  Tab        Auto-complete

Web:
  Cmd+R      Refresh
  Cmd+L      Search/Address bar
  Cmd+,      Settings (if available)
  Cmd+W      Close tab
  Cmd+Shift+N  New window

API (via Browser):
  Same as Web
```

### Performance Optimization on macBook

```python
# In config/settings.py

# Use fewer managers on older MacBooks
NUM_MANAGERS = 1  # Default: 2
WORKERS_PER_MANAGER = 2  # Default: 2

# Reduce memory footprint
WORK_VERSION_HISTORY_SIZE = 25  # Default: 50
SKILL_CACHE_TTL_SECONDS = 1800  # Default: 3600

# Smaller RAG depth
GRAPH_MAX_DEPTH = 3  # Default: 5
RAG_RETRIEVE_TOP_K = 3  # Default: 5
```

### System-Specific Logging

```python
# Add to config/settings.py
import platform

if platform.system() == "Darwin":  # macOS
    LOG_LEVEL = "INFO"
    ENABLE_MEMORY_OPTIMIZATION = True
    MAX_MEMORY_PERCENT = 75.0  # Be conservative on macBook
```

---

## 🚀 Getting Started on macBook

### Quick Start (10 minutes)

```bash
# 1. Install Python
brew install python@3.11

# 2. Clone and setup
git clone https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch.git
cd build-llm-from-scratch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run example
python3 examples/basic_example.py

# 4. Try CLI
python3 run_cli.py

# 5. Try Web
python3 run_web.py
# Open: http://localhost:8080
```

### Recommended Learning Path

1. **Day 1**: Run CLI interface, execute a simple objective
2. **Day 2**: Open Web interface, explore knowledge base
3. **Day 3**: Read GETTING_STARTED.md, understand architecture
4. **Day 4**: Create custom skills
5. **Day 5**: Build your knowledge base
6. **Day 6+**: Use as daily tool for complex tasks

---

## 📊 Interface Comparison Matrix

| Feature | CLI | Web | API | Jupyter | Library |
|---------|-----|-----|-----|---------|----------|
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Visual Feedback** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Automation** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Mobile Ready** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Learning Curve** | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## 💡 Pro Tips for macBook Users

1. **Use Terminal.app or iTerm2** for CLI - both work perfectly
2. **Keep Web interface open** in a separate browser tab for monitoring
3. **Use Safari** for web interface (optimized for macOS)
4. **Enable Dark Mode** in system preferences for eye comfort
5. **Use keyboard shortcuts** for faster navigation
6. **Monitor Activity Monitor** (`Cmd+Space` → "Activity Monitor") while running
7. **Check logs** with `tail -f logs/orchestrator.log`

---

## 🔗 Running Multiple Interfaces

You can run multiple interfaces simultaneously:

```bash
# Terminal 1: CLI
source venv/bin/activate
python3 run_cli.py

# Terminal 2: Web
source venv/bin/activate
python3 run_web.py

# Terminal 3: API
source venv/bin/activate
python3 run_api.py

# Terminal 4: Monitor logs
tail -f logs/orchestrator.log
```

All interfaces share the same system state, so changes in one reflect in others!

---

## ✅ Verification on macBook

```bash
# Check Python installation
python3 --version
# Expected: Python 3.10+

# Check virtual environment
which python
# Expected: /path/to/venv/bin/python

# Check dependencies
pip list | grep -E "loguru|pydantic|networkx"
# Expected: All packages listed

# Test import
python3 -c "from orchestrator.integration import OrchestratorSystem; print('✅ System Ready!')"

# Run quick test
python3 -c "from orchestrator.integration import OrchestratorSystem; s = OrchestratorSystem(); print(s.get_system_status())"
```

---

**Your LLM Orchestrator runs beautifully on macBook with multiple interface options for every use case!** 🍎✨
