"""
CoFound.ai Tester Agent

This module defines the Tester agent responsible for testing the generated code.
"""

import logging
from typing import Dict, Any, List, Optional

from cofoundai.core.base_agent import BaseAgent
from cofoundai.communication.message import Message
from cofoundai.utils.logger import get_agent_logger

class TesterAgent(BaseAgent):
    """
    Tester agent responsible for creating and executing tests.
    
    This agent handles:
    - Creating unit tests
    - Creating integration tests
    - Executing tests
    - Reporting test results
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tester agent.
        
        Args:
            config: Dictionary containing the agent's configuration settings
        """
        super().__init__(config)
        self.name = config.get("name", "Tester")
        self.description = config.get("description", "Agent that performs testing tasks")
        self.logger = get_agent_logger(self.name)
        self.logger.info(f"Tester agent initialized: {self.name}")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and create/execute tests.
        
        Args:
            input_data: Input data including code to test and testing requirements
            
        Returns:
            Output data including test results
        """
        self.logger.info("Processing testing request", extra={"input": str(input_data)[:200]})
        
        # Extract data
        code_files = input_data.get("code_files", {})
        test_requirements = input_data.get("test_requirements", [])
        
        # Placeholder for actual testing logic
        # In a real implementation, this would interface with LLM for generating tests
        
        # Log the testing process
        self.logger.info(
            "Creating and executing tests",
            extra={
                "code_files_count": len(code_files),
                "test_requirements_count": len(test_requirements)
            }
        )
        
        # Creating mock test results
        test_results = {
            "unit_tests": {
                "total": 15,
                "passed": 12,
                "failed": 3,
                "skipped": 0
            },
            "integration_tests": {
                "total": 8,
                "passed": 7,
                "failed": 1,
                "skipped": 0
            },
            "coverage": "87%",
            "failures": [
                {"test": "test_user_login", "message": "Expected status code 200, got 401"},
                {"test": "test_create_todo", "message": "Missing required field 'created_at'"},
                {"test": "test_database_connection", "message": "Connection timeout after 5s"}
            ]
        }
        
        self.logger.info(
            "Testing completed", 
            extra={
                "total_tests": test_results["unit_tests"]["total"] + test_results["integration_tests"]["total"],
                "failed_tests": test_results["unit_tests"]["failed"] + test_results["integration_tests"]["failed"],
                "coverage": test_results["coverage"]
            }
        )
        
        return {
            "status": "success" if test_results["unit_tests"]["failed"] + test_results["integration_tests"]["failed"] == 0 else "partial_success",
            "test_results": test_results,
            "message": "Testing completed with some failures" if test_results["unit_tests"]["failed"] + test_results["integration_tests"]["failed"] > 0 else "All tests passed"
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
        
        if "test" in content or "run tests" in content:
            # Extract code from metadata
            code_files = metadata.get("code_files", {})
            test_requirements = metadata.get("test_requirements", [])
            
            # Create input data for process function
            input_data = {
                "code_files": code_files,
                "test_requirements": test_requirements
            }
            
            # Process the testing request
            result = self.process(input_data)
            
            # Create and return response message
            return Message(
                sender=self.name,
                recipient=message.sender,
                content=result["message"],
                metadata={"test_results": result["test_results"]}
            )
        else:
            # Default to super implementation
            return super().process_message(message) 