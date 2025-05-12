#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai - Agent Communication Protocol (ACP) Test

This script tests agent-to-agent communication without making LLM API calls.
It verifies that all agents' process() methods are synchronized and data flow
is handled correctly within the workflow.
"""

import sys
import json
import tempfile
from pathlib import Path
import yaml
import logging
import os
import shutil

# Import CoFound.ai modules
from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent
from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.utils.logger import system_logger, get_workflow_logger
from cofoundai.tools import FileManager, VersionControl, Context7Adapter

def setup_logging():
    """Test logging configuration."""
    # Create handler to print detailed logs to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

def load_workflow_config(workflow_id):
    """
    Load workflow configuration.
    
    Args:
        workflow_id: Workflow ID'si
        
    Returns:
        Workflow configuration or None
    """
    config_path = Path("cofoundai/config/workflows.yaml")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if not config or "main" not in config or "workflows" not in config["main"]:
            print("Error: Valid workflow configuration not found!")
            return None
            
        # Find workflow by ID
        for workflow in config["main"]["workflows"]:
            if workflow.get("id") == workflow_id:
                return workflow
                
        print(f"Error: Workflow with ID '{workflow_id}' not found!")
        return None
    except Exception as e:
        print(f"Error: Failed to load configuration file: {e}")
        return None

def initialize_tools():
    """
    Initialize tools for testing.
    
    Returns:
        Dictionary with tool name -> tool object mapping
    """
    # Create temporary workspace directory
    workspace_dir = tempfile.mkdtemp(prefix="cofoundai_workspace_")
    print(f"Temporary workspace directory created: {workspace_dir}")
    
    # Araçları oluştur
    file_manager = FileManager(workspace_dir=workspace_dir)
    version_control = VersionControl(workspace_dir=workspace_dir)
    context7_adapter = Context7Adapter(cache_dir=os.path.join(workspace_dir, "context7_cache"))
    
    tools = {
        "FileManager": file_manager,
        "VersionControl": version_control,
        "Context7Adapter": context7_adapter,
        "workspace_dir": workspace_dir  # Save directory for cleanup
    }
    
    print(f"Tools initialized: {', '.join([k for k in tools.keys() if k != 'workspace_dir'])}")
    return tools

def initialize_agents(tools):
    """
    Initialize all agents for testing.
    
    Args:
        tools: Dictionary of tools to use
        
    Returns:
        Dictionary with agent name -> agent object mapping
    """
    # Basic configurations
    planner_config = {"name": "Planner", "description": "Project planning and task breakdown"}
    architect_config = {"name": "Architect", "description": "System architecture design"}
    developer_config = {"name": "Developer", "description": "Code implementation"}
    tester_config = {"name": "Tester", "description": "Code testing and quality assurance"}
    reviewer_config = {"name": "Reviewer", "description": "Code review and improvements"}
    documentor_config = {"name": "Documentor", "description": "Project documentation"}
    
    # Add tools to each agent
    for config in [planner_config, architect_config, developer_config, 
                  tester_config, reviewer_config, documentor_config]:
        config["tools"] = {
            "file_manager": tools["FileManager"],
            "version_control": tools["VersionControl"],
            "context7_adapter": tools["Context7Adapter"]
        }
    
    # Create agents
    agents = {
        "Planner": PlannerAgent(planner_config),
        "Architect": ArchitectAgent(architect_config),
        "Developer": DeveloperAgent(developer_config),
        "Tester": TesterAgent(tester_config),
        "Reviewer": ReviewerAgent(reviewer_config),
        "Documentor": DocumentorAgent(documentor_config)
    }
    
    print(f"Agents initialized: {', '.join(agents.keys())}")
    return agents

def main():
    """Main test function."""
    print("CoFound.ai Agent Communication Protocol (ACP) Test")
    print("==============================================\n")
    
    # Logging configuration
    setup_logging()
    
    # Initialize tools
    tools = initialize_tools()
    
    # Initialize agents (with tools)
    agents = initialize_agents(tools)
    
    # Test workflow ID
    workflow_id = "develop_app"
    print(f"Workflow ID: {workflow_id}\n")
    
    # Load workflow configuration
    workflow_config = load_workflow_config(workflow_id)
    if not workflow_config:
        cleanup(tools)
        return 1
        
    # Enable test mode (no LLM calls)
    workflow_config["test_mode"] = True
    
    print("Workflow information:")
    print(f"  Name: {workflow_config.get('name')}")
    print(f"  Description: {workflow_config.get('description')}")
    print(f"  Phase count: {len(workflow_config.get('phases', []))}\n")
    
    # Create LangGraph workflow
    workflow = LangGraphWorkflow(workflow_id, workflow_config, agents)
    
    # Initialize Git repository
    tools["VersionControl"].init_repository("TodoApp")
    print("Git repository initialized: TodoApp\n")
    
    # Test girdisi
    input_data = {
        "project_description": "Todo list API with FastAPI backend, SQLite database, and basic CRUD operations",
        "workflow_id": workflow_id,
        "workspace_dir": tools["workspace_dir"]  # Add workspace directory
    }
    
    print(f"Test input: {input_data['project_description']}\n")
    print("Running workflow...")
    
    try:
        # Run workflow
        result = workflow.run(input_data)
        
        # Print results
        print("\nWorkflow completed!")
        print(f"Result status: {result.get('status', 'unknown')}")
        
        # Show status of each agent
        print("\nAgent outputs:")
        for agent_name in agents.keys():
            if agent_name in result:
                status = result[agent_name].get("status", "unknown")
                message = result[agent_name].get("message", "No message")
                print(f"  {agent_name}: {status} - {message}")
        
        # List generated files
        workspace_dir = tools["workspace_dir"]
        print(f"\nGenerated files ({workspace_dir}):")
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                if not file.startswith('.git'):
                    rel_path = os.path.relpath(os.path.join(root, file), workspace_dir)
                    print(f"  {rel_path}")
    
        # Optionally show all results
        print("\nTo see detailed results, add the --verbose parameter.")
        if "--verbose" in sys.argv:
            print("\nDetailed results:")
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        print(f"Error running workflow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up
        cleanup(tools)

def cleanup(tools):
    """
    Cleanup after tests.
    
    Args:
        tools: Dictionary of tools to clean up
    """
    try:
        workspace_dir = tools.get("workspace_dir")
        if workspace_dir and os.path.exists(workspace_dir):
            print(f"\nCleaning up: {workspace_dir} being deleted...")
            shutil.rmtree(workspace_dir, ignore_errors=True)
    except Exception as e:
        print(f"Error cleaning up: {e}")

if __name__ == "__main__":
    sys.exit(main()) 