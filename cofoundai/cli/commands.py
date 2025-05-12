"""
CoFound.ai CLI commands

This module defines commands for the CoFound.ai CLI interface.
"""

import argparse
import sys
import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from cofoundai.utils.logger import system_logger, workflow_logger, get_agent_logger
from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent


def load_workflow_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to YAML file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        system_logger.info(f"Configuration file loaded: {config_path}")
        return config
    except Exception as e:
        system_logger.error(f"Error loading configuration file: {str(e)}")
        return {}


def initialize_agents() -> Dict[str, BaseAgent]:
    """
    Initialize and configure agents.
    
    Returns:
        Dictionary containing agent names and objects
    """
    # Create empty configuration dictionaries for each agent
    planner_config = {"name": "Planner", "description": "Project planning and task breakdown"}
    architect_config = {"name": "Architect", "description": "System architecture design"}
    developer_config = {"name": "Developer", "description": "Code implementation"}
    tester_config = {"name": "Tester", "description": "Code testing and quality assurance"}
    reviewer_config = {"name": "Reviewer", "description": "Code review and improvements"}
    documentor_config = {"name": "Documentor", "description": "Project documentation"}
    
    # Initialize agents with their respective configurations
    agents = {
        "Planner": PlannerAgent(planner_config),
        "Architect": ArchitectAgent(architect_config),
        "Developer": DeveloperAgent(developer_config),
        "Tester": TesterAgent(tester_config),
        "Reviewer": ReviewerAgent(reviewer_config),
        "Documentor": DocumentorAgent(documentor_config)
    }
    
    system_logger.info(f"Agents initialized: {', '.join(agents.keys())}")
    return agents


def run_workflow(workflow_id: str, project_description: str) -> Dict[str, Any]:
    """
    Run the specified workflow.
    
    Args:
        workflow_id: ID of the workflow to run
        project_description: Project description
        
    Returns:
        Workflow results
    """
    # Determine default configuration file path
    config_dir = Path(__file__).parent.parent / "config"
    workflow_config_path = config_dir / "workflows.yaml"
    
    # Initialize agents
    agents = initialize_agents()
    
    # Find the workflow with the specified ID
    config = load_workflow_config(str(workflow_config_path))
    
    if not config or "main" not in config or "workflows" not in config["main"]:
        system_logger.error("Invalid workflow configuration")
        return {"error": "Invalid workflow configuration"}
    
    # Find the workflow with the specified ID
    workflow_config = None
    for wf in config["main"]["workflows"]:
        if wf.get("id") == workflow_id:
            workflow_config = wf
            break
    
    if not workflow_config:
        system_logger.error(f"Workflow not found: {workflow_id}")
        return {"error": f"Workflow not found: {workflow_id}"}
    
    # Create and run the workflow
    workflow = LangGraphWorkflow(workflow_id, workflow_config, agents)
    
    if not workflow:
        system_logger.error(f"Could not create workflow: {workflow_id}")
        return {"error": "Failed to create workflow"}
    
    # Run the workflow
    system_logger.info(f"Starting workflow: {workflow_id}, Project: {project_description}")
    
    input_data = {
        "project_description": project_description,
        "workflow_id": workflow_id
    }
    
    result = workflow.run(input_data)
    
    return result


def start_project_command(args: argparse.Namespace) -> int:
    """
    Start a new project.
    
    Args:
        args: Command arguments
        
    Returns:
        Exit code (0: success, 1: error)
    """
    project_description = args.description
    workflow_id = args.workflow or "develop_app"
    
    if not project_description:
        system_logger.error("Project description is required")
        print("Error: Project description is required")
        return 1
    
    print(f"Starting project: {project_description}")
    print(f"Workflow: {workflow_id}")
    
    try:
        # Run the workflow
        result = run_workflow(workflow_id, project_description)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        
        print("Workflow completed.")
        
        # Display workflow results
        if args.verbose:
            print("\nWorkflow details:")
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        system_logger.error(f"Error running workflow: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


def demo_langgraph_command(args: argparse.Namespace) -> int:
    """
    Run a LangGraph demo.
    
    Args:
        args: Command arguments
        
    Returns:
        Exit code (0: success, 1: error)
    """
    workflow_id = args.workflow or "develop_app"
    
    print(f"Starting LangGraph demo: {workflow_id}")
    print("This demo simulates the workflow structure without making LLM calls")
    print("You can follow the workflow steps in the log files")
    
    # Example project description
    project_description = args.description or "Todo list API with FastAPI backend, SQLite database, and basic CRUD operations"
    
    try:
        # Run the workflow
        result = run_workflow(workflow_id, project_description)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        
        print("\nLangGraph demo workflow completed!")
        print(f"Completed phases: {', '.join(result.get('completed_phases', []))}")
        
        print("\nLog files:")
        print(f"- Workflow logs: logs/workflows/")
        print(f"- Agent logs: logs/agents/")
        print(f"- System logs: logs/system/system.log")
        
        return 0
    except Exception as e:
        system_logger.error(f"Error running demo: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


def list_workflows_command(args: argparse.Namespace) -> int:
    """
    List available workflows.
    
    Args:
        args: Command arguments
        
    Returns:
        Exit code (0: success, 1: error)
    """
    # Determine default configuration file path
    config_dir = Path(__file__).parent.parent / "config"
    workflow_config_path = config_dir / "workflows.yaml"
    
    try:
        # Load workflow configuration
        config = load_workflow_config(str(workflow_config_path))
        
        if not config or "main" not in config or "workflows" not in config["main"]:
            print("No workflows found in configuration")
            return 1
        
        workflows = config["main"]["workflows"]
        
        print(f"\nAvailable workflows ({len(workflows)}):")
        print("-------------------------------")
        
        for wf in workflows:
            wf_id = wf.get("id", "unknown")
            wf_name = wf.get("name", "Unnamed workflow")
            wf_desc = wf.get("description", "No description")
            
            print(f"ID: {wf_id}")
            print(f"Name: {wf_name}")
            print(f"Description: {wf_desc}")
            print("-------------------------------")
        
        return 0
    except Exception as e:
        system_logger.error(f"Error listing workflows: {str(e)}")
        print(f"Error: {str(e)}")
        return 1


def view_logs_command(args: argparse.Namespace) -> int:
    """
    View logs from workflows and agents.
    
    Args:
        args: Command arguments
        
    Returns:
        Exit code (0: success, 1: error)
    """
    log_type = args.type
    name = args.name
    limit = args.limit or 10
    
    from cofoundai.utils.logger import LogAnalyzer
    
    analyzer = LogAnalyzer()
    
    try:
        if log_type == "workflow":
            logs = analyzer.get_workflow_logs(name)
            type_name = f"workflow{f' {name}' if name else ''}"
        elif log_type == "agent":
            logs = analyzer.get_agent_logs(name)
            type_name = f"agent{f' {name}' if name else ''}"
        elif log_type == "system":
            logs = analyzer.get_system_logs()
            type_name = "system"
        else:
            print(f"Unknown log type: {log_type}")
            return 1
        
        if not logs:
            print(f"No {type_name} logs found")
            return 0
        
        print(f"\nLast {min(limit, len(logs))} {type_name} logs:")
        print("-------------------------------")
        
        # Display most recent logs first
        for log in logs[-limit:]:
            if isinstance(log, dict):
                # Format JSON logs
                timestamp = log.get("timestamp", "")
                level = log.get("level", "INFO")
                message = log.get("message", "")
                
                print(f"[{timestamp}] {level}: {message}")
                
                # Show details if verbose mode
                if args.verbose:
                    for key, value in log.items():
                        if key not in ["timestamp", "level", "message"]:
                            print(f"  {key}: {value}")
                
                print("-------------------------------")
            else:
                # Plain text logs
                print(log)
                print("-------------------------------")
        
        return 0
    except Exception as e:
        system_logger.error(f"Error viewing logs: {str(e)}")
        print(f"Error: {str(e)}")
        return 1 