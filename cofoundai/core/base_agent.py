"""
CoFound.ai Base Agent Class

This module defines the abstract base class used by all agents.
Each agent type inherits from this class and adds its own specialized functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from cofoundai.communication.message import Message
import json
from datetime import datetime

# Import the LLM interface and config loader
from cofoundai.core.llm_interface import LLMFactory, LLMResponse, BaseLLM
from cofoundai.core.config_loader import config_loader


class BaseAgent(ABC):
    """
    Base class for all agents. Defines the foundational functionality.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the base agent.
        
        Args:
            config: Dictionary containing the agent's configuration settings (default: None)
        """
        self.name = "BaseAgent"
        self.description = "Base agent class"
        self.config = config or {}
        self.memory = []  # Stores past interactions
        self.status = "idle"  # Agent status (idle, busy, error)
        self.tools = {}  # Dictionary to store registered tools
        
        # Check if dummy test mode is enabled
        self.use_dummy_test = self.config.get("use_dummy_test", False)
        
        # Initialize LLM (if needed)
        self._llm = None
    
    def get_llm(self) -> BaseLLM:
        """
        Get the LLM instance for this agent.
        
        Returns:
            LLM instance (created on first use)
        """
        if self._llm is None:
            # Get LLM configuration
            provider = self.config.get("llm_provider", config_loader.get_llm_provider())
            model_name = self.config.get("model_name", None)  # Will use default model if None
            
            # Create LLM instance
            self._llm = LLMFactory.create_llm(
                provider=provider,
                model_name=model_name,
                use_dummy=self.use_dummy_test
            )
            
        return self._llm
    
    def ask_llm(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Ask the LLM a question.
        
        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message
            messages: Optional chat history
            temperature: Optional temperature setting
            
        Returns:
            LLM response
        """
        llm = self.get_llm()
        return llm.generate(
            prompt=prompt,
            system_message=system_message,
            messages=messages,
            temperature=temperature
        )
    
    def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate an appropriate response.
        Default implementation extracts data from message and calls process().
        
        Args:
            message: The message object to process
            
        Returns:
            Response message
        """
        # Extract data from message
        input_data = {
            "content": message.content,
            **(message.metadata or {})
        }
        
        # Process the data
        try:
            result = self.process(input_data)
            
            # Create response message
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=result.get("message", f"Task completed by {self.name}"),
                metadata=result
            )
        except Exception as e:
            # Create error response
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=f"Error processing message: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and perform agent-specific tasks.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Output data with processing results
        """
        # Default implementation - should be overridden by concrete agent classes
        return {
            "status": "error",
            "message": f"{self.name} does not implement process() method",
            "error": "NotImplementedError"
        }
    
    def receive_message(self, message: Message) -> Message:
        """
        Receive a message, store it in memory, and route it for processing.
        
        Args:
            message: The received message
            
        Returns:
            Response message
        """
        # Store message
        self._add_to_memory(message)
        
        # Update status
        self.status = "busy"
        
        try:
            # Process message
            response = self.process_message(message)
            self.status = "idle"
            
            # Store response
            self._add_to_memory(response)
            
            return response
        except Exception as e:
            self.status = "error"
            error_response = Message(
                sender=self.name,
                recipient=message.sender,
                content=f"Error occurred during processing: {str(e)}",
                metadata={"error": str(e)}
            )
            self._add_to_memory(error_response)
            return error_response
    
    def register_tool(self, tool_name: str, tool_instance: Any) -> None:
        """
        Register a tool for use by the agent.
        
        Args:
            tool_name: Name to use for accessing the tool
            tool_instance: Instance of the tool to register
        """
        self.tools[tool_name] = tool_instance
        
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get a registered tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_name)
        
    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool with the given name is registered.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if the tool is registered, False otherwise
        """
        return tool_name in self.tools
    
    def _add_to_memory(self, message: Message) -> None:
        """
        Add a message to the agent's memory.
        
        Args:
            message: The message to store
        """
        self.memory.append({
            "timestamp": message.timestamp,
            "formatted_time": datetime.fromtimestamp(message.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "sender": message.sender,
            "recipient": message.recipient,
            "content": message.content,
            "metadata": message.metadata
        })
    
    def get_memory(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve messages from the agent's memory.
        
        Args:
            limit: Maximum number of messages to return (None for all)
            
        Returns:
            List of messages from memory
        """
        if limit is not None:
            return self.memory[-limit:]
        return self.memory
    
    def clear_memory(self) -> None:
        """
        Clear the agent's memory.
        """
        self.memory = []
    
    def get_status(self) -> str:
        """
        Get the agent's current status.
        
        Returns:
            Agent status
        """
        return self.status
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update the agent's configuration.
        
        Args:
            new_config: New configuration settings
        """
        self.config.update(new_config)
        
        # If the config update includes LLM settings, reset LLM
        if any(key in new_config for key in ["llm_provider", "model_name", "use_dummy_test"]):
            self._llm = None
            
    def __str__(self) -> str:
        """
        Return a string representation of the agent.
        
        Returns:
            String with agent information
        """
        return f"{self.name}: {self.description}" 