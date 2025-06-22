"""
CoFound.ai Agentic Graph Orchestration

This module implements a flexible, graph-based agentic workflow system using LangGraph.
It allows for dynamic routing between specialized agents, with each agent deciding 
whether to process a request or hand it off to another agent.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal, cast
import logging
import uuid
from datetime import datetime
import os

from langchain_core.messages import (
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage,
    ToolMessage
)
from langchain_core.tools import BaseTool, tool, StructuredTool
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from langgraph.graph import (
    END, StateGraph, MessagesState, 
    add_messages
)
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from cofoundai.communication.message import Message
from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
from cofoundai.agents.langgraph_agent import LangGraphAgent
from cofoundai.utils.logger import get_logger, get_workflow_logger, JSONLogger

# Set up logging
logger = get_logger(__name__)

class AgenticState(TypedDict):
    """State representation for the agentic workflow graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    project_description: str
    active_agent: Optional[str]
    previous_agent: Optional[str]
    artifacts: Dict[str, Any]
    metadata: Dict[str, Any]
    status: str

def create_handoff_tool(agent_name: str, description: str = None):
    """Create a handoff tool that transfers control to another agent."""

    description = description or f"Transfer to {agent_name} agent"
    tool_name = f"transfer_to_{agent_name}"

    def transfer_func(reason: str) -> str:
        """
        Transfer control to another agent.

        Args:
            reason: Explanation for why the transfer is needed

        Returns:
            Confirmation message
        """
        return f"Successfully transferred to {agent_name} with reason: {reason}"

    handoff_tool = StructuredTool.from_function(
        func=transfer_func,
        name=tool_name,
        description=description
    )

    return handoff_tool

class AgenticGraph:
    """
    Implements a flexible, graph-based agentic workflow system.

    This class uses LangGraph to create a graph of specialized agents that can
    dynamically route work between them based on the task at hand. Each agent can
    decide whether to process a request or hand it off to another agent.
    """

    def __init__(
            self, 
            project_id: str,
            llm: Optional[BaseChatModel] = None,
            config: Optional[Dict[str, Any]] = None,
            agents: Optional[Dict[str, LangGraphAgent]] = None,
            persist_directory: Optional[str] = None
        ):
        """
        Initialize the agentic graph.

        Args:
            project_id: ID of the project
            llm: Language model for the agents (default ChatAnthropic)
            config: Configuration dictionary
            agents: Pre-initialized agents to use
            persist_directory: Directory to persist project context and checkpoints
        """
        self.project_id = project_id
        self.config = config or {}

        # Default LLM if not provided
        if llm is None:
            try:
                # Use OpenAI GPT-4o as default
                model_name = os.environ.get("MODEL_NAME", "gpt-4o")
                provider = os.environ.get("LLM_PROVIDER", "openai")

                if provider == "openai":
                    self.llm = ChatOpenAI(model=model_name)
                    logger.info(f"Using OpenAI model: {model_name}")
                else:
                    # Fallback to Anthropic
                    self.llm = ChatAnthropic(model="claude-3-sonnet-20240229")
                    logger.info("Using Anthropic Claude as fallback")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                # Use test mode if all else fails
                from cofoundai.core.llm_interface import LLMFactory
                self.llm = LLMFactory.create_llm(use_dummy=True)
        else:
            self.llm = llm

        # Create checkpointer for workflow state persistence
        self.checkpointer = MemorySaver()

        # Initialize agents
        self.agents = agents or {}

        # Set up workflow logger
        self.workflow_logger = get_workflow_logger(f"agentic_graph_{project_id}")

        # Set up persistence directory
        self.persist_directory = persist_directory
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)

        # Build graph
        self.graph = self._build_graph()

        logger.info(f"Initialized agentic graph for project: {project_id}")
        self.workflow_logger.info("Graph initialized", project_id=project_id, agent_count=len(self.agents))

    def register_agent(self, agent: LangGraphAgent) -> None:
        """
        Register an agent with the workflow.

        Args:
            agent: Agent to register
        """
        self.agents[agent.name] = agent

        # Rebuild graph with the new agent
        self.graph = self._build_graph()

        logger.info(f"Registered agent: {agent.name}")
        self.workflow_logger.info("Agent registered", agent_name=agent.name)

    def _add_handoff_tools(self) -> None:
        """Add handoff tools to all registered agents."""
        for agent_name, agent in self.agents.items():
            # Clear existing handoff tools, only if agent has tool management methods
            # Check if the agent has tools attribute and get_tools method for compatibility
            agent_tools = getattr(agent, "tools", [])
            if hasattr(agent, "get_tools"):
                agent_tools = agent.get_tools()

            # If the agent is a LangGraphAgent and has the add_tool method
            if hasattr(agent, "add_tool"):
                # Filter out existing handoff tools
                if hasattr(agent, "tools"):
                    agent.tools = [tool for tool in agent.tools 
                                if not (hasattr(tool, "name") and 
                                        isinstance(tool.name, str) and 
                                        tool.name.startswith("transfer_to_"))]

                # Add handoff tools for all other agents
                for other_agent_name, other_agent in self.agents.items():
                    if other_agent_name != agent_name:
                        # Create handoff tool
                        handoff_tool = create_handoff_tool(
                            other_agent_name, 
                            f"Transfer to the {other_agent_name} agent when their expertise is needed"
                        )
                        agent.add_tool(handoff_tool)
            else:
                self.workflow_logger.warning(
                    "Agent does not support adding tools",
                    agent=agent_name
                )

            # Log the tools available to this agent
            if hasattr(agent, "tools"):
                tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in agent.tools]
                self.workflow_logger.debug(
                    "Agent tools configuration", 
                    agent=agent_name, 
                    tools=tool_names
                )

    def _route_messages(self, state: AgenticState) -> str:
        """Route messages to the appropriate agent."""
        messages = state["messages"]

        # Get the last message to check for handoff
        if not messages:
            # Start with planner if available, otherwise first agent
            initial_agent = None

            # Check if we have a preferred initial agent in config
            if self.config.get("initial_agent"):
                initial_agent = self.config.get("initial_agent")
                if initial_agent in self.agents:
                    self.workflow_logger.info("Starting with configured initial agent", agent=initial_agent)
                    return initial_agent

            # Otherwise use default hierarchy
            if "Planner" in self.agents:
                self.workflow_logger.info("Starting with Planner agent")
                return "Planner"
            elif self.agents:
                first_agent = next(iter(self.agents.keys()))
                self.workflow_logger.info("Starting with first available agent", agent=first_agent)
                return first_agent

            self.workflow_logger.error("No agents available, ending workflow")
            return END

        last_message = messages[-1]

        if state.get("active_agent"):
            # The handoff process was already started, go to the specified agent
            agent_name = state.get("active_agent")
            # Store the previous agent for context
            state["previous_agent"] = agent_name
            state["active_agent"] = None  # Reset after routing
            self.workflow_logger.info("Routing to active agent", agent=agent_name, previous=state.get("previous_agent"))
            return agent_name

        if isinstance(last_message, ToolMessage):
            # Extract agent name from tool name (transfer_to_X)
            if last_message.name.startswith("transfer_to_"):
                agent_name = last_message.name.replace("transfer_to_", "")
                self.workflow_logger.info(
                    "Transferring control", 
                    to_agent=agent_name, 
                    from_agent=state.get("previous_agent"),
                    reason=last_message.content
                )
                # Update state to track the active agent
                state["previous_agent"] = state.get("active_agent")
                state["active_agent"] = agent_name
                return agent_name

        # If status is "completed", end the workflow
        if state.get("status") == "completed":
            self.workflow_logger.info("Workflow completed, ending execution")
            return END

        # Default: if we can't determine where to go, check if we have an active agent
        current_agent = state.get("active_agent")
        if current_agent and current_agent in self.agents:
            self.workflow_logger.info("Continuing with current agent", agent=current_agent)
            return current_agent

        # If no active agent but we know the previous one, return to it
        if state.get("previous_agent") in self.agents:
            prev_agent = state.get("previous_agent")
            self.workflow_logger.info("Returning to previous agent", agent=prev_agent)
            return prev_agent

        # True fallback: start with planner if available, otherwise first agent
        if "Planner" in self.agents:
            self.workflow_logger.info("Fallback to Planner agent")
            return "Planner"
        elif self.agents:
            first_agent = next(iter(self.agents.keys()))
            self.workflow_logger.info("Fallback to first available agent", agent=first_agent)
            return first_agent

        # No valid next state, must end
        self.workflow_logger.error("No valid next agent, ending workflow")
        return END

    def _should_end(self, state: AgenticState) -> bool:
        """Determine if the workflow should end."""
        # Check if status is marked as completed
        if state.get("status") == "completed":
            self.workflow_logger.info("Workflow status is marked completed")
            return True

        # Look at the last message for completion signals
        messages = state["messages"]
        if not messages:
            return False

        # Find the last AI message
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                # If the message contains completion markers, end the workflow
                if "TASK COMPLETE" in message.content or "COMPLETED" in message.content:
                    self.workflow_logger.info("Task marked as complete, ending workflow")
                    return True
                break

        return False

    def _build_graph(self):
        """Build the LangGraph workflow."""
        if not self.agents:
            logger.warning("No agents registered, can't build graph")
            self.workflow_logger.warning("Cannot build graph, no agents registered")
            return None

        # Add handoff tools to all agents
        self._add_handoff_tools()

        # Define state structure
        workflow = StateGraph(AgenticState)

        # Add agent nodes to the graph
        added_agents = []
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'langgraph_agent') and agent.langgraph_agent:
                try:
                    workflow.add_node(agent_name, agent.langgraph_agent)
                    added_agents.append(agent_name)
                    self.workflow_logger.debug("Added agent to graph", agent=agent_name)
                except Exception as e:
                    self.workflow_logger.warning("Failed to add agent to graph", agent=agent_name, error=str(e))
            else:
                # Try to create a dummy implementation for testing
                try:
                    dummy_func = self._create_dummy_agent_function(agent)
                    workflow.add_node(agent_name, dummy_func)
                    added_agents.append(agent_name)
                    self.workflow_logger.debug("Added dummy agent to graph", agent=agent_name)
                except Exception as e:
                    self.workflow_logger.warning("Agent has no LangGraph implementation and couldn't create dummy", agent=agent_name)
                    self.workflow_logger.warning("Cannot add agent to graph", agent=agent_name, reason="No LangGraph implementation or dummy function")

        # Add edges between agents based on handoff tools, but only for agents that were added
        for agent_name, agent in self.agents.items():
            if agent_name not in added_agents:
                continue

            if hasattr(agent, 'tools'):
                for tool in agent.tools:
                    if hasattr(tool, 'name') and tool.name.startswith('transfer_to_'):
                        target_agent = tool.name.replace('transfer_to_', '')
                        if target_agent in self.agents and target_agent in added_agents:
                            try:
                                # Add conditional edge for handoff
                                workflow.add_conditional_edges(
                                    agent_name,
                                    self._route_messages,
                                    {target_agent: target_agent, END: END}
                                )
                                self.workflow_logger.debug("Added conditional edge", from_agent=agent_name, to_agent=target_agent)
                            except Exception as e:
                                self.workflow_logger.warning("Failed to add edge", from_agent=agent_name, to_agent=target_agent, error=str(e))

        # Set entry point - prefer Planner if available and added, otherwise use first added agent
        if "Planner" in added_agents:
            workflow.set_entry_point("Planner")
            self.workflow_logger.debug("Set entry point to Planner")
        elif added_agents:
            first_agent = added_agents[0]
            workflow.set_entry_point(first_agent)
            self.workflow_logger.debug("Set entry point to first agent", agent=first_agent)
        else:
            # Add default entry node if no agents were added
            workflow.add_node("start", lambda state: {"messages": [{"role": "assistant", "content": "No agents available"}]})
            workflow.set_entry_point("start")
            workflow.add_edge("start", END)
            self.workflow_logger.debug("Set default entry point")

        # Compile the graph
        self.workflow_logger.info("Building dynamic routing graph")
        graph = workflow.compile(checkpointer=self.checkpointer)

        self.workflow_logger.info("Graph built and compiled", agent_count=len(self.agents))

        return graph

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the workflow with user input.

        Args:
            user_input: User's request or message

        Returns:
            Final state of the workflow
        """
        if self.graph is None:
            logger.error("Agentic graph not built, no agents registered")
            self.workflow_logger.error("Cannot run workflow, graph not built")
            return {
                "status": "error",
                "message": "Agentic graph not built, no agents registered"
            }

        # Initialize LangSmith tracing
        tracer = get_tracer()
        session_id = tracer.start_workflow_session(self.project_id, user_input)

        # Create human message
        human_message = HumanMessage(content=user_input)

        # Generate a thread ID for persistence
        thread_id = f"thread_{self.project_id}_{uuid.uuid4().hex[:8]}"

        # Configure workflow execution
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Create initial state
        initial_state = {
            "messages": [human_message],
            "project_description": user_input,
            "active_agent": None,
            "previous_agent": None,
            "artifacts": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "thread_id": thread_id,
                "langsmith_session": session_id
            },
            "status": "in_progress"
        }

        # Log workflow start
        logger.info(f"Starting workflow with thread ID: {thread_id}")
        self.workflow_logger.info(
            "Workflow started", 
            thread_id=thread_id, 
            user_input=user_input[:100] + ("..." if len(user_input) > 100 else "")
        )

        # Run the workflow
        try:
            result = self.graph.invoke(initial_state, config=config)

            # Trace final result
            tracer.trace_agent_execution(
                agent_name="workflow_orchestrator",
                phase="complete",
                input_data={"user_input": user_input, "thread_id": thread_id},
                output_data={"status": result.get("status", "unknown"), "final_artifacts": result.get("artifacts", {})}
            )

            # End LangSmith session
            tracer.end_workflow_session(
                final_status=result.get("status", "unknown"),
                artifacts=result.get("artifacts", {})
            )

            # Log workflow completion
            logger.info(f"Workflow completed for thread ID: {thread_id}")
            self.workflow_logger.info(
                "Workflow completed", 
                thread_id=thread_id, 
                status=result.get("status", "unknown")
            )

            # Save workflow history to persist directory if configured
            if self.persist_directory:
                history_file = os.path.join(
                    self.persist_directory, 
                    f"workflow_{thread_id}.json"
                )
                try:
                    import json
                    with open(history_file, 'w') as f:
                        # Convert messages to serializable format
                        serializable_result = {**result}
                        if "messages" in serializable_result:
                            serializable_result["messages"] = [
                                {
                                    "type": msg.__class__.__name__,
                                    "content": msg.content,
                                    "additional_kwargs": msg.additional_kwargs
                                }
                                for msg in serializable_result["messages"]
                            ]
                        json.dump(serializable_result, f, indent=2, default=str)
                    self.workflow_logger.info("Saved workflow history", file=history_file)
                except Exception as e:
                    logger.error(f"Failed to save workflow history: {str(e)}")
                    self.workflow_logger.error("Failed to save workflow history", error=str(e))

            return result

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}")
            self.workflow_logger.error("Workflow execution failed", error=str(e), thread_id=thread_id)

            # End LangSmith session with error
            tracer.end_workflow_session("error", {})

            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "thread_id": thread_id
            }

    def stream(self, user_input: str):
        """
        Stream the workflow execution with user input.

        Args:
            user_input: User's request or message

        Yields:
            Intermediary states during workflow execution
        """
        if self.graph is None:
            logger.error("Agentic graph not built, no agents registered")
            self.workflow_logger.error("Cannot stream workflow, graph not built")
            yield {
                "status": "error",
                "message": "Agentic graph not built, no agents registered"
            }
            return

        # Create human message
        human_message = HumanMessage(content=user_input)

        # Generate a thread ID for persistence
        thread_id = f"thread_{self.project_id}_{uuid.uuid4().hex[:8]}"

        # Configure workflow execution
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Create initial state
        initial_state = {
            "messages": [human_message],
            "project_description": user_input,
            "active_agent": None,
            "previous_agent": None,
            "artifacts": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "thread_id": thread_id,
            },
            "status": "in_progress"
        }

        # Log streaming start
        logger.info(f"Starting streaming workflow with thread ID: {thread_id}")
        self.workflow_logger.info(
            "Streaming workflow started", 
            thread_id=thread_id,
            user_input=user_input[:100] + ("..." if len(user_input) > 100 else "")
        )

        try:
            # Stream the workflow execution
            for chunk in self.graph.stream(initial_state, config=config):
                # Log each step if it's a meaningful update
                if isinstance(chunk, dict) and "active_agent" in chunk and chunk["active_agent"]:
                    self.workflow_logger.debug(
                        "Stream update", 
                        thread_id=thread_id,
                        active_agent=chunk["active_agent"]
                    )
                yield chunk

            logger.info(f"Streaming workflow completed for thread ID: {thread_id}")
            self.workflow_logger.info("Streaming workflow completed", thread_id=thread_id)

        except Exception as e:
            logger.error(f"Error during streaming workflow: {str(e)}")
            self.workflow_logger.error("Streaming workflow failed", error=str(e), thread_id=thread_id)
            yield {
                "status": "error",
                "message": f"Streaming workflow failed: {str(e)}",
                "thread_id": thread_id
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
                "message": "Agentic graph not built"
            }

        try:
            return self.graph.get_graph().get_schema()
        except Exception as e:
            logger.error(f"Error getting graph schema: {str(e)}")
            self.workflow_logger.error("Failed to get graph schema", error=str(e))
            return {
                "status": "error",
                "message": f"Error getting graph schema: {str(e)}"
            }
    def _create_dummy_agent_function(self, agent):
        """Create a dummy agent function for testing purposes."""
        def dummy_agent_function(state):
            """Dummy function that simulates agent processing."""
            agent_name = agent.name if hasattr(agent, 'name') else 'UnknownAgent'
            logger.info(f"Dummy agent {agent_name} processing message")
            return state
        return dummy_agent_function