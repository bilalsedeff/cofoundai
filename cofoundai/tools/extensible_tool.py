"""
CoFound.ai Extensible Tool Components

This module contains the basic components for CoFound.ai's extensible tool system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type, Union
import inspect
import json
import logging

from cofoundai.utils.logger import get_logger
from cofoundai.core.extensibility import (
    ExtensibleComponent, ComponentType, ProviderType, Capability
)

logger = get_logger(__name__)

class ToolResult:
    """Tool execution result"""
    
    def __init__(self, 
                 success: bool, 
                 data: Any = None, 
                 error: Optional[str] = None):
        """
        Create a tool result.
        
        Args:
            success: Is the operation successful?
            data: Result data
            error: Error message (if unsuccessful)
        """
        self.success = success
        self.data = data
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the result as a dictionary"""
        result = {
            "success": self.success
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.error:
            result["error"] = self.error
            
        return result
    
    @classmethod
    def success_result(cls, data: Any = None) -> 'ToolResult':
        """Create a successful result"""
        return cls(success=True, data=data)
    
    @classmethod
    def error_result(cls, error: str) -> 'ToolResult':
        """Create an error result"""
        return cls(success=False, error=error)

class Tool(ExtensibleComponent):
    """
    Base class for extensible tools.
    
    This class provides the basic functionality for all extensible tools.
    """
    
    def __init__(self, 
                name: str, 
                description: str):
        """
        Create an extensible tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        super().__init__(
            name=name,
            description=description,
            component_type=ComponentType.TOOL,
            provider_type=ProviderType.INTERNAL
        )
    
    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """
        Run the tool.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Implementation of ExtensibleComponent.invoke method.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool result
        """
        try:
            result = self.run(**kwargs)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error invoking tool '{self.name}': {str(e)}")
            return ToolResult.error_result(str(e)).to_dict()

class FunctionTool(Tool):
    """
    Function-based tool.
    
    This class wraps a Python function as a tool.
    """
    
    def __init__(self, 
                func: Callable, 
                name: Optional[str] = None, 
                description: Optional[str] = None):
        """
        Create a function-based tool.
        
        Args:
            func: Function to wrap
            name: Tool name (None uses function name)
            description: Tool description (None uses function docstring)
        """
        self.func = func
        func_name = func.__name__
        
        # Analyze function parameters
        sig = inspect.signature(func)
        self.parameters = {}
        
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": param.annotation.__name__ if param.annotation != inspect._empty else "any",
                "required": param.default == inspect._empty
            }
            
            if param.default != inspect._empty:
                param_info["default"] = param.default
                
            self.parameters[param_name] = param_info
        
        # Determine name and description
        if name is None:
            name = func_name
            
        if description is None:
            description = func.__doc__ or f"Function tool: {func_name}"
            
        super().__init__(name=name, description=description)
        
        # Capability definition
        capability = Capability(
            name="run",
            description=description,
            parameters=self.parameters
        )
        self.add_capability(capability)
        
        # Add parameters to metadata
        self.set_metadata("parameters", self.parameters)
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run the function.
        
        Args:
            **kwargs: Function parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Call the function and return the result
            result = self.func(**kwargs)
            return ToolResult.success_result(result)
        except Exception as e:
            logger.error(f"Error executing function tool '{self.name}': {str(e)}")
            return ToolResult.error_result(str(e))

class CommandTool(Tool):
    """
    Command line tool.
    
    This class provides a tool for running system commands.
    """
    
    def __init__(self, 
                command_template: str, 
                name: str, 
                description: str,
                working_dir: Optional[str] = None):
        """
        Create a command line tool.
        
        Args:
            command_template: Command template (format string)
            name: Tool name
            description: Tool description
            working_dir: Working directory (optional)
        """
        super().__init__(name=name, description=description)
        
        self.command_template = command_template
        self.working_dir = working_dir
        
        # Example: Extract "message" parameter from "echo {message}" template
        import re
        self.parameters = {}
        
        for param_name in re.findall(r"{(.*?)}", command_template):
            self.parameters[param_name] = {
                "type": "str",
                "required": True
            }
        
        # Capability definition
        capability = Capability(
            name="run",
            description=description,
            parameters=self.parameters
        )
        self.add_capability(capability)
        
        # Add parameters and command template to metadata
        self.set_metadata("parameters", self.parameters)
        self.set_metadata("command_template", command_template)
        self.set_metadata("working_dir", working_dir)
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run the command.
        
        Args:
            **kwargs: Command parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Format the command template
            command = self.command_template.format(**kwargs)
            
            # Run the command
            import subprocess
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir
            )
            
            stdout, stderr = process.communicate()
            
            # Check the result
            if process.returncode == 0:
                return ToolResult.success_result({
                    "stdout": stdout.strip(),
                    "stderr": stderr.strip() if stderr else None,
                    "returncode": process.returncode
                })
            else:
                return ToolResult.error_result(f"Command failed with code {process.returncode}: {stderr}")
        except Exception as e:
            logger.error(f"Error executing command tool '{self.name}': {str(e)}")
            return ToolResult.error_result(str(e))

class RESTTool(Tool):
    """
    REST API-based tool.
    
    This class provides a tool for making REST API calls.
    """
    
    def __init__(self, 
                endpoint: str, 
                method: str, 
                name: str, 
                description: str,
                headers: Optional[Dict[str, str]] = None,
                auth: Optional[Dict[str, str]] = None,
                timeout: int = 30):
        """
        Create a REST API tool.
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            name: Tool name
            description: Tool description
            headers: HTTP headers (optional)
            auth: Authentication information (optional)
            timeout: Request timeout (seconds)
        """
        super().__init__(name=name, description=description)
        
        self.endpoint = endpoint
        self.method = method.upper()
        self.headers = headers or {}
        self.auth = auth
        self.timeout = timeout
        
        # Capability definition
        capability = Capability(
            name="run",
            description=description,
            parameters={
                "params": {
                    "type": "dict",
                    "required": False
                },
                "data": {
                    "type": "dict",
                    "required": False
                },
                "json_data": {
                    "type": "dict",
                    "required": False
                }
            }
        )
        self.add_capability(capability)
        
        # Add API information to metadata
        self.set_metadata("endpoint", endpoint)
        self.set_metadata("method", method)
        self.set_metadata("requires_auth", auth is not None)
    
    def run(self, 
           params: Optional[Dict[str, Any]] = None, 
           data: Optional[Dict[str, Any]] = None,
           json_data: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Make an API call.
        
        Args:
            params: URL parameters (optional)
            data: Form data (optional)
            json_data: JSON data (optional)
            
        Returns:
            Tool execution result
        """
        try:
            import requests
            
            # Configure the API request
            request_kwargs = {
                "headers": self.headers,
                "timeout": self.timeout
            }
            
            if params:
                request_kwargs["params"] = params
                
            if data:
                request_kwargs["data"] = data
                
            if json_data:
                request_kwargs["json"] = json_data
                
            if self.auth:
                request_kwargs["auth"] = (self.auth.get("username"), self.auth.get("password"))
            
            # Make the API request based on the HTTP method
            if self.method == "GET":
                response = requests.get(self.endpoint, **request_kwargs)
            elif self.method == "POST":
                response = requests.post(self.endpoint, **request_kwargs)
            elif self.method == "PUT":
                response = requests.put(self.endpoint, **request_kwargs)
            elif self.method == "DELETE":
                response = requests.delete(self.endpoint, **request_kwargs)
            else:
                return ToolResult.error_result(f"Unsupported HTTP method: {self.method}")
            
            # Process the response
            try:
                json_response = response.json()
            except:
                json_response = None
                
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": json_response if json_response else response.text
            }
            
            # Success response check
            if 200 <= response.status_code < 300:
                return ToolResult.success_result(result)
            else:
                return ToolResult.error_result(f"Request failed with status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error executing REST tool '{self.name}': {str(e)}")
            return ToolResult.error_result(str(e)) 