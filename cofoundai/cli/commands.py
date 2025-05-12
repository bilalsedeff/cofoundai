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
import getpass

from cofoundai.utils.logger import system_logger, workflow_logger, get_agent_logger
from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent
from cofoundai.agents.developer import DeveloperAgent
from cofoundai.agents.architect import ArchitectAgent
from cofoundai.agents.tester import TesterAgent
from cofoundai.agents.reviewer import ReviewerAgent
from cofoundai.agents.documentor import DocumentorAgent
from cofoundai.core.config_loader import config_loader


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


def setup_env_file() -> bool:
    """
    Check if .env file exists and set it up if needed.
    
    Returns:
        True if setup was successful or wasn't needed, False otherwise
    """
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"
    
    if env_path.exists():
        # .env dosyası zaten var, bir şey yapmaya gerek yok
        system_logger.info(".env file already exists, using existing configuration")
        return True
    
    # .env dosyası yoksa yeni oluşturalım
    print("\nEnvironment configuration not found. Let's set it up now.")
    
    try:
        # .env.example dosyasının içeriğini al (varsa)
        env_content = {}
        if env_example_path.exists():
            with open(env_example_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip().strip('"').strip("'")
        
        # Kullanıcıdan LLM provider bilgisini al
        print("\nWhich LLM provider would you like to use?")
        print("1. OpenAI (GPT-4, GPT-3.5-Turbo)")
        print("2. Anthropic (Claude)")
        print("3. Test mode (No real LLM calls)")
        
        provider_choice = input("Enter your choice (1-3) [3]: ").strip() or "3"
        
        if provider_choice == "1":
            provider = "openai"
            model = input("Enter the model to use [gpt-4]: ").strip() or "gpt-4"
            
            # OpenAI API key'i gizli şekilde al
            api_key = getpass.getpass("Enter your OpenAI API key: ").strip()
            if not api_key:
                print("No API key provided. Falling back to test mode.")
                provider = "test"
            
            env_content["LLM_PROVIDER"] = provider
            env_content["OPENAI_MODEL"] = model
            if api_key:
                env_content["OPENAI_API_KEY"] = api_key
                
        elif provider_choice == "2":
            provider = "anthropic"
            model = input("Enter the model to use [claude-3-sonnet-20240229]: ").strip() or "claude-3-sonnet-20240229"
            
            # Anthropic API key'i gizli şekilde al
            api_key = getpass.getpass("Enter your Anthropic API key: ").strip()
            if not api_key:
                print("No API key provided. Falling back to test mode.")
                provider = "test"
            
            env_content["LLM_PROVIDER"] = provider
            env_content["ANTHROPIC_MODEL"] = model
            if api_key:
                env_content["ANTHROPIC_API_KEY"] = api_key
        else:
            # Test modu
            provider = "test"
            env_content["LLM_PROVIDER"] = "test"
        
        # Dummy test modu için kullanıcıya sor
        if provider != "test":  # Test modu seçilmemişse
            dummy_mode = input("Enable dummy test mode by default? This will use mock responses instead of real API calls. (yes/no) [no]: ").lower().strip() or "no"
            env_content["DUMMY_TEST_MODE"] = "true" if dummy_mode.startswith("y") else "false"
        else:
            # Test provider seçilmişse dummy mode zaten aktif olmalı
            env_content["DUMMY_TEST_MODE"] = "true"
        
        # Dosyayı oluştur
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# CoFound.ai Environment Configuration\n")
            f.write("# Created by CoFound.ai CLI\n\n")
            
            for key, value in env_content.items():
                if key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
                    if value:  # API key varsa yaz
                        f.write(f"{key}={value}\n")
                else:
                    f.write(f"{key}={value}\n")
                    
        print(f"\n.env file has been created at: {env_path}")
        print("You can edit this file later to update your configuration.")
        
        # config_loader'ı yenile
        config_loader._load_env()
        
        return True
        
    except Exception as e:
        system_logger.error(f"Error setting up environment configuration: {str(e)}")
        print(f"Error setting up environment configuration: {str(e)}")
        print("You can manually create a .env file based on .env.example to set up your configuration.")
        return False


def initialize_agents(use_dummy_test: bool = False) -> Dict[str, BaseAgent]:
    """
    Initialize and configure agents.
    
    Args:
        use_dummy_test: Whether to use dummy test mode
        
    Returns:
        Dictionary containing agent names and objects
    """
    # Override use_dummy_test with env setting if it's set to true
    if config_loader.get_bool_env("DUMMY_TEST_MODE", False):
        use_dummy_test = True
    
    # Create empty configuration dictionaries for each agent
    planner_config = {"name": "Planner", "description": "Project planning and task breakdown", "use_dummy_test": use_dummy_test}
    architect_config = {"name": "Architect", "description": "System architecture design", "use_dummy_test": use_dummy_test}
    developer_config = {"name": "Developer", "description": "Code implementation", "use_dummy_test": use_dummy_test}
    tester_config = {"name": "Tester", "description": "Code testing and quality assurance", "use_dummy_test": use_dummy_test}
    reviewer_config = {"name": "Reviewer", "description": "Code review and improvements", "use_dummy_test": use_dummy_test}
    documentor_config = {"name": "Documentor", "description": "Project documentation", "use_dummy_test": use_dummy_test}
    
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
    if use_dummy_test:
        system_logger.info("Agents initialized in DUMMY TEST MODE - no real LLM calls will be made")
    return agents


def run_workflow(workflow_id: str, project_description: str, use_dummy_test: bool = False) -> Dict[str, Any]:
    """
    Run the specified workflow.
    
    Args:
        workflow_id: ID of the workflow to run
        project_description: Project description
        use_dummy_test: Whether to use dummy test mode
        
    Returns:
        Workflow results
    """
    # Override use_dummy_test with env setting if it's set to true
    if config_loader.get_bool_env("DUMMY_TEST_MODE", False):
        use_dummy_test = True
    
    # Determine default configuration file path
    config_dir = Path(__file__).parent.parent / "config"
    workflow_config_path = config_dir / "workflows.yaml"
    
    # Initialize agents
    agents = initialize_agents(use_dummy_test)
    
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
    
    # Add agents to workflow_config
    if workflow_config is None:
        workflow_config = {}
    workflow_config["agents"] = agents
    
    # Create and run the workflow
    workflow = LangGraphWorkflow(workflow_id, workflow_config)
    
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
    # Önce .env dosyasını kuralım (gerekiyorsa)
    if not setup_env_file():
        # Kurulum başarısız oldu, ancak yine de devam etmek isteyebilir
        proceed = input("Environment setup failed. Would you like to continue anyway? (yes/no) [no]: ").lower().strip() or "no"
        if not proceed.startswith("y"):
            print("Operation canceled.")
            return 1

    project_description = args.description
    workflow_id = args.workflow or "develop_app"
    
    # CLI'dan gelen dummy-test parametresi
    use_dummy_test = args.dummy_test
    
    # .env dosyasında DUMMY_TEST_MODE=true ise o da test modunu aktif edecek
    if config_loader.get_bool_env("DUMMY_TEST_MODE", False):
        use_dummy_test = True
    
    if not project_description:
        system_logger.error("Project description is required")
        print("Error: Project description is required")
        return 1
    
    print(f"Starting project: {project_description}")
    print(f"Workflow: {workflow_id}")
    
    if use_dummy_test:
        print("RUNNING IN DUMMY TEST MODE - No actual LLM API calls will be made")
        print("This is useful for testing workflow structure without API costs")
    
    try:
        # Run the workflow
        result = run_workflow(workflow_id, project_description, use_dummy_test)
        
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
    use_dummy_test = True  # Demo always uses dummy test mode
    
    print(f"Starting LangGraph demo: {workflow_id}")
    print("This demo simulates the workflow structure without making LLM calls")
    print("You can follow the workflow steps in the log files")
    
    # Example project description
    project_description = args.description or "Todo list API with FastAPI backend, SQLite database, and basic CRUD operations"
    
    try:
        # Run the workflow
        result = run_workflow(workflow_id, project_description, use_dummy_test)
        
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


def show_environment_command(args: argparse.Namespace) -> int:
    """
    Show environment and configuration details.
    
    Args:
        args: Command arguments
        
    Returns:
        Exit code (0: success, 1: error)
    """
    print("\nCoFound.ai Environment and Configuration")
    print("=======================================")
    
    # Show project root
    project_root = Path(__file__).parent.parent.parent
    print(f"Project root: {project_root}")
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if env_file.exists():
        print(f".env file: Present at {env_file}")
    else:
        print(f".env file: Not found (you can create one based on .env.example)")
    
    # Show active LLM settings
    print("\nLLM Configuration:")
    print(f"  Provider: {config_loader.get_llm_provider()}")
    print(f"  Dummy test mode: {config_loader.is_dummy_test_mode()}")
    
    # Show OpenAI status
    openai_key = config_loader.get_env("OPENAI_API_KEY", "")
    openai_model = config_loader.get_env("OPENAI_MODEL", "gpt-4")
    print("\nOpenAI:")
    if openai_key:
        print(f"  API Key: Configured (starts with {openai_key[:4]}...)")
    else:
        print("  API Key: Not configured")
    print(f"  Model: {openai_model}")
    
    # Show Anthropic status
    anthropic_key = config_loader.get_env("ANTHROPIC_API_KEY", "")
    anthropic_model = config_loader.get_env("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    print("\nAnthropic:")
    if anthropic_key:
        print(f"  API Key: Configured (starts with {anthropic_key[:4]}...)")
    else:
        print("  API Key: Not configured")
    print(f"  Model: {anthropic_model}")
    
    print("\nLog Directories:")
    for log_dir in ["logs/system", "logs/agents", "logs/workflows"]:
        log_path = project_root / log_dir
        if log_path.exists():
            print(f"  {log_dir}: Present")
        else:
            print(f"  {log_dir}: Not found")
    
    return 0 