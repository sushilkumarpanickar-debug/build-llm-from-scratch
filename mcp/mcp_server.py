"""
MCP (Model Context Protocol) Server: Seamless tool integration
Provides context-aware task execution without token consumption
"""

import uuid
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from config.settings import (
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
    MCP_AUTO_DISCOVER_TOOLS,
    MCP_TOOL_TIMEOUT,
)


class ToolType(Enum):
    """Types of tools in the MCP system."""
    TEXT_PROCESSING = "text_processing"
    DATA_ANALYSIS = "data_analysis"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    FILE_OPERATIONS = "file_operations"
    EXTERNAL_API = "external_api"
    CUSTOM = "custom"


@dataclass
class MCPTool:
    """Tool definition for MCP."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tool_type: ToolType = ToolType.CUSTOM
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    tokens_required: int = 0  # ALWAYS 0 - MCP uses zero-token mode
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPContext:
    """Context passed to MCP tools."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_message: str = ""
    task_description: str = ""
    session_data: Dict[str, Any] = field(default_factory=dict)
    previous_outputs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPResult:
    """Result from MCP tool execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    status: str = "pending"  # pending, running, completed, failed
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_used: int = 0  # ALWAYS 0
    created_at: datetime = field(default_factory=datetime.now)


class MCPServer:
    """
    Model Context Protocol Server.
    Manages tool integration and context-aware execution.
    Zero-token operation mode.
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.tools: Dict[str, MCPTool] = {}
        self.execution_history: List[MCPResult] = []
        self.context_stack: List[MCPContext] = []
        
        logger.info(f"MCP Server initialized on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    
    def register_tool(self, tool: MCPTool) -> None:
        """
        Register a tool with the MCP server.
        """
        
        self.tools[tool.id] = tool
        logger.info(f"Tool registered: {tool.name} ({tool.tool_type.value})")
    
    def discover_tools(self, query: str = "") -> List[MCPTool]:
        """
        Discover available tools based on query.
        Uses intelligent matching.
        """
        
        if not query:
            return list(self.tools.values())
        
        query_lower = query.lower()
        matching_tools = []
        
        for tool in self.tools.values():
            if not tool.enabled:
                continue
            
            # Match by name or description
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        logger.info(f"Discovered {len(matching_tools)} tools for query: {query}")
        return matching_tools
    
    def create_context(self, user_message: str, task_description: str = "") -> MCPContext:
        """
        Create a new context for task execution.
        """
        
        context = MCPContext(
            user_message=user_message,
            task_description=task_description,
        )
        
        self.context_stack.append(context)
        logger.info(f"Context created: {context.id}")
        
        return context
    
    def execute_tool(
        self,
        tool_id: str,
        context: MCPContext,
        input_data: Dict[str, Any]
    ) -> MCPResult:
        """
        Execute a tool with given context and input.
        Zero-token execution.
        """
        
        import time
        start_time = time.time()
        
        if tool_id not in self.tools:
            result = MCPResult(
                tool_name="Unknown",
                status="failed",
                error="Tool not found"
            )
            return result
        
        tool = self.tools[tool_id]
        result = MCPResult(tool_name=tool.name)
        
        try:
            logger.info(f"Executing tool: {tool.name}")
            
            # Execute handler
            if tool.handler:
                output = tool.handler(input_data, context)
                result.output = output
            else:
                result.output = self._default_tool_handler(tool, input_data)
            
            result.status = "completed"
            result.tokens_used = 0  # Zero-token mode
            
            logger.info(f"Tool {tool.name} executed successfully")
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            result.status = "failed"
            result.error = str(e)
            result.tokens_used = 0  # Zero-token mode even on failure
        
        finally:
            result.execution_time_ms = (time.time() - start_time) * 1000
            self.execution_history.append(result)
        
        return result
    
    def execute_tool_chain(
        self,
        tool_ids: List[str],
        context: MCPContext,
        inputs: List[Dict[str, Any]]
    ) -> List[MCPResult]:
        """
        Execute a chain of tools sequentially.
        Each tool's output becomes the next tool's input.
        """
        
        results = []
        current_output = {}
        
        for idx, (tool_id, input_data) in enumerate(zip(tool_ids, inputs)):
            # Merge previous output with current input
            merged_input = {**current_output, **input_data}
            
            # Execute tool
            result = self.execute_tool(tool_id, context, merged_input)
            results.append(result)
            
            # Use output as input for next tool
            current_output = result.output
            
            if result.status == "failed":
                logger.warning(f"Tool chain interrupted at step {idx+1}")
                break
        
        logger.info(f"Tool chain executed: {len(results)} tools, 0 tokens used")
        return results
    
    def _default_tool_handler(self, tool: MCPTool, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default handler for tools without custom handlers.
        """
        
        return {
            "tool_name": tool.name,
            "tool_type": tool.tool_type.value,
            "input_received": input_data,
            "message": f"Executed {tool.name} with zero token consumption",
            "tokens_used": 0,
        }
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """
        Retrieve a context by ID.
        """
        
        for context in self.context_stack:
            if context.id == context_id:
                return context
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get MCP server statistics.
        """
        
        return {
            "server_id": self.id,
            "host": MCP_SERVER_HOST,
            "port": MCP_SERVER_PORT,
            "total_tools": len(self.tools),
            "enabled_tools": sum(1 for t in self.tools.values() if t.enabled),
            "total_executions": len(self.execution_history),
            "total_tokens_used": 0,  # Zero-token mode
            "tool_types": self._count_tool_types(),
        }
    
    def _count_tool_types(self) -> Dict[str, int]:
        counts = {}
        for tool in self.tools.values():
            tool_type = tool.tool_type.value
            counts[tool_type] = counts.get(tool_type, 0) + 1
        return counts
