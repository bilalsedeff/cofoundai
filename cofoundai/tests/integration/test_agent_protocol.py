"""
CoFound.ai Agent Protocol Test

This script tests the Agent Protocol integration of CoFound.ai.
It performs the following steps:

1. Creates a simple LangGraph workflow
2. Registers the workflow with the Agent Protocol API 
3. Tests functionality by calling various endpoints in the Agent Protocol API
"""

import asyncio
import requests
import json
import logging
import sys
import os
import time
from typing import Dict, Any, List

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ap_test")

# API yapılandırması
API_HOST = os.environ.get("COFOUNDAI_AP_HOST", "localhost")
API_PORT = int(os.environ.get("COFOUNDAI_AP_PORT", "8000"))
API_URL = f"http://{API_HOST}:{API_PORT}"

# Test edilecek ajanın ID'si
TEST_AGENT_ID = "test-agent"

def create_test_workflow():
    """Create a simple LangGraph workflow for testing purposes."""
    try:
        from cofoundai.orchestration import LangGraphWorkflow
        from cofoundai.agents.langgraph_agent import LangGraphAgent
        
        # Basit bir test ajanı oluştur
        agent_config = {
            "name": "TestAgent",
            "description": "Test agent for Agent Protocol",
            "system_prompt": "You are a helpful test agent.",
            "llm_provider": "test",  # DummyLLM kullan
        }
        agent = LangGraphAgent(agent_config)
        
        # Workflow oluştur
        workflow = LangGraphWorkflow(
            name="test_workflow",
            config={"test_mode": True}
        )
        
        # Ajanı ekle
        workflow.add_agent(agent)
        
        # Grafiği oluştur
        workflow.build_graph()
        
        return workflow
    except Exception as e:
        logger.error(f"Workflow creation error: {str(e)}")
        return None

def register_workflow_as_agent(workflow):
    """Register the workflow with the Agent Protocol API."""
    try:
        result = workflow.register_as_agent(TEST_AGENT_ID)
        logger.info(f"Workflow registration result: {result}")
        return result
    except Exception as e:
        logger.error(f"Workflow registration error: {str(e)}")
        return False

def start_api_server():
    """Start the API server in a separate process."""
    try:
        import subprocess
        
        # Start the server
        api_process = subprocess.Popen(
            [
                sys.executable, 
                "-m", "cofoundai.api.app"
            ],
            env=os.environ.copy()
        )
        
        # Wait for the server to start
        logger.info("Starting API server...")
        time.sleep(5)  # Wait for 5 seconds for the server to start
        
        return api_process
    except Exception as e:
        logger.error(f"API server start error: {str(e)}")
        return None

def stop_api_server(api_process):
    """Stop the API server."""
    if api_process:
        try:
            api_process.terminate()
            api_process.wait(timeout=5)
            logger.info("API server stopped")
        except Exception as e:
            logger.error(f"API server stop error: {str(e)}")
            api_process.kill()  # Force kill

async def test_agent_protocol():
    """Test the Agent Protocol API."""
    # API health check
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            logger.info("API health check successful")
        else:
            logger.error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API health check error: {str(e)}")
        return False
    
    # Get agent information
    try:
        response = requests.get(f"{API_URL}/agents/{TEST_AGENT_ID}")
        if response.status_code == 200:
            agent_data = response.json()
            logger.info(f"Agent information: {json.dumps(agent_data, indent=2)}")
        else:
            logger.error(f"Failed to get agent information: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Agent information retrieval error: {str(e)}")
        return False
        
    # Create a thread
    thread_id = None
    try:
        response = requests.post(
            f"{API_URL}/threads",
            json={"thread_id": "test-thread", "metadata": {"test": True}}
        )
        if response.status_code == 200:
            thread = response.json()
            thread_id = thread["thread_id"]
            logger.info(f"Thread created: {thread_id}")
        else:
            logger.error(f"Failed to create thread: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Thread creation error: {str(e)}")
        return False
    
    # Create a run within the thread
    run_id = None
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/runs",
            json={
                "agent_id": TEST_AGENT_ID,
                "input": {"message": "Merhaba, bu bir test mesajıdır."}
            }
        )
        if response.status_code == 200:
            run = response.json()
            run_id = run["run_id"]
            logger.info(f"Run created: {run_id}")
        else:
            logger.error(f"Failed to create run: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Run creation error: {str(e)}")
        return False
    
    # Check run status
    try:
        for _ in range(10):  # Maximum 10 attempts
            response = requests.get(f"{API_URL}/runs/{run_id}")
            if response.status_code == 200:
                run_data = response.json()
                status = run_data.get("status")
                logger.info(f"Run status: {status}")
                
                if status in ["completed", "failed"]:
                    logger.info(f"Run result: {json.dumps(run_data.get('output'), indent=2)}")
                    break
                    
                await asyncio.sleep(1)  # 1 saniye bekle
            else:
                logger.error(f"Failed to get run status: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Run status check error: {str(e)}")
        return False
    
    # Store API testi
    try:
        # Add an item to the store
        response = requests.put(
            f"{API_URL}/store/items",
            json={
                "namespace": ["test"],
                "key": "test_item",
                "value": {"message": "Bu bir test itemıdır."}
            }
        )
        if response.status_code == 200:
            logger.info("Store item added")
        else:
            logger.error(f"Failed to add store item: {response.status_code}")
            return False
            
        # Get an item from the store
        response = requests.get(
            f"{API_URL}/store/items/test_item?namespace=test"
        )
        if response.status_code == 200:
            item = response.json()
            logger.info(f"Store item retrieved: {json.dumps(item, indent=2)}")
        else:
            logger.error(f"Failed to get store item: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Store API test error: {str(e)}")
        return False
    
    logger.info("Agent Protocol test completed successfully!")
    return True

async def run_tests():
    """Run tests."""
    # Start the API server
    api_process = start_api_server()
    if not api_process:
        logger.error("Failed to start API server, tests cancelled")
        return False
    
    try:
        # Test workflow oluştur
        workflow = create_test_workflow()
        if not workflow:
            logger.error("Failed to create test workflow, tests cancelled")
            return False
        
        # Workflow'u API'ye kaydet
        if not register_workflow_as_agent(workflow):
            logger.error("Failed to register workflow with API, tests cancelled")
            return False
        
        # Run the Agent Protocol tests
        test_result = await test_agent_protocol()
        return test_result
    finally:
        # Stop the API server in all cases
        stop_api_server(api_process)

if __name__ == "__main__":
    # Run the tests asynchronously
    try:
        result = asyncio.run(run_tests())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Test run error: {str(e)}")
        sys.exit(1) 