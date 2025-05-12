"""
CoFound.ai File Manager Tool

This module provides file system access tools for agents to read and write files.
It includes safety measures and logging to ensure proper file management.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path
import logging

from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class FileManager:
    """
    Tool for managing files and directories in the project workspace.
    Provides safe file operations with logging and access controls.
    """
    
    def __init__(self, workspace_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the file manager.
        
        Args:
            workspace_dir: Base directory for file operations (default: current directory)
            config: Configuration settings for the file manager
        """
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        self.config = config or {}
        
        # Create the workspace directory if it doesn't exist
        if not self.workspace_dir.exists():
            self.workspace_dir.mkdir(parents=True)
            logger.info(f"Created workspace directory: {self.workspace_dir}")
        
        # Safety: Define allowed paths to prevent file access outside workspace
        self.allowed_paths = [self.workspace_dir]
        if "additional_allowed_paths" in self.config:
            for path in self.config["additional_allowed_paths"]:
                self.allowed_paths.append(Path(path))
        
        logger.info(f"FileManager initialized with workspace: {self.workspace_dir}")
    
    def _is_path_allowed(self, path: Union[str, Path]) -> bool:
        """
        Check if a path is allowed for access.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is allowed, False otherwise
        """
        absolute_path = Path(path).resolve()
        
        # Check if path is within allowed paths
        for allowed_path in self.allowed_paths:
            try:
                # Resolve to absolute path
                allowed_absolute = Path(allowed_path).resolve()
                # Check if path is within allowed directory
                if absolute_path == allowed_absolute or allowed_absolute in absolute_path.parents:
                    return True
            except Exception as e:
                logger.warning(f"Error checking allowed path {allowed_path}: {e}")
                
        logger.warning(f"Access denied to path: {absolute_path}")
        return False
    
    def read_file(self, file_path: Union[str, Path], mode: str = 'r') -> str:
        """
        Read contents of a file.
        
        Args:
            file_path: Path to the file to read
            mode: File mode (default: 'r')
            
        Returns:
            File contents as string
            
        Raises:
            ValueError: If the file cannot be accessed
            FileNotFoundError: If the file does not exist
        """
        # Convert relative path to absolute path
        abs_path = Path(self._resolve_path(file_path))
        
        # Safety check
        if not self._is_path_allowed(abs_path):
            raise ValueError(f"File access denied: {abs_path}")
        
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        try:
            with open(abs_path, mode, encoding='utf-8') if 'b' not in mode else open(abs_path, mode) as f:
                content = f.read()
            
            logger.info(f"Read file: {abs_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {abs_path}: {e}")
            raise
    
    def write_file(self, file_path: Union[str, Path], content: Union[str, bytes], mode: str = 'w') -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            mode: File mode (default: 'w')
            
        Returns:
            True if successful, raises exception otherwise
            
        Raises:
            ValueError: If the file cannot be accessed
        """
        # Convert relative path to absolute path
        abs_path = Path(self._resolve_path(file_path))
        
        # Safety check
        if not self._is_path_allowed(abs_path):
            raise ValueError(f"File access denied: {abs_path}")
        
        # Create parent directories if they don't exist
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(abs_path, mode, encoding='utf-8') if 'b' not in mode else open(abs_path, mode) as f:
                f.write(content)
            
            logger.info(f"Wrote file: {abs_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {abs_path}: {e}")
            raise
    
    def _resolve_path(self, file_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path to an absolute path within the workspace.
        
        Args:
            file_path: Path to resolve
            
        Returns:
            Resolved absolute path
        """
        path = Path(file_path)
        
        # If path is absolute, return as is
        if path.is_absolute():
            return path
        
        # Otherwise, join with workspace directory
        return self.workspace_dir / path
    
    def list_directory(self, dir_path: Union[str, Path] = '.') -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            dir_path: Path to directory (default: '.')
            
        Returns:
            List of dictionaries with file information
            
        Raises:
            ValueError: If the directory cannot be accessed
            FileNotFoundError: If the directory does not exist
        """
        # Convert relative path to absolute path
        abs_path = Path(self._resolve_path(dir_path))
        
        # Safety check
        if not self._is_path_allowed(abs_path):
            raise ValueError(f"Directory access denied: {abs_path}")
        
        if not abs_path.exists():
            raise FileNotFoundError(f"Directory not found: {abs_path}")
        
        if not abs_path.is_dir():
            raise ValueError(f"Not a directory: {abs_path}")
        
        result = []
        
        try:
            for item in abs_path.iterdir():
                item_info = {
                    "name": item.name,
                    "path": str(item.relative_to(self.workspace_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                }
                result.append(item_info)
                
            logger.info(f"Listed directory: {abs_path}")
            return result
        except Exception as e:
            logger.error(f"Error listing directory {abs_path}: {e}")
            raise
    
    def create_directory(self, dir_path: Union[str, Path]) -> bool:
        """
        Create a directory.
        
        Args:
            dir_path: Path to the directory to create
            
        Returns:
            True if successful, raises exception otherwise
            
        Raises:
            ValueError: If the directory cannot be created
        """
        # Convert relative path to absolute path
        abs_path = Path(self._resolve_path(dir_path))
        
        # Safety check
        if not self._is_path_allowed(abs_path):
            raise ValueError(f"Directory access denied: {abs_path}")
        
        try:
            abs_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {abs_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory {abs_path}: {e}")
            raise
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, raises exception otherwise
            
        Raises:
            ValueError: If the file cannot be accessed
            FileNotFoundError: If the file does not exist
        """
        # Convert relative path to absolute path
        abs_path = Path(self._resolve_path(file_path))
        
        # Safety check
        if not self._is_path_allowed(abs_path):
            raise ValueError(f"File access denied: {abs_path}")
        
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        try:
            abs_path.unlink()
            logger.info(f"Deleted file: {abs_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {abs_path}: {e}")
            raise
    
    def read_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read JSON file and parse contents.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON content
            
        Raises:
            ValueError: If the file cannot be accessed
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        content = self.read_file(file_path)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file {file_path}: {e}")
            raise
    
    def write_json(self, file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write data to a JSON file.
        
        Args:
            file_path: Path to the JSON file
            data: Data to write
            indent: Indentation level (default: 2)
            
        Returns:
            True if successful, raises exception otherwise
            
        Raises:
            ValueError: If the file cannot be accessed
        """
        try:
            content = json.dumps(data, indent=indent)
            return self.write_file(file_path, content)
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            raise
    
    def read_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read YAML file and parse contents.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Parsed YAML content
            
        Raises:
            ValueError: If the file cannot be accessed
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the file contains invalid YAML
        """
        content = self.read_file(file_path)
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise
    
    def write_yaml(self, file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """
        Write data to a YAML file.
        
        Args:
            file_path: Path to the YAML file
            data: Data to write
            
        Returns:
            True if successful, raises exception otherwise
            
        Raises:
            ValueError: If the file cannot be accessed
        """
        try:
            content = yaml.dump(data, default_flow_style=False)
            return self.write_file(file_path, content)
        except Exception as e:
            logger.error(f"Error writing YAML file {file_path}: {e}")
            raise 