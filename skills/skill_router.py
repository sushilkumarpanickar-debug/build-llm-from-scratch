"""
OmniRoute-style Skill Router: Intelligent task routing with zero-token execution
Routes work through skills without consuming LLM API tokens or credits
"""

import uuid
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from config.settings import (
    SKILLS_ZERO_TOKEN_MODE,
)
from skills.skill_base import Skill, SkillInput, SkillOutput, SkillStatus, SkillType


class RoutingStrategy(Enum):
    """Strategies for routing tasks through skills."""
    SEQUENTIAL = "sequential"           # Execute skills one after another
    PARALLEL = "parallel"               # Execute multiple skills in parallel
    CONDITIONAL = "conditional"         # Route based on conditions
    LOOP = "loop"                       # Repeat until condition met
    FALLBACK = "fallback"               # Try alternative skills if primary fails


@dataclass
class RoutingRule:
    """Rule for routing tasks to skills."""
    source_skill: str
    target_skill: str
    condition: Optional[str] = None
    priority: int = 1
    strategy: RoutingStrategy = RoutingStrategy.SEQUENTIAL


@dataclass
class RoutingPath:
    """A path through skills for task execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_ids: List[str] = field(default_factory=list)
    strategy: RoutingStrategy = RoutingStrategy.SEQUENTIAL
    total_cost_tokens: int = 0  # ALWAYS 0 - zero-token mode
    total_cost_credits: int = 0  # ALWAYS 0 - unlimited
    execution_count: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


class SkillRouter:
    """
    Intelligent router for task execution through skills.
    OmniRoute-style architecture with zero token/credit consumption.
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.skills: Dict[str, Skill] = {}
        self.skill_graph: Dict[str, List[RoutingRule]] = {}
        self.routing_paths: Dict[str, RoutingPath] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info("SkillRouter initialized (Zero-Token Mode: ENABLED)")
    
    def register_skill(self, skill: Skill) -> None:
        """Register a skill in the router."""
        self.skills[skill.id] = skill
        self.skill_graph[skill.id] = []
        logger.info(f"Skill registered: {skill.name} (ID: {skill.id})")
    
    def register_routing_rule(self, rule: RoutingRule) -> None:
        """Register a routing rule between skills."""
        if rule.source_skill not in self.skill_graph:
            self.skill_graph[rule.source_skill] = []
        
        self.skill_graph[rule.source_skill].append(rule)
        logger.info(
            f"Routing rule: {self._get_skill_name(rule.source_skill)} "
            f"→ {self._get_skill_name(rule.target_skill)} ({rule.strategy.value})"
        )
    
    def execute_path(
        self,
        entry_skill_id: str,
        initial_input: SkillInput,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a task through a skill path using intelligent routing.
        Zero tokens/credits consumed.
        """
        
        start_time = datetime.now()
        path_id = str(uuid.uuid4())
        execution_log = []
        current_output: Optional[SkillOutput] = None
        visited_skills: Set[str] = set()
        iteration = 0
        
        logger.info(f"[Router {path_id}] Starting execution from skill {self._get_skill_name(entry_skill_id)}")
        
        try:
            current_skill_id = entry_skill_id
            
            while current_skill_id and iteration < max_iterations:
                iteration += 1
                
                if current_skill_id not in self.skills:
                    logger.warning(f"[Router {path_id}] Skill not found: {current_skill_id}")
                    break
                
                skill = self.skills[current_skill_id]
                visited_skills.add(current_skill_id)
                
                logger.info(f"[Router {path_id}] Executing: {skill.name}")
                
                # Execute skill (NO TOKEN COST - ZERO-TOKEN MODE)
                current_output = skill.run(initial_input)
                execution_log.append(current_output.to_dict())
                
                # Check for errors
                if current_output.status == SkillStatus.FAILED:
                    logger.warning(f"[Router {path_id}] Skill failed: {skill.name}")
                    # Try fallback if available
                    current_skill_id = self._get_fallback_skill(current_skill_id)
                    if current_skill_id:
                        logger.info(f"[Router {path_id}] Attempting fallback: {self._get_skill_name(current_skill_id)}")
                    continue
                
                # Route to next skill based on output
                next_skill_id = self._determine_next_skill(current_skill_id, current_output)
                
                if next_skill_id and next_skill_id not in visited_skills:
                    # Prepare input for next skill
                    initial_input = SkillInput(
                        data=current_output.output_data,
                        context=initial_input.context,
                        metadata={
                            "previous_skill": skill.name,
                            "iteration": iteration,
                        }
                    )
                    current_skill_id = next_skill_id
                else:
                    # No more skills to execute
                    current_skill_id = None
            
            # Aggregate results
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "status": "completed" if current_output and current_output.status == SkillStatus.COMPLETED else "failed",
                "path_id": path_id,
                "execution_steps": len(execution_log),
                "skills_executed": [log["skill_name"] for log in execution_log],
                "execution_log": execution_log,
                "final_output": current_output.output_data if current_output else None,
                "execution_time_ms": execution_time_ms,
                "total_tokens_used": 0,  # ZERO-TOKEN MODE
                "total_credits_used": 0,  # UNLIMITED CREDITS
                "iterations": iteration,
            }
            
            # Store in history
            self.execution_history.append(result)
            
            logger.info(
                f"[Router {path_id}] Completed in {execution_time_ms:.2f}ms "
                f"- {len(execution_log)} skills executed, 0 tokens used"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[Router {path_id}] Routing failed: {str(e)}")
            
            return {
                "status": "failed",
                "path_id": path_id,
                "error": str(e),
                "execution_log": execution_log,
                "total_tokens_used": 0,  # ZERO-TOKEN MODE
                "total_credits_used": 0,  # UNLIMITED CREDITS
            }
    
    def execute_parallel(
        self,
        skill_ids: List[str],
        initial_input: SkillInput
    ) -> Dict[str, Any]:
        """
        Execute multiple skills in parallel (simulated).
        Zero tokens/credits consumed.
        """
        
        start_time = datetime.now()
        path_id = str(uuid.uuid4())
        results = []
        
        logger.info(f"[Router {path_id}] Executing {len(skill_ids)} skills in parallel")
        
        for skill_id in skill_ids:
            if skill_id not in self.skills:
                continue
            
            skill = self.skills[skill_id]
            output = skill.run(initial_input)
            results.append(output.to_dict())
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "status": "completed",
            "path_id": path_id,
            "execution_strategy": "parallel",
            "skills_executed": [self.skills[sid].name for sid in skill_ids],
            "execution_log": results,
            "execution_time_ms": execution_time_ms,
            "total_tokens_used": 0,  # ZERO-TOKEN MODE
            "total_credits_used": 0,  # UNLIMITED CREDITS
        }
        
        self.execution_history.append(result)
        logger.info(f"[Router {path_id}] Parallel execution completed in {execution_time_ms:.2f}ms")
        
        return result
    
    def _determine_next_skill(
        self,
        current_skill_id: str,
        current_output: SkillOutput
    ) -> Optional[str]:
        """Determine the next skill to execute based on routing rules."""
        
        if current_skill_id not in self.skill_graph:
            return None
        
        rules = self.skill_graph[current_skill_id]
        
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            if rule.condition is None or self._evaluate_condition(rule.condition, current_output.output_data):
                return rule.target_skill
        
        return None
    
    def _get_fallback_skill(self, skill_id: str) -> Optional[str]:
        """Get a fallback skill if primary fails."""
        
        if skill_id not in self.skill_graph:
            return None
        
        rules = self.skill_graph[skill_id]
        
        for rule in rules:
            if rule.strategy == RoutingStrategy.FALLBACK:
                return rule.target_skill
        
        return None
    
    def _evaluate_condition(self, condition: str, data: Dict) -> bool:
        """Evaluate a routing condition."""
        if not condition or not data:
            return True
        
        # Simple condition evaluation
        if ":" in condition:
            key, expected = condition.split(":")
            return str(data.get(key)) == expected
        
        return True
    
    def _get_skill_name(self, skill_id: str) -> str:
        """Get skill name from ID."""
        if skill_id in self.skills:
            return self.skills[skill_id].name
        return skill_id[:8]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        
        total_tokens = 0  # ALWAYS 0
        total_credits = 0  # ALWAYS 0
        
        return {
            "router_id": self.id,
            "total_skills": len(self.skills),
            "total_routes": len(self.routing_paths),
            "executions": len(self.execution_history),
            "total_tokens_used": total_tokens,  # ZERO-TOKEN MODE
            "total_credits_used": total_credits,  # UNLIMITED
            "mode": "Zero-Token / Unlimited Credits",
            "skills": [
                skill.get_stats() for skill in self.skills.values()
            ]
        }
