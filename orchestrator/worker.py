"""
Worker: Execution Level of the Orchestrator Hierarchy
Executes skills with zero LLM API calls.
"""

import uuid
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from config.settings import (
    WORKER_EXECUTE_TIME,
    SKILLS_ZERO_TOKEN_MODE,
)


@dataclass
class SkillExecution:
    """Record of a skill execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = ""
    skill_version: str = "1.0"
    status: str = "pending"
    execution_time_seconds: float = 0.0
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0  # Should be 0 for zero-token mode
    created_at: datetime = field(default_factory=datetime.now)


class Worker:
    """
    Execution-level worker.
    
    Responsibilities:
    - Execute assigned tasks using skills
    - No direct LLM API calls (zero-token mode)
    - Track skill execution with versioning
    - Report results to Manager
    """
    
    def __init__(self, name: str, manager_id: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.manager_id = manager_id
        
        # Skill tracking
        self.active_skills: Dict[str, SkillExecution] = {}
        self.completed_skills: List[SkillExecution] = []
        self.total_skills_executed = 0
        
        logger.info(f"Worker '{self.name}' initialized (Zero-Token Mode: {SKILLS_ZERO_TOKEN_MODE})")
    
    def execute_skills(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        Execute skills for assigned tasks.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        logger.info(f"[{self.name}] Starting execution of {len(tasks)} tasks")
        
        results = []
        errors = []
        
        for task in tasks:
            try:
                logger.info(f"[{self.name}] Executing: {task.name}")
                
                # Simulate skill execution
                skill_result = self._execute_skill(task)
                
                results.append(skill_result)
                self.completed_skills.append(skill_result)
                self.total_skills_executed += 1
                
                logger.info(f"[{self.name}] ✓ Completed: {task.name}")
                
            except Exception as e:
                logger.error(f"[{self.name}] ✗ Failed: {task.name} - {str(e)}")
                errors.append(str(e))
        
        execution_time = time.time() - start_time
        
        result = {
            "worker_id": self.id,
            "worker_name": self.name,
            "status": "completed" if not errors else "partial",
            "total_tasks": len(tasks),
            "successful_tasks": len(results),
            "failed_tasks": len(errors),
            "total_skills_executed": len(results),
            "execution_time": execution_time,
            "tokens_used": 0,  # Zero-token mode
            "errors": errors,
            "result": self._generate_result_summary(results),
        }
        
        logger.info(
            f"[{self.name}] Execution complete: "
            f"{len(results)}/{len(tasks)} tasks successful in {execution_time:.2f}s"
        )
        
        return result
    
    def _execute_skill(self, task: Any) -> SkillExecution:
        """Execute a single skill for a task."""
        
        skill_exec = SkillExecution(
            skill_name=f"skill_for_{task.name}",
            status="in_progress"
        )
        
        start_time = time.time()
        
        # Simulate skill execution
        logger.debug(f"[{self.name}] Executing skill: {skill_exec.skill_name}")
        
        time.sleep(WORKER_EXECUTE_TIME)  # Simulate work
        
        # Process input
        skill_exec.input_data = {
            "task_id": task.id,
            "task_name": task.name,
            "task_description": task.description,
        }
        
        # Execute skill logic (zero-token mode - no LLM calls)
        skill_exec.output_data = self._execute_skill_logic(skill_exec.input_data)
        
        skill_exec.status = "completed"
        skill_exec.execution_time_seconds = time.time() - start_time
        skill_exec.tokens_used = 0  # Zero-token mode
        
        return skill_exec
    
    def _execute_skill_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the actual skill logic.
        This is where local processing happens without LLM calls.
        """
        
        task_name = input_data.get("task_name", "")
        task_desc = input_data.get("task_description", "")
        
        # Example skill implementations (zero-token)
        output = {
            "processed": True,
            "task_name": task_name,
            "status": "processed",
        }
        
        # Skill-specific logic
        if "gathering" in task_name.lower():
            output["action"] = "Gathered information through local sources"
            output["items_processed"] = 5
            
        elif "analysis" in task_name.lower():
            output["action"] = "Analyzed data locally"
            output["insights_found"] = 3
            
        elif "synthesis" in task_name.lower():
            output["action"] = "Synthesized results into formatted output"
            output["output_format"] = "structured"
        
        else:
            output["action"] = "Generic task processing"
            output["items_processed"] = 10
        
        return output
    
    def _generate_result_summary(self, results: List[SkillExecution]) -> str:
        """Generate summary of skill execution results."""
        
        summary = f"\n[{self.name} Results]:\n"
        summary += f"Total Skills Executed: {len(results)}\n"
        summary += f"Total Execution Time: {sum(r.execution_time_seconds for r in results):.2f}s\n"
        summary += f"Tokens Used: 0 (Zero-Token Mode)\n\n"
        
        summary += "Skill Details:\n"
        for exec_record in results:
            summary += (
                f"  • {exec_record.skill_name}: "
                f"{exec_record.status} ({exec_record.execution_time_seconds:.2f}s)\n"
            )
            if exec_record.output_data:
                summary += f"    Output: {exec_record.output_data.get('action', 'N/A')}\n"
        
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of this Worker."""
        return {
            "id": self.id,
            "name": self.name,
            "active_skills": len(self.active_skills),
            "completed_skills": len(self.completed_skills),
            "total_skills_executed": self.total_skills_executed,
            "zero_token_mode": SKILLS_ZERO_TOKEN_MODE,
        }
    
    def get_skill_history(self, limit: int = 10) -> List[SkillExecution]:
        """Get recent skill execution history."""
        return self.completed_skills[-limit:]
