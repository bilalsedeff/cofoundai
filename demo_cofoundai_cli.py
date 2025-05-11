#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoFound.ai CLI Demo

This script demonstrates the CoFound.ai architecture with a focus on showing
the agent hierarchy and workflow structure without actual LLM integration.
It uses simulated agent responses to show how the system would work.
"""

import os
import sys
import uuid
import json
import tempfile
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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


def setup_colored_logging():
    """Set up colored console output for better visualization"""
    import colorama
    colorama.init()
    
    # Add a console handler with better formatting
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)


def print_colored(text, color=None, bold=False):
    """Print colored text in the terminal"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
    }
    
    bold_code = '\033[1m' if bold else ''
    color_code = colors.get(color, '')
    reset_code = '\033[0m'
    
    print(f"{bold_code}{color_code}{text}{reset_code}")


def display_workflow_header():
    """Display an attractive header for the demo"""
    print("\n")
    print_colored("=" * 80, 'blue', bold=True)
    print_colored("                         CoFound.ai CLI Demo                         ", 'cyan', bold=True)
    print_colored("           Multi-Agent Software Development Platform with LangGraph ", 'cyan')
    print_colored("=" * 80, 'blue', bold=True)
    print("\n")


def display_agent_hierarchy():
    """Display the agent hierarchy to visualize team structure"""
    print_colored("Software Development Team Hierarchy:", 'yellow', bold=True)
    print_colored("├── 🧠 Planner (Project planning and task breakdown)", 'green')
    print_colored("├── 🏗️ Architect (System architecture design)", 'green')
    print_colored("├── 👨‍💻 Developer (Code implementation)", 'green')
    print_colored("├── 🧪 Tester (Code testing and quality assurance)", 'green')
    print_colored("├── 🔍 Reviewer (Code review and improvements)", 'green')
    print_colored("└── 📝 Documentor (Project documentation)", 'green')
    print("\n")


def run_workflow_demo(workflow_id: str, project_description: str, verbose: bool = False):
    """
    Run a demo of the workflow with the specified ID.
    
    Args:
        workflow_id: ID of the workflow to demonstrate
        project_description: Description of the project
        verbose: Enable verbose output
    """
    # Create a unique project ID and test directory
    project_id = f"demo-project-{uuid.uuid4().hex[:8]}"
    project_dir = Path(tempfile.mkdtemp(prefix="cofoundai_workflow_"))
    print_colored(f"Created project: {project_id}", 'blue')
    print_colored(f"Project directory: {project_dir}", 'blue')
    
    try:
        # Initialize the version control system for this project
        vc = VersionControl(project_id=project_id, workspace_dir=str(project_dir))
        result = vc.init_repo()
        if result["status"] == "success":
            print_colored("✅ Version control initialized", 'green')
        else:
            print_colored(f"❌ Version control initialization failed: {result.get('message')}", 'red')
            return
            
        # Initialize file manager for this project
        project_workspace = project_dir / project_id
        file_manager = FileManager(workspace_dir=str(project_workspace))
        
        # Load workflow configuration
        workflow_config = load_workflow_config(workflow_id)
        if not workflow_config:
            print_colored(f"❌ Could not load workflow configuration for {workflow_id}", 'red')
            return
            
        print_colored(f"Loaded workflow: {workflow_config.get('name', workflow_id)}", 'green')
        print_colored(f"Description: {workflow_config.get('description', 'No description')}", 'cyan')
        
        # Initialize agents with test mode enabled
        print_colored("\nInitializing software development team...", 'yellow')
        agents = {
            "planner": PlannerAgent({"name": "Planner", "description": "Project planning and task breakdown"}),
            "architect": ArchitectAgent({"name": "Architect", "description": "System architecture design"}),
            "developer": DeveloperAgent({"name": "Developer", "description": "Code implementation"}),
            "tester": TesterAgent({"name": "Tester", "description": "Code testing and quality assurance"}),
            "reviewer": ReviewerAgent({"name": "Reviewer", "description": "Code review and improvements"}),
            "documentor": DocumentorAgent({"name": "Documentor", "description": "Project documentation"})
        }
        
        # Print agent initialization
        for agent_name, agent in agents.items():
            print_colored(f"  ✓ {agent.name} agent initialized", 'green')
            
        # Inject the tools into the agents
        print_colored("\nRegistering tools with agents...", 'yellow')
        for agent_name, agent in agents.items():
            agent.register_tool("file_manager", file_manager)
            agent.register_tool("version_control", vc)
        print_colored("  ✓ File Manager registered", 'green')
        print_colored("  ✓ Version Control registered", 'green')
        
        # Initialize the workflow
        print_colored("\nInitializing LangGraph workflow...", 'yellow')
        workflow_config["test_mode"] = True  # Enable test mode
        workflow = LangGraphWorkflow(
            name=workflow_id,
            config=workflow_config,
            agents=agents
        )
        print_colored("  ✓ Workflow initialized", 'green')
        
        # Create the initial message
        initial_message = {
            "project_description": project_description,
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print_colored("\n🔄 Starting workflow execution...", 'magenta', bold=True)
        print_colored(f"User Request: {project_description}", 'cyan')
        
        # Execute the workflow in test mode
        results = workflow.run(initial_message)
        
        print_colored("\n✅ Workflow execution completed", 'magenta', bold=True)
        
        # Display workflow steps
        if "steps" in results:
            step_count = len(results["steps"])
            print_colored(f"Workflow completed with {step_count} steps", 'green')
            
            # Show workflow steps if verbose
            if verbose:
                print_colored("\nWorkflow Steps:", 'yellow')
                for i, step in enumerate(results["steps"], 1):
                    agent_name = step.get("agent", "unknown")
                    status = step.get("status", "unknown")
                    print_colored(f"  Step {i}: {agent_name} → {status}", 'cyan')
        
        # Create a snapshot of the project state
        snapshot_result = vc.create_project_snapshot("Project completed by multi-agent team")
        if snapshot_result["status"] == "success":
            print_colored(f"✅ Created project snapshot: {snapshot_result.get('snapshot_id', '')[:8]}", 'green')
        
        # Create simulated files to demonstrate outputs
        demo_files = {
            "app.py": "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nMain application file generated by CoFound.ai\n\"\"\"\n\ndef main():\n    print(\"Hello from CoFound.ai!\")\n    \nif __name__ == \"__main__\":\n    main()",
            "README.md": f"# {project_id}\n\nThis project was generated by CoFound.ai\n\n## Description\n\n{project_description}\n\n## Setup\n\n```bash\npip install -r requirements.txt\npython app.py\n```",
            "requirements.txt": "# Project dependencies\nfastapi==0.115.0\nuvicorn==0.22.0\npydantic==2.0.0\n"
        }
        
        # Write demo files
        for filename, content in demo_files.items():
            file_manager.write_file(filename, content)
            
        # Display created files
        print_colored("\nFiles created by the workflow:", 'yellow')
        for file_path in os.listdir(project_workspace):
            if file_path.startswith('.git') or file_path.startswith('.cofoundai'):
                continue
            print_colored(f"- {file_path}", 'cyan')
            
            # Show first few lines of text files
            if file_path.endswith(('.py', '.md', '.txt')):
                try:
                    content = file_manager.read_file(file_path)
                    lines = content.split('\n')
                    for i in range(min(3, len(lines))):
                        print(f"  {lines[i]}")
                    print("  ...")
                except Exception as e:
                    print(f"  Error reading file: {str(e)}")
        
        # Export workflow results for analysis
        workflow_log_path = project_workspace / "workflow_log.json"
        with open(workflow_log_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print_colored(f"\nWorkflow log saved to: {workflow_log_path}", 'green')
        
        print_colored("\nProject artifacts available at:", 'yellow')
        print_colored(f"{project_workspace}", 'green')
        
    except Exception as e:
        print_colored(f"❌ Workflow failed: {str(e)}", 'red')
        raise
    finally:
        print_colored("\nNote: Test project directory was not deleted for inspection.", 'yellow')
        print_colored(f"You can find it at: {project_dir}", 'yellow')


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="CoFound.ai CLI Demo - Multi-Agent Software Development Platform"
    )
    parser.add_argument(
        "--workflow", 
        default="develop_app",
        help="ID of the workflow to demonstrate (default: develop_app)"
    )
    parser.add_argument(
        "--description",
        default="Create a simple TODO list API with FastAPI, with task creation, completion, and listing functionality",
        help="Project description"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """Main function"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up colored logging
    setup_colored_logging()
    
    # Display header and agent hierarchy
    display_workflow_header()
    display_agent_hierarchy()
    
    # Run the workflow demo
    run_workflow_demo(
        workflow_id=args.workflow,
        project_description=args.description,
        verbose=args.verbose
    )
    
    # Update the changelog
    try:
        changelog_path = Path("HIGHLEVEL-CHANGELOG.txt")
        if changelog_path.exists():
            with open(changelog_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                timestamp = datetime.now().strftime("%Y-%m-%d")
                new_entry = f"2025-05-11: Eklendi: demo_cofoundai_cli.py - CoFound.ai CLI demo without LLM integration\n"
                if new_entry not in content:
                    f.write(content.replace("# CoFound.ai Project Changelog\n\n", f"# CoFound.ai Project Changelog\n\n{new_entry}"))
            print_colored("\nChangelog updated", 'green')
    except Exception as e:
        print_colored(f"Failed to update changelog: {str(e)}", 'red')
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 