"""
CoFound.ai Agentic Graph Test

This script tests the Agentic Graph structure in the CoFound.ai project.
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional

# Logging settings
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agentic_graph():
    """
    Tests the Agentic Graph structure.
    """
    try:
        print("Testing CoFound.ai Agentic Graph structure...")
        
        # Import modules
        from cofoundai.communication.message import Message
        from cofoundai.communication.agent_command import Command, CommandType
        
        # Test the basic structure without changing LangGraph configuration
        from cofoundai.orchestration.langgraph_workflow import LangGraphWorkflow
        
        print("Required modules successfully imported.")
        
        # Create a simple workflow
        workflow_config = {
            "name": "test_workflow",
            "test_mode": True,  # Run in test mode
            "test_agent_order": ["agent1", "agent2"],
        }
        
        workflow = LangGraphWorkflow(
            name="test_workflow", 
            config=workflow_config
        )
        
        print(f"Workflow created: {workflow.name}")
        
        # Run the test mode workflow
        initial_state = {
            "project_description": "Simple calculator application",
            "user_request": "Develop a calculator that can perform addition, subtraction, multiplication, and division",
        }
        
        print("Running workflow...")
        result = workflow.run(initial_state)
        
        print(f"Workflow result: {result.get('status', 'unknown')}")
        
        # Use assert instead of return
        assert workflow.name == "test_workflow", "Workflow name should be 'test_workflow'"
        assert isinstance(result, dict), "Workflow result should be a dictionary"
        
        print("\nAgentic Graph test successful!")
        
    except Exception as e:
        print(f"ERROR: Error during test: {str(e)}")
        traceback.print_exc()
        # Fail the test
        assert False, f"Test failed: {str(e)}"

if __name__ == "__main__":
    print("Starting CoFound.ai Agentic Graph test...")
    
    try:
        test_agentic_graph()
        print("\nTEST SUCCESSFUL: Agentic Graph test completed successfully")
    except Exception as e:
        print(f"\nCRITICAL ERROR DURING TEST: {str(e)}")
        traceback.print_exc() 