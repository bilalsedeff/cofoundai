#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai Multi-Agent Workflow Demo

This script demonstrates the LangGraph-based multi-agent workflow using
the project-specific version control system. It simulates a software
development process without using actual LLM calls.
"""

import os
import sys
import uuid
import json
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, cast

from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.architect import ArchitectAgent  
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent
from cofoundai.communication.message import Message, MessageContent
from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.tools import FileManager, VersionControl
from cofoundai.utils.logger import get_logger, system_logger
from cofoundai.config import load_workflow_config

# Set up logging
logger = system_logger
logger.setLevel(logging.INFO)

def simulate_multi_agent_workflow():
    """
    Simulate a multi-agent workflow for software development.
    """
    print("Starting CoFound.ai Multi-Agent Workflow Demo...")
    
    # Create a unique project ID and test directory
    project_id = f"demo-project-{uuid.uuid4().hex[:8]}"
    project_dir = Path(tempfile.mkdtemp(prefix="cofoundai_workflow_"))
    print(f"Created project: {project_id} in {project_dir}")
    
    try:
        # Initialize the version control system for this project
        vc = VersionControl(project_id=project_id, workspace_dir=str(project_dir))
        result = vc.init_repo()
        if result["status"] == "success":
            print("✅ Version control initialized")
        else:
            print(f"❌ Version control initialization failed: {result.get('message')}")
            return
            
        # Initialize file manager for this project
        project_workspace = project_dir / project_id
        file_manager = FileManager(workspace_dir=str(project_workspace))
        
        # Load workflow configuration
        workflow_config = load_workflow_config("software_development")
        
        # Initialize agents with test mode enabled
        agents = {
            "planner": PlannerAgent(test_mode=True),
            "architect": ArchitectAgent(test_mode=True),
            "developer": DeveloperAgent(test_mode=True),
            "tester": TesterAgent(test_mode=True),
            "reviewer": ReviewerAgent(test_mode=True),
            "documentor": DocumentorAgent(test_mode=True)
        }
        
        # Inject the tools into the agents
        for agent_name, agent in agents.items():
            agent.register_tool("file_manager", file_manager)
            agent.register_tool("version_control", vc)
        
        # Initialize the workflow
        workflow = LangGraphWorkflow(
            name="software_development",
            config=workflow_config,
            agents=agents
        )
        
        # Create a simple application specification
        user_request = """
        Create a simple Python calculator application with the following features:
        - Addition, subtraction, multiplication, and division operations
        - Command-line interface
        - Error handling for invalid inputs
        - Basic memory function to store the last result
        """
        
        print("\n🔄 Starting workflow execution...")
        print(f"User Request: {user_request[:50]}...")
        
        # Create the initial message
        initial_message = Message(
            sender="user",
            receivers=["planner"],
            content=MessageContent(text=user_request)
        )
        
        # Execute the workflow in test mode
        results = workflow.run(initial_message, max_steps=25)
        
        print("\n✅ Workflow execution completed")
        print(f"Executed {len(results['steps'])} steps")
        
        # Create a snapshot of the project state
        snapshot_result = vc.create_project_snapshot("Project completed by multi-agent team")
        if snapshot_result["status"] == "success":
            print(f"✅ Created project snapshot: {snapshot_result.get('snapshot_id', '')[:8]}")
        
        # Display created files
        print("\nFiles created by the workflow:")
        for file_path in os.listdir(project_workspace):
            if file_path.startswith('.git') or file_path.startswith('.cofoundai'):
                continue
            print(f"- {file_path}")
            
            # Show first few lines of Python files
            if file_path.endswith('.py'):
                try:
                    content = file_manager.read_file(file_path)
                    print(f"  {content.split('\\n')[0]}")
                    print(f"  {content.split('\\n')[1] if len(content.split('\\n')) > 1 else ''}")
                    print("  ...")
                except Exception as e:
                    print(f"  Error reading file: {str(e)}")
        
        # Export workflow steps for analysis
        workflow_log_path = project_workspace / "workflow_log.json"
        with open(workflow_log_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nWorkflow log saved to: {workflow_log_path}")
        
        print("\nProject artifacts available at:", project_workspace)
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        raise
    finally:
        # Note: Not removing the project directory so user can inspect the results
        print("\nNote: Test project directory was not deleted for inspection.")
        print(f"You can find it at: {project_dir}")

if __name__ == "__main__":
    simulate_multi_agent_workflow() 