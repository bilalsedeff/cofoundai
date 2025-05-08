"""
CoFound.ai LangGraph Workflow Engine

This module defines the LangGraph-based workflow engine for CoFound.ai.
LangGraph is used to manage complex agent workflows and states.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Set
import json
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, END

from cofoundai.core.base_agent import BaseAgent
from cofoundai.utils.logger import workflow_logger


class LangGraphWorkflow:
    """
    LangGraph-based workflow engine.
    
    This class defines and manages state machine-based workflows using the
    LangGraph library. Workflows can be created from configuration in YAML files.
    """
    
    def __init__(self, name: str, config: Dict[str, Any], agents: Dict[str, BaseAgent] = None):
        """
        Initialize a LangGraph workflow.
        
        Args:
            name: Workflow name
            config: Workflow configuration
            agents: Collection of agents to use in the workflow
        """
        self.name = name
        self.config = config
        self.agents = agents or {}
        self.logger = workflow_logger
        self.graph = None
        self._initialize_graph()
        
    def _initialize_graph(self) -> None:
        """
        Initialize the LangGraph state graph according to configuration.
        """
        self.logger.info(f"Initializing LangGraph workflow: {self.name}")
        
        # Define workflow state (shared state between agents)
        workflow_state = {
            "messages": [],
            "current_phase": None,
            "completed_phases": [],
            "artifacts": {},
            "metadata": {},
            "error": None
        }
        
        # Create state graph
        builder = StateGraph(workflow_state)
        
        # Define states and transitions
        if "langgraph" in self.config:
            lg_config = self.config["langgraph"]
            states = {state["name"]: state for state in lg_config.get("states", [])}
            
            # Add node for each state
            for state_name, state_info in states.items():
                agent_name = state_info.get("agent")
                if agent_name in self.agents:
                    # Add a node using real agent function
                    builder.add_node(state_name, self._create_state_handler(agent_name, state_info))
                else:
                    # If agent doesn't exist, add a placeholder function (for logging)
                    self.logger.warning(f"Agent not found: {agent_name}, using placeholder")
                    builder.add_node(state_name, self._create_placeholder_handler(state_name, state_info))
            
            # Add transitions
            for transition in lg_config.get("transitions", []):
                from_state = transition.get("from")
                to_state = transition.get("to")
                
                if to_state is None:
                    builder.add_edge(from_state, END)
                    self.logger.debug(f"Added transition: {from_state} -> END")
                else:
                    builder.add_edge(from_state, to_state)
                    self.logger.debug(f"Added transition: {from_state} -> {to_state}")
            
            # Determine entry point (first state)
            if lg_config.get("states"):
                entry_state = lg_config["states"][0]["name"]
                builder.set_entry_point(entry_state)
                self.logger.info(f"Entry point set: {entry_state}")
        
        # Compile graph
        self.graph = builder.compile()
        self.logger.info(f"LangGraph workflow compiled: {self.name}")
    
    def _create_state_handler(self, agent_name: str, state_info: Dict[str, Any]) -> Callable:
        """
        Creates a function for a specific state.
        
        Args:
            agent_name: Name of agent to perform the function
            state_info: Information about the state
            
        Returns:
            State handling function
        """
        def state_handler(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            State handling function.
            
            Args:
                state: Current workflow state
                
            Returns:
                Updated workflow state
            """
            self.logger.info(f"Processing workflow state: {agent_name} - {state_info.get('name')}")
            
            # Update state
            state["current_phase"] = state_info.get("name")
            
            try:
                # Call actual agent function (currently simulated)
                agent = self.agents.get(agent_name)
                if agent:
                    # At this point, LLM call would be made in agent's process_input method
                    # For now, we're just logging
                    self.logger.info(f"Calling agent: {agent_name}")
                    
                    # When agent is called, we'll add a message to the state
                    message = {
                        "from": agent_name,
                        "content": f"Completed [{state_info.get('name')}] operation",
                        "timestamp": "__timestamp__",  # Real timestamp will be added
                        "metadata": {
                            "phase": state_info.get("name"),
                            "description": state_info.get("description", "")
                        }
                    }
                    state["messages"].append(message)
                    
                    # Update completed phases
                    if state_info.get("name") not in state["completed_phases"]:
                        state["completed_phases"].append(state_info.get("name"))
            except Exception as e:
                # Record error state
                error_msg = f"Error while processing state: {str(e)}"
                self.logger.error(error_msg)
                state["error"] = error_msg
            
            return state
            
        return state_handler
    
    def _create_placeholder_handler(self, state_name: str, state_info: Dict[str, Any]) -> Callable:
        """
        Creates a placeholder function to use when an agent doesn't exist.
        
        Args:
            state_name: State name
            state_info: Information about the state
            
        Returns:
            Placeholder state handling function
        """
        def placeholder_handler(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            Placeholder state handling function.
            
            Args:
                state: Current workflow state
                
            Returns:
                Updated workflow state
            """
            self.logger.warning(f"Placeholder function called: {state_name}")
            
            # Update state
            state["current_phase"] = state_name
            
            # Add a placeholder message
            message = {
                "from": "system",
                "content": f"Placeholder function executed for [{state_name}].",
                "timestamp": "__timestamp__",
                "metadata": {
                    "phase": state_name,
                    "description": state_info.get("description", "No description"),
                    "placeholder": True
                }
            }
            state["messages"].append(message)
            
            # Update completed phases
            if state_name not in state["completed_phases"]:
                state["completed_phases"].append(state_name)
                
            return state
            
        return placeholder_handler
    
    def run(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the workflow.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Final state of the workflow
        """
        if self.graph is None:
            self.logger.error("Workflow graph not yet initialized")
            return {"error": "Workflow graph not initialized"}
        
        self.logger.info(f"Running workflow: {self.name}")
        
        # Prepare initial state
        initial_state = {
            "messages": [],
            "current_phase": None,
            "completed_phases": [],
            "artifacts": {},
            "metadata": {},
            "input": input_data or {}
        }
        
        try:
            # Run the graph
            for state in self.graph.stream(initial_state):
                # Log for each intermediate state
                phase = state["current_phase"]
                self.logger.info(f"Workflow state updated: {phase}")
                self.logger.debug(f"Current state: {json.dumps(state, indent=2)}")
            
            # Get final state
            final_state = state
            self.logger.info(f"Workflow completed: {self.name}")
            self.logger.info(f"Completed phases: {', '.join(final_state['completed_phases'])}")
            
            return final_state
        except Exception as e:
            error_msg = f"Error while running workflow: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": error_msg,
                "state": "error"
            }
    
    @classmethod
    def from_config_file(cls, config_file: str, agents: Dict[str, BaseAgent] = None):
        """
        Creates a workflow instance from a configuration file.
        
        Args:
            config_file: Path to YAML configuration file
            agents: Collection of agents to use in the workflow
            
        Returns:
            LangGraphWorkflow instance
        """
        import yaml
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Find main configuration block
            main_config = config.get("main", {})
            
            # Get workflows list
            workflows_list = main_config.get("workflows", [])
            
            if not workflows_list:
                workflow_logger.error("No workflows found in configuration file")
                return None
                
            # Create workflow instance for the first workflow in the list
            first_workflow = workflows_list[0]
            workflow_id = first_workflow.get("id")
            
            if not workflow_id:
                workflow_logger.error("Workflow ID not found in configuration")
                return None
                
            return cls(workflow_id, first_workflow, agents)
            
        except Exception as e:
            workflow_logger.error(f"Error loading configuration file: {str(e)}")
            return None 