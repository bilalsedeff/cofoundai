#!/usr/bin/env python
"""
CoFound.ai - CLI Entry Point

This module is the main entry point for the CoFound.ai CLI application.
It processes command line arguments and starts the multi-agent system.
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# Import CLI commands
from cofoundai.cli.commands import (
    start_project_command,
    list_workflows_command,
    view_logs_command,
    demo_langgraph_command
)
from cofoundai.utils.logger import system_logger, setup_log_directory


def setup_environment():
    """
    Prepare application environment variables and directories.
    """
    # Create log directories
    from cofoundai.utils.logger import DEFAULT_LOG_DIR, WORKFLOW_LOG_DIR, AGENT_LOG_DIR, SYSTEM_LOG_DIR
    
    setup_log_directory(DEFAULT_LOG_DIR)
    setup_log_directory(WORKFLOW_LOG_DIR)
    setup_log_directory(AGENT_LOG_DIR)
    setup_log_directory(SYSTEM_LOG_DIR)
    
    # Other environment variable settings can go here
    system_logger.info("Environment variables and directories prepared")


def create_parser() -> argparse.ArgumentParser:
    """
    Create command line argument parser.
    
    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(
        description="CoFound.ai - Multi-Agent Software Development System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # General arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed output"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start project command
    start_parser = subparsers.add_parser("start", help="Start a new project")
    start_parser.add_argument("description", help="Project description")
    start_parser.add_argument(
        "-w", "--workflow",
        default="develop_app",
        help="Workflow to use (default: develop_app)"
    )
    start_parser.set_defaults(func=start_project_command)
    
    # LangGraph demo command
    demo_parser = subparsers.add_parser("demo", help="Run LangGraph demo")
    demo_parser.add_argument(
        "-w", "--workflow",
        default="develop_app",
        help="Workflow to use (default: develop_app)"
    )
    demo_parser.add_argument(
        "-d", "--description",
        help="Optional project description (default will be used if not specified)"
    )
    demo_parser.set_defaults(func=demo_langgraph_command)
    
    # List workflows command
    list_parser = subparsers.add_parser("list", help="List available workflows")
    list_parser.set_defaults(func=list_workflows_command)
    
    # View logs command
    logs_parser = subparsers.add_parser("logs", help="View log files")
    logs_parser.add_argument(
        "type",
        choices=["workflow", "agent", "system"],
        help="Type of log to view"
    )
    logs_parser.add_argument(
        "-n", "--name",
        help="Specific workflow or agent name to view (all will be shown if not specified)"
    )
    logs_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Maximum number of log entries to display (default: 10)"
    )
    logs_parser.set_defaults(func=view_logs_command)
    
    return parser


def main():
    """
    Main entry point for the CLI application.
    """
    # Prepare environment variables and directories
    setup_environment()
    
    # Create argument parser
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help message
    if not args.command:
        parser.print_help()
        return 0
    
    # If verbose output requested, set log level to DEBUG
    if args.verbose:
        system_logger.setLevel(logging.DEBUG)
        system_logger.debug("Verbose logging enabled")
    
    # Execute the command
    try:
        return args.func(args)
    except Exception as e:
        system_logger.error(f"Error executing command: {str(e)}")
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 