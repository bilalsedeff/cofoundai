"""
CoFound.ai Logging System

This module defines customized logging tools for CoFound.ai.
Used to track workflow stages, agent activities, and system status.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import json
import time
import threading
import sys
import codecs
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Constants for log directories
DEFAULT_LOG_DIR = "logs"
WORKFLOW_LOG_DIR = os.path.join(DEFAULT_LOG_DIR, "workflows")
AGENT_LOG_DIR = os.path.join(DEFAULT_LOG_DIR, "agents")
SYSTEM_LOG_DIR = os.path.join(DEFAULT_LOG_DIR, "system")

# Log file size and rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def setup_log_directory(log_dir: str) -> None:
    """
    Create log directory.
    
    Args:
        log_dir: Log directory to create
    """
    os.makedirs(log_dir, exist_ok=True)


class Utf8ConsoleHandler(logging.StreamHandler):
    """
    Custom StreamHandler with UTF-8 encoding for Windows systems.
    Allows proper handling of non-ASCII characters in logs.
    """
    
    def __init__(self, stream=None):
        # Use stderr as default stream but try to set its encoding to UTF-8
        if stream is None:
            stream = sys.stderr
        
        # Try to force UTF-8 encoding on Windows
        if hasattr(stream, 'buffer'):
            stream = codecs.getwriter('utf-8')(stream.buffer, 'replace')
        
        super().__init__(stream)


def get_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Create a named logger.
    
    Args:
        name: Logger name
        log_file: Log file path (if None, logs only to console)
        level: Log level
        
    Returns:
        Configured logger object
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # If logger already has handlers, reconfigure
    if logger.handlers:
        return logger
    
    # Configure log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler with UTF-8 encoding
    console_handler = Utf8ConsoleHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler (if log_file is specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            setup_log_directory(log_dir)
        
        # Add rotating file handler with UTF-8 encoding
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class JSONLogger:
    """
    Maintains structured log records in JSON format.
    Configured for workflow and agent interaction logging.
    """
    
    def __init__(self, name: str, log_dir: str, console_output: bool = True):
        """
        Initialize JSON logger.
        
        Args:
            name: Logger name
            log_dir: Log directory
            console_output: Whether to output logs to console
        """
        self.name = name
        self.log_dir = log_dir
        
        # Create log directory
        setup_log_directory(log_dir)
        
        # Create log file path
        self.log_file = os.path.join(log_dir, f"{name.lower().replace(' ', '_')}.json")
        
        # Configure standard logger
        self.logger = logging.getLogger(f"json_logger_{name}")
        self.logger.setLevel(logging.INFO)
        
        # Clear handlers if they exist
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Configure log format
        formatter = logging.Formatter('%(message)s')
        
        # Add file handler with UTF-8 encoding
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Add console handler if requested (with UTF-8 encoding)
        if console_output:
            console_handler = Utf8ConsoleHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def log(self, data: Dict[str, Any], level: str = "INFO") -> None:
        """
        Create log record in JSON format.
        
        Args:
            data: Log data
            level: Log level
        """
        with self.lock:
            # Create basic log structure
            log_entry = {
                "timestamp": time.time(),
                "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "logger": self.name,
                "level": level,
                "data": data
            }
            
            # Write log in JSON format
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def info(self, message: str, **kwargs) -> None:
        """
        Write log at INFO level.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        data = {"message": message, **kwargs}
        self.log(data, "INFO")
    
    def warning(self, message: str, **kwargs) -> None:
        """
        Write log at WARNING level.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        data = {"message": message, **kwargs}
        self.log(data, "WARNING")
    
    def error(self, message: str, **kwargs) -> None:
        """
        Write log at ERROR level.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        data = {"message": message, **kwargs}
        self.log(data, "ERROR")
    
    def debug(self, message: str, **kwargs) -> None:
        """
        Write log at DEBUG level.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        data = {"message": message, **kwargs}
        self.log(data, "DEBUG")


# Pre-configured loggers
system_logger = get_logger("system", os.path.join(SYSTEM_LOG_DIR, "system.log"))
workflow_logger = JSONLogger("workflow", WORKFLOW_LOG_DIR)


def get_workflow_logger(workflow_name: str) -> Union[logging.Logger, JSONLogger]:
    """
    Get a logger for a specific workflow.
    
    Args:
        workflow_name: Name of the workflow
        
    Returns:
        Logger configured for the workflow
    """
    # For structured logging, return a JSON logger
    workflow_log_dir = os.path.join(WORKFLOW_LOG_DIR, workflow_name.lower().replace('.', '_'))
    return JSONLogger(workflow_name, workflow_log_dir)


def get_agent_logger(agent_name: str) -> JSONLogger:
    """
    Create or get an agent-specific logger.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        JSON logger configured for the agent
    """
    agent_log_dir = os.path.join(AGENT_LOG_DIR, agent_name.lower())
    return JSONLogger(agent_name, agent_log_dir)


class LogAnalyzer:
    """
    Analyzes and retrieves log data from various log sources.
    """
    
    def __init__(self, log_dir: str = DEFAULT_LOG_DIR):
        """
        Initialize the log analyzer.
        
        Args:
            log_dir: Base log directory
        """
        self.log_dir = log_dir
    
    def get_workflow_logs(self, workflow_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get workflow logs.
        
        Args:
            workflow_name: Optional workflow name filter
            
        Returns:
            List of workflow log entries
        """
        workflow_dir = os.path.join(self.log_dir, "workflows")
        logs = []
        
        if not os.path.exists(workflow_dir):
            return logs
        
        try:
            # If specific workflow name provided, look for that log file
            if workflow_name:
                log_file = os.path.join(workflow_dir, f"{workflow_name.lower().replace(' ', '_')}.json")
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                pass
            else:
                # Otherwise get all workflow logs
                for file in os.listdir(workflow_dir):
                    if file.endswith('.json'):
                        log_file = os.path.join(workflow_dir, file)
                        with open(log_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    logs.append(json.loads(line))
                                except json.JSONDecodeError:
                                    # Skip invalid JSON lines
                                    pass
        except Exception as e:
            system_logger.error(f"Error reading workflow logs: {str(e)}")
        
        return logs
    
    def get_agent_logs(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get agent logs.
        
        Args:
            agent_name: Optional agent name filter
            
        Returns:
            List of agent log entries
        """
        agent_dir = os.path.join(self.log_dir, "agents")
        logs = []
        
        if not os.path.exists(agent_dir):
            return logs
        
        try:
            if agent_name:
                # If specific agent name, check its directory
                agent_log_dir = os.path.join(agent_dir, agent_name.lower())
                if os.path.exists(agent_log_dir):
                    for file in os.listdir(agent_log_dir):
                        if file.endswith('.json'):
                            log_file = os.path.join(agent_log_dir, file)
                            with open(log_file, 'r', encoding='utf-8') as f:
                                for line in f:
                                    try:
                                        logs.append(json.loads(line))
                                    except json.JSONDecodeError:
                                        # Skip invalid JSON lines
                                        pass
            else:
                # Otherwise check all agent directories
                for agent_dir_name in os.listdir(agent_dir):
                    agent_log_dir = os.path.join(agent_dir, agent_dir_name)
                    if os.path.isdir(agent_log_dir):
                        for file in os.listdir(agent_log_dir):
                            if file.endswith('.json'):
                                log_file = os.path.join(agent_log_dir, file)
                                with open(log_file, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        try:
                                            logs.append(json.loads(line))
                                        except json.JSONDecodeError:
                                            # Skip invalid JSON lines
                                            pass
        except Exception as e:
            system_logger.error(f"Error reading agent logs: {str(e)}")
        
        return logs
    
    def get_system_logs(self) -> List[str]:
        """
        Get system logs.
        
        Returns:
            List of system log lines
        """
        system_log_file = os.path.join(self.log_dir, "system", "system.log")
        logs = []
        
        if not os.path.exists(system_log_file):
            return logs
        
        try:
            with open(system_log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
        except Exception as e:
            # Just return empty list if we can't read the file
            pass
        
        return logs 