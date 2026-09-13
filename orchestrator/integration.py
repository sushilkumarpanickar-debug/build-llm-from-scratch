"""
Integration Layer: Connects all components together
Orchestrator + Skills + RAG + MCP + Work Tracking
"""

import uuid
from typing import Any, Dict, List, Optional
from dataclasses import asdict, dataclass
from datetime import datetime
from loguru import logger

from orchestrator.commander import Commander
from skills.skill_router import SkillRouter, SkillInput
from rag.knowledge_graph import KnowledgeGraph
from mcp.mcp_server import MCPServer
from work_management.work_tracker import WorkTracker


@dataclass
class SystemConfig:
    """Configuration for the integrated system."""
    num_managers: int = 2
    workers_per_manager: int = 2
    enable_rag: bool = True
    enable_mcp: bool = True
    enable_work_tracking: bool = True
    zero_token_mode: bool = True  # Always True


class OrchestratorSystem:
    """
    Integrated LLM Orchestrator System.
    Combines all components: Commander, Managers, Workers, Skills, RAG, MCP, Work Tracking.
    
    Your complete second brain and second-in-command.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.id = str(uuid.uuid4())
        self.config = config or SystemConfig()
        
        # Initialize components
        self.commander = Commander(
            num_managers=self.config.num_managers,
            workers_per_manager=self.config.workers_per_manager,
        )
        
        self.skill_router = SkillRouter()
        self.work_tracker = WorkTracker()
        
        self.knowledge_graph: Optional[KnowledgeGraph] = None
        self.mcp_server: Optional[MCPServer] = None
        
        if self.config.enable_rag:
            self.knowledge_graph = KnowledgeGraph()
        
        if self.config.enable_mcp:
            self.mcp_server = MCPServer()
        
        logger.info(
            f"OrchestratorSystem initialized (ID: {self.id})"
            f" - Zero-Token Mode: ENABLED"
        )
    
    def execute_objective(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a high-level objective through the entire system.
        
        Flow:
        1. Retrieve context from RAG (if enabled)
        2. Commander decomposes objective
        3. Managers plan and allocate work
        4. Workers execute skills
        5. Track work versions
        6. Store results in knowledge graph
        """
        
        logger.info(f"[System] Executing objective: {objective}")
        
        # Step 1: Retrieve RAG context
        rag_context = {}
        if use_rag and self.knowledge_graph:
            rag_result = self.knowledge_graph.query(objective, top_k=3)
            rag_context = {
                "retrieved_documents": rag_result.get("top_results", []),
                "context": rag_result.get("context", []),
            }
            logger.info(f"[System] Retrieved {len(rag_result.get('top_results', []))} RAG results")
        
        # Step 2: Execute through Commander
        merged_context = {**(context or {}), **rag_context}
        execution_result = asdict(self.commander.execute(objective, merged_context))
        
        # Step 3: Track work
        if self.config.enable_work_tracking:
            work = self.work_tracker.create_work(
                name=objective[:50],
                description=objective,
                work_type="objective_execution"
            )
            
            self.work_tracker.add_version(
                work_id=work.id,
                input_data={"objective": objective, "context": merged_context},
                output_data=execution_result,
                skills_used=self._extract_skills_from_result(execution_result),
                execution_time_ms=execution_result.get("execution_time_seconds", 0) * 1000,
                status="completed" if execution_result.get("status") == "completed" else "failed",
            )
        
        # Step 4: Store in knowledge graph
        if self.knowledge_graph:
            self.knowledge_graph.add_document(
                title=f"Execution: {objective[:50]}",
                content=str(execution_result),
                source="system_execution"
            )
        
        return execution_result
    
    def execute_with_skills(
        self,
        entry_skill_id: str,
        input_data: Dict[str, Any],
        track_work: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task through the skill router.
        
        Uses OmniRoute-style intelligent routing.
        Zero-token execution.
        """
        
        logger.info(f"[System] Executing with skill: {entry_skill_id}")
        
        # Prepare input
        skill_input = SkillInput(
            data=input_data,
            context={"system_id": self.id}
        )
        
        # Execute through router
        result = self.skill_router.execute_path(entry_skill_id, skill_input)
        
        # Track work
        if track_work and self.config.enable_work_tracking:
            work = self.work_tracker.create_work(
                name=f"Skill Execution",
                description=f"Executed through skill routing",
                work_type="skill_execution"
            )
            
            self.work_tracker.add_version(
                work_id=work.id,
                input_data=input_data,
                output_data=result,
                skills_used=result.get("skills_executed", []),
                execution_time_ms=result.get("execution_time_ms", 0),
                status="completed",
            )
        
        return result
    
    def add_knowledge(
        self,
        title: str,
        content: str,
        source: str = "user_input"
    ) -> Optional[Dict[str, Any]]:
        """
        Add knowledge to the system's second brain (knowledge graph).
        """
        
        if not self.knowledge_graph:
            logger.warning("[System] RAG not enabled")
            return None
        
        doc = self.knowledge_graph.add_document(title, content, source)
        
        return {
            "document_id": doc.id,
            "title": doc.title,
            "chunks": len(doc.chunks),
            "entities": len(doc.entities),
            "tokens_used": 0,
        }
    
    def query_knowledge(
        self,
        query: str,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Query the knowledge graph.
        """
        
        if not self.knowledge_graph:
            logger.warning("[System] RAG not enabled")
            return None
        
        return self.knowledge_graph.query(query, top_k)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        """
        
        status = {
            "system_id": self.id,
            "mode": "Zero-Token / Unlimited Credits",
            "commander": self.commander.get_status(),
            "work_tracking": self.work_tracker.get_all_stats() if self.config.enable_work_tracking else None,
        }
        
        if self.knowledge_graph:
            status["knowledge_graph"] = self.knowledge_graph.get_stats()
        
        if self.mcp_server:
            status["mcp_server"] = self.mcp_server.get_stats()
        
        status["skill_router"] = self.skill_router.get_stats()
        
        return status
    
    def _extract_skills_from_result(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract skill names from execution result.
        """
        
        skills = []
        
        if "results" in result:
            for manager_result in result.get("results", []):
                synthesis = manager_result.get("synthesis", "")
                # Simple extraction - could be enhanced
                if "Skill" in synthesis:
                    skills.append("skill_execution")
        
        return skills
