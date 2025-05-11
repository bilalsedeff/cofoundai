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
        
    def __str__(self) -> str:
        """
        Return a string representation of the agent.
        
        Returns:
            String with agent information
        """
        return f"{self.name}: {self.description}" 