"""
CoFound.ai Orchestration Engine

This module defines the orchestration engine that coordinates interactions between agents.
The orchestration engine is responsible for task distribution, agent coordination,
and workflow management.
"""

from typing import Dict, List, Any, Optional, Type, Callable
from cofoundai.communication.message import Message
from cofoundai.core.base_agent import BaseAgent
import logging
import threading
import time


class Orchestrator:
    """
    Class that coordinates multiple AI agents and manages workflow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the orchestration engine.
        
        Args:
            config: Dictionary containing the orchestrator's configuration settings
        """
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}  # Access agents by name
        self.workflows: Dict[str, Dict[str, Any]] = {}  # Named workflows
        self.message_queue: List[Message] = []  # Queue of messages to process
        self.message_history: List[Dict[str, Any]] = []  # History of all messages
        self.running = False
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """
        Set up a logger for the orchestrator.
        
        Returns:
            Configured logger object
        """
        logger = logging.getLogger("orchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: Agent object to register
        """
        self.agents[agent.name] = agent
        self.logger.info(f"Agent registered: {agent.name}")
        
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the orchestrator.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if successful, False if agent not found
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"Agent unregistered: {agent_name}")
            return True
        
        self.logger.warning(f"Agent not found: {agent_name}")
        return False
        
    def register_workflow(self, name: str, workflow: Dict[str, Any]) -> None:
        """
        Register a workflow with the orchestrator.
        
        Args:
            name: Name of the workflow
            workflow: Dictionary containing workflow definition
        """
        self.workflows[name] = workflow
        self.logger.info(f"Workflow registered: {name}")
        
    def send_message(self, message: Message) -> None:
        """
        Add a message to the queue for processing.
        
        Args:
            message: Message object to send
        """
        self.message_queue.append(message)
        self._add_to_history(message)
        self.logger.debug(f"Message added to queue: {message}")
        
    def _add_to_history(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the history record.
        
        Args:
            message: Message to record
        """
        if isinstance(message, Message):
            message_dict = message.to_dict()
        else:
            message_dict = message
            
        self.message_history.append(message_dict)
        
    def start(self) -> None:
        """
        Start the orchestration engine and message processing loop.
        """
        if self.running:
            self.logger.warning("Orchestrator is already running")
            return
            
        self.running = True
        self.logger.info("Orchestrator started")
        
        # Start message processing loop in a separate thread
        threading.Thread(target=self._message_processing_loop, daemon=True).start()
        
    def stop(self) -> None:
        """
        Stop the orchestration engine.
        """
        self.running = False
        self.logger.info("Orchestrator stopped")
        
    def _message_processing_loop(self) -> None:
        """
        Continuously process messages from the queue.
        """
        while self.running:
            if self.message_queue:
                message = self.message_queue.pop(0)
                self._process_message(message)
            else:
                time.sleep(0.1)  # Short sleep to reduce CPU usage
                
    def _process_message(self, message: Message) -> None:
        """
        Process a message and route it to the appropriate recipient.
        
        Args:
            message: Message object to process
        """
        recipient = message.recipient
        
        # Route message to appropriate agent
        if recipient in self.agents:
            self.logger.debug(f"Routing message to agent: {recipient}")
            try:
                response = self.agents[recipient].receive_message(message)
                if response:
                    self.send_message(response)
            except Exception as e:
                self.logger.error(f"Message processing error: {str(e)}")
        elif recipient == "Orchestrator":
            self._handle_orchestrator_message(message)
        else:
            self.logger.warning(f"Recipient not found: {recipient}")
            
    def _handle_orchestrator_message(self, message: Message) -> None:
        """
        Process messages directed to the orchestrator.
        
        Args:
            message: Message object to process
        """
        content = message.content.lower()
        
        if "start" in content or "run" in content:
            workflow_name = message.metadata.get("workflow")
            if workflow_name and workflow_name in self.workflows:
                self._run_workflow(workflow_name, message.metadata.get("input", {}))
                
                response = Message(
                    sender="Orchestrator",
                    recipient=message.sender,
                    content=f"Workflow '{workflow_name}' started",
                    metadata={"workflow": workflow_name, "status": "started"}
                )
                self.send_message(response)
            else:
                response = Message(
                    sender="Orchestrator",
                    recipient=message.sender,
                    content=f"Workflow not found: {workflow_name}",
                    metadata={"error": "workflow_not_found"}
                )
                self.send_message(response)
        elif "status" in content:
            # Report status of all agents
            statuses = {name: agent.get_status() for name, agent in self.agents.items()}
            
            response = Message(
                sender="Orchestrator",
                recipient=message.sender,
                content="System status",
                metadata={"agent_statuses": statuses}
            )
            self.send_message(response)
        else:
            # Handle other orchestration commands
            response = Message(
                sender="Orchestrator",
                recipient=message.sender,
                content="Unrecognized orchestration command",
                metadata={"original_message": message.content}
            )
            self.send_message(response)
            
    def _run_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> None:
        """
        Run the specified workflow.
        
        Args:
            workflow_name: Name of the workflow to run
            input_data: Input data for the workflow
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            self.logger.error(f"Workflow not found: {workflow_name}")
            return
            
        # Create initial message to start workflow
        initiator = workflow.get("initiator", "Planner")
        initial_message = Message(
            sender="Orchestrator",
            recipient=initiator,
            content=workflow.get("initial_prompt", "Start workflow"),
            metadata={"workflow": workflow_name, "input": input_data}
        )
        
        self.send_message(initial_message)
        self.logger.info(f"Workflow '{workflow_name}' started")
        
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent object or None if not found
        """
        return self.agents.get(agent_name)
        
    def get_agent_names(self) -> List[str]:
        """
        Get the names of all registered agents.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())
        
    def get_workflow_names(self) -> List[str]:
        """
        Get the names of all registered workflows.
        
        Returns:
            List of workflow names
        """
        return list(self.workflows.keys())
        
    def get_message_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the message history.
        
        Args:
            limit: Maximum number of messages to return (None for all)
            
        Returns:
            Message history
        """
        if limit is not None:
            return self.message_history[-limit:]
        return self.message_history
        
    def clear_message_history(self) -> None:
        """
        Clear the message history.
        """
        self.message_history = []
        self.logger.info("Message history cleared") 