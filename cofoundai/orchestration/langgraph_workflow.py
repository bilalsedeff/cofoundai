"""
CoFound.ai LangGraph Workflow

This module defines the LangGraph-based workflow system for agent orchestration.
"""

import logging
import os
from typing import Dict, Any, List, Optional, Union, Type, Callable

from langchain_core.messages import (
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage,
    ToolMessage
)
from langchain_core.tools import BaseTool

from langgraph.graph import (
    END, StateGraph, MessagesState, 
    add_messages
)
from langgraph.checkpoint.memory import MemorySaver

from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.langgraph_agent import LangGraphAgent

# Circular import prevention by importing register_agent_graph later
# Check if API package is available

# Logger
logger = logging.getLogger(__name__)


class LangGraphWorkflow:
    """
    LangGraph-based workflow that orchestrates agent interactions.
    
    This class provides a graph-based workflow system for agent orchestration
    using LangGraph.
    """
    
    def __init__(
            self, 
            name: str,
            config: Optional[Dict[str, Any]] = None
        ):
        """
        Initialize workflow.
        
        Args:
            name: Workflow name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.agents: Dict[str, BaseAgent] = {}
        self.graph = None
        self.graph_builder = None
        self.workdir = self.config.get("workdir", os.getcwd())
        self.checkpointer = MemorySaver()
        
        # If agents exist, add them from config
        if "agents" in self.config and isinstance(self.config["agents"], dict):
            for agent_name, agent in self.config["agents"].items():
                if isinstance(agent, BaseAgent):
                    self.add_agent(agent, agent_name)
        
        # Workflow initialization
        logger.info(f"Initialized workflow: {name}")
    
    def add_agent(self, agent: BaseAgent, name: Optional[str] = None) -> None:
        """
        Add agent to workflow.
        
        Args:
            agent: Agent instance
            name: Name to use for agent (default: agent.name)
        """
        agent_name = name or agent.name
        self.agents[agent_name] = agent
        logger.info(f"Added agent {agent_name} to workflow {self.name}")
    
    def build_graph(self, entry_point: Optional[Union[str, Callable]] = None) -> StateGraph:
        """
        Build the workflow graph.
        
        Args:
            entry_point: Entry point node or function
            
        Returns:
            Built StateGraph
        """
        if not self.agents:
            logger.warning("No agents registered to workflow, can't build graph")
            return None
            
        # Create state graph 
        workflow = StateGraph(MessagesState)
        
        # Keep track of valid nodes
        valid_nodes = []
        
        # Add all agent nodes
        for name, agent in self.agents.items():
            try:
                if isinstance(agent, LangGraphAgent) and agent.langgraph_agent:
                    workflow.add_node(name, agent.langgraph_agent)
                    valid_nodes.append(name)
                    logger.debug(f"Added {name} node to graph")
                else:
                    # Dummy node function for non-LangGraph agents
                    def create_dummy_node(agent_name):
                        def dummy_node_func(state):
                            # Just pass through the state with a placeholder message
                            if "messages" in state and len(state["messages"]) > 0:
                                state["messages"].append(AIMessage(
                                    content=f"[{agent_name} processed message but can't respond in LangGraph format]"
                                ))
                            return state
                        return dummy_node_func
                    
                    # Add dummy node
                    workflow.add_node(name, create_dummy_node(name))
                    valid_nodes.append(name)
                    logger.debug(f"Added dummy node for {name}")
            except Exception as e:
                logger.error(f"Error adding node for agent {name}: {str(e)}")
                # Not adding this node to valid_nodes
        
        # Add edges, but only between valid nodes
        if len(valid_nodes) > 1:
            for i in range(len(valid_nodes) - 1):
                current = valid_nodes[i]
                next_agent = valid_nodes[i + 1]
                try:
                    workflow.add_edge(current, next_agent)
                    logger.debug(f"Added edge: {current} -> {next_agent}")
                except Exception as e:
                    logger.error(f"Error adding edge from {current} to {next_agent}: {str(e)}")
                
            # Add edge from last to END
            try:
                workflow.add_edge(valid_nodes[-1], END)
                logger.debug(f"Added edge: {valid_nodes[-1]} -> END")
            except Exception as e:
                logger.error(f"Error adding edge from {valid_nodes[-1]} to END: {str(e)}")
                
        elif len(valid_nodes) == 1:
            # Only one agent, connect directly to END
            try:
                workflow.add_edge(valid_nodes[0], END)
                logger.debug(f"Added edge: {valid_nodes[0]} -> END")
            except Exception as e:
                logger.error(f"Error adding edge from {valid_nodes[0]} to END: {str(e)}")
            
        # Set entry point, but only if it's a valid node
        if entry_point in valid_nodes:
            workflow.set_entry_point(entry_point)
            logger.debug(f"Set entry point to: {entry_point}")
        elif valid_nodes:
            workflow.set_entry_point(valid_nodes[0])
            logger.debug(f"Set entry point to: {valid_nodes[0]}")
        else:
            logger.error("No valid nodes found, cannot set entry point")
            return None
            
        # Compile graph
        try:
            graph = workflow.compile()
            
            # Store for later use
            self.graph_builder = workflow
            self.graph = graph
            
            logger.info(f"Built graph for workflow: {self.name}")
            return graph
        except Exception as e:
            logger.error(f"Error compiling graph: {str(e)}")
            return None
    
    def run(self, input_data: Any) -> Dict[str, Any]:
        """
        Run the workflow with input data.
        
        Args:
            input_data: Input for the workflow
            
        Returns:
            Output from workflow execution
        """
        if not self.graph:
            self.build_graph()
            
        if not self.graph:
            logger.error("Cannot run workflow, graph not built")
            return {"error": "Cannot run workflow, graph not built"}
            
        # Create input based on type
        if isinstance(input_data, str):
            input_message = HumanMessage(content=input_data)
            initial_state = {"messages": [input_message]}
        elif isinstance(input_data, BaseMessage):
            initial_state = {"messages": [input_data]}
        elif isinstance(input_data, dict):
            if "messages" in input_data:
                initial_state = input_data
            else:
                # Convert dict to HumanMessage
                input_message = HumanMessage(content=str(input_data))
                initial_state = {"messages": [input_message]}
        else:
            # Default conversion for other types
            input_message = HumanMessage(content=str(input_data))
            initial_state = {"messages": [input_message]}
        
        # Configure workflow execution
        config = {
            "configurable": {
                "thread_id": f"{self.name}_{id(self)}"
            }
        }
        
        try:
            # Run the workflow
            result = self.graph.invoke(initial_state, config=config)
            return result
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            return {"error": f"Workflow execution failed: {str(e)}"}
    
    def stream(self, input_data: Any):
        """
        Stream the workflow execution.
        
        Args:
            input_data: Input for the workflow
            
        Yields:
            State updates during execution
        """
        if not self.graph:
            self.build_graph()
            
        if not self.graph:
            logger.error("Cannot stream workflow, graph not built")
            yield {"error": "Cannot stream workflow, graph not built"}
            return
            
        # Create input based on type
        if isinstance(input_data, str):
            input_message = HumanMessage(content=input_data)
            initial_state = {"messages": [input_message]}
        elif isinstance(input_data, BaseMessage):
            initial_state = {"messages": [input_data]}
        elif isinstance(input_data, dict):
            if "messages" in input_data:
                initial_state = input_data
            else:
                # Convert dict to HumanMessage
                input_message = HumanMessage(content=str(input_data))
                initial_state = {"messages": [input_message]}
        else:
            # Default conversion for other types
            input_message = HumanMessage(content=str(input_data))
            initial_state = {"messages": [input_message]}
        
        # Configure workflow execution
        config = {
            "configurable": {
                "thread_id": f"{self.name}_{id(self)}"
            }
        }
        
        try:
            # Stream the workflow execution
            for chunk in self.graph.stream(initial_state, config=config):
                yield chunk
        except Exception as e:
            logger.error(f"Error in workflow streaming: {str(e)}")
            yield {"error": f"Workflow streaming failed: {str(e)}"}
    
    def register_as_agent(self, agent_id: str) -> bool:
        """
        Register this workflow with the Agent Protocol API.
        
        This function makes the workflow available as an agent through the API.
        It checks for the existence of the API module and registers if available.
        
        Args:
            agent_id: Agent ID to use in the API
            
        Returns:
            Was registration successful? (True/False)
        """
        try:
            # Dynamically import API module
            # This allows for optional API module
            from cofoundai.api.app import register_agent_graph
            
            if not self.graph:
                self.build_graph()
                
            if self.graph:
                # Register the workflow
                result = register_agent_graph(agent_id, self.graph)
                if result:
                    logger.info(f"Workflow {self.name} registered as agent {agent_id}")
                    return True
                else:
                    logger.error(f"Failed to register workflow {self.name} as agent {agent_id}")
            else:
                logger.error(f"Cannot register workflow {self.name} as agent, graph not built")
        except ImportError:
            logger.warning("API module not available, skipping agent registration")
        except Exception as e:
            logger.error(f"Error registering workflow as agent: {str(e)}")
            
        return False 