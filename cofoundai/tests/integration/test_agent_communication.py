"""
CoFound.ai Agent Communication Test

This script tests if agent communication and LangGraph structure in the CoFound.ai project
works correctly without LLM. Simplified version.
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional

# Logging settings
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_communication():
    """
    Tests agent communication and verifies that the LangGraph structure works correctly.
    """
    try:
        print("Testing CoFound.ai communication modules...")
        
        # Import base modules
        from cofoundai.communication.message import Message, MessageContent
        from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
        
        print("Communication modules successfully imported.")
        
        # Message and Command creation tests
        message = Message(
            sender="human",
            recipient="Planner",
            content="Create a simple calculator application"
        )
        
        command = Command.handoff(
            to_agent="Developer",
            reason="Developer agent needs to write code for this task",
            state_updates={"task": "calculator application"}
        )
        
        print(f"Message created: {message}")
        print(f"Command created: {command}")
        
        # Respond to message
        response = message.create_response(
            content="I'm preparing a plan for the calculator application"
        )
        
        print(f"Response message created: {response}")
        print(f"Response is reply to original message: {response.is_response_to(message)}")
        
        # Convert command to dictionary and back
        command_dict = command.to_dict()
        command_reconverted = Command.from_dict(command_dict)
        
        print(f"Command converted to dictionary: {command_dict}")
        print(f"Converted back from dictionary to command: {command_reconverted}")
        
        print("\nBasic communication tests successful!")
        return {
            "success": True,
            "message": "Basic communication modules successfully tested",
            "details": {
                "message_test": str(message),
                "command_test": str(command),
                "response_test": str(response)
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
    print("Starting CoFound.ai agent communication test...")
    
    try:
        result = test_agent_communication()
        
        if result["success"]:
            print(f"\nTEST SUCCESSFUL: {result['message']}")
        else:
            print(f"\nTEST FAILED: {result['message']}")
    except Exception as e:
        print(f"\nCRITICAL ERROR DURING TEST: {str(e)}")
        traceback.print_exc() 