"""
CoFound.ai Project Context Memory Implementation

This module implements project context storage, managing information about
the project structure, requirements, and other contextual information needed
by agents to perform their tasks effectively.
"""

from typing import Dict, List, Optional, Any, Union
import json
import os
from pathlib import Path
import pickle
from datetime import datetime

from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class ProjectContext:
    """
    Maintains persistent context about the software project being developed.
    
    This class stores requirements, architecture decisions, file structure,
    and other contextual information needed by agents to understand the project.
    """
    
    def __init__(self, project_id: str, persist_directory: Optional[str] = None):
        """
        Initialize project context memory.
        
        Args:
            project_id: Unique identifier for the project
            persist_directory: Directory to persist context (defaults to ./data/projects/{project_id})
        """
        self.project_id = project_id
        self.persist_directory = persist_directory or os.path.join("data", "projects", project_id)
        self.context_file = os.path.join(self.persist_directory, "context.json")
        self.checkpoint_directory = os.path.join(self.persist_directory, "checkpoints")
        
        # Create directories if they don't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize context data
        self.context = self._load_context()
        
        logger.info(f"Initialized project context for project: {project_id}")
    
    def _load_context(self) -> Dict[str, Any]:
        """Load context from disk or initialize if not exists."""
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, 'r') as f:
                    context = json.load(f)
                logger.info(f"Loaded project context from {self.context_file}")
                return context
            except Exception as e:
                logger.error(f"Error loading project context: {e}")
                return self._initialize_context()
        else:
            return self._initialize_context()
    
    def _initialize_context(self) -> Dict[str, Any]:
        """Initialize an empty context structure."""
        context = {
            "project_id": self.project_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "name": "",
            "description": "",
            "requirements": [],
            "architecture": {
                "components": [],
                "decisions": []
            },
            "file_structure": [],
            "dependencies": [],
            "tasks": [],
            "metadata": {}
        }
        
        # Save the initial context
        self._save_context(context)
        logger.info("Initialized new project context")
        return context
    
    def _save_context(self, context: Dict[str, Any]) -> None:
        """Save context to disk."""
        context["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(self.context_file, 'w') as f:
                json.dump(context, f, indent=2)
            logger.info(f"Saved project context to {self.context_file}")
        except Exception as e:
            logger.error(f"Error saving project context: {e}")
    
    def create_checkpoint(self, label: Optional[str] = None) -> str:
        """
        Create a checkpoint of the current context state.
        
        Args:
            label: Optional label for the checkpoint
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = datetime.now().strftime("%Y%m%d%H%M%S")
        if label:
            checkpoint_id = f"{checkpoint_id}_{label}"
        
        checkpoint_file = os.path.join(self.checkpoint_directory, f"{checkpoint_id}.pkl")
        
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(self.context, f)
            logger.info(f"Created checkpoint: {checkpoint_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}")
            return ""
    
    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore context from a checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to restore
            
        Returns:
            True if restored successfully, False otherwise
        """
        checkpoint_file = os.path.join(self.checkpoint_directory, f"{checkpoint_id}.pkl")
        
        if not os.path.exists(checkpoint_file):
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return False
        
        try:
            with open(checkpoint_file, 'rb') as f:
                self.context = pickle.load(f)
            
            # Save the restored context
            self._save_context(self.context)
            logger.info(f"Restored checkpoint: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Error restoring checkpoint: {e}")
            return False
    
    def get_checkpoint_list(self) -> List[str]:
        """
        Get a list of available checkpoint IDs.
        
        Returns:
            List of checkpoint IDs
        """
        try:
            return [file.split('.')[0] for file in os.listdir(self.checkpoint_directory) 
                   if file.endswith('.pkl')]
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return []
    
    def update(self, update_data: Dict[str, Any]) -> None:
        """
        Update the project context with new data.
        
        Args:
            update_data: Dictionary with data to update (will be merged with existing)
        """
        # Deep update/merge of dictionaries
        def deep_update(original, update):
            for key, value in update.items():
                if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                    deep_update(original[key], value)
                elif key in original and isinstance(original[key], list) and isinstance(value, list):
                    original[key].extend(value)
                else:
                    original[key] = value
        
        deep_update(self.context, update_data)
        self._save_context(self.context)
        logger.info("Updated project context")
    
    def get(self, path: Optional[str] = None) -> Any:
        """
        Get data from the project context.
        
        Args:
            path: Optional dot-separated path to specific data (e.g., 'architecture.components')
            
        Returns:
            Requested data or entire context if path is None
        """
        if path is None:
            return self.context
        
        try:
            current = self.context
            for key in path.split('.'):
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def set(self, path: str, value: Any) -> None:
        """
        Set a specific value in the project context.
        
        Args:
            path: Dot-separated path to the data (e.g., 'architecture.components')
            value: Value to set
        """
        keys = path.split('.')
        current = self.context
        
        # Navigate to the correct position
        for key in keys[:-1]:
            if key not in current:
                if key.isdigit():  # Handle list indices
                    current[int(key)] = {} if keys[-1].isdigit() else []
                else:
                    current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        self._save_context(self.context)
        logger.info(f"Set value at path: {path}")
    
    def add_requirement(self, requirement: Dict[str, Any]) -> None:
        """
        Add a project requirement.
        
        Args:
            requirement: Dictionary containing requirement details (must have 'id' and 'description')
        """
        if 'id' not in requirement or 'description' not in requirement:
            logger.error("Requirement must have 'id' and 'description'")
            return
        
        if 'created_at' not in requirement:
            requirement['created_at'] = datetime.now().isoformat()
        
        self.context['requirements'].append(requirement)
        self._save_context(self.context)
        logger.info(f"Added requirement: {requirement['id']}")
    
    def add_architectural_decision(self, decision: Dict[str, Any]) -> None:
        """
        Add an architectural decision record.
        
        Args:
            decision: Dictionary containing decision details
        """
        if 'id' not in decision or 'title' not in decision or 'description' not in decision:
            logger.error("Decision must have 'id', 'title', and 'description'")
            return
        
        if 'date' not in decision:
            decision['date'] = datetime.now().isoformat()
        
        self.context['architecture']['decisions'].append(decision)
        self._save_context(self.context)
        logger.info(f"Added architectural decision: {decision['id']}")
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Add a development task.
        
        Args:
            task: Dictionary containing task details
        """
        if 'id' not in task or 'description' not in task:
            logger.error("Task must have 'id' and 'description'")
            return
        
        if 'created_at' not in task:
            task['created_at'] = datetime.now().isoformat()
        
        if 'status' not in task:
            task['status'] = 'pending'
        
        self.context['tasks'].append(task)
        self._save_context(self.context)
        logger.info(f"Added task: {task['id']}")
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status for the task
            
        Returns:
            True if successful, False otherwise
        """
        for task in self.context['tasks']:
            if task['id'] == task_id:
                task['status'] = status
                task['updated_at'] = datetime.now().isoformat()
                self._save_context(self.context)
                logger.info(f"Updated task {task_id} status to {status}")
                return True
        
        logger.error(f"Task not found: {task_id}")
        return False 