"""
CoFound.ai Documenter Agent

This module defines the Documenter agent responsible for creating project documentation.
"""

import logging
from typing import Dict, Any, List, Optional

from cofoundai.core.base_agent import BaseAgent
from cofoundai.communication.message import Message
from cofoundai.utils.logger import get_agent_logger

class DocumentorAgent(BaseAgent):
    """
    Documenter agent responsible for creating project documentation.
    
    This agent handles:
    - Creating README files
    - Generating API documentation
    - Creating user guides
    - Documenting architecture and design decisions
    """
    
    def __init__(self, config: Dict[str, Any], test_mode: bool = False):
        """
        Initialize the Documenter agent.
        
        Args:
            config: Dictionary containing the agent's configuration settings
            test_mode: Whether to run in test mode with simulated responses
        """
        super().__init__(config)
        self.name = config.get("name", "Documentor")
        self.description = config.get("description", "Agent that creates project documentation")
        self.logger = get_agent_logger(self.name)
        self.logger.info(f"Documenter agent initialized: {self.name}")
        self.test_mode = test_mode
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and create documentation.
        
        Args:
            input_data: Input data including code, architecture, and project details
            
        Returns:
            Output data including generated documentation
        """
        self.logger.info("Processing documentation request", extra={"input": str(input_data)[:200]})
        
        # Extract data
        project_name = input_data.get("project_name", "Untitled Project")
        project_description = input_data.get("project_description", "")
        code_files = input_data.get("code_files", {})
        architecture = input_data.get("architecture", {})
        
        # Placeholder for actual documentation generation logic
        # In a real implementation, this would interface with LLM for generating documentation
        
        # Log the documentation process
        self.logger.info(
            "Creating project documentation",
            extra={
                "project_name": project_name,
                "code_files_count": len(code_files)
            }
        )
        
        # Creating mock documentation output
        documentation = {
            "readme": f"# {project_name}\n\n{project_description}\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\npython app.py\n```",
            "api_docs": [
                {"endpoint": "/api/users", "method": "GET", "description": "Get all users", "parameters": [], "responses": {"200": "Success", "401": "Unauthorized"}},
                {"endpoint": "/api/users/{id}", "method": "GET", "description": "Get user by ID", "parameters": [{"name": "id", "type": "integer", "required": True}], "responses": {"200": "Success", "404": "User not found"}}
            ],
            "architecture_docs": "# System Architecture\n\n## Components\n\n- Frontend: React with TypeScript\n- Backend: FastAPI\n- Database: PostgreSQL\n\n## Data Flow\n\n1. User requests handled by Frontend\n2. API requests sent to Backend\n3. Backend processes and stores in Database",
            "user_guide": "# User Guide\n\n## Getting Started\n\n1. Register an account\n2. Login with your credentials\n3. Create your first project\n\n## Features\n\n- Project management\n- Task tracking\n- Reporting"
        }
        
        self.logger.info("Documentation completed", extra={"doc_types_count": len(documentation)})
        
        return {
            "status": "success",
            "documentation": documentation,
            "message": "Project documentation created successfully"
        }
        
    def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate an appropriate response.
        
        Args:
            message: The message object to process
            
        Returns:
            Response message
        """
        content = message.content.lower()
        metadata = message.metadata or {}
        
        if "document" in content or "documentation" in content or "create docs" in content:
            # Extract information from metadata
            project_name = metadata.get("project_name", "Untitled Project")
            project_description = metadata.get("project_description", "")
            code_files = metadata.get("code_files", {})
            architecture = metadata.get("architecture", {})
            
            # Create input data for process function
            input_data = {
                "project_name": project_name,
                "project_description": project_description,
                "code_files": code_files,
                "architecture": architecture
            }
            
            # Process the documentation request
            result = self.process(input_data)
            
            # Create and return response message
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=result["message"],
                metadata={"documentation": result["documentation"]}
            )
        else:
            # Default to super implementation
            return super().process_message(message) 