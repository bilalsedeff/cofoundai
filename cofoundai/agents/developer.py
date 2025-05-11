"""
CoFound.ai Developer Agent

This module defines an AI agent that performs software development tasks.
The developer agent is responsible for code writing, revising, and debugging.
"""

from typing import Dict, List, Any, Optional
from cofoundai.core.base_agent import BaseAgent
from cofoundai.communication.message import Message
from cofoundai.tools.code_generator import CodeGenerator


class DeveloperAgent(BaseAgent):
    """
    AI agent that performs code development and programming tasks.
    """

    def __init__(self, config: Dict[str, Any], test_mode: bool = False):
        """
        Initialize the developer agent.
        
        Args:
            config: Dictionary containing the agent's configuration settings
            test_mode: Whether to run in test mode with simulated responses
        """
        super().__init__(config)
        self.name = config.get("name", "Developer")
        self.description = config.get("description", "Agent that performs code development tasks")
        self.code_generator = CodeGenerator(config.get("code_generator", {}))
        self.current_task = None
        self.current_context = {}
        self.test_mode = test_mode
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and develop code.
        
        Args:
            input_data: Input data including task description and context
            
        Returns:
            Output data including generated code
        """
        # Extract task information
        project_description = input_data.get("project_description", "")
        architecture = input_data.get("previous_results", {}).get("Architecture", {}).get("architecture", {})
        
        # Use architecture to determine the appropriate language and framework
        language = "python"
        framework = "fastapi"
        
        # Try to determine language and framework from architecture if available
        if architecture and "components" in architecture:
            for component in architecture.get("components", []):
                if component.get("type") == "API" or component.get("name") == "Backend":
                    if "technologies" in component:
                        for tech in component["technologies"]:
                            if tech.lower() in ["python", "javascript", "typescript", "java", "go"]:
                                language = tech.lower()
                            if tech.lower() in ["fastapi", "flask", "django", "express", "spring"]:
                                framework = tech.lower()
        
        # Create context for code generation
        context = {
            "language": language,
            "framework": framework,
            "architecture": architecture,
            "project_description": project_description
        }
        
        # Generate code for the project
        task_description = f"Create a basic {framework} application for: {project_description}"
        code_result = self.write_code(task_description, context)
        
        return {
            "status": "success",
            "message": f"Code developed for {framework} application",
            "code_files": {
                code_result["file_path"]: code_result["code"]
            },
            "language": language,
            "framework": framework,
            "dependencies": code_result.get("metadata", {}).get("dependencies", [])
        }
        
    def write_code(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code based on a task description.
        
        Args:
            task_description: Description of the task and requirements
            context: Development context (existing code, architecture info, etc.)
            
        Returns:
            Dictionary containing the generated code and metadata
        """
        # Store task and context information
        self.current_task = task_description
        self.current_context = context
        
        # Generate code using LLM via the code generator tool
        code_result = self.code_generator.generate_code(
            task_description=task_description,
            language=context.get("language", "python"),
            framework=context.get("framework", ""),
            existing_code=context.get("existing_code", ""),
            architecture_info=context.get("architecture", "")
        )
        
        return {
            "code": code_result["code"],
            "file_path": code_result.get("file_path", ""),
            "language": context.get("language", "python"),
            "description": f"Code generated for task '{task_description}'",
            "status": "Completed",
            "metadata": {
                "task": task_description,
                "dependencies": code_result.get("dependencies", []),
                "imports": code_result.get("imports", [])
            }
        }
    
    def revise_code(self, code: str, feedback: str) -> Dict[str, Any]:
        """
        Revise existing code based on feedback.
        
        Args:
            code: The code to revise
            feedback: Feedback for revision
            
        Returns:
            Dictionary containing the revised code and changes
        """
        # Revise code using the code generator tool based on feedback
        revised_code = self.code_generator.revise_code(
            original_code=code,
            feedback=feedback,
            context=self.current_context
        )
        
        return {
            "code": revised_code["code"],
            "file_path": revised_code.get("file_path", ""),
            "description": "Code revised based on feedback",
            "status": "Revised",
            "changes": revised_code.get("changes", []),
            "original_code": code
        }
    
    def debug_code(self, code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Debug code and fix any errors.
        
        Args:
            code: The code to debug
            error_message: Error message, if available
            
        Returns:
            Dictionary containing the debugged code and fixes
        """
        # Debug code using the code generator tool
        debug_result = self.code_generator.debug_code(
            code=code, 
            error_message=error_message,
            context=self.current_context
        )
        
        return {
            "code": debug_result["code"],
            "file_path": debug_result.get("file_path", ""),
            "description": "Debugged code",
            "status": "Fixed",
            "original_error": error_message,
            "fixes": debug_result.get("fixes", []),
            "original_code": code
        }
    
    def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate an appropriate response.
        
        Args:
            message: The message object to process
            
        Returns:
            Response message
        """
        # Process message based on content
        content = message.content.lower()
        metadata = message.metadata or {}
        
        if "write code" in content or "generate code" in content or "develop" in content:
            # Process code generation request
            task_desc = message.content
            context = metadata.get("context", {})
            result = self.write_code(task_desc, context)
            
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=f"Code developed for task '{task_desc}'",
                metadata={"result": result}
            )
            
        elif "revise" in content or "fix" in content:
            # Process code revision request
            code = metadata.get("code", "")
            feedback = message.content
            
            if not code:
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content="No code found to revise. Please include the code in the metadata."
                )
                
            result = self.revise_code(code, feedback)
            return Message(
                sender=self.name,
                recipient=message.sender,
                content="Code revised according to feedback",
                metadata={"result": result}
            )
            
        elif "error" in content or "debug" in content:
            # Process debugging request
            code = metadata.get("code", "")
            error = metadata.get("error", "")
            
            if not code:
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    content="No code found to debug. Please include the code in the metadata."
                )
                
            result = self.debug_code(code, error)
            return Message(
                sender=self.name,
                recipient=message.sender,
                content="Code debugging completed",
                metadata={"result": result}
            )
            
        else:
            # Default to super implementation which will call process()
            return super().process_message(message) 