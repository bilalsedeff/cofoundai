#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai CLI Demo

This script demonstrates the CoFound.ai multi-agent orchestration system.
It sets up a software development workflow with a team of agents
and processes a user's software request.
"""

import os
import sys
import time
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent
from cofoundai.core.base_agent import BaseAgent
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.communication.message import Message
from cofoundai.utils.logger import get_logger, LogAnalyzer
from cofoundai.config import load_system_config, load_workflow_config

# Constants
DEFAULT_WORKFLOW = "develop_app"
TEST_MODE_ENV_VAR = "COFOUNDAI_TEST_MODE"
DEFAULT_PROJECT_DIR = "projects"

# Setup logging
logger = get_logger("cli_demo")


def create_project_directory(project_id: str) -> str:
    """
    Create project directory for artifacts.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        Path to project directory
    """
    project_dir = os.path.join(DEFAULT_PROJECT_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    return project_dir


def create_agents(system_config: Dict[str, Any], test_mode: bool = False) -> Dict[str, BaseAgent]:
    """
    Create and configure agents based on system configuration.
    
    Args:
        system_config: System configuration data
        test_mode: Whether to run in test mode with predefined responses
        
    Returns:
        Dictionary of agent names to agent instances
    """
    agents = {}
    agent_config = system_config.get("agents", {})
    
    # Create agent instances based on config
    if "planner" in agent_config:
        agents["Planner"] = PlannerAgent(config=agent_config["planner"], test_mode=test_mode)
        
    if "architect" in agent_config:
        agents["Architect"] = ArchitectAgent(config=agent_config["architect"], test_mode=test_mode)
        
    if "developer" in agent_config:
        agents["Developer"] = DeveloperAgent(config=agent_config["developer"], test_mode=test_mode)
        
    if "tester" in agent_config:
        agents["Tester"] = TesterAgent(config=agent_config["tester"], test_mode=test_mode)
        
    if "reviewer" in agent_config:
        agents["Reviewer"] = ReviewerAgent(config=agent_config["reviewer"], test_mode=test_mode)
        
    if "documentor" in agent_config:
        agents["Documentor"] = DocumentorAgent(config=agent_config["documentor"], test_mode=test_mode)
    
    logger.info(f"Created {len(agents)} agents: {', '.join(agents.keys())}")
    return agents


def setup_workflow(
    project_id: str,
    workflow_id: str,
    system_config: Dict[str, Any],
    test_mode: bool
) -> AgenticGraph:
    """
    Set up the workflow with agents.
    
    Args:
        project_id: Project identifier
        workflow_id: Workflow identifier
        system_config: System configuration
        test_mode: Whether to run in test mode
        
    Returns:
        Configured workflow
    """
    # Load workflow configuration
    workflow_config = load_workflow_config(workflow_id)
    if not workflow_config:
        logger.error(f"Workflow configuration not found for {workflow_id}")
        sys.exit(1)
    
    # Create agents
    agents = create_agents(system_config, test_mode)
    
    # Create project directory for persistence
    project_dir = create_project_directory(project_id)
    
    # Create and configure AgenticGraph
    graph = AgenticGraph(
        project_id=project_id,
        config=workflow_config,
        agents=agents,
        persist_directory=project_dir
    )
    
    logger.info(f"Agentic graph configured for project {project_id}")
    return graph


def format_progress_message(agent_name: str, message: str, progress: int) -> str:
    """
    Format a progress message for display.
    
    Args:
        agent_name: Name of the current agent
        message: Message to display
        progress: Progress percentage (0-100)
        
    Returns:
        Formatted progress message
    """
    progress_bar = f"[{'=' * (progress // 5)}>{' ' * (20 - (progress // 5))}]"
    return f"[{agent_name}] {progress_bar} {progress}% - {message}"


def run_cli_demo(args: argparse.Namespace) -> None:
    """
    Run the CLI demo with the provided arguments.
    
    Args:
        args: Command-line arguments
    """
    # Load system configuration
    system_config = load_system_config()
    
    # Determine test mode
    test_mode = os.environ.get(TEST_MODE_ENV_VAR, "false").lower() == "true"
    if args.test:
        test_mode = True
    
    # Log mode
    if test_mode:
        logger.info("Running in TEST MODE with simulated agent responses")
    else:
        logger.info("Running in PRODUCTION MODE with actual LLM calls")
    
    # Generate project ID
    project_id = f"proj_{int(time.time())}"
    
    # Display welcome message
    print("\n" + "=" * 80)
    print(f"{'CoFound.ai CLI Demo':^80}")
    print("=" * 80)
    print(f"{'A multi-agent software development orchestration system':^80}")
    print(f"{'':^80}")
    if test_mode:
        print(f"{'** TEST MODE ACTIVE - Using simulated responses **':^80}")
    print("=" * 80 + "\n")
    
    # Get user request
    if args.request:
        user_request = args.request
    else:
        print("Enter your software development request:")
        print("(Example: 'Build a simple calculator app with addition and subtraction')")
        user_request = input("> ")
    
    # Setup workflow
    workflow_id = args.workflow or DEFAULT_WORKFLOW
    print(f"\nInitializing {workflow_id} workflow for project {project_id}...")
    workflow = setup_workflow(project_id, workflow_id, system_config, test_mode)
    
    # Process the request
    print("\nProcessing request through agent workflow...")
    print(f"Request: {user_request}\n")
    
    if args.stream:
        # Run in streaming mode
        print("Starting workflow execution (streaming updates):\n")
        
        current_agent = None
        for state_update in workflow.stream(user_request):
            # Extract active agent if available
            if isinstance(state_update, dict):
                # If there's a new active agent, print it
                if "active_agent" in state_update and state_update["active_agent"] != current_agent:
                    current_agent = state_update["active_agent"]
                    if current_agent:
                        print(f"\n--> Transferring to {current_agent} Agent...")
                
                # If there are messages, print the last one
                if "messages" in state_update and state_update["messages"]:
                    last_message = state_update["messages"][-1]
                    if hasattr(last_message, "content"):
                        content = last_message.content
                        # Print small preview of the message
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"Message: {preview}")
        
        print("\nWorkflow execution completed.")
    else:
        # Run synchronously
        print("Starting workflow execution:\n")
        
        result = workflow.run(user_request)
        
        print("\nWorkflow completed with result:")
        
        # Extract notable results to display
        if "messages" in result:
            # Find the last AI message
            ai_messages = [msg for msg in result["messages"] if hasattr(msg, "__class__") and 
                        msg.__class__.__name__ == "AIMessage"]
            if ai_messages:
                final_message = ai_messages[-1]
                print(f"\nFinal output:\n{final_message.content}")
        
        # Show status
        status = result.get("status", "unknown")
        print(f"\nFinal status: {status}")
    
    # Show log analysis option
    print("\nWorkflow execution completed. You can review logs in the 'logs/' directory.")
    if args.logs:
        analyzer = LogAnalyzer()
        workflow_logs = analyzer.get_workflow_logs(f"agentic_graph_{project_id}")
        
        print("\nWorkflow Log Summary:")
        for log in workflow_logs:
            log_data = log.get("data", {})
            print(f"[{log.get('formatted_time')}] {log_data.get('message', '')}")
    
    # Show completion message
    print("\nThank you for using CoFound.ai CLI Demo!")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="CoFound.ai CLI Demo")
    
    parser.add_argument(
        "--request", "-r",
        type=str,
        help="Software development request to process"
    )
    
    parser.add_argument(
        "--workflow", "-w",
        type=str,
        help=f"Workflow ID to use (default: {DEFAULT_WORKFLOW})"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run in test mode with simulated responses"
    )
    
    parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="Stream workflow execution results"
    )
    
    parser.add_argument(
        "--logs", "-l",
        action="store_true",
        help="Show logs after execution"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_cli_demo(args) 