#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command Line Interface (CLI) for CoFound.ai.

This module serves as the entry point for the CoFound.ai CLI application.
"""

import argparse
import sys
import os

# Geçici olarak bağımlılıkları devre dışı bırakıyorum
# from cofoundai.cli.commands import (
#     start_workflow,
#     run_demo,
#     list_workflows,
#     view_logs
# )

def main():
    """Main function to parse command-line arguments and execute the appropriate commands."""
    parser = argparse.ArgumentParser(
        description="CoFound.ai CLI - Multi-Agent AI System for Software Development"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Temporarily disabled due to dependencies
    # start_parser = subparsers.add_parser("start", help="Start a new CoFound.ai project")
    # start_parser.add_argument("project_description", help="Description of the project")
    # start_parser.add_argument("--workflow", help="Workflow to use", default="develop_app")
    
    # demo_parser = subparsers.add_parser("demo", help="Run LangGraph demonstration")
    
    # list_parser = subparsers.add_parser("list", help="List available workflows")
    
    # logs_parser = subparsers.add_parser("logs", help="View logs")
    # logs_parser.add_argument("--type", choices=["system", "workflow"], default="workflow", help="Type of logs to view")
    
    # Hello World command for testing
    hello_parser = subparsers.add_parser("hello", help="Test command - prints Hello World")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Temporarily add hello world command
    if args.command == "hello":
        print("Merhaba, CoFound.ai dünyasına hoş geldiniz!")
        print("Bu sistem çoklu ajan tabanlı yazılım geliştirme platformudur.")
        print("Not: Gerçek işlevsellik için Python 3.9+ ve langgraph paketi gereklidir.")
        return
    
    # Temporarily disabled due to dependencies
    # if args.command == "start":
    #     start_workflow(args.project_description, args.workflow)
    # elif args.command == "demo":
    #     run_demo()
    # elif args.command == "list":
    #     list_workflows()
    # elif args.command == "logs":
    #     view_logs(args.type)

if __name__ == "__main__":
    main() 