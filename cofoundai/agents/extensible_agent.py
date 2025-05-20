"""
CoFound.ai Extensible Agent Components

This module contains the core components for CoFound.ai's extensible agent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type, Union, Set
import uuid
import json
import logging
import asyncio
from enum import Enum

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, Capability
)
from cofoundai.communication.message import Message, MessageRole, MessageType

logger = get_logger(__name__)

class AgentState(str, Enum):
    """Agent state enumeration"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"

class Agent(ExtensibleComponent):
    """
    Base class for extensible agents.
    
    This class provides the core functionality for all extensible agents.
    """
    
    def __init__(self, 
                name: str, 
                description: str):
        """
        Create an extensible agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        super().__init__(
            name=name,
            description=description,
            component_type=ComponentType.AGENT,
            provider_type=ProviderType.INTERNAL
        )
        
        self.state = AgentState.INITIALIZING
        self.session_id = str(uuid.uuid4())
        self.message_history: List[Message] = []
        self.allowed_tools: Set[str] = set()
    
    def set_state(self, state: AgentState) -> None:
        """
        Update the agent state.
        
        Args:
            state: New state
        """
        logger.info(f"Agent '{self.name}' state changed: {self.state} -> {state}")
        self.state = state
    
    def add_message(self, message: Message) -> None:
        """
        Add a new message to the message history.
        
        Args:
            message: Message to add
        """
        self.message_history.append(message)
    
    def get_messages(self, 
                   limit: Optional[int] = None, 
                   role: Optional[MessageRole] = None,
                   message_type: Optional[MessageType] = None) -> List[Message]:
        """
        Get messages from the message history.
        
        Args:
            limit: Maximum number of messages
            role: Filter by role (optional)
            message_type: Filter by message type (optional)
            
        Returns:
            Filtered message list
        """
        messages = self.message_history
        
        # Role filter
        if role:
            messages = [m for m in messages if m.role == role]
        
        # Message type filter
        if message_type:
            messages = [m for m in messages if m.type == message_type]
        
        # Maximum number of messages
        if limit:
            messages = messages[-limit:]
            
        return messages
    
    def allow_tool(self, tool_id: str) -> None:
        """
        Allow the agent to use a tool.
        
        Args:
            tool_id: Tool ID to allow
        """
        self.allowed_tools.add(tool_id)
    
    def is_tool_allowed(self, tool_id: str) -> bool:
        """
        Check if a tool is allowed.
        
        Args:
            tool_id: Tool ID to check
            
        Returns:
            Is tool allowed
        """
        return tool_id in self.allowed_tools
    
    @abstractmethod
    def process_message(self, message: Message) -> Optional[Message]:
        """
        Process a message and return a response.
        
        Args:
            message: Message to process
            
        Returns:
            Response message (optional)
        """
        pass
    
    def invoke(self, 
              capability_name: str, 
              inputs: Dict[str, Any], 
              **kwargs) -> Dict[str, Any]:
        """
        Implementation of ExtensibleComponent.invoke method.
        
        Args:
            capability_name: Capability name to invoke
            inputs: Input parameters
            **kwargs: Additional parameters
            
        Returns:
            Operation result
        """
        try:
            # Find and invoke the relevant capability method
            if capability_name == "process_message" and "message" in inputs:
                message = Message.from_dict(inputs["message"]) if isinstance(inputs["message"], dict) else inputs["message"]
                response = self.process_message(message)
                return {"response": response.to_dict() if response else None}
            else:
                raise ValueError(f"Unknown capability: {capability_name}")
        except Exception as e:
            logger.error(f"Error invoking agent '{self.name}': {str(e)}")
            return {"error": str(e)}

class LLMAgent(Agent):
    """
    LLM-based agent.
    
    This class provides the core functionality for an LLM-based agent.
    """
    
    def __init__(self, 
                name: str, 
                description: str,
                model,  # LLM model
                prompt_template: str,
                system_message: Optional[str] = None):
        """
        Create an LLM-based agent.
        
        Args:
            name: Agent name
            description: Agent description
            model: LLM model to use
            prompt_template: Message template
            system_message: System message (optional)
        """
        super().__init__(name=name, description=description)
        
        self.model = model
        self.prompt_template = prompt_template
        self.system_message = system_message
        
        # LLM agent-specific metadata
        self.set_metadata("model_info", getattr(model, "model_info", {"name": str(model)}))
        
        # Capability definition
        capability = Capability(
            name="process_message",
            description=f"Process messages with {name}",
            parameters={
                "message": {
                    "type": "object",
                    "required": True
                }
            }
        )
        self.add_capability(capability)
        
        # Update initial state
        self.set_state(AgentState.IDLE)
    
    def _prepare_prompt(self, message: Message) -> str:
        """
        Create a prompt from the input message.
        
        Args:
            message: Input message
            
        Returns:
            Formatted prompt
        """
        # Use shortened message history format
        history_str = "\n".join([
            f"{m.role}: {m.content}" 
            for m in self.get_messages(limit=10)
        ])
        
        # Format the template
        return self.prompt_template.format(
            message=message.content,
            history=history_str,
            agent_name=self.name,
            session_id=self.session_id
        )
    
    def process_message(self, message: Message) -> Optional[Message]:
        """
        Process a message using the LLM and return a response.
        
        Args:
            message: Message to process
            
        Returns:
            Response message
        """
        try:
            # Update state
            self.set_state(AgentState.THINKING)
            
            # Add message to history
            self.add_message(message)
            
            # Prepare prompt
            prompt = self._prepare_prompt(message)
            
            # Model call
            logger.debug(f"Sending prompt to LLM model: {prompt[:100]}...")
            
            # Use system message if available
            messages = []
            
            if self.system_message:
                messages.append({"role": "system", "content": self.system_message})
                
            # Add message history and new message
            for m in self.get_messages(limit=10):
                messages.append({"role": m.role, "content": m.content})
            
            # Call the LLM model
            if hasattr(self.model, "chat") and callable(self.model.chat):
                # Chat API (OpenAI, Anthropic, etc.)
                response_text = self.model.chat(messages)
            else:
                # Standart completion API
                response_text = self.model.complete(prompt)
            
            # Create response message
            response = Message(
                content=response_text,
                role=MessageRole.ASSISTANT,
                type=MessageType.TEXT,
                sender=self.name,
                receiver=message.sender
            )
            
            # Add response to history
            self.add_message(response)
            
            # Update state
            self.set_state(AgentState.IDLE)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message in LLM agent '{self.name}': {str(e)}")
            self.set_state(AgentState.ERROR)
            
            # Return error message
            error_message = Message(
                content=f"Error processing your message: {str(e)}",
                role=MessageRole.ASSISTANT,
                type=MessageType.ERROR,
                sender=self.name,
                receiver=message.sender
            )
            
            self.add_message(error_message)
            return error_message

class ToolAgent(Agent):
    """
    Tool-using agent.
    
    This class provides the core functionality for an agent that can use tools.
    """
    
    def __init__(self, 
                name: str, 
                description: str,
                model,  # LLM model
                prompt_template: str,
                system_message: Optional[str] = None,
                tools: Optional[Dict[str, Any]] = None):
        """
        Create a tool-using agent.
        
        Args:
            name: Agent name
            description: Agent description
            model: LLM model to use
            prompt_template: Message template
            system_message: System message (optional)
            tools: Available tools (optional)
        """
        super().__init__(name=name, description=description)
        
        self.model = model
        self.prompt_template = prompt_template
        self.system_message = system_message
        self.tools = tools or {}
        
        # Add allowed tools to the list
        for tool_id in self.tools:
            self.allow_tool(tool_id)
        
        # Tool-using agent-specific metadata
        self.set_metadata("model_info", getattr(model, "model_info", {"name": str(model)}))
        self.set_metadata("tools_available", list(self.tools.keys()))
        
        # Capability definition
        capability = Capability(
            name="process_message",
            description=f"Process messages with {name} using tools",
            parameters={
                "message": {
                    "type": "object",
                    "required": True
                }
            }
        )
        self.add_capability(capability)
        
        # Update initial state
        self.set_state(AgentState.IDLE)
    
    def _prepare_prompt_with_tools(self, message: Message) -> str:
        """
        Create a prompt with tools.
        
        Args:
            message: Input message
            
        Returns:
            Formatted prompt
        """
        # Use shortened message history format
        history_str = "\n".join([
            f"{m.role}: {m.content}" 
            for m in self.get_messages(limit=10)
        ])
        
        # Add tool definitions
        tools_str = ""
        for tool_id, tool in self.tools.items():
            tools_str += f"Tool ID: {tool_id}\n"
            tools_str += f"Name: {tool.name}\n"
            tools_str += f"Description: {tool.description}\n"
            tools_str += "Parameters:\n"
            
            for param_name, param_info in tool.get_metadata("parameters", {}).items():
                required = "Required" if param_info.get("required", False) else "Optional"
                param_type = param_info.get("type", "any")
                tools_str += f"- {param_name} ({param_type}): {required}\n"
            
            tools_str += "\n"
        
        # Format the template
        return self.prompt_template.format(
            message=message.content,
            history=history_str,
            tools=tools_str,
            agent_name=self.name,
            session_id=self.session_id
        )
    
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from the text.
        
        Args:
            text: Text containing tool calls
            
        Returns:
            List of tool calls
        """
        tool_calls = []
        
        # Simple regex-based extraction
        # In a real application, a more powerful parser should be used
        import re
        
        # Tool call format: <tool id="tool_id" params={"param1": "value1"}>
        tool_pattern = r'<tool\s+id=["\']([^"\']+)["\'](?:\s+params=([^>]+))?\s*>'
        
        for match in re.finditer(tool_pattern, text):
            tool_id = match.group(1)
            params_str = match.group(2) or "{}"
            
            try:
                # Parse parameters from JSON format
                params = json.loads(params_str)
                
                tool_calls.append({
                    "tool_id": tool_id,
                    "params": params
                })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool parameters: {params_str}")
        
        return tool_calls
    
    def _execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_id: ID of the tool to execute
            params: Tool parameters
            
        Returns:
            Tool result
        """
        # Tool permission check
        if not self.is_tool_allowed(tool_id):
            return {"error": f"Tool '{tool_id}' is not allowed for this agent"}
        
        # Find the tool
        tool = self.tools.get(tool_id)
        if not tool:
            return {"error": f"Tool '{tool_id}' not found"}
        
        # Execute the tool
        try:
            self.set_state(AgentState.EXECUTING)
            result = tool.invoke(**params)
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{tool_id}': {str(e)}")
            return {"error": str(e)}
        finally:
            self.set_state(AgentState.THINKING)
    
    def process_message(self, message: Message) -> Optional[Message]:
        """
        Process the message, use tools if needed, and return a response.
        
        Args:
            message: Message to process
            
        Returns:
            Response message
        """
        try:
            # Update state
            self.set_state(AgentState.THINKING)
            
            # Add message to history
            self.add_message(message)
            
            # Prepare prompt
            prompt = self._prepare_prompt_with_tools(message)
            
            # Model call
            logger.debug(f"Sending prompt to LLM model: {prompt[:100]}...")
            
            # Use system message if available
            messages = []
            
            if self.system_message:
                messages.append({"role": "system", "content": self.system_message})
                
            # Add message history and new message
            for m in self.get_messages(limit=10):
                messages.append({"role": m.role, "content": m.content})
            
            # Call the LLM model
            if hasattr(self.model, "chat") and callable(self.model.chat):
                # Chat API (OpenAI, Anthropic, etc.)
                response_text = self.model.chat(messages)
            else:
                # Standart completion API
                response_text = self.model.complete(prompt)
            
            # Extract tool calls
            tool_calls = self._extract_tool_calls(response_text)
            
            # If there are tool calls, execute them
            tool_results = []
            
            for tool_call in tool_calls:
                tool_id = tool_call["tool_id"]
                params = tool_call["params"]
                
                # Execute the tool
                result = self._execute_tool(tool_id, params)
                
                # Add the result
                tool_results.append({
                    "tool_id": tool_id,
                    "params": params,
                    "result": result
                })
                
                # Add the tool result to the response
                result_str = json.dumps(result, indent=2)
                response_text = response_text.replace(
                    f'<tool id="{tool_id}" params={json.dumps(params)}>',
                    f'<tool id="{tool_id}" result={result_str}>'
                )
            
            # Create the response message
            response = Message(
                content=response_text,
                role=MessageRole.ASSISTANT,
                type=MessageType.TEXT,
                sender=self.name,
                receiver=message.sender,
                metadata={"tool_results": tool_results} if tool_results else {}
            )
            
            # Add the response to history
            self.add_message(response)
            
            # Update state
            self.set_state(AgentState.IDLE)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message in tool agent '{self.name}': {str(e)}")
            self.set_state(AgentState.ERROR)
            
            # Return error message
            error_message = Message(
                content=f"Error processing your message: {str(e)}",
                role=MessageRole.ASSISTANT,
                type=MessageType.ERROR,
                sender=self.name,
                receiver=message.sender
            )
            
            self.add_message(error_message)
            return error_message 