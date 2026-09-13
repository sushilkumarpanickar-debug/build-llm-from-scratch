"""
Multi-LLM Provider Integration with Intelligent Routing
Supports: OpenAI (ChatGPT), Anthropic (Claude), Microsoft (Copilot), Perplexity
"""

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger

from config.settings import (
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    AZURE_API_KEY,
    PERPLEXITY_API_KEY,
)


class LLMProvider(Enum):
    """Available LLM Providers."""
    OPENAI = "openai"           # ChatGPT (GPT-4, GPT-3.5)
    ANTHROPIC = "anthropic"     # Claude (Opus, Sonnet, Haiku)
    AZURE = "azure"             # Microsoft Copilot
    PERPLEXITY = "perplexity"   # Perplexity AI
    LOCAL = "local"             # Local LLM (Ollama)
    OFFLINE = "offline"         # Offline mode (no LLM)


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    enabled: bool = True
    priority: int = 1  # Higher = higher priority
    cost_per_1k_tokens: float = 0.0  # Cost tracking
    fallback_providers: List[LLMProvider] = field(default_factory=list)


@dataclass
class LLMRequest:
    """Request to send to an LLM."""
    prompt: str
    system_prompt: Optional[str] = None
    task_type: str = "general"  # For routing decision
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM."""
    id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    provider: LLMProvider = LLMProvider.OFFLINE
    model: str = ""
    content: str = ""
    tokens_used: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0
    execution_time_ms: float = 0.0
    status: str = "success"  # success, failed, rate_limited
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class LLMBase(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.execution_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate configuration."""
        pass
    
    @abstractmethod
    def call(self, request: LLMRequest) -> LLMResponse:
        """Call the LLM."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "execution_count": self.execution_count,
            "total_tokens": self.total_tokens,
            "total_cost": f"${self.total_cost:.4f}",
            "enabled": self.config.enabled,
        }


class OpenAILLM(LLMBase):
    """OpenAI (ChatGPT) Integration."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        
        if self.validate_config():
            try:
                import openai
                openai.api_key = config.api_key or OPENAI_API_KEY
                self.client = openai.ChatCompletion
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        api_key = self.config.api_key or OPENAI_API_KEY
        if not api_key:
            logger.warning("OpenAI API key not found")
            return False
        return True
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API."""
        import time
        start_time = time.time()
        
        response = LLMResponse(
            provider=LLMProvider.OPENAI,
            model=self.config.model
        )
        
        if not self.client:
            response.status = "failed"
            response.error = "OpenAI client not initialized"
            return response
        
        try:
            import openai
            openai.api_key = self.config.api_key or OPENAI_API_KEY
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            api_response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=messages,
                temperature=request.temperature or self.config.temperature,
                max_tokens=request.max_tokens or self.config.max_tokens,
                top_p=self.config.top_p,
            )
            
            response.content = api_response.choices[0].message.content
            response.tokens_input = api_response.usage.prompt_tokens
            response.tokens_output = api_response.usage.completion_tokens
            response.tokens_used = api_response.usage.total_tokens
            
            # Calculate cost (approximate)
            if "gpt-4" in self.config.model:
                response.cost = (response.tokens_input * 0.00003 + response.tokens_output * 0.00006)
            else:
                response.cost = (response.tokens_input * 0.0000015 + response.tokens_output * 0.000002)
            
            response.status = "success"
            
        except Exception as e:
            response.status = "failed"
            response.error = str(e)
            logger.error(f"OpenAI call failed: {str(e)}")
        
        finally:
            response.execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_tokens += response.tokens_used
            self.total_cost += response.cost
        
        return response


class AnthropicLLM(LLMBase):
    """Anthropic (Claude) Integration."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        
        if self.validate_config():
            try:
                import anthropic
                self.client = anthropic.Anthropic(
                    api_key=config.api_key or ANTHROPIC_API_KEY
                )
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic package not installed. Install with: pip install anthropic")
    
    def validate_config(self) -> bool:
        """Validate Anthropic configuration."""
        api_key = self.config.api_key or ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("Anthropic API key not found")
            return False
        return True
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """Call Anthropic API."""
        import time
        start_time = time.time()
        
        response = LLMResponse(
            provider=LLMProvider.ANTHROPIC,
            model=self.config.model
        )
        
        if not self.client:
            response.status = "failed"
            response.error = "Anthropic client not initialized"
            return response
        
        try:
            system_msg = request.system_prompt or "You are a helpful assistant."
            
            api_response = self.client.messages.create(
                model=self.config.model,
                max_tokens=request.max_tokens or self.config.max_tokens,
                system=system_msg,
                messages=[{"role": "user", "content": request.prompt}],
            )
            
            response.content = api_response.content[0].text
            response.tokens_input = api_response.usage.input_tokens
            response.tokens_output = api_response.usage.output_tokens
            response.tokens_used = response.tokens_input + response.tokens_output
            
            # Calculate cost (approximate)
            if "opus" in self.config.model:
                response.cost = (response.tokens_input * 0.000015 + response.tokens_output * 0.000075)
            elif "sonnet" in self.config.model:
                response.cost = (response.tokens_input * 0.000003 + response.tokens_output * 0.000015)
            else:  # Haiku
                response.cost = (response.tokens_input * 0.00000025 + response.tokens_output * 0.00000125)
            
            response.status = "success"
            
        except Exception as e:
            response.status = "failed"
            response.error = str(e)
            logger.error(f"Anthropic call failed: {str(e)}")
        
        finally:
            response.execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_tokens += response.tokens_used
            self.total_cost += response.cost
        
        return response


class PerplexityLLM(LLMBase):
    """Perplexity AI Integration."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        
        if self.validate_config():
            try:
                import openai
                self.client = openai.OpenAI(
                    api_key=config.api_key or PERPLEXITY_API_KEY,
                    base_url="https://api.perplexity.ai"
                )
                logger.info("Perplexity client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
    
    def validate_config(self) -> bool:
        """Validate Perplexity configuration."""
        api_key = self.config.api_key or PERPLEXITY_API_KEY
        if not api_key:
            logger.warning("Perplexity API key not found")
            return False
        return True
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """Call Perplexity API."""
        import time
        start_time = time.time()
        
        response = LLMResponse(
            provider=LLMProvider.PERPLEXITY,
            model=self.config.model
        )
        
        if not self.client:
            response.status = "failed"
            response.error = "Perplexity client not initialized"
            return response
        
        try:
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            api_response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=request.temperature or self.config.temperature,
            )
            
            response.content = api_response.choices[0].message.content
            response.tokens_used = getattr(api_response.usage, 'total_tokens', 0)
            response.cost = (response.tokens_used * 0.000001)  # Approximate
            response.status = "success"
            
        except Exception as e:
            response.status = "failed"
            response.error = str(e)
            logger.error(f"Perplexity call failed: {str(e)}")
        
        finally:
            response.execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_tokens += response.tokens_used
            self.total_cost += response.cost
        
        return response


class LocalLLM(LLMBase):
    """Local LLM Support (Ollama)."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        
        if self.validate_config():
            try:
                import requests
                self.base_url = config.api_base or "http://localhost:11434"
                # Test connection
                response = requests.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    self.client = requests
                    logger.info(f"Local LLM connected at {self.base_url}")
            except Exception as e:
                logger.warning(f"Could not connect to local LLM: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate local LLM configuration."""
        return True  # Local LLM is optional
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """Call local LLM."""
        import time
        start_time = time.time()
        
        response = LLMResponse(
            provider=LLMProvider.LOCAL,
            model=self.config.model
        )
        
        if not self.client:
            response.status = "failed"
            response.error = "Local LLM not available"
            return response
        
        try:
            prompt_text = request.prompt
            if request.system_prompt:
                prompt_text = f"{request.system_prompt}\n\n{request.prompt}"
            
            api_response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt_text,
                    "temperature": request.temperature or self.config.temperature,
                    "stream": False,
                },
                timeout=300
            )
            
            if api_response.status_code == 200:
                result = api_response.json()
                response.content = result.get("response", "")
                response.tokens_used = 0  # Local LLM doesn't track tokens
                response.cost = 0.0  # Free
                response.status = "success"
            else:
                response.status = "failed"
                response.error = f"Local LLM error: {api_response.status_code}"
        
        except Exception as e:
            response.status = "failed"
            response.error = str(e)
            logger.error(f"Local LLM call failed: {str(e)}")
        
        finally:
            response.execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_tokens += response.tokens_used
            self.total_cost += response.cost
        
        return response
