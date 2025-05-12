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
        
        print("\nAgentic Graph test successful!")
        return {
            "success": True,
            "message": "Agentic Graph test completed successfully",
            "details": {
                "workflow": workflow.name,
                "status": result.get("status", "unknown")
            }
        }
        
    except Exception as e:
        print(f"ERROR: Error during test: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Test failed: {str(e)}",
            "error": str(e)
        }

if __name__ == "__main__":
    print("Starting CoFound.ai Agentic Graph test...")
    
    try:
        result = test_agentic_graph()
        
        if result["success"]:
            print(f"\nTEST SUCCESSFUL: {result['message']}")
        else:
            print(f"\nTEST FAILED: {result['message']}")
    except Exception as e:
        print(f"\nCRITICAL ERROR DURING TEST: {str(e)}")
        traceback.print_exc() 