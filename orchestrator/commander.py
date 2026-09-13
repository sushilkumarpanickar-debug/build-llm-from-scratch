"""
Commander: Strategic Level of the Orchestrator Hierarchy
Handles high-level objectives and coordinates Managers.
"""

import uuid
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from config.settings import (
    COMMANDER_THINK_TIME,
    COMMANDER_NAME,
    NUM_MANAGERS,
    WORKERS_PER_MANAGER,
)
from orchestrator.manager import Manager


@dataclass
class Objective:
    """High-level objective from the user."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=low, 5=high
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed


@dataclass
class ExecutionPlan:
    """Strategic plan decomposed by Commander."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objective_id: str = ""
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    manager_assignments: Dict[str, List[str]] = field(default_factory=dict)
    reasoning: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Final result after execution."""
    objective_id: str = ""
    plan_id: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed
    results: List[Dict[str, Any]] = field(default_factory=list)
    synthesis: str = ""
    execution_time_seconds: float = 0.0
    total_skills_executed: int = 0
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class Commander:
    """
    Strategic-level orchestrator.
    
    Responsibilities:
    - Receive high-level objectives
    - Decompose into tasks
    - Create execution plans
    - Delegate to Managers
    - Synthesize final results
    """
    
    def __init__(
        self,
        name: str = COMMANDER_NAME,
        num_managers: int = NUM_MANAGERS,
        workers_per_manager: int = WORKERS_PER_MANAGER,
    ):
        if num_managers < 1:
            raise ValueError("num_managers must be at least 1")
        if workers_per_manager < 1:
            raise ValueError("workers_per_manager must be at least 1")

        self.id = str(uuid.uuid4())
        self.name = name
        self.num_managers = num_managers
        self.workers_per_manager = workers_per_manager
        
        # Initialize subordinate Managers
        self.managers: List[Manager] = [
            Manager(
                name=f"Manager-{i+1}",
                workers_per_manager=workers_per_manager,
                commander_id=self.id,
            )
            for i in range(num_managers)
        ]
        
        # Tracking
        self.execution_history: List[ExecutionResult] = []
        self.active_objectives: Dict[str, Objective] = {}
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        
        logger.info(
            f"Commander '{self.name}' initialized with {num_managers} managers "
            f"and {workers_per_manager} workers per manager"
        )
    
    def execute(self, objective_description: str, context: Optional[Dict] = None) -> ExecutionResult:
        """
        Execute a high-level objective through the hierarchy.
        
        Args:
            objective_description: High-level objective
            context: Additional context for execution
            
        Returns:
            ExecutionResult with synthesis and details
        """
        start_time = time.time()
        
        # Step 1: Create objective
        objective = Objective(
            description=objective_description,
            context=context or {},
            status="in_progress"
        )
        self.active_objectives[objective.id] = objective
        
        logger.info(f"[COMMANDER] Received objective: {objective_description}")
        
        try:
            # Step 2: Analyze and decompose (strategic thinking)
            logger.info(f"[COMMANDER] Thinking... ({COMMANDER_THINK_TIME}s)")
            time.sleep(COMMANDER_THINK_TIME)
            
            plan = self._create_execution_plan(objective)
            self.execution_plans[plan.id] = plan
            
            logger.info(f"[COMMANDER] Plan created with {len(plan.tasks)} tasks")
            logger.debug(f"[COMMANDER] Reasoning: {plan.reasoning}")
            
            # Step 3: Delegate to managers
            manager_results = self._delegate_to_managers(plan)
            
            # Step 4: Synthesize results
            result = self._synthesize_results(
                objective=objective,
                plan=plan,
                manager_results=manager_results,
                execution_time=time.time() - start_time
            )
            
            # Store result
            self.execution_history.append(result)
            objective.status = "completed"
            
            logger.info(
                f"[COMMANDER] Objective completed in {result.execution_time_seconds:.2f}s "
                f"({result.total_skills_executed} skills executed)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[COMMANDER] Execution failed: {str(e)}")
            objective.status = "failed"
            
            result = ExecutionResult(
                objective_id=objective.id,
                status="failed",
                errors=[str(e)],
                execution_time_seconds=time.time() - start_time
            )
            
            self.execution_history.append(result)
            return result
    
    def _create_execution_plan(self, objective: Objective) -> ExecutionPlan:
        """Decompose objective into tasks and create manager assignments."""
        plan = ExecutionPlan(objective_id=objective.id)
        
        # Strategic decomposition (simplified example)
        # In production, this would use LLM analysis
        
        plan.reasoning = (
            f"Analyzed objective: {objective.description}\n"
            f"Priority level: {objective.priority}/5\n"
            "Decomposed into manageable tasks for parallel execution"
        )
        
        # Create sample tasks (would be LLM-generated in production)
        tasks = [
            {
                "id": str(uuid.uuid4()),
                "name": "Task 1: Information Gathering",
                "description": f"Gather relevant information for: {objective.description[:50]}...",
                "priority": objective.priority,
                "estimated_duration": 5.0,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Task 2: Analysis & Processing",
                "description": "Analyze gathered information and identify key insights",
                "priority": objective.priority - 1 if objective.priority > 1 else 1,
                "estimated_duration": 10.0,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Task 3: Synthesis & Formatting",
                "description": "Synthesize results into final output",
                "priority": objective.priority - 1 if objective.priority > 1 else 1,
                "estimated_duration": 5.0,
            }
        ]
        
        plan.tasks = tasks
        
        # Assign tasks to managers (round-robin)
        for idx, task in enumerate(tasks):
            manager_idx = idx % len(self.managers)
            manager_name = self.managers[manager_idx].name
            
            if manager_name not in plan.manager_assignments:
                plan.manager_assignments[manager_name] = []
            
            plan.manager_assignments[manager_name].append(task["id"])
        
        return plan
    
    def _delegate_to_managers(self, plan: ExecutionPlan) -> List[Dict]:
        """Send tasks to managers for execution."""
        results = []
        
        for manager in self.managers:
            task_ids = plan.manager_assignments.get(manager.name, [])
            
            if not task_ids:
                continue
            
            # Get actual task objects
            tasks_for_manager = [t for t in plan.tasks if t["id"] in task_ids]
            
            logger.info(f"[COMMANDER] Delegating {len(tasks_for_manager)} tasks to {manager.name}")
            
            # Manager processes tasks
            manager_result = manager.execute_tasks(tasks_for_manager)
            results.append(manager_result)
        
        return results
    
    def _synthesize_results(
        self,
        objective: Objective,
        plan: ExecutionPlan,
        manager_results: List[Dict],
        execution_time: float
    ) -> ExecutionResult:
        """Synthesize manager results into final output."""
        
        result = ExecutionResult(
            objective_id=objective.id,
            plan_id=plan.id,
            status="completed",
            execution_time_seconds=execution_time,
        )
        
        # Aggregate results from managers
        total_skills = 0
        all_errors = []
        result_texts = []
        
        for manager_result in manager_results:
            result.results.append(manager_result)
            total_skills += manager_result.get("total_skills_executed", 0)
            all_errors.extend(manager_result.get("errors", []))
            result_texts.append(manager_result.get("synthesis", ""))
        
        result.total_skills_executed = total_skills
        result.errors = all_errors
        
        # Synthesize synthesis
        result.synthesis = self._generate_synthesis(objective, result_texts, plan)
        
        return result
    
    def _generate_synthesis(
        self,
        objective: Objective,
        manager_results: List[str],
        plan: ExecutionPlan
    ) -> str:
        """Generate final synthesis from manager outputs."""
        
        synthesis = f"""
=== EXECUTION SYNTHESIS ===

OBJECTIVE: {objective.description}

EXECUTION PLAN:
{plan.reasoning}

RESULTS FROM EXECUTION:
"""
        
        for idx, result_text in enumerate(manager_results, 1):
            synthesis += f"\n[Manager {idx} Output]:\n{result_text}\n"
        
        synthesis += "\n=== END SYNTHESIS ==="
        
        return synthesis
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Commander and all subordinates."""
        return {
            "commander": {
                "id": self.id,
                "name": self.name,
                "active_objectives": len(self.active_objectives),
                "completed_executions": len(self.execution_history),
            },
            "managers": [
                {
                    "name": manager.name,
                    "active_tasks": len(manager.active_tasks),
                    "workers_count": len(manager.workers),
                }
                for manager in self.managers
            ],
            "workers": sum(len(manager.workers) for manager in self.managers),
        }
    
    def get_execution_history(self, limit: int = 10) -> List[ExecutionResult]:
        """Get recent execution history."""
        return self.execution_history[-limit:]
