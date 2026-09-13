"""
Graph-Based RAG System: Knowledge graph with document indexing
Your second brain for persistent knowledge management
"""

import uuid
import json
import os
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from loguru import logger

from config.settings import (
    GRAPH_MAX_DEPTH,
    RAG_RETRIEVE_TOP_K,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
)


@dataclass
class Document:
    """Document indexed in the knowledge graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    source: str = ""  # URL, file path, etc.
    chunks: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphNode:
    """Node in the knowledge graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str = ""  # document, entity, concept
    label: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    embeddings: List[float] = field(default_factory=list)  # For semantic search
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """Edge in the knowledge graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    edge_type: str = ""  # mentions, relates_to, extracted_from, etc.
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class KnowledgeGraph:
    """
    Graph-based RAG system for knowledge management.
    Acts as your second brain for persistent learning.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.id = str(uuid.uuid4())
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.documents: Dict[str, Document] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self.storage_path = storage_path
        self._loading = False
        self._load()
        
        logger.info("KnowledgeGraph initialized (Your Second Brain)")
    
    def add_document(self, title: str, content: str, source: str = "") -> Document:
        """
        Add a document to the knowledge graph.
        Automatically chunks and indexes content.
        """
        
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        for existing in self.documents.values():
            if existing.metadata.get("content_sha256") == content_hash:
                logger.info(f"Skipped duplicate document: {title}")
                return existing

        doc = Document(
            title=title,
            content=content,
            source=source,
            metadata={"content_sha256": content_hash},
        )
        
        # Chunk document
        doc.chunks = self._chunk_document(content)
        
        # Extract entities
        doc.entities = self._extract_entities(content)
        
        # Store document
        self.documents[doc.id] = doc
        
        # Create document node
        doc_node = GraphNode(
            node_type="document",
            label=title,
            data={
                "doc_id": doc.id,
                "chunk_count": len(doc.chunks),
                "entity_count": len(doc.entities),
            }
        )
        self.nodes[doc_node.id] = doc_node
        
        # Create chunk nodes and edges
        for idx, chunk in enumerate(doc.chunks):
            chunk_node = GraphNode(
                node_type="chunk",
                label=f"{title} - Chunk {idx+1}",
                data={
                    "doc_id": doc.id,
                    "chunk_index": idx,
                    "chunk_text": chunk[:200],  # Preview
                }
            )
            self.nodes[chunk_node.id] = chunk_node
            
            # Create edge from document to chunk
            edge = GraphEdge(
                source_id=doc_node.id,
                target_id=chunk_node.id,
                edge_type="contains_chunk",
            )
            self.edges[edge.id] = edge
            self.adjacency_list[doc_node.id].append(chunk_node.id)
            self.reverse_adjacency[chunk_node.id].append(doc_node.id)
        
        # Create entity nodes and edges
        for entity in doc.entities:
            entity_node = GraphNode(
                node_type="entity",
                label=entity,
                data={"doc_id": doc.id}
            )
            self.nodes[entity_node.id] = entity_node
            
            # Create edge from document to entity
            edge = GraphEdge(
                source_id=doc_node.id,
                target_id=entity_node.id,
                edge_type="mentions",
            )
            self.edges[edge.id] = edge
            self.adjacency_list[doc_node.id].append(entity_node.id)
            self.reverse_adjacency[entity_node.id].append(doc_node.id)
        
        logger.info(f"Document added: {title} ({len(doc.chunks)} chunks, {len(doc.entities)} entities)")
        self._save()
        return doc

    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return bounded, source-traceable document metadata without raw content."""
        return [
            {
                "id": document.id,
                "title": document.title,
                "source": document.source,
                "chunks": len(document.chunks),
                "entities": len(document.entities),
                "created_at": document.created_at.isoformat(),
            }
            for document in list(self.documents.values())[-limit:]
        ]

    def _load(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        try:
            records = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Unable to read the DAKSH knowledge store.") from error
        if not isinstance(records, list):
            raise RuntimeError("The DAKSH knowledge store is invalid.")
        self._loading = True
        try:
            for record in records:
                if not isinstance(record, dict) or not all(
                    isinstance(record.get(key), str) for key in ("title", "content", "source")
                ):
                    raise RuntimeError("The DAKSH knowledge store is invalid.")
                document = self.add_document(record["title"], record["content"], record["source"])
                metadata = record.get("metadata")
                if isinstance(metadata, dict):
                    document.metadata.update(metadata)
                saved_id = record.get("id")
                if isinstance(saved_id, str) and saved_id and saved_id != document.id:
                    generated_id = document.id
                    self.documents.pop(generated_id)
                    document.id = saved_id
                    self.documents[saved_id] = document
                    for node in self.nodes.values():
                        if node.data.get("doc_id") == generated_id:
                            node.data["doc_id"] = saved_id
        finally:
            self._loading = False

    def _save(self) -> None:
        if self.storage_path is None or self._loading:
            return
        records = [
            {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "source": document.source,
                "metadata": document.metadata,
            }
            for document in self.documents.values()
        ]
        self.storage_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.storage_path.parent, delete=False
            ) as temporary_file:
                json.dump(records, temporary_file, ensure_ascii=False, separators=(",", ":"))
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
                temporary_path = Path(temporary_file.name)
            os.chmod(temporary_path, 0o600)
            temporary_path.replace(self.storage_path)
        except OSError as error:
            raise RuntimeError("Unable to persist the DAKSH knowledge store.") from error
    
    def query(self, query_text: str, top_k: int = RAG_RETRIEVE_TOP_K) -> Dict[str, Any]:
        """
        Query the knowledge graph for relevant information.
        Returns ranked results with context.
        """
        
        logger.info(f"Query: {query_text}")
        
        # Extract query entities
        query_entities = self._extract_entities(query_text)
        
        # Find matching nodes
        relevant_nodes = self._find_relevant_nodes(query_text, query_entities)
        
        # Score and rank results
        ranked_results = self._rank_results(relevant_nodes, query_text)
        
        # Get context around top results
        context = self._get_context(ranked_results[:top_k])
        
        result = {
            "query": query_text,
            "query_entities": query_entities,
            "matched_nodes": len(relevant_nodes),
            "top_results": ranked_results[:top_k],
            "context": context,
            "total_tokens_used": 0,  # Zero-token RAG
        }
        
        logger.info(f"Query returned {len(ranked_results[:top_k])} results")
        return result
    
    def _chunk_document(self, content: str) -> List[str]:
        """
        Split document into overlapping chunks.
        """
        
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), RAG_CHUNK_SIZE - RAG_CHUNK_OVERLAP):
            chunk_words = words[i:i + RAG_CHUNK_SIZE]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
        
        return chunks
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from text using simple patterns.
        """
        
        import re
        entities = []
        
        # Extract capitalized phrases (simplified NER)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized)
        
        # Extract technical terms (words followed by colon)
        technical = re.findall(r'(\w+):', text)
        entities.extend(technical)
        
        return list(set(entities))  # Remove duplicates
    
    def _find_relevant_nodes(self, query: str, entities: List[str]) -> List[Tuple[str, float]]:
        """
        Find nodes relevant to the query.
        Returns list of (node_id, relevance_score) tuples.
        """
        
        relevant = []
        query_words = set(query.lower().split())
        
        for node_id, node in self.nodes.items():
            score = 0.0
            
            # Score based on label match
            label_words = set(node.label.lower().split())
            common_words = query_words & label_words
            score += len(common_words) * 2.0
            
            # Score based on entity match
            for entity in entities:
                if entity.lower() in node.label.lower():
                    score += 1.5
            
            # Score based on node type
            if node.node_type == "chunk":
                score += 0.5
            
            if score > 0:
                relevant.append((node_id, score))
        
        return relevant
    
    def _rank_results(self, relevant_nodes: List[Tuple[str, float]], query: str) -> List[Dict[str, Any]]:
        """
        Rank results by relevance score.
        """
        
        # Sort by score (descending)
        ranked = sorted(relevant_nodes, key=lambda x: x[1], reverse=True)
        
        # Convert to result dicts
        results = []
        for node_id, score in ranked:
            node = self.nodes[node_id]
            results.append({
                "node_id": node_id,
                "label": node.label,
                "type": node.node_type,
                "score": score,
                "data": node.data,
            })
        
        return results
    
    def _get_context(self, results: List[Dict]) -> List[Dict]:
        """
        Get surrounding context for results.
        """
        
        context = []
        for result in results:
            node_id = result["node_id"]
            node = self.nodes[node_id]
            
            # Get connected nodes
            connected = []
            for connected_id in self.adjacency_list.get(node_id, [])[:3]:
                connected.append({
                    "label": self.nodes[connected_id].label,
                    "type": self.nodes[connected_id].node_type,
                })
            
            context.append({
                "result": result,
                "connected_nodes": connected,
            })
        
        return context
    
    def traverse_graph(self, start_node_id: str, max_depth: int = GRAPH_MAX_DEPTH) -> Dict[str, Any]:
        """
        Traverse the graph from a starting node.
        Useful for exploring related knowledge.
        """
        
        visited = set()
        traversal_result = {
            "start_node": start_node_id,
            "max_depth": max_depth,
            "nodes_visited": 0,
            "edges_traversed": 0,
            "graph": {}
        }
        
        # BFS traversal
        queue = [(start_node_id, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            traversal_result["nodes_visited"] += 1
            
            if node_id not in self.nodes:
                continue
            
            node = self.nodes[node_id]
            traversal_result["graph"][node_id] = {
                "label": node.label,
                "type": node.node_type,
            }
            
            # Add connected nodes to queue
            for next_id in self.adjacency_list.get(node_id, []):
                if next_id not in visited:
                    queue.append((next_id, depth + 1))
                    traversal_result["edges_traversed"] += 1
        
        return traversal_result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        """
        
        return {
            "graph_id": self.id,
            "total_documents": len(self.documents),
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": self._count_node_types(),
            "edge_types": self._count_edge_types(),
            "tokens_used": 0,  # Zero-token RAG
        }
    
    def _count_node_types(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for node in self.nodes.values():
            counts[node.node_type] += 1
        return dict(counts)
    
    def _count_edge_types(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for edge in self.edges.values():
            counts[edge.edge_type] += 1
        return dict(counts)
