"""
CoFound.ai Extensible Orchestrator

This module integrates CoFound.ai's LangGraph-based orchestration system
with an extensible component architecture.
"""

from typing import Dict, List, Any, Optional, Union, Callable, Type
import uuid
import json
import logging
import os
import importlib
from enum import Enum
import asyncio

import langgraph.graph as lg
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, component_registry
)
from cofoundai.core.component_factory import component_factory
from cofoundai.communication.message import Message, MessageRole, MessageType
from cofoundai.agents.extensible_agent import Agent, AgentState

logger = get_logger(__name__)

class GraphNodeType(str, Enum):
    """LangGraph node types"""
    AGENT = "agent"        # Agent node
    CONDITIONAL = "conditional"  # Conditional node
    TOOL = "tool"          # Tool node
    ROUTER = "router"      # Router node

class GraphState(dict):
    """
    LangGraph state object.
    
    This class represents the data flowing between components.
    """
    
    def __init__(self, **kwargs):
        """
        Create a state object.
        
        Args:
            **kwargs: Initial state data
        """
        super().__init__(**kwargs)
        
        # Initialize default state fields
        self.setdefault("messages", [])
        self.setdefault("workflow_id", str(uuid.uuid4()))
        self.setdefault("node_states", {})
        self.setdefault("error", None)
        self.setdefault("status", "running")
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get the message list"""
        return self.get("messages", [])
    
    @property
    def workflow_id(self) -> str:
        """Get the workflow ID"""
        return self.get("workflow_id", "")
    
    @property
    def status(self) -> str:
        """Get the workflow status"""
        return self.get("status", "")
    
    @property
    def error(self) -> Optional[str]:
        """Get the error message"""
        return self.get("error", None)
    
    def add_message(self, message: Union[Message, Dict[str, Any]]) -> None:
        """
        Add a new message to the state messages.
        
        Args:
            message: Message to add (Message object or dictionary)
        """
        if isinstance(message, Message):
            message_dict = message.to_dict()
        else:
            message_dict = message
            
        self["messages"] = self.messages + [message_dict]
    
    def get_node_state(self, node_id: str) -> Dict[str, Any]:
        """
        Get the node state.
        
        Args:
            node_id: Node ID to get the state
            
        Returns:
            Node state data
        """
        node_states = self.get("node_states", {})
        return node_states.get(node_id, {})
    
    def set_node_state(self, node_id: str, state_data: Dict[str, Any]) -> None:
        """
        Set the node state.
        
        Args:
            node_id: Node ID to set the state
            state_data: Node state data
        """
        node_states = self.get("node_states", {})
        node_states[node_id] = state_data
        self["node_states"] = node_states
    
    def set_error(self, error_message: str) -> None:
        """
        Set the error message.
        
        Args:
            error_message: Error message
        """
        self["error"] = error_message
        self["status"] = "error"
    
    def set_completed(self) -> None:
        """Mark the workflow as completed"""
        self["status"] = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the state data to a dictionary"""
        return dict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphState':
        """Create a state object from a dictionary"""
        return cls(**data)

class ExtensibleOrchestrator:
    """
    Orchestrator with an extensible component architecture.
    
    This class integrates different component types into a LangGraph graph.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the extensible orchestrator.
        
        Args:
            config_path: Configuration file path (optional)
        """
        self.config = {}
        self.nodes = {}
        self.graph = None
        self.executor = None
        
        if config_path:
            self._load_config(config_path)
            
        logger.info("Extensible orchestrator initialized")
    
    def _load_config(self, config_path: str) -> None:
        """
        Load the orchestrator configuration.
        
        Args:
            config_path: Configuration file path
        """
        try:
            if not os.path.exists(config_path):
                logger.error(f"Config file not found: {config_path}")
                return
                
            # If the configuration is a YAML file
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                import yaml
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # JSON file
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    
            # Load components
            if "components_config" in self.config:
                component_factory.create_components_from_config(self.config["components_config"])
                
            logger.info(f"Loaded orchestrator config from {config_path}")
        except Exception as e:
            logger.error(f"Error loading orchestrator config: {str(e)}")
    
    def _create_agent_node(self, node_config: Dict[str, Any]) -> Optional[Callable]:
        """
        Create an agent node.
        
        Args:
            node_config: Node configuration
            
        Returns:
            Node function
        """
        try:
            agent_id = node_config.get("agent_id", "")
            
            if not agent_id:
                logger.error("Agent ID is required for agent node")
                return None
                
            # Find the agent
            agent = component_registry.get(agent_id)
            
            if not agent or not isinstance(agent, Agent):
                logger.error(f"Agent not found or not an Agent instance: {agent_id}")
                return None
                
            # Node function
            def agent_node_func(state: Dict[str, Any]) -> Dict[str, Any]:
                # Convert to GraphState
                graph_state = GraphState.from_dict(state)
                
                # Get the last message
                last_message = None
                if graph_state.messages:
                    last_message_dict = graph_state.messages[-1]
                    last_message = Message.from_dict(last_message_dict)
                    
                if not last_message:
                    # Create a default message
                    last_message = Message(
                        content="",
                        role=MessageRole.SYSTEM,
                        type=MessageType.TEXT,
                        sender="system",
                        receiver=agent.name
                    )
                
                try:
                    # Call the agent
                    response = agent.process_message(last_message)
                    
                    # Add the response to the state
                    if response:
                        graph_state.add_message(response)
                        
                except Exception as e:
                    logger.error(f"Error processing message in agent '{agent.name}': {str(e)}")
                    error_message = Message(
                        content=f"Error in agent '{agent.name}': {str(e)}",
                        role=MessageRole.SYSTEM,
                        type=MessageType.ERROR,
                        sender="system",
                        receiver="user"
                    )
                    graph_state.add_message(error_message)
                    graph_state.set_error(str(e))
                
                return graph_state.to_dict()
                
            return agent_node_func
        except Exception as e:
            logger.error(f"Error creating agent node: {str(e)}")
            return None
    
    def _create_tool_node(self, node_config: Dict[str, Any]) -> Optional[Callable]:
        """
        Create a tool node.
        
        Args:
            node_config: Node configuration
            
        Returns:
            Node function
        """
        try:
            tool_id = node_config.get("tool_id", "")
            
            if not tool_id:
                logger.error("Tool ID is required for tool node")
                return None
                
            # Find the tool
            tool = component_registry.get(tool_id)
            
            if not tool:
                logger.error(f"Tool not found: {tool_id}")
                return None
                
            # Node function
            def tool_node_func(state: Dict[str, Any]) -> Dict[str, Any]:
                # Convert to GraphState
                graph_state = GraphState.from_dict(state)
                
                # Get the tool parameters
                params = node_config.get("params", {})
                
                # Process dynamic parameters
                processed_params = {}
                for key, value in params.items():
                    if isinstance(value, str) and value.startswith("$state."):
                        # Get the value from the state (e.g., $state.messages[-1].content)
                        path = value[7:].split('.')
                        curr = state
                        for p in path:
                            if p.endswith(']') and '[' in p:
                                # Process list index
                                base_key, index_str = p.split('[')
                                index = int(index_str.rstrip(']'))
                                curr = curr.get(base_key, [])[index]
                            else:
                                curr = curr.get(p, {})
                        processed_params[key] = curr
                    else:
                        processed_params[key] = value
                
                try:
                    # Call the tool
                    result = tool.invoke(**processed_params)
                    
                    # Add the result to the state
                    tool_result_message = Message(
                        content=json.dumps(result, indent=2),
                        role=MessageRole.SYSTEM,
                        type=MessageType.TOOL_RESULT,
                        sender=tool.name,
                        receiver="workflow",
                        metadata={"tool_id": tool_id, "result": result}
                    )
                    graph_state.add_message(tool_result_message)
                    
                except Exception as e:
                    logger.error(f"Error invoking tool '{tool.name}': {str(e)}")
                    error_message = Message(
                        content=f"Error in tool '{tool.name}': {str(e)}",
                        role=MessageRole.SYSTEM,
                        type=MessageType.ERROR,
                        sender="system",
                        receiver="user"
                    )
                    graph_state.add_message(error_message)
                    graph_state.set_error(str(e))
                
                return graph_state.to_dict()
                
            return tool_node_func
        except Exception as e:
            logger.error(f"Error creating tool node: {str(e)}")
            return None
    
    def _create_conditional_node(self, node_config: Dict[str, Any]) -> Optional[Callable]:
        """
        Create a conditional node.
        
        Args:
            node_config: Node configuration
            
        Returns:
            Node function
        """
        try:
            condition_type = node_config.get("condition_type", "")
            
            if condition_type == "message_contains":
                # Check if the message contains any of the keywords
                keywords = node_config.get("keywords", [])
                message_index = node_config.get("message_index", -1)
                
                def condition_func(state: Dict[str, Any]) -> str:
                    try:
                        graph_state = GraphState.from_dict(state)
                        
                        if not graph_state.messages:
                            return "default"
                            
                        # Get the message to check
                        messages = graph_state.messages
                        if abs(message_index) > len(messages):
                            return "default"
                            
                        message = messages[message_index]
                        content = message.get("content", "")
                        
                        # Check if any of the keywords are in the message
                        for keyword in keywords:
                            if keyword.lower() in content.lower():
                                return "true"
                                
                        return "false"
                    except Exception as e:
                        logger.error(f"Error in conditional node: {str(e)}")
                        return "error"
                        
                return condition_func
                
            elif condition_type == "message_type":
                # Check if the message type is as specified
                message_type = node_config.get("message_type", "")
                message_index = node_config.get("message_index", -1)
                
                def condition_func(state: Dict[str, Any]) -> str:
                    try:
                        graph_state = GraphState.from_dict(state)
                        
                        if not graph_state.messages:
                            return "default"
                            
                        # Get the message to check
                        messages = graph_state.messages
                        if abs(message_index) > len(messages):
                            return "default"
                            
                        message = messages[message_index]
                        msg_type = message.get("type", "")
                        
                        # Check if the message type is as specified
                        if msg_type == message_type:
                            return "true"
                            
                        return "false"
                    except Exception as e:
                        logger.error(f"Error in conditional node: {str(e)}")
                        return "error"
                        
                return condition_func
                
            elif condition_type == "custom":
                # Custom condition function
                condition_module = node_config.get("condition_module", "")
                condition_function = node_config.get("condition_function", "")
                
                if not condition_module or not condition_function:
                    logger.error("Condition module and function are required for custom condition")
                    return None
                
                try:
                    module = importlib.import_module(condition_module)
                    func = getattr(module, condition_function)
                    return func
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error importing condition function {condition_module}.{condition_function}: {str(e)}")
                    return None
                    
            else:
                logger.error(f"Unsupported condition type: {condition_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating conditional node: {str(e)}")
            return None
    
    def _create_router_node(self, node_config: Dict[str, Any]) -> Optional[Callable]:
        """
        Create a router node.
        
        Args:
            node_config: Node configuration
            
        Returns:
            Node function
        """
        try:
            router_type = node_config.get("router_type", "")
            
            if router_type == "message_router":
                # Route based on message content
                routes = node_config.get("routes", {})
                default_route = node_config.get("default", None)
                
                def router_func(state: Dict[str, Any]) -> str:
                    try:
                        graph_state = GraphState.from_dict(state)
                        
                        if not graph_state.messages:
                            return default_route or "default"
                            
                        # Get the last message
                        last_message = graph_state.messages[-1]
                        content = last_message.get("content", "").lower()
                        
                        # Check if any of the keywords are in the message
                        for keyword, route in routes.items():
                            if keyword.lower() in content:
                                return route
                                
                        return default_route or "default"
                    except Exception as e:
                        logger.error(f"Error in router node: {str(e)}")
                        return default_route or "error"
                        
                return router_func
                
            elif router_type == "message_type_router":
                # Route based on message type
                routes = node_config.get("routes", {})
                default_route = node_config.get("default", None)
                
                def router_func(state: Dict[str, Any]) -> str:
                    try:
                        graph_state = GraphState.from_dict(state)
                        
                        if not graph_state.messages:
                            return default_route or "default"
                            
                        # Get the last message
                        last_message = graph_state.messages[-1]
                        msg_type = last_message.get("type", "")
                        
                        # Check if the message type matches
                        if msg_type in routes:
                            return routes[msg_type]
                            
                        return default_route or "default"
                    except Exception as e:
                        logger.error(f"Error in router node: {str(e)}")
                        return default_route or "error"
                        
                return router_func
                
            elif router_type == "custom":
                # Custom router function
                router_module = node_config.get("router_module", "")
                router_function = node_config.get("router_function", "")
                
                if not router_module or not router_function:
                    logger.error("Router module and function are required for custom router")
                    return None
                
                try:
                    module = importlib.import_module(router_module)
                    func = getattr(module, router_function)
                    return func
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error importing router function {router_module}.{router_function}: {str(e)}")
                    return None
                    
            else:
                logger.error(f"Unsupported router type: {router_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating router node: {str(e)}")
            return None
    
    def build_graph(self, graph_config: Optional[Dict[str, Any]] = None) -> Optional[lg.StateGraph]:
        """
        Create a LangGraph graph.
        
        Args:
            graph_config: Graph configuration (optional, read from configuration if None)
            
        Returns:
            Created LangGraph graph
        """
        try:
            # Check configuration
            if graph_config is None:
                graph_config = self.config.get("graph", {})
                
            if not graph_config:
                logger.error("Graph configuration is required")
                return None
                
            # Create nodes
            nodes_config = graph_config.get("nodes", [])
            
            for node_config in nodes_config:
                node_id = node_config.get("id", "")
                node_type = node_config.get("type", "")
                
                if not node_id or not node_type:
                    logger.error("Node ID and type are required")
                    continue
                    
                # Create node based on type
                if node_type == GraphNodeType.AGENT:
                    node_func = self._create_agent_node(node_config)
                elif node_type == GraphNodeType.TOOL:
                    node_func = self._create_tool_node(node_config)
                elif node_type == GraphNodeType.CONDITIONAL:
                    node_func = self._create_conditional_node(node_config)
                elif node_type == GraphNodeType.ROUTER:
                    node_func = self._create_router_node(node_config)
                else:
                    logger.error(f"Unsupported node type: {node_type}")
                    continue
                    
                if node_func:
                    self.nodes[node_id] = node_func
                    
            # Create graph
            entry_point = graph_config.get("entry_point", "")
            
            if not entry_point or entry_point not in self.nodes:
                logger.error(f"Invalid entry point: {entry_point}")
                return None
                
            # Create StateGraph
            builder = lg.StateGraph(GraphState)
            
            # Add nodes
            for node_id, node_func in self.nodes.items():
                builder.add_node(node_id, node_func)
                
            # Add edges
            edges = graph_config.get("edges", [])
            
            for edge in edges:
                source = edge.get("source", "")
                target = edge.get("target", "")
                condition = edge.get("condition", None)
                
                if not source or not target:
                    logger.error("Edge source and target are required")
                    continue
                    
                if source not in self.nodes:
                    logger.error(f"Invalid edge source: {source}")
                    continue
                    
                if target != END and target not in self.nodes:
                    logger.error(f"Invalid edge target: {target}")
                    continue
                    
                # Add edge based on type
                if condition is None:
                    # Simple edge
                    builder.add_edge(source, target)
                else:
                    # Conditional edge
                    builder.add_conditional_edges(
                        source,
                        condition if callable(condition) else self.nodes[condition],
                        {
                            edge.get("condition_value", "true"): target,
                            **edge.get("condition_branches", {})
                        }
                    )
            
            # Set entry point
            builder.set_entry_point(entry_point)
            
            self.graph = builder.compile()
            
            # Create memory manager
            self.executor = self.graph
            
            logger.info("Built LangGraph with %d nodes and %d edges", len(self.nodes), len(edges))
            return self.graph
            
        except Exception as e:
            logger.error(f"Error building graph: {str(e)}")
            return None
    
    def run(self, 
           initial_input: Optional[Dict[str, Any]] = None, 
           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the workflow.
        
        Args:
            initial_input: Initial input (optional)
            config: Run configuration (optional)
            
        Returns:
            Workflow result
        """
        try:
            if not self.graph or not self.executor:
                logger.error("Graph not built yet")
                return {"error": "Graph not built yet"}
                
            # Create initial state
            initial_state = GraphState()
            
            # Add initial message
            if initial_input:
                if "message" in initial_input:
                    message_content = initial_input["message"]
                    user_id = initial_input.get("user_id", "user")
                    
                    user_message = Message(
                        content=message_content,
                        role=MessageRole.USER,
                        type=MessageType.TEXT,
                        sender=user_id,
                        receiver="workflow"
                    )
                    
                    initial_state.add_message(user_message)
                    
                # Add other inputs
                for key, value in initial_input.items():
                    if key != "message":
                        initial_state[key] = value
            
            # Run the workflow
            result = self.executor.invoke(initial_state.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"Error running workflow: {str(e)}")
            return {"error": str(e)}
    
    async def arun(self, 
                 initial_input: Optional[Dict[str, Any]] = None, 
                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the workflow asynchronously.
        
        Args:
            initial_input: Initial input (optional)
            config: Run configuration (optional)
            
        Returns:
            Workflow result
        """
        try:
            if not self.graph or not self.executor:
                logger.error("Graph not built yet")
                return {"error": "Graph not built yet"}
                
            # Create initial state
            initial_state = GraphState()
            
            # Add initial message
            if initial_input:
                if "message" in initial_input:
                    message_content = initial_input["message"]
                    user_id = initial_input.get("user_id", "user")
                    
                    user_message = Message(
                        content=message_content,
                        role=MessageRole.USER,
                        type=MessageType.TEXT,
                        sender=user_id,
                        receiver="workflow"
                    )
                    
                    initial_state.add_message(user_message)
                    
                # Add other inputs
                for key, value in initial_input.items():
                    if key != "message":
                        initial_state[key] = value
            
            # Run the workflow asynchronously
            result = await self.executor.ainvoke(initial_state.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"Error running workflow asynchronously: {str(e)}")
            return {"error": str(e)}
    
    def stream(self, 
              initial_input: Optional[Dict[str, Any]] = None, 
              config: Optional[Dict[str, Any]] = None):
        """
        Run the workflow in stream mode.
        
        Args:
            initial_input: Initial input (optional)
            config: Run configuration (optional)
            
        Returns:
            Stream of status updates
        """
        try:
            if not self.graph or not self.executor:
                logger.error("Graph not built yet")
                yield {"error": "Graph not built yet"}
                return
                
            # Create initial state
            initial_state = GraphState()
            
            # Add initial message
            if initial_input:
                if "message" in initial_input:
                    message_content = initial_input["message"]
                    user_id = initial_input.get("user_id", "user")
                    
                    user_message = Message(
                        content=message_content,
                        role=MessageRole.USER,
                        type=MessageType.TEXT,
                        sender=user_id,
                        receiver="workflow"
                    )
                    
                    initial_state.add_message(user_message)
                    
                # Add other inputs
                for key, value in initial_input.items():
                    if key != "message":
                        initial_state[key] = value
            
            # Run the workflow in stream mode
            for update in self.executor.stream(initial_state.to_dict()):
                yield update
                
        except Exception as e:
            logger.error(f"Error streaming workflow: {str(e)}")
            yield {"error": str(e)}
    
    async def astream(self, 
                    initial_input: Optional[Dict[str, Any]] = None, 
                    config: Optional[Dict[str, Any]] = None):
        """
        Run the workflow asynchronously in stream mode.
        
        Args:
            initial_input: Initial input (optional)
            config: Run configuration (optional)
            
        Returns:
            Stream of status updates
        """
        try:
            if not self.graph or not self.executor:
                logger.error("Graph not built yet")
                yield {"error": "Graph not built yet"}
                return
                
            # Create initial state
            initial_state = GraphState()
            
            # Add initial message
            if initial_input:
                if "message" in initial_input:
                    message_content = initial_input["message"]
                    user_id = initial_input.get("user_id", "user")
                    
                    user_message = Message(
                        content=message_content,
                        role=MessageRole.USER,
                        type=MessageType.TEXT,
                        sender=user_id,
                        receiver="workflow"
                    )
                    
                    initial_state.add_message(user_message)
                    
                # Add other inputs
                for key, value in initial_input.items():
                    if key != "message":
                        initial_state[key] = value
            
            # Run the workflow asynchronously in stream mode
            async for update in self.executor.astream(initial_state.to_dict()):
                yield update
                
        except Exception as e:
            logger.error(f"Error streaming workflow asynchronously: {str(e)}")
            yield {"error": str(e)} 