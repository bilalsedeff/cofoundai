"""
CoFound.ai Supervisor Implementation

This module implements a LangGraph-based supervisor orchestration pattern
for multi-agent workflow management.
"""

from typing import Dict, List, Any, TypedDict, Annotated, Callable, Optional, cast, Literal
import os
import uuid
from datetime import datetime

from langchain_core.messages import (
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage,
    ToolMessage
)
from langchain_core.tools import BaseTool, tool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from langgraph.graph import (
    END, StateGraph, MessagesState, 
    add_messages
)
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent

from cofoundai.communication.message import Message
from cofoundai.memory.project_context import ProjectContext
from cofoundai.utils.logger import get_logger
from cofoundai.core.config import load_config

logger = get_logger(__name__)

class SupervisorState(TypedDict):
    """State type for the supervisor."""
    messages: Annotated[List[BaseMessage], add_messages]
    project_context: ProjectContext
    active_agent: Optional[str]


def create_handoff_tool(agent_name: str, description: str = None):
    """Create a handoff tool that transfers control to another agent."""
    
    description = description or f"Transfer to {agent_name} agent"
    name = f"transfer_to_{agent_name}"
    
    @tool(name=name, description=description)
    def handoff_to_agent(reason: str) -> str:
        """
        Transfer control to another agent.
        
        Args:
            reason: Explanation for why the transfer is needed
            
        Returns:
            Confirmation message
        """
        return f"Successfully transferred to {agent_name} with reason: {reason}"
    
    return handoff_to_agent


class SupervisorWorkflow:
    """Implements a supervisor-based workflow for managing software development agents."""
    
    def __init__(
            self, 
            project_id: str,
            llm: Optional[BaseChatModel] = None,
            config_path: Optional[str] = None,
            persist_directory: Optional[str] = None
        ):
        """
        Initialize the supervisor workflow.
        
        Args:
            project_id: ID of the project
            llm: Language model for the supervisor agent (default ChatAnthropic)
            config_path: Path to config file (default uses the one from core.config)
            persist_directory: Directory to persist project context and checkpoints
        """
        self.project_id = project_id
        
        # Default LLM if not provided
        if llm is None:
            try:
                model_name = os.environ.get("COFOUNDAI_MODEL_NAME", "claude-3-sonnet-20240229")
                self.llm = ChatAnthropic(model=model_name)
            except:
                logger.warning("ChatAnthropic not configured, falling back to ChatOpenAI")
                self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
        else:
            self.llm = llm
            
        # Load config
        self.config = load_config(config_path) if config_path else load_config()
        
        # Initialize project context
        self.project_context = ProjectContext(
            project_id=project_id,
            persist_directory=persist_directory
        )
        
        # Create checkpointer for workflow state persistence
        self.checkpointer = MemorySaver()
        
        # Build workflow components
        self.agents = self._build_agents()
        self.graph = self._build_graph()
        
        logger.info(f"Initialized supervisor workflow for project: {project_id}")
    
    def _build_agents(self) -> Dict[str, Any]:
        """Build all agent nodes for the workflow."""
        
        # Create agent instances
        planner = PlannerAgent()
        architect = ArchitectAgent()
        developer = DeveloperAgent()
        tester = TesterAgent()
        reviewer = ReviewerAgent()
        documentor = DocumentorAgent()
        
        # Create agent tools including handoff tools
        agent_tools = {
            "planner": [
                create_handoff_tool("architect", "Transfer to the architecture design agent"),
                create_handoff_tool("developer", "Transfer to the development agent"),
                create_handoff_tool("tester", "Transfer to the testing agent"),
                create_handoff_tool("reviewer", "Transfer to the code review agent"),
                create_handoff_tool("documentor", "Transfer to the documentation agent"),
                *planner.get_tools(),
            ],
            "architect": [
                create_handoff_tool("planner", "Transfer to the planning agent"),
                create_handoff_tool("developer", "Transfer to the development agent"),
                *architect.get_tools(),
            ],
            "developer": [
                create_handoff_tool("planner", "Transfer to the planning agent"),
                create_handoff_tool("architect", "Transfer to the architecture design agent"),
                create_handoff_tool("tester", "Transfer to the testing agent"),
                create_handoff_tool("reviewer", "Transfer to the code review agent"),
                *developer.get_tools(),
            ],
            "tester": [
                create_handoff_tool("developer", "Transfer to the development agent"),
                create_handoff_tool("reviewer", "Transfer to the code review agent"),
                *tester.get_tools(),
            ],
            "reviewer": [
                create_handoff_tool("developer", "Transfer to the development agent"),
                create_handoff_tool("tester", "Transfer to the testing agent"),
                create_handoff_tool("documentor", "Transfer to the documentation agent"),
                *reviewer.get_tools(),
            ],
            "documentor": [
                create_handoff_tool("planner", "Transfer to the planning agent"),
                create_handoff_tool("developer", "Transfer to the development agent"),
                create_handoff_tool("reviewer", "Transfer to the code review agent"),
                *documentor.get_tools(),
            ],
        }
        
        # Create agent system prompts
        agent_prompts = {
            "planner": (
                "You are the planning agent in a software development team. "
                "You define tasks, priorities, and coordinate work. "
                "If a request requires architecture design, transfer to the architect agent. "
                "If implementation is needed, transfer to the developer agent. "
                "Transfer to appropriate specialists when their expertise is required."
            ),
            "architect": (
                "You are the architecture agent in a software development team. "
                "You design system components, define interfaces, and make technical decisions. "
                "If a request requires planning or refinement, transfer to the planner agent. "
                "If ready for implementation, transfer to the developer agent."
            ),
            "developer": (
                "You are the developer agent in a software development team. "
                "You implement code according to requirements and architectural specifications. "
                "If you need architectural guidance, transfer to the architect agent. "
                "When code is ready for testing, transfer to the tester agent. "
                "If you need planning clarification, transfer to the planner agent."
            ),
            "tester": (
                "You are the testing agent in a software development team. "
                "You create tests and verify functionality meets requirements. "
                "If bugs are found, transfer to the developer agent. "
                "When testing is complete, transfer to the reviewer agent."
            ),
            "reviewer": (
                "You are the code review agent in a software development team. "
                "You review code for quality, best practices, and potential issues. "
                "If you find issues, transfer to the developer agent. "
                "When review is complete, transfer to the documentor agent."
            ),
            "documentor": (
                "You are the documentation agent in a software development team. "
                "You create user guides, API docs, and ensure knowledge is captured. "
                "If you need additional details, transfer to the developer agent. "
                "If more planning is needed, transfer to the planner agent."
            ),
        }
        
        # Create LangGraph agents
        agents = {}
        for name in agent_tools.keys():
            agent = create_react_agent(
                self.llm,
                agent_tools[name],
                system=agent_prompts[name],
                name=name
            )
            agents[name] = agent
        
        # Create supervisor agent
        supervisor_prompt = (
            "You are the supervisor agent that manages a team of specialized software development agents. "
            "Based on the user request and current context, you will determine which agent should handle the task. "
            "\n\n"
            "Your team consists of the following agents:\n"
            "- planner: Creates development plans, breaks down tasks, and coordinates work\n"
            "- architect: Designs system architecture, components, and interfaces\n"
            "- developer: Implements code according to plans and specifications\n"
            "- tester: Creates tests, runs test suites, and verifies functionality\n"
            "- reviewer: Reviews code quality and provides feedback\n"
            "- documentor: Creates documentation for code, APIs, and user guides\n"
            "\n\n"
            "Always choose the most appropriate agent for the current task."
        )
        
        # Create LangGraph supervisor agent
        supervisor_agent = create_react_agent(
            self.llm,
            tools=[],  # Supervisor doesn't need tools, just needs to select an agent
            system=supervisor_prompt,
            name="supervisor"
        )
        agents["supervisor"] = supervisor_agent
        
        return agents
    
    def _route_messages(self, state):
        """Route messages to the appropriate agent."""
        messages = state["messages"]
        
        # Get the last message to check for handoff
        if not messages:
            return "supervisor"  # Start with supervisor if no messages
        
        last_message = messages[-1]
        
        if state.get("active_agent"):
            # The handoff process was already started, go to the specified agent
            agent_name = state.get("active_agent")
            state["active_agent"] = None  # Reset after routing
            return agent_name
            
        if isinstance(last_message, ToolMessage):
            # Extract agent name from tool name (transfer_to_X)
            if last_message.name.startswith("transfer_to_"):
                agent_name = last_message.name.replace("transfer_to_", "")
                logger.info(f"Transferring to {agent_name} agent based on tool message")
                return agent_name
        
        # Default to supervisor for new messages or uncertain cases
        return "supervisor"
    
    def _should_end(self, state):
        """Determine if the workflow should end."""
        messages = state["messages"]
        
        # Find the last AI message
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                # If the message contains TASK COMPLETE marker, end the workflow
                if "TASK COMPLETE" in message.content:
                    logger.info("Task marked as complete, ending workflow")
                    return True
                break
                
        return False
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Define state structure
        workflow = StateGraph(SupervisorState)
        
        # Add all agent nodes to the graph
        for name, agent in self.agents.items():
            workflow.add_node(name, agent)
        
        # Set conditional routing based on message content
        workflow.add_conditional_edges(
            "supervisor",
            self._route_messages,
            {
                "planner": "planner",
                "architect": "architect",
                "developer": "developer",
                "tester": "tester",
                "reviewer": "reviewer",
                "documentor": "documentor",
            }
        )
        
        # Define edges for all agent transitions
        for agent_name in ["planner", "architect", "developer", "tester", "reviewer", "documentor"]:
            # Check if we should end or route to another agent
            workflow.add_conditional_edges(
                agent_name,
                self._should_end,
                {
                    True: END,
                    False: self._route_messages,
                }
            )
        
        # Set the entry point to the supervisor
        workflow.set_entry_point("supervisor")
        
        # Compile the graph
        graph = workflow.compile()
        
        return graph
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the workflow with user input.
        
        Args:
            user_input: User's request or message
            
        Returns:
            Final state of the workflow
        """
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
        
        # Run the workflow
        logger.info(f"Starting workflow with thread ID: {thread_id}")
        result = self.graph.invoke(
            {
                "messages": [human_message],
                "project_context": self.project_context,
                "active_agent": None
            }, 
            config=config
        )
        
        logger.info(f"Workflow completed for thread ID: {thread_id}")
        
        return result
    
    def stream(self, user_input: str):
        """
        Stream the workflow execution with user input.
        
        Args:
            user_input: User's request or message
            
        Yields:
            Intermediary states during workflow execution
        """
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
        
        # Stream the workflow execution
        logger.info(f"Starting streaming workflow with thread ID: {thread_id}")
        
        for chunk in self.graph.stream(
            {
                "messages": [human_message],
                "project_context": self.project_context,
                "active_agent": None
            }, 
            config=config
        ):
            yield chunk
            
        logger.info(f"Streaming workflow completed for thread ID: {thread_id}")
    
    def resume(self, thread_id: str, user_input: str) -> Dict[str, Any]:
        """
        Resume an interrupted workflow.
        
        Args:
            thread_id: Thread ID of the interrupted workflow
            user_input: User's response message
            
        Returns:
            Final state of the workflow
        """
        from langgraph.types import Command
        
        # Create human message
        human_message = HumanMessage(content=user_input)
        
        # Configure workflow execution
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Resume the workflow
        logger.info(f"Resuming workflow with thread ID: {thread_id}")
        result = self.graph.invoke(
            Command(resume=human_message),
            config=config
        )
        
        logger.info(f"Resumed workflow completed for thread ID: {thread_id}")
        
        return result 