"""
Intelligent LLM Router - Decides which LLM to use based on task characteristics
Zero-token skills are preferred, LLMs only when necessary
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from llm_providers.provider_base import (
    LLMProvider, LLMConfig, LLMRequest, LLMResponse,
    LLMBase, OpenAILLM, AnthropicLLM, PerplexityLLM, LocalLLM
)


@dataclass
class RoutingDecision:
    """Decision made by the router."""
    id: str = ""
    use_llm: bool = False  # Should we use LLM at all?
    provider: Optional[LLMProvider] = None
    reason: str = ""  # Why this decision
    confidence: float = 0.0  # 0-1 confidence score
    fallback_providers: List[LLMProvider] = None  # If primary fails
    estimated_cost: float = 0.0
    estimated_time_ms: float = 0.0
    created_at: datetime = None


class LLMRouter:
    """
    Intelligent router that decides whether and which LLM to use.
    
    Routing Logic:
    1. If skill can handle it → Use skill (0 tokens)
    2. If LLM optional → Skip (save money)
    3. If LLM required → Pick best provider based on:
       - Task type (analysis, coding, reasoning, etc.)
       - Cost
       - Latency
       - Availability
       - Provider strengths
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.providers: Dict[LLMProvider, LLMBase] = {}
        self.routing_history: List[RoutingDecision] = []
        self.task_provider_mapping: Dict[str, List[LLMProvider]] = self._init_task_mapping()
        
        logger.info("LLMRouter initialized")
    
    def register_provider(self, config: LLMConfig) -> None:
        """Register an LLM provider."""
        
        if config.provider == LLMProvider.OPENAI:
            provider = OpenAILLM(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            provider = AnthropicLLM(config)
        elif config.provider == LLMProvider.PERPLEXITY:
            provider = PerplexityLLM(config)
        elif config.provider == LLMProvider.LOCAL:
            provider = LocalLLM(config)
        else:
            logger.warning(f"Unknown provider: {config.provider}")
            return
        
        self.providers[config.provider] = provider
        logger.info(f"Provider registered: {config.provider.value}")
    
    def decide(self, request: LLMRequest, use_skills: bool = True) -> RoutingDecision:
        """
        Make routing decision: should we use LLM and which one?
        
        Args:
            request: LLM request with task details
            use_skills: Whether skills are available for this task
        
        Returns:
            RoutingDecision with provider selection
        """
        
        decision = RoutingDecision(
            id=str(uuid.uuid4()),
            created_at=datetime.now(),
            fallback_providers=[]
        )
        
        # Step 1: Check if skills can handle this
        if use_skills and self._can_skill_handle(request):
            decision.use_llm = False
            decision.reason = "Task can be handled by zero-token skill"
            decision.confidence = 0.95
            logger.info(f"[Router {decision.id}] Using skill instead of LLM")
            self.routing_history.append(decision)
            return decision
        
        # Step 2: Get suitable providers for this task type
        suitable_providers = self.task_provider_mapping.get(
            request.task_type, 
            list(self.providers.keys())
        )
        
        if not suitable_providers or not any(p in self.providers and self.providers[p].config.enabled for p in suitable_providers):
            decision.use_llm = False
            decision.reason = "No suitable LLM providers available"
            decision.confidence = 0.0
            logger.warning(f"[Router {decision.id}] No available LLM providers")
            self.routing_history.append(decision)
            return decision
        
        # Step 3: Score and rank providers
        provider_scores = self._score_providers(suitable_providers, request)
        
        if not provider_scores:
            decision.use_llm = False
            decision.reason = "All LLM providers disabled or unavailable"
            decision.confidence = 0.0
            self.routing_history.append(decision)
            return decision
        
        # Step 4: Select best provider
        best_provider, score = max(provider_scores, key=lambda x: x[1])
        
        decision.use_llm = True
        decision.provider = best_provider
        decision.confidence = score / 100.0  # Convert to 0-1
        decision.reason = f"Selected {best_provider.value} (score: {score:.1f}/100)"
        
        # Set fallback providers (other ranked providers)
        other_providers = [p for p, _ in sorted(
            provider_scores, key=lambda x: x[1], reverse=True
        )[1:3]]
        decision.fallback_providers = other_providers
        
        # Estimate cost and time
        selected = self.providers[best_provider]
        decision.estimated_cost = self._estimate_cost(request, selected)
        decision.estimated_time_ms = self._estimate_time(best_provider)
        
        logger.info(
            f"[Router {decision.id}] Routing to {best_provider.value} "
            f"(confidence: {decision.confidence:.1%}, cost: ${decision.estimated_cost:.4f})"
        )
        
        self.routing_history.append(decision)
        return decision
    
    def execute(self, request: LLMRequest, decision: RoutingDecision) -> LLMResponse:
        """
        Execute based on routing decision.
        """
        
        if not decision.use_llm:
            # Return offline response
            return LLMResponse(
                provider=LLMProvider.OFFLINE,
                content="[Skill-based execution - no LLM call]",
                tokens_used=0,
                cost=0.0,
                status="success"
            )
        
        if decision.provider not in self.providers:
            response = LLMResponse(
                provider=LLMProvider.OFFLINE,
                status="failed",
                error=f"Provider {decision.provider.value} not available"
            )
            return response
        
        # Try primary provider
        provider = self.providers[decision.provider]
        response = provider.call(request)
        
        # If failed and fallbacks available, try them
        if response.status != "success" and decision.fallback_providers:
            logger.warning(
                f"Primary provider {decision.provider.value} failed. "
                f"Trying fallback: {decision.fallback_providers[0].value}"
            )
            
            for fallback in decision.fallback_providers:
                if fallback in self.providers:
                    response = self.providers[fallback].call(request)
                    if response.status == "success":
                        logger.info(f"Fallback provider {fallback.value} succeeded")
                        response.provider = fallback
                        break
        
        return response
    
    def _can_skill_handle(self, request: LLMRequest) -> bool:
        """
        Check if this task can be handled by zero-token skills.
        """
        
        # Tasks that don't need LLM
        no_llm_tasks = [
            "text_processing",
            "data_analysis",
            "knowledge_retrieval",
            "synthesis",
            "chunking",
            "formatting",
        ]
        
        if request.task_type in no_llm_tasks:
            return True
        
        # Check prompt length - very short tasks might not need LLM
        if len(request.prompt) < 100 and "simple" in request.task_type.lower():
            return True
        
        return False
    
    def _score_providers(self, providers: List[LLMProvider], request: LLMRequest) -> List[Tuple[LLMProvider, float]]:
        """
        Score providers based on suitability for task.
        
        Scoring factors:
        - Provider strength for task type
        - Cost
        - Latency
        - Success rate
        - Priority
        """
        
        scores = []
        
        for provider_type in providers:
            if provider_type not in self.providers:
                continue
            
            provider = self.providers[provider_type]
            if not provider.config.enabled:
                continue
            
            score = 50.0  # Base score
            
            # Task-specific scoring
            if request.task_type == "reasoning":
                # Claude excels at reasoning
                if provider_type == LLMProvider.ANTHROPIC:
                    score += 25
                elif provider_type == LLMProvider.OPENAI:
                    score += 15
            
            elif request.task_type == "coding":
                # GPT-4 is best for coding
                if provider_type == LLMProvider.OPENAI:
                    score += 25
                elif provider_type == LLMProvider.ANTHROPIC:
                    score += 15
            
            elif request.task_type == "web_search":
                # Perplexity is best for search
                if provider_type == LLMProvider.PERPLEXITY:
                    score += 30
            
            elif request.task_type == "general":
                # All are reasonable
                score += 10
            
            # Cost factor (prefer cheaper)
            cost_estimate = self._estimate_cost(request, provider)
            if cost_estimate < 0.01:
                score += 10
            elif cost_estimate > 0.1:
                score -= 15
            
            # Availability factor
            if provider.execution_count == 0:
                score += 5  # Prefer fresh providers
            
            # Priority factor
            score += provider.config.priority * 5
            
            scores.append((provider_type, score))
        
        return scores
    
    def _estimate_cost(self, request: LLMRequest, provider: LLMBase) -> float:
        """
        Estimate cost for this request.
        """
        
        # Rough token estimation: ~4 characters per token
        estimated_tokens = (len(request.prompt) + len(request.system_prompt or "")) // 4
        estimated_output_tokens = (request.max_tokens or 500) * 0.3  # Assume 30% output
        
        if provider.config.provider == LLMProvider.OPENAI:
            if "gpt-4" in provider.config.model:
                return (estimated_tokens * 0.00003 + estimated_output_tokens * 0.00006)
            else:
                return (estimated_tokens * 0.0000015 + estimated_output_tokens * 0.000002)
        
        elif provider.config.provider == LLMProvider.ANTHROPIC:
            if "opus" in provider.config.model:
                return (estimated_tokens * 0.000015 + estimated_output_tokens * 0.000075)
            elif "sonnet" in provider.config.model:
                return (estimated_tokens * 0.000003 + estimated_output_tokens * 0.000015)
            else:
                return (estimated_tokens * 0.00000025 + estimated_output_tokens * 0.00000125)
        
        elif provider.config.provider == LLMProvider.PERPLEXITY:
            return estimated_tokens * 0.000001
        
        elif provider.config.provider == LLMProvider.LOCAL:
            return 0.0  # Free
        
        return 0.001  # Default estimate
    
    def _estimate_time(self, provider: LLMProvider) -> float:
        """
        Estimate execution time based on provider.
        """
        
        latencies = {
            LLMProvider.OPENAI: 1000,      # ~1s
            LLMProvider.ANTHROPIC: 1500,   # ~1.5s
            LLMProvider.PERPLEXITY: 2000,  # ~2s (includes search)
            LLMProvider.LOCAL: 3000,       # ~3s (slower)
            LLMProvider.OFFLINE: 0,
        }
        
        return latencies.get(provider, 1000)
    
    def _init_task_mapping(self) -> Dict[str, List[LLMProvider]]:
        """
        Initialize task type to provider mapping.
        """
        
        return {
            "reasoning": [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.LOCAL],
            "coding": [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.LOCAL],
            "analysis": [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.LOCAL],
            "summary": [LLMProvider.OPENAI, LLMProvider.ANTHROPIC],
            "creative": [LLMProvider.ANTHROPIC, LLMProvider.OPENAI],
            "web_search": [LLMProvider.PERPLEXITY],
            "general": [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.PERPLEXITY],
            "planning": [LLMProvider.ANTHROPIC, LLMProvider.OPENAI],
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics.
        """
        
        total_routed = len(self.routing_history)
        llm_used = sum(1 for d in self.routing_history if d.use_llm)
        skill_used = total_routed - llm_used
        
        total_cost = sum(
            self.providers[d.provider].total_cost 
            for d in self.routing_history 
            if d.use_llm and d.provider in self.providers
        )
        
        return {
            "router_id": self.id,
            "total_decisions": total_routed,
            "llm_used": llm_used,
            "skill_used": skill_used,
            "skill_percentage": f"{(skill_used / max(total_routed, 1)) * 100:.1f}%",
            "total_cost": f"${total_cost:.4f}",
            "providers": {
                p.value: provider.get_stats()
                for p, provider in self.providers.items()
            }
        }
