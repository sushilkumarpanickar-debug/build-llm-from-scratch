"""
Work Management: Track, version, and manage repeated work
Integrates skill execution with versioning and history
"""

import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from loguru import logger

from config.settings import (
    WORK_VERSIONING_ENABLED,
    WORK_VERSION_HISTORY_SIZE,
    EXECUTION_LOG_RETENTION_DAYS,
)


@dataclass
class WorkVersion:
    """Version of a work item."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    work_id: str = ""
    version_number: int = 1
    status: str = "pending"  # pending, in_progress, completed, failed
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    tokens_used: int = 0  # Always 0
    skills_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Work:
    """Work item with version history."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    work_type: str = ""  # skill_execution, analysis, synthesis, etc.
    versions: List[WorkVersion] = field(default_factory=list)
    latest_version: Optional[WorkVersion] = None
    current_status: str = "pending"
    execution_count: int = 0
    success_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class WorkTracker:
    """
    Track, version, and manage work items.
    Provides version history and comparison capabilities.
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.works: Dict[str, Work] = {}
        self.version_history: Dict[str, List[WorkVersion]] = defaultdict(list)
        self.execution_log: List[Dict[str, Any]] = []
        
        logger.info("WorkTracker initialized (Versioning: ENABLED)")
    
    def create_work(self, name: str, description: str, work_type: str = "skill_execution") -> Work:
        """
        Create a new work item.
        """
        
        work = Work(
            name=name,
            description=description,
            work_type=work_type,
        )
        
        self.works[work.id] = work
        logger.info(f"Work created: {name} ({work_type})")
        
        return work
    
    def add_version(
        self,
        work_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        skills_used: List[str],
        execution_time_ms: float,
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> WorkVersion:
        """
        Add a new version to a work item.
        """
        
        if work_id not in self.works:
            logger.error(f"Work not found: {work_id}")
            return None
        
        work = self.works[work_id]
        version_number = len(work.versions) + 1
        
        version = WorkVersion(
            work_id=work_id,
            version_number=version_number,
            status=status,
            input_data=input_data,
            output_data=output_data,
            execution_time_ms=execution_time_ms,
            tokens_used=0,  # Zero-token mode
            skills_used=skills_used,
            error_message=error_message,
            completed_at=datetime.now() if status == "completed" else None,
        )
        
        work.versions.append(version)
        work.latest_version = version
        work.execution_count += 1
        work.updated_at = datetime.now()
        work.current_status = status
        
        if status == "completed":
            work.success_count += 1
        
        self.version_history[work_id].append(version)
        
        # Trim history if too large
        if len(work.versions) > WORK_VERSION_HISTORY_SIZE:
            work.versions.pop(0)
        
        logger.info(
            f"Version {version_number} added to {work.name} "
            f"({len(work.versions)} total versions)"
        )
        
        return version
    
    def compare_versions(
        self,
        work_id: str,
        version_num_1: int,
        version_num_2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of a work item.
        """
        
        if work_id not in self.works:
            return {"error": "Work not found"}
        
        work = self.works[work_id]
        
        if version_num_1 > len(work.versions) or version_num_2 > len(work.versions):
            return {"error": "Version not found"}
        
        v1 = work.versions[version_num_1 - 1]
        v2 = work.versions[version_num_2 - 1]
        
        comparison = {
            "work_id": work_id,
            "work_name": work.name,
            "version_1": {
                "number": v1.version_number,
                "status": v1.status,
                "execution_time_ms": v1.execution_time_ms,
                "created_at": v1.created_at.isoformat(),
            },
            "version_2": {
                "number": v2.version_number,
                "status": v2.status,
                "execution_time_ms": v2.execution_time_ms,
                "created_at": v2.created_at.isoformat(),
            },
            "differences": {
                "status_changed": v1.status != v2.status,
                "time_improvement_ms": v1.execution_time_ms - v2.execution_time_ms,
                "skills_changed": v1.skills_used != v2.skills_used,
            }
        }
        
        return comparison
    
    def get_version_history(self, work_id: str) -> List[WorkVersion]:
        """
        Get full version history for a work item.
        """
        
        if work_id not in self.works:
            return []
        
        return self.works[work_id].versions
    
    def get_work_stats(self, work_id: str) -> Dict[str, Any]:
        """
        Get statistics for a work item.
        """
        
        if work_id not in self.works:
            return {"error": "Work not found"}
        
        work = self.works[work_id]
        
        if not work.versions:
            return {
                "work_id": work_id,
                "work_name": work.name,
                "versions": 0,
                "status": "no_executions"
            }
        
        execution_times = [v.execution_time_ms for v in work.versions]
        
        stats = {
            "work_id": work_id,
            "work_name": work.name,
            "work_type": work.work_type,
            "total_versions": len(work.versions),
            "execution_count": work.execution_count,
            "success_count": work.success_count,
            "success_rate": work.success_count / max(work.execution_count, 1),
            "latest_status": work.current_status,
            "execution_times": {
                "min_ms": min(execution_times),
                "max_ms": max(execution_times),
                "avg_ms": sum(execution_times) / len(execution_times),
            },
            "total_tokens_used": 0,  # Zero-token mode
            "created_at": work.created_at.isoformat(),
            "updated_at": work.updated_at.isoformat(),
        }
        
        return stats
    
    def log_execution(
        self,
        work_id: str,
        task_description: str,
        execution_result: Dict[str, Any]
    ) -> None:
        """
        Log an execution in the execution history.
        """
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "work_id": work_id,
            "task_description": task_description,
            "result": execution_result,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.execution_log.append(log_entry)
        logger.info(f"Execution logged for work {work_id}")
    
    def get_execution_log(
        self,
        work_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get execution log (filtered by work_id if provided).
        """
        
        if work_id:
            filtered = [log for log in self.execution_log if log["work_id"] == work_id]
        else:
            filtered = self.execution_log
        
        return filtered[-limit:]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics across all work items.
        """
        
        total_versions = sum(len(w.versions) for w in self.works.values())
        total_executions = sum(w.execution_count for w in self.works.values())
        total_successes = sum(w.success_count for w in self.works.values())
        
        return {
            "tracker_id": self.id,
            "total_works": len(self.works),
            "total_versions": total_versions,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / max(total_executions, 1),
            "total_tokens_used": 0,  # Zero-token mode
            "execution_log_size": len(self.execution_log),
        }
