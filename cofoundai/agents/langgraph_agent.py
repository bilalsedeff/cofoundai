"""
CoFound.ai LangGraph Agent

This module defines the LangGraph-compatible agent implementation.
It extends the base agent concept with LangGraph-specific functionality.
"""

from typing import Dict, Any, List, Optional, Callable, Union, Literal, Type
import logging
from abc import abstractmethod

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate

from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command as LGCommand

from cofoundai.core.base_agent import BaseAgent
from cofoundai.communication.message import Message, MessageContent
from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
from cofoundai.core.llm_interface import BaseLLM, LLMFactory


# Set up logging
logger = logging.getLogger(__name__)


class LangGraphAgent(BaseAgent):
    """
    Agent implementation that wraps LangGraph functionality.

    This class bridges the CoFound.ai BaseAgent API with LangGraph's agent implementation.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LangGraph agent.

        Args:
            config: Configuration dictionary containing agent settings
        """
        super().__init__(config)

        # Agent configuration
        self.name = config.get("name", "LangGraphAgent")
        self.description = config.get("description", "LangGraph-powered agent")
        self.system_prompt = config.get("system_prompt", f"You are {self.name}, {self.description}")
        self.tools = []

        # Initialize LLM
        self._initialize_llm(config)

        # Create LangGraph agent
        self._initialize_agent()

    def _initialize_llm(self, config: Dict[str, Any]) -> None:
        """
        Initialize the language model for this agent.

        Args:
            config: Agent configuration
        """
        if "llm" in config:
            # LLM already provided
            self.llm = config["llm"]
        else:
            # Create LLM based on configuration
            provider = config.get("llm_provider", "test")
            model_name = config.get("model_name")
            llm_config = config.get("llm_config", {})

            # Create LLM instance
            try:
                self.llm = LLMFactory.create_llm(
                    provider=provider,
                    model_name=model_name,
                    config=llm_config
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {str(e)}")
                # Fallback to test LLM
                self.llm = LLMFactory.create_llm("test")

    def _initialize_agent(self) -> None:
        """Initialize the LangGraph agent."""
        # This will be implemented after tools are added
        self.langgraph_agent = None

    def add_tool(self, tool: Union[BaseTool, Callable]) -> None:
        """
        Add a tool to the agent.

        Args:
            tool: Tool to add
        """
        self.tools.append(tool)

        # Re-initialize the agent with updated tools
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the LangGraph agent with current configuration."""
        # Convert our LLM to LangChain LLM if needed
        langchain_llm = self._get_langchain_llm()

        try:
            # Create a ReAct agent
            if langchain_llm and self.tools:
                # Create system message from system_prompt
                from langchain_core.messages import SystemMessage
                messages = [SystemMessage(content=self.system_prompt)] if self.system_prompt else []

                self.langgraph_agent = create_react_agent(
                    langchain_llm,
                    self.tools,
                    messages_modifier=messages
                )
            else:
                self.langgraph_agent = None
                logger.warning(f"Could not create LangGraph agent for {self.name}: missing LLM or tools")
            logger.info(f"Initialized LangGraph agent: {self.name}")
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph agent: {str(e)}")
            self.langgraph_agent = None

    def _get_langchain_llm(self) -> BaseChatModel:
        """
        Convert our LLM to a LangChain LLM.

        Returns:
            LangChain-compatible LLM
        """
        # If it's already a LangChain LLM, return it
        if isinstance(self.llm, BaseChatModel):
            return self.llm

        # Create a ChatAnthropic or ChatOpenAI instance based on the provider
        provider = self.config.get("llm_provider", "").lower()

        try:
            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=self.llm.model_name,
                    anthropic_api_key=self.llm.api_key,
                    temperature=self.llm.config.get("temperature", 0.7)
                )
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=self.llm.model_name,
                    openai_api_key=self.llm.api_key,
                    temperature=self.llm.config.get("temperature", 0.7)
                )
            else:
                # Default dummy LLM for testing
                class DummyLLM(BaseChatModel):
                    @property
                    def _llm_type(self) -> str:
                        """Return type of llm."""
                        return "dummy"

                    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                        return AIMessage(content="This is a dummy response for testing.")

                    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
                        return AIMessage(content="This is a dummy response for testing.")

                return DummyLLM()
        except ImportError as e:
            logger.error(f"Failed to import necessary LangChain package: {str(e)}")
            # Return a dummy LLM as fallback
            class DummyLLM(BaseChatModel):
                @property
                def _llm_type(self) -> str:
                    """Return type of llm."""
                    return "dummy"

                def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                    return AIMessage(content="This is a dummy response for testing.")

                async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
                    return AIMessage(content="This is a dummy response for testing.")

            return DummyLLM()

    def _convert_to_langchain_message(self, message: Message) -> BaseMessage:
        """
        Convert a CoFound.ai Message to a LangChain BaseMessage.

        Args:
            message: CoFound.ai message

        Returns:
            LangChain message
        """
        content = message.content.text if hasattr(message.content, "text") else str(message.content)

        if message.sender == "system":
            return SystemMessage(content=content)
        elif message.sender == "human" or message.sender == "user":
            return HumanMessage(content=content)
        else:
            return AIMessage(content=content, name=message.sender)

    def _convert_from_langchain_message(self, message: BaseMessage) -> Message:
        """
        Convert a LangChain BaseMessage to a CoFound.ai Message.

        Args:
            message: LangChain message

        Returns:
            CoFound.ai message
        """
        if isinstance(message, SystemMessage):
            sender = "system"
            recipient = self.name
        elif isinstance(message, HumanMessage):
            sender = "human"
            recipient = self.name
        else:
            sender = message.name if hasattr(message, "name") else self.name
            recipient = "human"

        return Message(
            sender=sender,
            recipient=recipient,
            content=message.content,
            metadata=message.additional_kwargs if hasattr(message, "additional_kwargs") else {}
        )

    def _convert_command_to_langgraph(self, command: Command) -> LGCommand:
        """
        Convert a CoFound.ai Command to a LangGraph Command.

        Args:
            command: CoFound.ai Command

        Returns:
            LangGraph Command
        """
        # Import LangGraph Command class
        try:
            from langgraph.types import Command as LGCommand
        except ImportError:
            logger.error("LangGraph not installed properly")
            raise

        # Build LangGraph Command
        kwargs = {}

        # Set goto if present
        if command.goto is not None:
            kwargs["goto"] = command.goto

        # Set graph target
        if command.target == CommandTarget.PARENT:
            kwargs["graph"] = LGCommand.PARENT
        elif command.target == CommandTarget.CHILD:
            kwargs["graph"] = "child"  # This might need adjustment based on child graph name

        # Set state updates
        if command.update:
            kwargs["update"] = command.update

        return LGCommand(**kwargs)

    def process_message(self, message: Message) -> Message:
        """
        Process an incoming message with the LangGraph agent.

        Args:
            message: Incoming message

        Returns:
            Response message
        """
        if self.langgraph_agent is None:
            logger.warning(f"LangGraph agent {self.name} not initialized, using BaseAgent implementation")
            return super().process_message(message)

        try:
            # Convert to LangChain format
            lc_message = self._convert_to_langchain_message(message)

            # Prepare state for LangGraph agent
            state = {"messages": [lc_message]}

            # Invoke the agent
            result = self.langgraph_agent.invoke(state)

            # Get the last message from the result
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                response = self._convert_from_langchain_message(last_message)

                # Check if there's a handoff command
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        if tool_call["name"].startswith("transfer_to_"):
                            # This is a handoff tool call
                            agent_name = tool_call["name"].replace("transfer_to_", "")
                            reason = tool_call["args"].get("reason", "")

                            # Create a command for handoff
                            command = Command.handoff(
                                to_agent=agent_name,
                                reason=reason
                            )

                            # Add command to response metadata
                            response.metadata["command"] = command.to_dict()

                return response

            # Fallback response if no message is found
            return Message(
                sender=self.name,
                recipient=message.sender,
                content="Processed message but no response was generated",
                metadata={"error": "No response from LangGraph agent"}
            )

        except Exception as e:
            logger.error(f"Error processing message with LangGraph agent: {str(e)}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=f"Error processing message: {str(e)}",
                metadata={"error": str(e)}
            )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data with the LangGraph agent.

        Args:
            input_data: Input data for processing

        Returns:
            Output data with processing results
        """
        # Extract message content if present
        content = input_data.get("content", "")

        # Create a message for processing
        message = Message(
            sender="human",
            recipient=self.name,
            content=content,
            metadata=input_data
        )

        # Process the message
        response = self.process_message(message)

        # Convert response to output format
        output_data = {
            "status": "success",
            "message": response.content.text if hasattr(response.content, "text") else str(response.content),
            **response.metadata
        }

        return output_data

    def get_tools(self) -> List[Any]:
        """
        Get the agent's tools.

        Returns:
            List of tools
        """
        return self.tools

    def set_system_prompt(self, prompt: str) -> None:
        """
        Set the agent's system prompt.

        Args:
            prompt: New system prompt
        """
        self.system_prompt = prompt

        # Re-initialize agent
        self._initialize_agent()


class PlannerLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for planning tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the planner agent."""
        if "name" not in config:
            config["name"] = "Planner"
        if "description" not in config:
            config["description"] = "Planning agent that breaks down user requirements into tasks and coordinates workflows"
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are a planning agent that specializes in breaking down complex requirements into manageable tasks. "
                "You analyze requirements, create detailed plans, and coordinate workflows. "
                "When appropriate, you delegate to specialist agents via the transfer tools."
            )

        super().__init__(config)


class ArchitectLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for architecture design tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the architect agent."""
        if "name" not in config:
            config["name"] = "Architect"
        if "description" not in config:
            config["description"] = "Architecture design agent that creates system designs and technical specifications"
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are an architecture agent that specializes in system design. "
                "You create high-level designs, define components and interfaces, and make key technical decisions. "
                "When appropriate, you delegate to other specialists via the transfer tools."
            )

        super().__init__(config)


class DeveloperLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for development tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the developer agent."""
        if "name" not in config:
            config["name"] = "Developer"
        if "description" not in config:
            config["description"] = "Development agent that writes code based on specifications"
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are a developer agent that specializes in writing clean, maintainable code. "
                "You implement features according to specifications, fix bugs, and improve code quality. "
                "When appropriate, you delegate to other specialists via the transfer tools."
            )

        super().__init__(config)


class TesterLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for testing tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the tester agent."""
        if "name" not in config:
            config["name"] = "Tester"
        if "description" not in config:
            config["description"] = "Testing agent that creates and runs tests to verify functionality"
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are a testing agent that specializes in quality assurance. "
                "You create test plans, write test cases, and verify that code works as expected. "
                "When appropriate, you delegate to other specialists via the transfer tools."
            )

        super().__init__(config)


class ReviewerLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for code review tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the reviewer agent."""
        if "name" not in config:
            config["name"] = "Reviewer"
        if "description" not in config:
            config["description"] = "Code review agent that evaluates code quality and suggests improvements"
```python
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are a code review agent that specializes in evaluating code quality. "
                "You review code for bugs, maintainability issues, and areas for improvement. "
                "When appropriate, you delegate to other specialists via the transfer tools."
            )

        super().__init__(config)


class DocumentorLangGraphAgent(LangGraphAgent):
    """LangGraph agent specialized for documentation tasks."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the documentor agent."""
        if "name" not in config:
            config["name"] = "Documentor"
        if "description" not in config:
            config["description"] = "Documentation agent that creates user guides and technical documentation"
        if "system_prompt" not in config:
            config["system_prompt"] = (
                "You are a documentation agent that specializes in creating clear and helpful documentation. "
                "You create user guides, API documentation, and technical reference materials. "
                "When appropriate, you delegate to other specialists via the transfer tools."
            )

        super().__init__(config)