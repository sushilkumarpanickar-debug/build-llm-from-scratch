"""
Skill Base: Foundation for all reusable work units
Mimics OmniRoute's intelligent routing and execution model
"""

import uuid
import time
import re
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger

from config.settings import (
    SKILL_CACHE_ENABLED,
    SKILL_CACHE_TTL_SECONDS,
    SKILL_VERSION_RETENTION,
    SKILLS_ZERO_TOKEN_MODE,
)


class SkillType(Enum):
    """Types of skills the system can execute."""
    TRANSFORMATION = "transformation"      # Data transformation
    EXTRACTION = "extraction"              # Information extraction
    ANALYSIS = "analysis"                  # Data analysis
    SYNTHESIS = "synthesis"                # Result synthesis
    RETRIEVAL = "retrieval"                # Knowledge retrieval
    ROUTING = "routing"                    # Task routing
    VALIDATION = "validation"              # Validation logic


class SkillStatus(Enum):
    """Skill execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class SkillInput:
    """Structured input for skill execution."""
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillOutput:
    """Structured output from skill execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = ""
    skill_version: str = "1.0"
    status: SkillStatus = SkillStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    tokens_used: int = 0  # Always 0 in zero-token mode
    cache_hit: bool = False
    next_skills: List[str] = field(default_factory=list)  # Routing info
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_time_ms": self.execution_time_ms,
            "tokens_used": self.tokens_used,
            "cache_hit": self.cache_hit,
            "next_skills": self.next_skills,
        }


@dataclass
class SkillVersion:
    """Version tracking for skills."""
    version: str
    skill_id: str
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    changes: str = ""


class Skill(ABC):
    """
    Abstract base class for all skills.
    Implements OmniRoute-style routing and execution.
    """
    
    def __init__(
        self,
        name: str,
        skill_type: SkillType,
        description: str = "",
        version: str = "1.0",
        dependencies: Optional[List[str]] = None,
        routing_rules: Optional[Dict[str, Any]] = None,
        slug: Optional[str] = None,
        input_schema: Optional[Dict[str, str]] = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.skill_type = skill_type
        self.description = description
        self.version = version
        self.dependencies = dependencies or []
        self.routing_rules = routing_rules or {}
        self.slug = slug or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        self.input_schema = input_schema or {}
        
        # Execution tracking
        self.execution_count = 0
        self.total_execution_time_ms = 0.0
        self.success_count = 0
        self.cache: Dict[str, SkillOutput] = {}
        self.versions: List[SkillVersion] = []
        
        logger.info(f"Skill initialized: {name} ({skill_type.value})")
    
    @abstractmethod
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        """
        Execute the skill.
        Subclasses must implement this.
        """
        pass
    
    @abstractmethod
    def can_handle(self, task_description: str) -> bool:
        """
        Determine if this skill can handle the task.
        Used for intelligent routing.
        """
        pass
    
    def run(self, skill_input: SkillInput) -> SkillOutput:
        """
        Run the skill with caching, error handling, and routing.
        This is the entry point called by the worker.
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(skill_input)
        if SKILL_CACHE_ENABLED and cache_key in self.cache:
            cached_output = self.cache[cache_key]
            cached_output.cache_hit = True
            logger.info(f"[{self.name}] Cache HIT - {cache_key}")
            return cached_output
        
        try:
            # Execute skill
            output = self.execute(skill_input)
            output.skill_name = self.name
            output.skill_version = self.version
            output.status = SkillStatus.COMPLETED
            output.tokens_used = 0  # Zero-token mode
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            output.execution_time_ms = execution_time_ms
            
            # Determine next skills (routing)
            output.next_skills = self._determine_next_skills(output)
            
            # Cache result
            if SKILL_CACHE_ENABLED:
                self.cache[cache_key] = output
            
            # Update tracking
            self.execution_count += 1
            self.success_count += 1
            self.total_execution_time_ms += execution_time_ms
            
            logger.info(
                f"[{self.name}] Executed successfully in {execution_time_ms:.2f}ms "
                f"→ Next: {output.next_skills}"
            )
            
            return output
            
        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {str(e)}")
            
            output = SkillOutput(
                skill_name=self.name,
                skill_version=self.version,
                status=SkillStatus.FAILED,
                input_data=skill_input.data,
                execution_time_ms=(time.time() - start_time) * 1000,
                tokens_used=0,
            )
            
            self.execution_count += 1
            return output
    
    def _generate_cache_key(self, skill_input: SkillInput) -> str:
        """Generate a cache key from input."""
        import hashlib
        import json
        
        key_data = json.dumps(skill_input.data, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _determine_next_skills(self, output: SkillOutput) -> List[str]:
        """
        Determine which skills should execute next based on output.
        Implements OmniRoute-style intelligent routing.
        """
        next_skills = []
        
        # Check routing rules
        for condition, next_skill_names in self.routing_rules.items():
            # Simple condition evaluation
            if self._evaluate_condition(condition, output.output_data):
                if isinstance(next_skill_names, str):
                    next_skills.append(next_skill_names)
                else:
                    next_skills.extend(next_skill_names)
        
        return next_skills
    
    def _evaluate_condition(self, condition: str, data: Dict) -> bool:
        """Evaluate a routing condition against output data."""
        # Simplified condition evaluation
        # In production, this would use a more sophisticated evaluation engine
        if not condition or not data:
            return False
        
        # Example: "success:true" checks if data['success'] == True
        if ":" in condition:
            key, expected = condition.split(":")
            return str(data.get(key)) == expected
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics for this skill."""
        avg_time = (
            self.total_execution_time_ms / self.execution_count
            if self.execution_count > 0
            else 0
        )
        success_rate = (
            (self.success_count / self.execution_count)
            if self.execution_count > 0
            else 0
        )
        
        return {
            "slug": self.slug,
            "name": self.name,
            "type": self.skill_type.value,
            "description": self.description,
            "version": self.version,
            "input_schema": self.input_schema,
            "side_effect_free": True,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "avg_execution_time_ms": avg_time,
            "total_execution_time_ms": self.total_execution_time_ms,
            "cache_size": len(self.cache),
        }
