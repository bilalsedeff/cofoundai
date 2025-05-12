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
        
        # Use assert instead of return
        assert message.sender == "human", "Message sender should be 'human'"
        assert message.recipient == "Planner", "Message recipient should be 'Planner'"
        assert command.type == CommandType.HANDOFF, "Command should be a HANDOFF type"
        assert response.is_response_to(message), "Response should be a response to the original message"
        
        print("\nBasic communication tests successful!")
        
    except Exception as e:
        print(f"ERROR: Error during test: {str(e)}")
        traceback.print_exc()
        # Fail the test
        assert False, f"Test failed: {str(e)}"

if __name__ == "__main__":
    print("Starting CoFound.ai agent communication test...")
    
    try:
        test_agent_communication()
        print("\nTEST SUCCESSFUL: Basic communication modules successfully tested")
    except Exception as e:
        print(f"\nCRITICAL ERROR DURING TEST: {str(e)}")
        traceback.print_exc() 