"""
CoFound.ai Version Control Tool

This module provides Git version control functionality for agents to work with project-specific code.
It allows agents to perform Git operations such as init, commit, push, pull, and branch.
Each user project has its own isolated Git repository.
"""

import os
import subprocess
import logging
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import json

from cofoundai.tools.file_manager import FileManager
from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class GitException(Exception):
    """Exception raised for Git command errors."""
    pass

class VersionControl:
    """
    Tool for project-specific Git version control operations.
    Allows agents to interact with Git repositories for each user project.
    """
    
    def __init__(self, 
                project_id: str,
                workspace_dir: Optional[str] = None, 
                config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Version Control tool.
        
        Args:
            project_id: Unique identifier for the user's project
            workspace_dir: Base directory for project repositories
            config: Configuration settings
        """
        self.project_id = project_id
        self.config = config or {}
        
        # Set up the workspace directory
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
        else:
            default_workspace = Path(os.environ.get("COFOUNDAI_WORKSPACE", 
                                                   Path.home() / "cofoundai_projects"))
            self.workspace_dir = default_workspace
        
        # Ensure the workspace directory exists
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Create project-specific directory
        self.project_dir = self.workspace_dir / self.project_id
        os.makedirs(self.project_dir, exist_ok=True)
        
        # For file operations
        self.file_manager = FileManager(workspace_dir=str(self.project_dir), config=config)
        
        # Git configuration
        self.git_config = self.config.get("git", {})
        self.default_branch = self.git_config.get("default_branch", "main")
        self.default_message = self.git_config.get("default_commit_message", "Update by CoFound.ai agent")
        self.user_name = self.git_config.get("user_name", "CoFound.ai Agent")
        self.user_email = self.git_config.get("user_email", "agent@cofound.ai")
        
        logger.info(f"VersionControl initialized for project {project_id} in {self.project_dir}")
    
    def run_git_command(self, *args: str, cwd: Optional[str] = None) -> Tuple[str, str]:
        """
        Run a Git command and return its output.
        
        Args:
            *args: Git command arguments
            cwd: Working directory for the command
            
        Returns:
            Tuple of (stdout, stderr)
            
        Raises:
            GitException: If the command fails
        """
        cmd = ["git"] + list(args)
        working_dir = cwd or str(self.project_dir)
        
        logger.debug(f"Running Git command: {' '.join(cmd)} in {working_dir}")
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Git command failed: {stderr}")
                raise GitException(f"Git command failed: {stderr}")
                
            return stdout.strip(), stderr.strip()
            
        except Exception as e:
            logger.error(f"Error running Git command: {str(e)}")
            raise GitException(f"Error running Git command: {str(e)}")
    
    def is_git_repo(self) -> bool:
        """
        Check if the current project directory is a Git repository.
        
        Returns:
            True if the directory is a Git repository, False otherwise
        """
        try:
            self.run_git_command("rev-parse", "--is-inside-work-tree")
            return True
        except GitException:
            return False
    
    def init_repo(self, initial_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize a new Git repository for the project.
        
        Args:
            initial_branch: Name of the initial branch (defaults to self.default_branch)
            
        Returns:
            Status information about the operation
        """
        if self.is_git_repo():
            logger.info(f"Repository already initialized in {self.project_dir}")
            return {"status": "success", "message": "Repository already initialized", "path": str(self.project_dir)}
        
        branch = initial_branch or self.default_branch
        
        try:
            # Initialize the repository
            self.run_git_command("init")
            
            # Configure user information
            self.run_git_command("config", "user.name", self.user_name)
            self.run_git_command("config", "user.email", self.user_email)
            
            # Configure initial branch name
            self.run_git_command("config", "init.defaultBranch", branch)
            
            # Create .gitignore with common exclusions
            gitignore_content = """
# CoFound.ai generated .gitignore
__pycache__/
*.py[cod]
*$py.class
.env
.venv
env/
venv/
ENV/
.DS_Store
*.log
"""
            self.file_manager.write_file(".gitignore", gitignore_content)
            
            logger.info(f"Git repository initialized in {self.project_dir} with branch {branch}")
            return {
                "status": "success", 
                "message": f"Repository initialized with branch '{branch}'",
                "path": str(self.project_dir)
            }
            
        except GitException as e:
            logger.error(f"Failed to initialize repository: {str(e)}")
            return {"status": "error", "message": f"Failed to initialize repository: {str(e)}"}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the Git repository.
        
        Returns:
            Dictionary with status information
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            status_output, _ = self.run_git_command("status", "--porcelain")
            branch_output, _ = self.run_git_command("branch", "--show-current")
            
            # Get unstaged and staged files
            unstaged_files = []
            staged_files = []
            
            for line in status_output.splitlines():
                if not line.strip():
                    continue
                    
                status = line[:2]
                file_path = line[3:]
                
                if status[0] != ' ':  # Staged changes
                    staged_files.append(file_path)
                if status[1] != ' ':  # Unstaged changes
                    unstaged_files.append(file_path)
            
            return {
                "status": "success",
                "current_branch": branch_output,
                "has_changes": bool(status_output),
                "unstaged_files": unstaged_files,
                "staged_files": staged_files
            }
            
        except GitException as e:
            logger.error(f"Failed to get repository status: {str(e)}")
            return {"status": "error", "message": f"Failed to get repository status: {str(e)}"}
    
    def add_files(self, files: List[str]) -> Dict[str, Any]:
        """
        Stage files for commit.
        
        Args:
            files: List of file paths to stage
            
        Returns:
            Status information about the operation
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            if not files:
                self.run_git_command("add", ".")
                logger.info("All files staged")
                return {"status": "success", "message": "All files staged for commit"}
            
            for file_path in files:
                self.run_git_command("add", file_path)
            
            logger.info(f"Files staged: {', '.join(files)}")
            return {"status": "success", "message": f"Files staged: {', '.join(files)}"}
            
        except GitException as e:
            logger.error(f"Failed to stage files: {str(e)}")
            return {"status": "error", "message": f"Failed to stage files: {str(e)}"}
    
    def commit(self, message: Optional[str] = None, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Commit staged changes.
        
        Args:
            message: Commit message
            files: Optional list of files to stage before committing
            
        Returns:
            Status information about the operation
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            # Stage files if provided
            if files:
                self.add_files(files)
            
            # Use default message if none provided
            commit_message = message or self.default_message
            
            # Commit the changes
            output, _ = self.run_git_command("commit", "-m", commit_message)
            
            logger.info(f"Changes committed: {output}")
            return {"status": "success", "message": output}
            
        except GitException as e:
            logger.error(f"Failed to commit changes: {str(e)}")
            return {"status": "error", "message": f"Failed to commit changes: {str(e)}"}
    
    def checkout_branch(self, branch_name: str, create: bool = False) -> Dict[str, Any]:
        """
        Checkout a branch.
        
        Args:
            branch_name: Name of the branch to checkout
            create: Whether to create the branch if it doesn't exist
            
        Returns:
            Status information about the operation
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            if create:
                self.run_git_command("checkout", "-b", branch_name)
                logger.info(f"Created and checked out branch: {branch_name}")
                return {"status": "success", "message": f"Created and checked out branch: {branch_name}"}
            else:
                self.run_git_command("checkout", branch_name)
                logger.info(f"Checked out branch: {branch_name}")
                return {"status": "success", "message": f"Checked out branch: {branch_name}"}
                
        except GitException as e:
            logger.error(f"Failed to checkout branch: {str(e)}")
            return {"status": "error", "message": f"Failed to checkout branch: {str(e)}"}
    
    def list_branches(self) -> Dict[str, Any]:
        """
        List all branches in the repository.
        
        Returns:
            Dictionary with list of branches
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            output, _ = self.run_git_command("branch")
            
            branches = []
            current_branch = None
            
            for line in output.splitlines():
                branch = line.strip()
                if branch.startswith('*'):
                    # Current branch has an asterisk
                    current_branch = branch[1:].strip()
                    branches.append(current_branch)
                else:
                    branches.append(branch)
            
            return {
                "status": "success", 
                "branches": branches, 
                "current_branch": current_branch
            }
            
        except GitException as e:
            logger.error(f"Failed to list branches: {str(e)}")
            return {"status": "error", "message": f"Failed to list branches: {str(e)}"}
    
    def log(self, n: int = 10) -> Dict[str, Any]:
        """
        Get the commit history.
        
        Args:
            n: Number of commits to retrieve
            
        Returns:
            Dictionary with commit history
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            # Format: hash, author, date, message
            format_str = "--pretty=format:%H|%an|%ad|%s"
            output, _ = self.run_git_command("log", format_str, f"-n{n}")
            
            commits = []
            for line in output.splitlines():
                if not line.strip():
                    continue
                    
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commit = {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    }
                    commits.append(commit)
            
            return {"status": "success", "commits": commits}
            
        except GitException as e:
            logger.error(f"Failed to get commit history: {str(e)}")
            return {"status": "error", "message": f"Failed to get commit history: {str(e)}"}
    
    def get_diff(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the diff for unstaged changes.
        
        Args:
            file_path: Optional specific file to get diff for
            
        Returns:
            Dictionary with diff information
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        try:
            if file_path:
                output, _ = self.run_git_command("diff", file_path)
            else:
                output, _ = self.run_git_command("diff")
            
            return {"status": "success", "diff": output}
            
        except GitException as e:
            logger.error(f"Failed to get diff: {str(e)}")
            return {"status": "error", "message": f"Failed to get diff: {str(e)}"}
    
    def create_project_snapshot(self, description: str = "Project snapshot") -> Dict[str, Any]:
        """
        Create a snapshot of the current project state by committing all changes.
        
        Args:
            description: Description of the snapshot
            
        Returns:
            Status information about the operation
        """
        if not self.is_git_repo():
            # Initialize repo if it doesn't exist
            init_result = self.init_repo()
            if init_result["status"] == "error":
                return init_result
        
        try:
            # Add all files
            self.add_files([])
            
            # Create a timestamp for the snapshot
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Commit with snapshot message
            message = f"Snapshot: {description} ({timestamp})"
            result = self.commit(message)
            
            if result["status"] == "success":
                # Get the commit hash
                commit_hash, _ = self.run_git_command("rev-parse", "HEAD")
                result["snapshot_id"] = commit_hash
                
                # Create a snapshot metadata file
                snapshot_meta = {
                    "id": commit_hash,
                    "description": description,
                    "timestamp": timestamp,
                    "created_by": self.user_name
                }
                
                snapshots_dir = self.project_dir / ".cofoundai" / "snapshots"
                os.makedirs(snapshots_dir, exist_ok=True)
                
                with open(snapshots_dir / f"{commit_hash}.json", 'w') as f:
                    json.dump(snapshot_meta, f, indent=2)
            
            return result
            
        except GitException as e:
            logger.error(f"Failed to create snapshot: {str(e)}")
            return {"status": "error", "message": f"Failed to create snapshot: {str(e)}"}
    
    def list_snapshots(self) -> Dict[str, Any]:
        """
        List all available project snapshots.
        
        Returns:
            Dictionary with list of snapshots
        """
        snapshots_dir = self.project_dir / ".cofoundai" / "snapshots"
        
        if not os.path.exists(snapshots_dir):
            return {"status": "success", "snapshots": []}
        
        try:
            snapshots = []
            for file_name in os.listdir(snapshots_dir):
                if file_name.endswith('.json'):
                    with open(snapshots_dir / file_name, 'r') as f:
                        snapshot = json.load(f)
                        snapshots.append(snapshot)
            
            # Sort snapshots by timestamp (newest first)
            snapshots.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {"status": "success", "snapshots": snapshots}
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {str(e)}")
            return {"status": "error", "message": f"Failed to list snapshots: {str(e)}"}
    
    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Restore the project to a specific snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to restore (commit hash)
            
        Returns:
            Status information about the operation
        """
        if not self.is_git_repo():
            return {"status": "error", "message": "Not a Git repository"}
        
        snapshots_dir = self.project_dir / ".cofoundai" / "snapshots"
        snapshot_file = snapshots_dir / f"{snapshot_id}.json"
        
        if not os.path.exists(snapshot_file):
            return {"status": "error", "message": f"Snapshot {snapshot_id} not found"}
        
        try:
            # Read snapshot metadata
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
            
            # Create a backup branch of current state
            current_branch, _ = self.run_git_command("branch", "--show-current")
            backup_branch = f"backup_{current_branch}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.run_git_command("branch", backup_branch)
            
            # Checkout the snapshot commit
            self.run_git_command("checkout", snapshot_id)
            
            logger.info(f"Restored to snapshot: {snapshot.get('description')} ({snapshot_id})")
            return {
                "status": "success", 
                "message": f"Restored to snapshot: {snapshot.get('description')}", 
                "backup_branch": backup_branch
            }
            
        except GitException as e:
            logger.error(f"Failed to restore snapshot: {str(e)}")
            return {"status": "error", "message": f"Failed to restore snapshot: {str(e)}"} 