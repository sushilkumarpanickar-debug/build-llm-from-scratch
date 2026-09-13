"""
Initialization script for multi-LLM setup with DAKSH
"""

from llm_providers.provider_base import LLMProvider, LLMConfig
from llm_providers.router import LLMRouter
from daksh.interface import DAKSH, DAKSHConfig
from config.settings import (
    OPENAI_API_KEY, ANTHROPIC_API_KEY, PERPLEXITY_API_KEY,
    LOCAL_LLM_BASE_URL, LOCAL_LLM_MODEL,
    DAKSH_VOICE_ENABLED, DAKSH_PERSONALITY, DAKSH_VOICE_PROFILE
)
from loguru import logger


def setup_llm_providers() -> LLMRouter:
    """
    Initialize and register all available LLM providers.
    Returns configured LLMRouter.
    """
    router = LLMRouter()
    
    # Register OpenAI (ChatGPT)
    if OPENAI_API_KEY:
        openai_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            temperature=0.7,
            max_tokens=2048,
            api_key=OPENAI_API_KEY,
            enabled=True,
            priority=3,
        )
        router.register_provider(openai_config)
        logger.info("✓ OpenAI (GPT-4) registered")
    
    # Register Anthropic (Claude)
    if ANTHROPIC_API_KEY:
        anthropic_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-opus-4",
            temperature=0.7,
            max_tokens=2048,
            api_key=ANTHROPIC_API_KEY,
            enabled=True,
            priority=3,
        )
        router.register_provider(anthropic_config)
        logger.info("✓ Anthropic (Claude) registered")
    
    # Register Perplexity
    if PERPLEXITY_API_KEY:
        perplexity_config = LLMConfig(
            provider=LLMProvider.PERPLEXITY,
            model="pplx-7b-online",
            temperature=0.7,
            max_tokens=2048,
            api_key=PERPLEXITY_API_KEY,
            enabled=True,
            priority=2,
        )
        router.register_provider(perplexity_config)
        logger.info("✓ Perplexity AI registered")
    
    # Register Local LLM (Ollama)
    local_config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model=LOCAL_LLM_MODEL,
        api_base=LOCAL_LLM_BASE_URL,
        enabled=True,
        priority=1,  # Lower priority (slower)
    )
    router.register_provider(local_config)
    logger.info(f"✓ Local LLM ({LOCAL_LLM_MODEL}) registered")
    
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY and not PERPLEXITY_API_KEY:
        logger.warning(
            "⚠ No cloud LLM API keys configured. Only local LLM will be used. "
            "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or PERPLEXITY_API_KEY in .env"
        )
    
    return router


def setup_daksh(llm_router: LLMRouter) -> DAKSH:
    """
    Initialize DAKSH with configured settings.
    Returns configured DAKSH instance.
    """
    daksh_config = DAKSHConfig(
        voice_enabled=DAKSH_VOICE_ENABLED,
        text_enabled=True,
        visual_effects=True,
        voice_profile=DAKSH_VOICE_PROFILE,
        personality=DAKSH_PERSONALITY,
    )
    
    daksh = DAKSH(daksh_config)
    
    # Attach LLM router
    daksh.llm_router = llm_router
    
    logger.info(f"✓ DAKSH initialized with {daksh_config.personality} personality")
    
    return daksh


def initialize_system() -> tuple[LLMRouter, DAKSH]:
    """
    Complete system initialization.
    Returns: (LLMRouter, DAKSH)
    """
    logger.info("="*80)
    logger.info("Initializing Multi-LLM System with DAKSH Interface")
    logger.info("="*80)
    
    # Setup LLM providers
    llm_router = setup_llm_providers()
    
    # Setup DAKSH
    daksh = setup_daksh(llm_router)
    
    logger.info("="*80)
    logger.info("System initialized successfully!")
    logger.info(f"Available providers: {', '.join(p.value for p in llm_router.providers.keys())}")
    logger.info("="*80)
    
    return llm_router, daksh


if __name__ == "__main__":
    # Quick test
    router, daksh = initialize_system()
    print("\n✓ System ready!")
    print(f"\nRouter stats:\n{router.get_stats()}")
    print(f"\nDAKSH stats:\n{daksh.get_stats()}")
