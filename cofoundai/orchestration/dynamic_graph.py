"""
CoFound.ai Dynamic Graph Orchestration

This module implements a dynamic, flexible graph-based workflow system that allows
agents to communicate and collaborate in a more fluid manner than static workflows.
"""

from typing import Dict, Any, List, Optional, Union, Callable, Type, Set, Tuple, cast
import logging
from enum import Enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import create_react_agent, create_tools_extraction_agent

from cofoundai.communication.agent_command import Command, CommandType, CommandTarget, AgentState, HandoffTool
from cofoundai.communication.message import Message
from cofoundai.agents.langgraph_agent import LangGraphAgent


# Set up logging
logger = logging.getLogger(__name__)


class WorkflowState(AgentState):
    """
    State representation for the dynamic workflow graph.
    
    This class extends AgentState with workflow-specific fields.
    """
    
    # Overall workflow status
    workflow_status: str = "starting"  # starting, in_progress, completed, failed
    
    # The task/project being worked on
    project_description: str = ""
    
    # Current workflow step
    current_step: str = "initialize"
    
    # Workflow history
    steps_completed: List[str] = Field(default_factory=list)
    
    # Final output
    output: Optional[Dict[str, Any]] = None


class DynamicWorkflow:
    """
    Dynamic workflow implementation using LangGraph.
    
    This class creates a flexible, dynamic workflow graph that can be
    reconfigured at runtime by agent decisions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the dynamic workflow.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.name = config.get("name", "DynamicWorkflow")
        self.description = config.get("description", "Dynamic agent workflow")
        
        # Registered agents
        self.agents: Dict[str, LangGraphAgent] = {}
        
        # LangGraph graph
        self.graph = None
        
        # Workflow state
        self.initial_state = WorkflowState()
        
        # Initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the workflow graph."""
        self._build_graph()
    
    def register_agent(self, agent: LangGraphAgent) -> None:
        """
        Register an agent with the workflow.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.name] = agent
        
        # Add handoff tools to agent
        self._add_handoff_tools(agent)
        
        # Rebuild graph with the new agent
        self._build_graph()
    
    def _add_handoff_tools(self, agent: LangGraphAgent) -> None:
        """
        Add handoff tools to an agent for all other registered agents.
        
        Args:
            agent: Agent to add tools to
        """
        for other_agent_name, other_agent in self.agents.items():
            if other_agent_name != agent.name:
                # Create handoff tool
                handoff_tool = HandoffTool(other_agent_name)
                try:
                    # Add as LangChain tool
                    lc_tool = handoff_tool.get_langchain_tool()
                    agent.add_tool(lc_tool)
                except Exception as e:
                    logger.error(f"Failed to add handoff tool to {agent.name}: {str(e)}")
    
    def _build_graph(self) -> None:
        """Build the workflow graph with registered agents."""
        if not self.agents:
            logger.warning("No agents registered, skipping graph build")
            return
        
        try:
            # Create a new state graph
            builder = StateGraph(WorkflowState)
            
            # Add nodes for each agent
            for agent_name, agent in self.agents.items():
                builder.add_node(agent_name, self._create_agent_node(agent))
            
            # Add supervisor node
            builder.add_node("supervisor", self._create_supervisor_node())
            
            # Add entry point
            builder.set_entry_point("supervisor")
            
            # Connect nodes with conditional routing
            for agent_name in self.agents.keys():
                # Each agent can potentially route to any other agent or END
                builder.add_conditional_edges(
                    agent_name,
                    self._route_agent_output,
                    {other_name: self._create_condition(other_name) for other_name in self.agents.keys()}
                )
                
                # Add conditional route to END
                builder.add_edge(agent_name, END, self._should_end)
            
            # Supervisor can route to any agent
            builder.add_conditional_edges(
                "supervisor",
                self._route_supervisor_output,
                {agent_name: self._create_condition(agent_name) for agent_name in self.agents.keys()}
            )
            
            # Add edge from supervisor to END
            builder.add_edge("supervisor", END, self._should_end)
            
            # Compile the graph
            self.graph = builder.compile()
            
            logger.info(f"Built workflow graph with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to build workflow graph: {str(e)}")
            self.graph = None
    
    def _create_agent_node(self, agent: LangGraphAgent) -> Callable:
        """
        Create a graph node function for an agent.
        
        Args:
            agent: The agent to create a node for
            
        Returns:
            Node function
        """
        def agent_node(state: WorkflowState) -> WorkflowState:
            """Agent node function."""
            try:
                # Get the last message
                if state.messages:
                    last_message = state.messages[-1]
                    
                    # Create a Message object
                    if isinstance(last_message, dict):
                        # Assume it's already in the correct format
                        message = Message(
                            sender=last_message.get("sender", "human"),
                            recipient=agent.name,
                            content=last_message.get("content", ""),
                            metadata=last_message.get("metadata", {})
                        )
                    else:
                        # Convert from LangChain message
                        message = agent._convert_from_langchain_message(last_message)
                        message.recipient = agent.name
                    
                    # Process the message
                    response = agent.process_message(message)
                    
                    # Update the state
                    updated_state = state.copy()
                    updated_state.messages.append(response.to_dict())
                    
                    # Check for commands in the response
                    if "command" in response.metadata:
                        command_data = response.metadata["command"]
                        command = Command.from_dict(command_data)
                        
                        # Apply the command to update state
                        updated_state = updated_state.update_from_command(command)
                    
                    return updated_state
                
                # If there are no messages, return the state unchanged
                return state
                
            except Exception as e:
                logger.error(f"Error in agent node {agent.name}: {str(e)}")
                
                # Create an error state
                error_state = state.copy()
                error_state.errors.append({
                    "timestamp": datetime.now().timestamp(),
                    "agent": agent.name,
                    "error": str(e)
                })
                error_state.status = "error"
                
                return error_state
        
        return agent_node
    
    def _create_supervisor_node(self) -> Callable:
        """
        Create the supervisor node function.
        
        Returns:
            Supervisor node function
        """
        def supervisor_node(state: WorkflowState) -> WorkflowState:
            """Supervisor node function."""
            # If this is the first step, initialize workflow
            if state.workflow_status == "starting":
                # Update state to in_progress
                updated_state = state.copy()
                updated_state.workflow_status = "in_progress"
                
                # If there are agents, route to the first agent (usually planner)
                if "Planner" in self.agents:
                    updated_state.current_agent = "Planner"
                elif self.agents:
                    # Get the first agent
                    updated_state.current_agent = next(iter(self.agents.keys()))
                
                return updated_state
            
            # If there's a current command, process it
            if state.current_command:
                updated_state = state.copy()
                
                # If it's a handoff, update current agent
                if state.current_command.type == CommandType.HANDOFF and state.current_command.goto:
                    updated_state.current_agent = state.current_command.goto
                
                # If it's an end command, complete the workflow
                elif state.current_command.type == CommandType.END:
                    updated_state.workflow_status = "completed"
                    
                    # Set final output if available
                    if state.current_command.metadata and "final_message" in state.current_command.metadata:
                        updated_state.output = {
                            "status": "success",
                            "message": state.current_command.metadata["final_message"]
                        }
                
                # Clear the current command
                updated_state.current_command = None
                
                return updated_state
            
            # Default: maintain current state and agent
            return state
        
        return supervisor_node
    
    def _route_agent_output(self, state: WorkflowState) -> str:
        """
        Route agent output to the next agent or node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Name of the next node
        """
        # If there's a current_agent set, route to that agent
        if state.current_agent and state.current_agent in self.agents:
            return state.current_agent
        
        # Default to routing to the supervisor
        return "supervisor"
    
    def _route_supervisor_output(self, state: WorkflowState) -> str:
        """
        Route supervisor output to the next node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Name of the next node
        """
        # If there's a current_agent set, route to that agent
        if state.current_agent and state.current_agent in self.agents:
            return state.current_agent
        
        # If workflow is completed or failed, end
        if state.workflow_status in ["completed", "failed"]:
            return END
        
        # Default to staying in supervisor
        return "supervisor"
    
    def _create_condition(self, agent_name: str) -> Callable:
        """
        Create a routing condition for an agent.
        
        Args:
            agent_name: Name of the agent to route to
            
        Returns:
            Condition function
        """
        def condition(state: WorkflowState) -> bool:
            """Check if we should route to this agent."""
            return state.current_agent == agent_name
        
        return condition
    
    def _should_end(self, state: WorkflowState) -> bool:
        """
        Check if the workflow should end.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if the workflow should end
        """
        # End if workflow is completed or failed
        return state.workflow_status in ["completed", "failed"]
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the workflow.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Workflow output
        """
        if self.graph is None:
            logger.error("Workflow graph not built")
            return {
                "status": "error",
                "message": "Workflow graph not built"
            }
        
        try:
            # Create initial state
            state = WorkflowState()
            
            # Set project description if provided
            if "project_description" in input_data:
                state.project_description = input_data["project_description"]
            
            # Add initial message if provided
            if "message" in input_data:
                state.messages.append({
                    "sender": "human",
                    "recipient": "system",
                    "content": input_data["message"],
                    "metadata": {}
                })
            
            # Run the workflow
            result = self.graph.invoke(state)
            
            # Process the result
            if result.output:
                return result.output
            
            # Fallback output
            if result.workflow_status == "completed":
                return {
                    "status": "success",
                    "message": "Workflow completed successfully",
                    "messages": result.messages
                }
            elif result.workflow_status == "failed":
                return {
                    "status": "error",
                    "message": "Workflow failed",
                    "errors": result.errors,
                    "messages": result.messages
                }
            else:
                return {
                    "status": "unknown",
                    "message": f"Workflow ended with status: {result.workflow_status}",
                    "messages": result.messages
                }
            
        except Exception as e:
            logger.error(f"Error running workflow: {str(e)}")
            return {
                "status": "error",
                "message": f"Error running workflow: {str(e)}"
            }
    
    def get_graph_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the workflow graph.
        
        Returns:
            Graph schema
        """
        if self.graph is None:
            return {
                "status": "error",
                "message": "Workflow graph not built"
            }
        
        try:
            return self.graph.get_graph().get_schema()
        except Exception as e:
            logger.error(f"Error getting graph schema: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting graph schema: {str(e)}"
            }


class SoftwareDevelopmentWorkflow(DynamicWorkflow):
    """
    Specialized dynamic workflow for software development.
    
    This class provides a pre-configured workflow for software development tasks,
    with appropriate agents and tools.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the software development workflow."""
        if "name" not in config:
            config["name"] = "SoftwareDevelopmentWorkflow"
        if "description" not in config:
            config["description"] = "Dynamic workflow for software development tasks"
            
        super().__init__(config) 