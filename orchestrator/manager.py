"""
Manager: Tactical level of the orchestrator hierarchy.
Plans assigned work, distributes it to local workers, and reports aggregation.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger

from config.settings import MANAGER_PLAN_TIME
from orchestrator.worker import Worker


@dataclass
class Task:
    """A locally executable task created by the Commander."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: int = 1
    estimated_duration: float = 0.0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)


class Manager:
    """Coordinate a fixed pool of local workers for a Commander."""

    def __init__(self, name: str, workers_per_manager: int, commander_id: str):
        if workers_per_manager < 1:
            raise ValueError("workers_per_manager must be at least 1")

        self.id = str(uuid.uuid4())
        self.name = name
        self.commander_id = commander_id
        self.workers = [
            Worker(name=f"{name}-Worker-{index + 1}", manager_id=self.id)
            for index in range(workers_per_manager)
        ]
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []

        logger.info(f"Manager '{self.name}' initialized with {len(self.workers)} workers")

    def execute_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Plan, allocate, and execute Commander tasks through local workers."""
        start_time = time.time()
        normalized_tasks = [self._coerce_task(task) for task in tasks]
        self.active_tasks.update({task.id: task for task in normalized_tasks})

        if MANAGER_PLAN_TIME:
            time.sleep(MANAGER_PLAN_TIME)

        assignments: List[List[Task]] = [[] for _ in self.workers]
        for index, task in enumerate(normalized_tasks):
            task.status = "in_progress"
            assignments[index % len(self.workers)].append(task)

        worker_results = []
        errors = []
        for worker, assigned_tasks in zip(self.workers, assignments):
            if not assigned_tasks:
                continue
            worker_result = worker.execute_skills(assigned_tasks)
            worker_results.append(worker_result)
            errors.extend(worker_result["errors"])
            for task in assigned_tasks:
                task.status = "completed" if not worker_result["errors"] else "partial"
                self.active_tasks.pop(task.id, None)
                self.completed_tasks.append(task)

        successful_tasks = sum(result["successful_tasks"] for result in worker_results)
        return {
            "manager_id": self.id,
            "manager_name": self.name,
            "status": "completed" if not errors else "partial",
            "total_tasks": len(normalized_tasks),
            "successful_tasks": successful_tasks,
            "failed_tasks": len(normalized_tasks) - successful_tasks,
            "total_skills_executed": sum(
                result["total_skills_executed"] for result in worker_results
            ),
            "execution_time": time.time() - start_time,
            "errors": errors,
            "worker_results": worker_results,
            "synthesis": "\n".join(result["result"] for result in worker_results),
        }

    @staticmethod
    def _coerce_task(task: Any) -> Task:
        if isinstance(task, Task):
            return task
        if isinstance(task, dict):
            return Task(
                id=task.get("id", str(uuid.uuid4())),
                name=task.get("name", ""),
                description=task.get("description", ""),
                priority=task.get("priority", 1),
                estimated_duration=task.get("estimated_duration", 0.0),
            )
        return Task(
            id=getattr(task, "id", str(uuid.uuid4())),
            name=getattr(task, "name", ""),
            description=getattr(task, "description", ""),
            priority=getattr(task, "priority", 1),
            estimated_duration=getattr(task, "estimated_duration", 0.0),
        )
