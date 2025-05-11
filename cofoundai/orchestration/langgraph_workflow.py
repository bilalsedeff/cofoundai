"""
CoFound.ai LangGraph Workflow Engine

This module defines the LangGraph workflow engine for agent orchestration.
Handles state management and workflow graph construction.
"""

import logging
from typing import Dict, Any, Callable, List, Optional, Type

from cofoundai.core.base_agent import BaseAgent
from cofoundai.utils.logger import get_workflow_logger


class LangGraphWorkflow:
    """
    LangGraph-based workflow manager for coordinating agent interactions.
    """
    
    def __init__(self, name: str, config: Dict[str, Any], agents: Optional[Dict[str, BaseAgent]] = None):
        """
        Initialize the LangGraph workflow.
        
        Args:
            name: Name of the workflow
            config: Workflow configuration settings
            agents: Optional dictionary of agent names to agent objects to automatically register
        """
        self.name = name
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.state_map: Dict[str, Callable] = {}
        self.logger = get_workflow_logger(f"workflow.{name}")
        self.test_mode = config.get("test_mode", False)
        
        # Auto-register agents if provided
        if agents:
            for agent_name, agent in agents.items():
                self.register_agent(agent)
            self.logger.info(f"Auto-registered {len(agents)} agents")
        
    def register_agent(self, agent: BaseAgent, state_name: Optional[str] = None) -> None:
        """
        Register an agent with the workflow.
        
        Args:
            agent: Agent to register
            state_name: Optional state name for the agent (defaults to agent name)
        """
        agent_name = agent.name
        self.agents[agent_name] = agent
        
        # If no state name is provided, use the agent name
        if state_name is None:
            state_name = agent_name
            
        # Create state handler for this agent
        self.state_map[state_name] = self._create_state_handler(agent_name, {})
        
        self.logger.info(f"Agent registered: {agent_name} as state: {state_name}")

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
            self.logger.info(f"Executing state: {agent_name}")
            self.logger.debug(f"Input state: {state}")
            
            # Get the agent
            agent = self.agents.get(agent_name)
            if not agent:
                self.logger.error(f"Agent not found: {agent_name}")
                return {
                    **state,
                    "error": f"Agent not found: {agent_name}",
                    "status": "error"
                }
                
            try:
                # Process the current state data with the agent
                result = agent.process(state)
                
                # Update state with agent's result
                updated_state = {
                    **state,
                    "previous_results": {
                        **(state.get("previous_results", {})),
                        agent_name: result
                    },
                    "current_agent": agent_name,
                    "status": result.get("status", "success")
                }
                
                # Store the raw result as well
                updated_state[agent_name] = result
                
                self.logger.info(f"State {agent_name} completed: {result.get('status', 'success')}")
                self.logger.debug(f"Output state: {updated_state}")
                
                return updated_state
                
            except Exception as e:
                self.logger.error(f"Error in state {agent_name}: {str(e)}")
                return {
                    **state,
                    "error": str(e),
                    "current_agent": agent_name,
                    "status": "error"
                }
                
        return state_handler
        
    def build_graph(self) -> Any:
        """
        Build the LangGraph workflow graph.
        
        In test mode, returns a simple callable function that simulates the graph execution.
        
        Returns:
            Workflow graph object (or simulation function in test mode)
        """
        if self.test_mode:
            return self._build_test_graph()
            
        try:
            # This would normally import and use LangGraph
            # For prototype testing without LLM, we're using a simpler approach
            
            from langchain.agents import AgentType, initialize_agent, Tool
            from langchain.chains import LLMChain
            
            # Create a simple graph for testing - this is a placeholder
            # In a real implementation, this would create the actual LangGraph workflow
            
            self.logger.info(f"Building workflow graph: {self.name}")
            
            return self._build_test_graph()  # Fallback to test graph for now
                
        except ImportError:
            self.logger.warning("LangGraph not available, using test mode fallback")
            return self._build_test_graph()
            
    def _build_test_graph(self):
        """
        Build a simple function that simulates LangGraph execution for testing.
        
        Returns:
            Function that executes the workflow
        """
        def execute_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
            """
            Execute the workflow in a linear fashion for testing.
            
            Args:
                initial_state: Initial state for the workflow
                
            Returns:
                Final workflow state
            """
            self.logger.info(f"Executing test workflow: {self.name}")
            
            # Start with the initial state
            current_state = initial_state.copy()
            current_state["status"] = "starting"
            current_state["previous_results"] = {}
            
            # Get the agent execution order from config or use all agents in registration order
            agent_order = self.config.get("test_agent_order", list(self.agents.keys()))
            
            for agent_name in agent_order:
                # Log the transition
                self.logger.info(f"Transitioning to agent: {agent_name}")
                
                # Execute the state handler for this agent
                if agent_name in self.state_map:
                    try:
                        current_state = self.state_map[agent_name](current_state)
                        
                        # Check for error status
                        if current_state.get("status") == "error":
                            self.logger.error(f"Workflow stopped due to error in {agent_name}")
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error during {agent_name} execution: {str(e)}")
                        current_state["status"] = "error"
                        current_state["error"] = str(e)
                        break
                else:
                    self.logger.warning(f"State handler not found for agent: {agent_name}")
            
            # Mark workflow as complete
            if current_state.get("status") != "error":
                current_state["status"] = "complete"
                
            self.logger.info(f"Workflow completed with status: {current_state.get('status')}")
            return current_state
            
        return execute_workflow
        
    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the workflow with the given initial state.
        
        Args:
            initial_state: Initial state for the workflow
            
        Returns:
            Final workflow state
        """
        self.logger.info(f"Running workflow: {self.name}")
        
        # Build the graph (or get the testing function)
        graph = self.build_graph()
        
        # Run the workflow
        result = graph(initial_state)
        
        return result 