# Multi-LLM Provider Integration with DAKSH

A production-ready, modular system for integrating multiple Large Language Models (LLMs) with intelligent routing, featuring DAKSH—a J.A.R.V.I.S-style voice and text interface.

## Features

### 🚀 Multi-LLM Support
- **OpenAI (ChatGPT)**: GPT-4, GPT-3.5-Turbo
- **Anthropic (Claude)**: Opus, Sonnet, Haiku
- **Microsoft (Copilot)**: Azure OpenAI integration
- **Perplexity AI**: Web-aware search capabilities
- **Local LLM**: Ollama support for privacy-focused deployment

### 🧠 Intelligent Routing
- **Zero-Token Skills First**: Prefers skill-based execution over LLM calls
- **Task-Aware Provider Selection**: Routes to best provider based on task type
- **Cost Optimization**: Tracks and minimizes API costs
- **Fallback Strategy**: Automatic failover to alternative providers
- **Performance Metrics**: Tracks latency, tokens, and success rates

### 🎤 DAKSH Interface (J.A.R.V.I.S-Style)
- **Voice Input/Output**: Speech recognition and text-to-speech
- **Natural Conversation**: Context-aware multi-turn interactions
- **Web Dashboard**: Beautiful J.A.R.V.I.S-inspired UI
- **Multi-Modal**: Supports voice, text, and visual feedback
- **Auto-Routing**: Seamlessly switches between providers

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch.git
cd build-llm-from-scratch
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the root directory:

```env
# ============================================================================
# LLM PROVIDER KEYS
# ============================================================================

# OpenAI (ChatGPT)
OPENAI_API_KEY=sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Perplexity AI
PERPLEXITY_API_KEY=pplx-...

# Azure (Copilot)
AZURE_API_KEY=your-key

# ============================================================================
# LLM ROUTER CONFIGURATION
# ============================================================================

LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
ENABLE_INTELLIGENT_ROUTING=true
MAX_COST_PER_REQUEST=0.10
PREFER_CHEAPER=true

# ============================================================================
# DAKSH CONFIGURATION
# ============================================================================

# Voice settings
DAKSH_VOICE_ENABLED=true
DAKSH_VOICE_PROFILE=neutral  # neutral, british, american, indian
DAKSH_LISTEN_TIMEOUT=10.0
DAKSH_RESPONSE_SPEED=1.0

# Interface settings
DAKSH_VISUAL_EFFECTS=true
DAKSH_PERSONALITY=professional  # professional, friendly, casual
DAKSH_AUTO_EXECUTE=false

# Web dashboard
DAKSH_WEB_PORT=9000
DAKSH_WEB_HOST=localhost

# ============================================================================
# LOCAL LLM (OLLAMA)
# ============================================================================

LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=mistral

# ============================================================================
# ENVIRONMENT
# ============================================================================

ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## Quick Start

### 1. Terminal Interface

```python
from scripts.setup import initialize_system

# Initialize system
router, daksh = initialize_system()

# Start interactive session
daksh.interactive_session()
```

Then in the interactive session:
```
DAKSH Mode [1/2/3/quit]: 2
You: execute analyze customer sentiment in recent feedback
DAKSH: Executing objective: analyze customer sentiment in recent feedback
[Response with analysis]
```

### 2. Web Dashboard

```bash
python -m daksh.web_dashboard
```

Then navigate to `http://localhost:9000`

## Private iPhone Access with iCloud Drive and Tailscale

DAKSH saves conversation history to iCloud Drive by default at
`~/Library/Mobile Documents/com~apple~CloudDocs/DAKSH/interaction_history.json`.
This keeps the history available on Apple devices signed into the same iCloud
account. Do not place `.env` in iCloud Drive: API keys must remain only on the
laptop running DAKSH.

Run the dashboard only on the loopback interface:

```bash
DAKSH_WEB_HOST=127.0.0.1 python -m daksh.web_dashboard
```

Then, after installing and signing in to Tailscale on the laptop and iPhone,
publish that local service to the private tailnet:

```bash
tailscale serve --https=443 http://127.0.0.1:9000
```

Open the HTTPS URL shown by `tailscale serve status` on the iPhone while signed
in to the same Tailscale tailnet. Tailscale authentication protects the
dashboard without exposing it to the public Internet.

## Local-First Release

This release targets an Apple Silicon Mac with 8 GB unified memory using
Ollama's `qwen2.5:3b` model. Install Ollama on macOS, start the Ollama app,
then download the model once:

```bash
ollama pull qwen2.5:3b
```

DAKSH routes every model task to Ollama first. `CLOUD_FALLBACK_ENABLED=false`
is the default and guarantees that OpenAI, Anthropic, and Perplexity API keys
are never used. To evaluate cloud fallbacks temporarily, set it to `true`;
set it back to `false` and remove cloud API keys for the final local-only
configuration.

## Local OpenCode Coding Agent

DAKSH can request noninteractive coding jobs from the local dashboard at
`POST /api/opencode/jobs` with `{"prompt": "..."}` and retrieve the bounded
result at `GET /api/opencode/jobs/<id>`. Every submitted job remains
`pending_approval` until the configured Telegram chat approves it. Jobs are
automatic **only** in this DAKSH repository; the wrapper rejects every other
workspace.

Install the required local tools on macOS, then start Ollama and pull the
fixed model:

```bash
brew install anomalyco/tap/opencode
brew install --cask ollama
ollama pull qwen2.5:3b
```

The wrapper invokes:

```bash
opencode run --model ollama/qwen2.5:3b --format json -- "your prompt"
```

It supplies OpenCode configuration that enables only the local Ollama provider
at `http://localhost:11434/v1`, disables project configuration and sharing,
allows read/edit/bash only in the repository, and denies
`external_directory`, web fetch, and web search. It never sends cloud-provider
credentials to the process. The dashboard emits no CORS headers and its
existing CSP permits connections only to the same origin. Set
`DAKSH_OPENCODE_TIMEOUT_SECONDS` and `DAKSH_OPENCODE_MAX_OUTPUT_BYTES` to
bound individual jobs and returned output. If OpenCode, Ollama, or the model
is unavailable, submission returns a clear `503` setup error.

### Telegram approval setup

Create a bot with [@BotFather](https://t.me/BotFather), copy its token, start
a private chat with the bot, and determine that chat's numeric ID. Set these
values locally (never commit the token):

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_CHAT_ID=...
```

DAKSH sends requests only to that exact chat and processes updates only from
it. Approvals are persisted in `DAKSH_DATA_DIR`, expire after
`DAKSH_TELEGRAM_APPROVAL_EXPIRY_SECONDS` (15 minutes by default), and accept
only the exact commands shown in the message: `APPROVE <approval-id>` or
`DENY <approval-id>`. Telegram HTTP calls use the bounded
`DAKSH_TELEGRAM_REQUEST_TIMEOUT_SECONDS` timeout. Missing configuration or a
delivery failure causes submission to return an explicit `503`; the bot token
is never logged. WhatsApp approval support is intentionally future/optional.

Install and sign in to Tailscale on both devices before using the private
iPhone-access instructions above. The laptop must remain powered on, connected
to the Internet, and running both Ollama and DAKSH.

### 3. Programmatic Usage

```python
from scripts.setup import initialize_system
from llm_providers.router import LLMRequest

# Initialize
router, daksh = initialize_system()

# Create request
request = LLMRequest(
    prompt="Explain quantum computing",
    system_prompt="You are an expert in quantum physics.",
    task_type="explanation"
)

# Get routing decision
decision = router.decide(request)

print(f"Use LLM: {decision.use_llm}")
print(f"Provider: {decision.provider.value if decision.provider else 'N/A'}")
print(f"Confidence: {decision.confidence:.1%}")
print(f"Estimated Cost: ${decision.estimated_cost:.4f}")

# Execute
if decision.use_llm:
    response = router.execute(request, decision)
    print(f"Response: {response.content}")
    print(f"Cost: ${response.cost:.4f}")
    print(f"Tokens: {response.tokens_used}")
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                      DAKSH Interface                     │
│            (Voice, Text, Web Dashboard)                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   LLM Router                             │
│    (Intelligent Routing & Decision Making)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • Task Analysis                                  │  │
│  │ • Provider Scoring                               │  │
│  │ • Cost Optimization                              │  │
│  │ • Fallback Strategy                              │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────┬──────────────────┬──────────────────────┘
                 │                  │
    ┌────────────┴────────────┬─────┴─────────────┬──────────────┐
    │                        │                   │              │
┌───▼──┐  ┌─────────┐  ┌────▼────┐  ┌──────────▼───┐  ┌─────▼───┐
│ GPT  │  │ Claude  │  │Perplexity│  │ Azure Copilot│  │  Local  │
│  4   │  │         │  │          │  │   (OpenAI)   │  │  Ollama │
└──────┘  └─────────┘  └──────────┘  └──────────────┘  └─────────┘
```

### Task-to-Provider Mapping

| Task Type | Primary | Secondary | Tertiary |
|-----------|---------|-----------|----------|
| Reasoning | Claude (Opus) | GPT-4 | Local |
| Coding | GPT-4 | Claude | Local |
| Analysis | Claude | GPT-4 | Local |
| Web Search | Perplexity | GPT-4 | Claude |
| General | GPT-4 | Claude | Perplexity |
| Creative | Claude | GPT-4 | N/A |
| Planning | Claude | GPT-4 | Local |

## Usage Examples

### Example 1: Basic Query

```python
from daksh.interface import DAKSH

daksh = DAKSH()
interaction = daksh.process_input("What is machine learning?")
print(interaction.system_response)
```

### Example 2: Voice Interaction

```python
daksh = DAKSH()

# Listen for voice input
user_input = daksh.listen(timeout=10)

# Process and respond
if user_input:
    interaction = daksh.process_input(user_input, input_type="voice")
    daksh.speak(interaction.system_response)  # Speak the response
```

### Example 3: Cost-Conscious Routing

```python
from llm_providers.router import LLMRouter, LLMRequest

router = LLMRouter()

# Request with cost preference
request = LLMRequest(
    prompt="Summarize the benefits of renewable energy",
    task_type="summary"
)

# Routing decision will prefer cheaper providers
decision = router.decide(request)
print(f"Selected: {decision.provider.value}")
print(f"Cost: ${decision.estimated_cost:.4f}")
```

### Example 4: Objective Execution

```python
daksh = DAKSH()

# Execute multi-step objective
interaction = daksh.process_input(
    "execute analyze sales data from last quarter and generate insights"
)
print(interaction.system_response)
```

## Configuration Options

### Router Configuration

```python
from llm_providers.router import LLMRouter, LLMRequest

router = LLMRouter()

# Get routing statistics
stats = router.get_stats()
print(f"Total decisions: {stats['total_decisions']}")
print(f"LLM used: {stats['llm_used']}")
print(f"Skills used: {stats['skill_used']}")
print(f"Total cost: {stats['total_cost']}")
```

### DAKSH Configuration

```python
from daksh.interface import DAKSH, DAKSHConfig

config = DAKSHConfig(
    voice_enabled=True,
    text_enabled=True,
    visual_effects=True,
    response_speed=1.5,  # 1.5x speed
    voice_profile="british",
    personality="friendly",
    auto_execute=False,
    context_memory=20  # Remember last 20 interactions
)

daksh = DAKSH(config)
```

## Performance Metrics

### Routing Efficiency

```python
# Get router statistics
stats = router.get_stats()

# Example output:
# {
#     'router_id': 'abc-123',
#     'total_decisions': 150,
#     'llm_used': 45,  # 30%
#     'skill_used': 105,  # 70%
#     'skill_percentage': '70.0%',
#     'total_cost': '$1.23',
#     'providers': {
#         'openai': {'execution_count': 20, 'total_cost': '$0.85'},
#         'anthropic': {'execution_count': 15, 'total_cost': '$0.38'}
#     }
# }
```

### Provider Statistics

```python
# Individual provider stats
openai_provider = router.providers[LLMProvider.OPENAI]
stats = openai_provider.get_stats()

# Example output:
# {
#     'provider': 'openai',
#     'model': 'gpt-4',
#     'execution_count': 20,
#     'total_tokens': 25000,
#     'total_cost': '$0.85',
#     'enabled': True
# }
```

## Troubleshooting

### Issue: "OpenAI client not initialized"
**Solution**: Ensure `OPENAI_API_KEY` is set in `.env`:
```bash
export OPENAI_API_KEY=sk-...
```

### Issue: "Speech recognition not available"
**Solution**: Install required package:
```bash
pip install SpeechRecognition pyaudio
```

### Issue: "Local LLM not available"
**Solution**: Install and run Ollama:
```bash
# Visit https://ollama.ai for installation
ollama pull mistral
ollama serve
```

### Issue: "No suitable LLM providers available"
**Solution**: Configure at least one API key in `.env` or set up local LLM.

## API Reference

### LLMRouter

```python
class LLMRouter:
    def decide(request: LLMRequest, use_skills: bool = True) -> RoutingDecision
    def execute(request: LLMRequest, decision: RoutingDecision) -> LLMResponse
    def get_stats() -> Dict[str, Any]
```

### DAKSH

```python
class DAKSH:
    def listen(timeout: Optional[float] = None) -> Optional[str]
    def speak(text: str, wait: bool = True) -> None
    def process_input(user_input: str, input_type: str = "text") -> DAKSHInteraction
    def interactive_session() -> None
    def get_stats() -> Dict[str, Any]
```

## Advanced Usage

### Custom Provider Integration

```python
from llm_providers.provider_base import LLMBase, LLMConfig, LLMResponse

class CustomLLM(LLMBase):
    def validate_config(self) -> bool:
        return True
    
    def call(self, request) -> LLMResponse:
        # Your implementation
        pass

# Register custom provider
config = LLMConfig(
    provider=LLMProvider.CUSTOM,
    model="custom-model"
)
router.register_provider(config)
```

### Custom Routing Logic

```python
from llm_providers.router import LLMRouter

class CustomRouter(LLMRouter):
    def _score_providers(self, providers, request):
        # Custom scoring logic
        return [(p, score) for p, score in super()._score_providers(providers, request)]
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
- GitHub Issues: https://github.com/sushilkumarpanickar-debug/build-llm-from-scratch/issues
- Email: sushilkumarpanickar@gmail.com

## Roadmap

- [ ] Web UI improvements
- [ ] Real-time cost tracking dashboard
- [ ] Advanced caching with semantic search
- [ ] Multi-language support
- [ ] Custom LLM fine-tuning
- [ ] Streaming responses
- [ ] Advanced analytics and reporting

---

**Made with ⚡ by Sushil Kumar Panickar**
