# v0.2.0 - Local-First DAKSH

- Added a local-first Ollama routing policy with `qwen2.5:3b` as the default
  model for Apple Silicon Macs with 8 GB unified memory.
- Made cloud providers an explicit, disabled-by-default fallback so API
  credits cannot be consumed accidentally.
- Added iCloud Drive persistence for DAKSH interaction history.
- Documented private iPhone access through Tailscale Serve.
- Removed unrestricted dashboard CORS and its unused dependency.
- Restored the missing manager runtime component and configuration values
  required by the documented local orchestration path.
