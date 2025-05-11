"""
CoFound.ai Agent Command

This module defines command structures for agent communication and workflow control.
It enables agents to dynamically route messages, transfer control, and update state.
"""

from typing import Dict, Any, List, Optional, Union, Literal, TypeVar, Generic, cast
from enum import Enum
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# Type definitions
T = TypeVar('T')


class CommandType(str, Enum):
    """Types of agent commands."""
    
    GOTO = "goto"                # Transfer control to another agent
    UPDATE = "update"            # Update the workflow state
    RESPONSE = "response"        # Send a response message
    TOOL_USE = "tool_use"        # Use a tool
    END = "end"                  # End the workflow
    ERROR = "error"              # Report an error
    HANDOFF = "handoff"          # Hand off to another agent


class CommandTarget(str, Enum):
    """Target scope for commands."""
    
    PARENT = "parent"            # Route to parent graph
    SELF = "self"                # Route within current graph
    CHILD = "child"              # Route to a child graph
    END = "end"                  # End the execution
    SAME = "same"                # Stay in the same node/agent


class Command(BaseModel):
    """
    Command for agent communication and workflow control.
    
    This class is used to represent commands passed between agents in the workflow.
    It enables dynamic routing, state updates, and communication control.
    """
    
    # Command type and parameters
    type: CommandType = CommandType.GOTO
    
    # Target agent or node
    goto: Optional[str] = None
    
    # Target graph scope - where should this command apply?
    target: CommandTarget = CommandTarget.SELF
    
    # Data to update in the state
    update: Optional[Dict[str, Any]] = None
    
    # Command ID
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Timestamp
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    @classmethod
    def handoff(
        cls, 
        to_agent: str, 
        reason: str = "",
        state_updates: Optional[Dict[str, Any]] = None
    ) -> "Command":
        """
        Create a command to hand off to another agent.
        
        Args:
            to_agent: Name of agent to hand off to
            reason: Reason for the handoff
            state_updates: Optional state updates to include
            
        Returns:
            Command object
        """
        return cls(
            type=CommandType.HANDOFF,
            goto=to_agent,
            target=CommandTarget.PARENT,
            update=state_updates or {},
            metadata={"reason": reason}
        )
    
    @classmethod
    def update_state(cls, updates: Dict[str, Any]) -> "Command":
        """
        Create a command to update state.
        
        Args:
            updates: State updates to apply
            
        Returns:
            Command object
        """
        return cls(
            type=CommandType.UPDATE,
            update=updates
        )
    
    @classmethod
    def end_workflow(cls, final_message: Optional[str] = None) -> "Command":
        """
        Create a command to end the workflow.
        
        Args:
            final_message: Optional final message before ending
            
        Returns:
            Command object
        """
        metadata = {}
        if final_message:
            metadata["final_message"] = final_message
            
        return cls(
            type=CommandType.END,
            target=CommandTarget.END,
            metadata=metadata
        )
    
    @classmethod
    def error(cls, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> "Command":
        """
        Create a command to report an error.
        
        Args:
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            Command object
        """
        return cls(
            type=CommandType.ERROR,
            metadata={
                "error_message": error_message,
                "error_details": error_details or {}
            }
        )
    
    @classmethod
    def use_tool(cls, tool_name: str, tool_parameters: Dict[str, Any]) -> "Command":
        """
        Create a command to use a tool.
        
        Args:
            tool_name: Name of the tool to use
            tool_parameters: Parameters for the tool
            
        Returns:
            Command object
        """
        return cls(
            type=CommandType.TOOL_USE,
            metadata={
                "tool_name": tool_name,
                "tool_parameters": tool_parameters
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "goto": self.goto,
            "target": self.target.value,
            "update": self.update,
            "command_id": self.command_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        """Create from dictionary."""
        # Convert string values to enums
        if "type" in data and isinstance(data["type"], str):
            data["type"] = CommandType(data["type"])
        if "target" in data and isinstance(data["target"], str):
            data["target"] = CommandTarget(data["target"])
            
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation."""
        return f"Command({self.type}, goto={self.goto}, target={self.target})"


class HandoffTool:
    """
    Tool for agents to hand off control to other agents.
    
    This class creates standardized tools that agents can use to transfer
    control to other agents in the workflow.
    """
    
    def __init__(self, agent_name: str, description: Optional[str] = None):
        """
        Initialize a handoff tool.
        
        Args:
            agent_name: Name of the agent to hand off to
            description: Tool description (default: auto-generated)
        """
        self.agent_name = agent_name
        self.tool_name = f"transfer_to_{agent_name}"
        self.description = description or f"Transfer control to the {agent_name} agent"
    
    def __call__(self, reason: str = "") -> Command:
        """
        Execute the handoff.
        
        Args:
            reason: Reason for the handoff
            
        Returns:
            Command object
        """
        return Command.handoff(
            to_agent=self.agent_name,
            reason=reason
        )
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Get the LangGraph tool schema.
        
        Returns:
            Tool schema
        """
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for transferring to this agent"
                    }
                },
                "required": []
            }
        }
    
    def get_langchain_tool(self):
        """
        Get a LangChain tool object for this handoff.
        
        Returns:
            LangChain tool
        """
        try:
            from langchain_core.tools import tool
            
            @tool(self.tool_name, description=self.description)
            def handoff_tool(reason: str = "") -> str:
                """Handoff to another agent."""
                return f"Successfully transferred to {self.agent_name} with reason: {reason}"
            
            # Attach the command to the tool for reference
            handoff_tool.command = self.__call__
            
            return handoff_tool
        
        except ImportError:
            raise ImportError("langchain_core not installed. Run: pip install langchain_core")


class AgentState(BaseModel):
    """
    State class for agent interactions.
    
    This base model can be extended with additional fields needed for
    specific workflow state management.
    """
    
    # Messages exchanged
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Current active agent
    current_agent: Optional[str] = None
    
    # Status of the workflow
    status: str = "starting"
    
    # Command being processed
    current_command: Optional[Command] = None
    
    # Agent-specific states - map of agent name to agent state
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def update_from_command(self, command: Command) -> "AgentState":
        """
        Update state from a command.
        
        Args:
            command: Command to apply
            
        Returns:
            Updated state
        """
        # Create a copy of self
        updated = self.copy()
        
        # Set the current command
        updated.current_command = command
        
        # Apply state updates if present
        if command.update:
            for key, value in command.update.items():
                if key == "messages" and hasattr(self, "messages") and isinstance(self.messages, list):
                    # Special handling for messages - append rather than replace
                    if isinstance(value, list):
                        updated.messages.extend(value)
                    else:
                        updated.messages.append(value)
                else:
                    # General case - set the attribute
                    setattr(updated, key, value)
        
        # Handle specific command types
        if command.type == CommandType.HANDOFF:
            # Update current agent if this is a handoff
            if command.goto:
                updated.current_agent = command.goto
                
        elif command.type == CommandType.ERROR:
            # Add error to the errors list
            if command.metadata:
                updated.errors.append({
                    "timestamp": command.timestamp,
                    "message": command.metadata.get("error_message", "Unknown error"),
                    "details": command.metadata.get("error_details", {})
                })
            updated.status = "error"
            
        elif command.type == CommandType.END:
            # Mark workflow as complete
            updated.status = "complete"
        
        return updated 