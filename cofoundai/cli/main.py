#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command Line Interface (CLI) for CoFound.ai.

This module serves as the entry point for the CoFound.ai CLI application.
"""

import argparse
import sys
import os
from pathlib import Path

# Import command functions
from cofoundai.cli.commands import (
    start_project_command,
    demo_langgraph_command,
    list_workflows_command,
    view_logs_command
)

def main():
    """Main function to parse command-line arguments and execute the appropriate commands."""
    parser = argparse.ArgumentParser(
        description="CoFound.ai CLI - Multi-Agent AI System for Software Development"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start project command
    start_parser = subparsers.add_parser("start", help="Start a new CoFound.ai project")
    start_parser.add_argument("description", help="Description of the project")
    start_parser.add_argument("--workflow", help="Workflow to use", default="develop_app")
    start_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    
    # Demo LangGraph command
    demo_parser = subparsers.add_parser("demo", help="Run LangGraph demonstration without LLM calls")
    demo_parser.add_argument("--workflow", help="Workflow to use", default="develop_app")
    demo_parser.add_argument("--description", help="Optional project description")
    
    # List workflows command
    list_parser = subparsers.add_parser("list", help="List available workflows")
    
    # View logs command
    logs_parser = subparsers.add_parser("logs", help="View logs")
    logs_parser.add_argument("--type", choices=["system", "workflow", "agent"], default="workflow", help="Type of logs to view")
    logs_parser.add_argument("--name", help="Name of workflow or agent (optional)")
    logs_parser.add_argument("--limit", type=int, help="Number of log entries to show", default=10)
    logs_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed log information")
    
    # Hello World command for testing
    hello_parser = subparsers.add_parser("hello", help="Test command - prints Hello World")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Execute the appropriate command
    if args.command == "hello":
        print("Merhaba, CoFound.ai dünyasına hoş geldiniz!")
        print("Bu sistem çoklu ajan tabanlı yazılım geliştirme platformudur.")
        print("LangGraph ve gerekli paketler başarıyla yüklenmiş. Sistem kullanıma hazır.")
        return 0
    elif args.command == "start":
        return start_project_command(args)
    elif args.command == "demo":
        return demo_langgraph_command(args)
    elif args.command == "list":
        return list_workflows_command(args)
    elif args.command == "logs":
        return view_logs_command(args)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 