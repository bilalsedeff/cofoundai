"""
CoFound.ai MCP (Model Context Protocol) Adapter

This module contains the CoFound.ai Model Context Protocol (MCP) adapter.
It implements the MCP protocol to interact with external models and tools.
"""

import json
import uuid
import requests
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
import logging
import time

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, Capability
)

logger = get_logger(__name__)

class MCPToolType(str, Enum):
    """MCP tool types"""
    FUNCTION = "function"
    SERVICE = "service"
    RETRIEVAL = "retrieval"
    MODEL = "model"

class MCPAdapter:
    """
    Model Context Protocol (MCP) adapter.
    
    This class provides an adapter for interacting with external MCP-compatible services.
    """
    
    def __init__(self, 
                endpoint_url: str,
                api_key: Optional[str] = None,
                timeout: int = 30):
        """
        Initialize the MCP adapter.
        
        Args:
            endpoint_url: URL of the MCP service
            api_key: API key (optional)
            timeout: Request timeout (seconds)
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        logger.info(f"Initialized MCP adapter for {endpoint_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Create HTTP headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools.
        
        Returns:
            List of tools
        """
        try:
            response = requests.get(
                f"{self.endpoint_url}/tools",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}")
            return []
    
    def call_tool(self, 
                 tool_id: str, 
                 inputs: Dict[str, Any],
                 context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Call a specific tool.
        
        Args:
            tool_id: ID of the tool to call
            inputs: Input parameters
            context_id: Context ID (optional)
            
        Returns:
            Tool response
        """
        # Create context ID if not provided
        if not context_id:
            context_id = str(uuid.uuid4())
            
        payload = {
            "tool_id": tool_id,
            "inputs": inputs,
            "context_id": context_id
        }
        
        try:
            response = requests.post(
                f"{self.endpoint_url}/invoke",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling MCP tool '{tool_id}': {str(e)}")
            return {"error": str(e)}
    
    def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        Get a specific context.
        
        Args:
            context_id: ID of the context to retrieve
            
        Returns:
            Context data
        """
        try:
            response = requests.get(
                f"{self.endpoint_url}/context/{context_id}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting MCP context '{context_id}': {str(e)}")
            return {"error": str(e)}
    
    def update_context(self, 
                      context_id: str, 
                      updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update context data.
        
        Args:
            context_id: ID of the context to update
            updates: Data to update
            
        Returns:
            Update result
        """
        try:
            response = requests.post(
                f"{self.endpoint_url}/context/{context_id}",
                headers=self._get_headers(),
                json=updates,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating MCP context '{context_id}': {str(e)}")
            return {"error": str(e)}
    
    def search_context(self, 
                      query: str, 
                      context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Search within context.
        
        Args:
            query: Search query
            context_id: Context ID to search (optional)
            
        Returns:
            Search results
        """
        params = {"query": query}
        if context_id:
            params["context_id"] = context_id
            
        try:
            response = requests.get(
                f"{self.endpoint_url}/search",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching MCP context: {str(e)}")
            return {"error": str(e)}

class MCPToolComponent(ExtensibleComponent):
    """
    Represents a tool accessed via the MCP protocol.
    """
    
    def __init__(self, 
                name: str, 
                description: str,
                tool_id: str,
                tool_type: MCPToolType,
                adapter: MCPAdapter):
        """
        Initialize the MCP tool component.
        
        Args:
            name: Tool name
            description: Tool description
            tool_id: MCP tool ID
            tool_type: Tool type
            adapter: MCP adapter to use
        """
        super().__init__(
            name=name,
            description=description,
            component_type=ComponentType.TOOL,
            provider_type=ProviderType.MCP
        )
        self.tool_id = tool_id
        self.tool_type = tool_type
        self.adapter = adapter
        
        # Set tool metadata
        self.set_metadata("tool_id", tool_id)
        self.set_metadata("tool_type", tool_type.value)
        
        # Capability definition
        main_capability = Capability(
            name="invoke",
            description=f"Invoke the {name} tool"
        )
        self.add_capability(main_capability)
    
    def invoke(self, inputs: Dict[str, Any], context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Call the tool.
        
        Args:
            inputs: Input parameters
            context_id: Context ID (optional)
            
        Returns:
            Tool response
        """
        return self.adapter.call_tool(self.tool_id, inputs, context_id)

class MCPRetrievalComponent(MCPToolComponent):
    """
    Represents a tool that retrieves documents via the MCP protocol.
    """
    
    def __init__(self, 
                name: str, 
                description: str,
                tool_id: str,
                adapter: MCPAdapter):
        """
        Initialize the MCP retrieval component.
        
        Args:
            name: Tool name
            description: Tool description
            tool_id: MCP tool ID
            adapter: MCP adapter to use
        """
        super().__init__(
            name=name,
            description=description,
            tool_id=tool_id,
            tool_type=MCPToolType.RETRIEVAL,
            adapter=adapter
        )
        
        # Belge arama yeteneği ekle
        search_capability = Capability(
            name="search",
            description=f"Search documents in {name}"
        )
        self.add_capability(search_capability)
    
    def search(self, query: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Search documents.
        
        Args:
            query: Search query
            context_id: Context ID (optional)
            
        Returns:
            Search results
        """
        inputs = {"query": query}
        return self.invoke(inputs, context_id)

class MCPModelComponent(ExtensibleComponent):
    """
    Represents a model accessed via the MCP protocol.
    """
    
    def __init__(self, 
                name: str, 
                description: str,
                model_id: str,
                adapter: MCPAdapter):
        """
        Initialize the MCP model component.
        
        Args:
            name: Model adı
            description: Model description
            model_id: MCP model ID
            adapter: MCP adapter to use
        """
        super().__init__(
            name=name,
            description=description,
            component_type=ComponentType.AGENT,  # Model is represented as an agent
            provider_type=ProviderType.MCP
        )
        self.model_id = model_id
        self.adapter = adapter
        
        # Set model metadata
        self.set_metadata("model_id", model_id)
        
        # Capability definition
        main_capability = Capability(
            name="complete",
            description=f"Generate completion with {name} model"
        )
        self.add_capability(main_capability)
    
    def invoke(self, 
              prompt: Union[str, List[Dict[str, str]]], 
              context_id: Optional[str] = None,
              **model_params) -> Dict[str, Any]:
        """
        Call the model and generate completion.
        
        Args:
            prompt: Text or chat messages
            context_id: Context ID (optional)
            **model_params: Additional model parameters
            
        Returns:
            Model response
        """
        inputs = {
            "prompt": prompt,
            **model_params
        }
        
        return self.adapter.call_tool(self.model_id, inputs, context_id)
    
    def complete(self, 
               prompt: str, 
               context_id: Optional[str] = None,
               **model_params) -> str:
        """
        Complete the text (simplified).
        
        Args:
            prompt: Text to complete
            context_id: Context ID (optional)
            **model_params: Additional model parameters
            
        Returns:
            Completed text
        """
        response = self.invoke(prompt, context_id, **model_params)
        
        if "error" in response:
            raise RuntimeError(f"Error completing text: {response['error']}")
        
        return response.get("completion", "")
    
    def chat(self, 
            messages: List[Dict[str, str]], 
            context_id: Optional[str] = None,
            **model_params) -> Dict[str, str]:
        """
        Generate a chat response.
        
        Args:
            messages: Message list (role/content format)
            context_id: Context ID (optional)
            **model_params: Additional model parameters
            
        Returns:
            Model response message
        """
        response = self.invoke(messages, context_id, **model_params)
        
        if "error" in response:
            raise RuntimeError(f"Error in chat: {response['error']}")
        
        return response.get("message", {"role": "assistant", "content": ""}) 