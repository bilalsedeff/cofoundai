"""
CoFound.ai Config package

This module contains components for managing system configurations and settings.
Environment variables, API keys, model selections, and
other configuration parameters are defined in this package.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# Get the package directory
_package_dir = Path(__file__).parent


def load_system_config() -> Dict[str, Any]:
    """
    Load system configuration from system_config.yaml
    
    Returns:
        Dictionary containing system configuration
    """
    config_path = _package_dir / "system_config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"System configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config or {}


def load_workflow_config(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Load workflow configuration for a specific workflow ID
    
    Args:
        workflow_id: ID of the workflow to load
        
    Returns:
        Dictionary containing workflow configuration, or None if not found
    """
    workflows_path = _package_dir / "workflows.yaml"
    
    if not workflows_path.exists():
        raise FileNotFoundError(f"Workflows configuration file not found: {workflows_path}")
    
    with open(workflows_path, 'r', encoding='utf-8') as f:
        workflows = yaml.safe_load(f)
    
    if not workflows or "workflows" not in workflows:
        return None
    
    # Find the workflow with the specified ID
    for workflow in workflows["workflows"]:
        if workflow.get("id") == workflow_id:
            return workflow
    
    return None 