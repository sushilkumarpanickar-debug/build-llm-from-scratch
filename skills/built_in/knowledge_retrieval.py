"""
Knowledge Retrieval Skill: Retrieve and format knowledge from graph
Zero-token execution - no LLM calls
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from skills.skill_base import Skill, SkillInput, SkillOutput, SkillType


class KnowledgeRetrievalSkill(Skill):
    """Retrieve knowledge from the knowledge graph without LLM calls."""
    
    def __init__(self):
        super().__init__(
            name="Knowledge Retrieval",
            skill_type=SkillType.RETRIEVAL,
            description="Retrieve and format knowledge from graph",
            version="1.0",
            routing_rules={
                "success:true": ["Synthesis"],
                "success:false": [],
            }
        )
        self.knowledge_base = self._initialize_knowledge_base()
    
    def execute(self, skill_input: SkillInput) -> SkillOutput:
        """Execute knowledge retrieval."""
        
        output = SkillOutput()
        query = skill_input.data.get("query", "")
        retrieval_type = skill_input.data.get("retrieval_type", "semantic")
        
        try:
            if retrieval_type == "semantic":
                result = self._semantic_retrieval(query)
            elif retrieval_type == "keyword":
                result = self._keyword_retrieval(query)
            elif retrieval_type == "graph":
                result = self._graph_traversal(query)
            else:
                result = self._semantic_retrieval(query)
            
            output.output_data = result
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {str(e)}")
            output.output_data = {"error": str(e), "success": False}
        
        return output
    
    def can_handle(self, task_description: str) -> bool:
        """Check if this skill can handle the task."""
        keywords = ["retrieve", "query", "find", "search", "knowledge", "knowledge base"]
        return any(kw in task_description.lower() for kw in keywords)
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize a simple knowledge base."""
        
        return {
            "documents": [
                {"id": "doc1", "title": "LLM Orchestrator Architecture", "content": "Three-tier hierarchy system"},
                {"id": "doc2", "title": "Skill System", "content": "Reusable skills with zero-token execution"},
                {"id": "doc3", "title": "Graph-Based RAG", "content": "Knowledge graph for retrieval"},
            ],
            "entities": [
                {"name": "Commander", "type": "role", "description": "Strategic level orchestrator"},
                {"name": "Manager", "type": "role", "description": "Tactical level coordinator"},
                {"name": "Worker", "type": "role", "description": "Execution level processor"},
            ],
            "relationships": [
                {"from": "Commander", "to": "Manager", "type": "delegates_to"},
                {"from": "Manager", "to": "Worker", "type": "coordinates"},
            ]
        }
    
    def _semantic_retrieval(self, query: str) -> Dict[str, Any]:
        """Retrieve semantically similar knowledge."""
        
        # Simple keyword matching (would use embeddings in production)
        query_lower = query.lower()
        matched_docs = []
        matched_entities = []
        
        for doc in self.knowledge_base["documents"]:
            if any(word in doc["content"].lower() for word in query_lower.split()):
                matched_docs.append(doc)
        
        for entity in self.knowledge_base["entities"]:
            if any(word in entity["description"].lower() for word in query_lower.split()):
                matched_entities.append(entity)
        
        return {
            "success": True,
            "retrieval_type": "semantic",
            "query": query,
            "matched_documents": matched_docs,
            "matched_entities": matched_entities,
            "match_count": len(matched_docs) + len(matched_entities),
        }
    
    def _keyword_retrieval(self, query: str) -> Dict[str, Any]:
        """Retrieve by exact keyword match."""
        
        keywords = query.lower().split()
        results = []
        
        for doc in self.knowledge_base["documents"]:
            for keyword in keywords:
                if keyword in doc["title"].lower() or keyword in doc["content"].lower():
                    results.append(doc)
                    break
        
        return {
            "success": True,
            "retrieval_type": "keyword",
            "query": query,
            "keywords": keywords,
            "results": results,
            "match_count": len(results),
        }
    
    def _graph_traversal(self, query: str) -> Dict[str, Any]:
        """Traverse the knowledge graph."""
        
        # Find starting node
        start_entity = None
        for entity in self.knowledge_base["entities"]:
            if query.lower() in entity["name"].lower():
                start_entity = entity
                break
        
        if not start_entity:
            return {
                "success": False,
                "retrieval_type": "graph",
                "error": "Starting entity not found"
            }
        
        # Traverse relationships
        connected = []
        for rel in self.knowledge_base["relationships"]:
            if rel["from"] == start_entity["name"]:
                connected.append(rel)
        
        return {
            "success": True,
            "retrieval_type": "graph",
            "query": query,
            "start_entity": start_entity,
            "connected_to": connected,
            "traversal_depth": 1,
        }
