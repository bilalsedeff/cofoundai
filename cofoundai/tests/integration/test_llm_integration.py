"""
CoFound.ai LLM Integration Test

This script tests the integration with LLM providers to ensure API calls work correctly.
Skip tests if LLM API keys are not available or DUMMY_TEST_MODE is enabled.
"""

import os
import pytest
import logging
from typing import Dict, Any, Optional

from cofoundai.core.config_loader import config_loader
from cofoundai.core.base_agent import BaseAgent
from cofoundai.agents.planner import PlannerAgent

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_llm_available():
    """Check if LLM API keys are available and not in dummy test mode."""
    # Skip if dummy test mode is enabled
    if config_loader.is_dummy_test_mode():
        return False, "DUMMY_TEST_MODE is enabled, skipping LLM API tests"
    
    # Check provider and API keys
    provider = config_loader.get_llm_provider()
    
    if provider == "openai":
        if not config_loader.get_env("OPENAI_API_KEY"):
            return False, "OpenAI API key not found"
    elif provider == "anthropic":
        if not config_loader.get_env("ANTHROPIC_API_KEY"):
            return False, "Anthropic API key not found"
    elif provider == "test":
        return False, "LLM Provider is set to 'test'"
    else:
        return False, f"Unknown LLM provider: {provider}"
    
    return True, f"LLM ({provider}) is available"

@pytest.mark.skipif(not check_llm_available()[0], reason=check_llm_available()[1])
def test_llm_simple_query():
    """Test a simple LLM query to ensure API connectivity."""
    # Create a planner agent (which uses LLM)
    planner_config = {
        "name": "Planner",
        "description": "Project planning and task breakdown",
        "use_dummy_test": False  # Explicitly disable dummy test for this test
    }
    
    planner = PlannerAgent(planner_config)
    
    # Simple query
    query = "Create a simple TODO list application"
    
    # Process the query
    response = planner.process({
        "query": query,
        "test_mode": False  # Ensure test mode is off
    })
    
    # Verify response with assertions
    assert response is not None, "No response received from LLM"
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "output" in response, "Response should have 'output' field"
    
    output = response.get("output", "")
    logger.info(f"LLM Response (truncated): {output[:100]}...")
    
    # The response content doesn't matter as much as getting a valid response
    assert len(output) > 10, "Response too short, likely not a valid LLM response"
    
    # Log success information
    logger.info(f"LLM integration test successful with provider: {config_loader.get_llm_provider()}")
    logger.info(f"Response length: {len(output)} characters") 