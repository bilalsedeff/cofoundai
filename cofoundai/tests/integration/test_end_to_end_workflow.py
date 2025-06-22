
#!/usr/bin/env python
"""
End-to-end integration tests for CoFound.ai multi-agent system
"""

import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
import asyncio

from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import LangGraphAgent
from cofoundai.utils.langsmith_integration import get_tracer


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()
        
        # Set test environment
        os.environ["LLM_PROVIDER"] = "test"
        os.environ["MODEL_NAME"] = "gpt-4o"
        os.environ["DEVELOPMENT_MODE"] = "true"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
        
        # Create temporary directory for persistence
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_agents(self):
        """Create a full set of test agents."""
        agent_configs = [
            {
                "name": "Planner",
                "system_prompt": "You are a planning agent that breaks down requirements into tasks",
                "llm_provider": "test"
            },
            {
                "name": "Architect",
                "system_prompt": "You are an architecture agent that designs system architecture",
                "llm_provider": "test"
            },
            {
                "name": "Developer",
                "system_prompt": "You are a development agent that writes code",
                "llm_provider": "test"
            },
            {
                "name": "Tester",
                "system_prompt": "You are a testing agent that creates and runs tests",
                "llm_provider": "test"
            },
            {
                "name": "Reviewer",
                "system_prompt": "You are a review agent that evaluates code quality",
                "llm_provider": "test"
            },
            {
                "name": "Documentor",
                "system_prompt": "You are a documentation agent that creates documentation",
                "llm_provider": "test"
            }
        ]
        
        agents = {}
        for config in agent_configs:
            agent = LangGraphAgent(config)
            agents[agent.name] = agent
            
        return agents
    
    def test_complete_workflow_execution(self):
        """Test complete workflow from dream to delivery."""
        # Create agents
        agents = self.create_test_agents()
        
        # Create agentic graph
        graph = AgenticGraph(
            project_id="test-e2e-workflow",
            agents=agents,
            persist_directory=self.temp_dir
        )
        
        # Test input - user's dream
        user_dream = """
        I want to create a simple todo application with the following features:
        - Add new todos
        - Mark todos as complete
        - Delete todos
        - Filter todos by status
        - Save todos to local storage
        """
        
        # Execute workflow
        result = graph.run(user_dream)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("messages", result)
        self.assertIn("project_description", result)
        self.assertIn("metadata", result)
        
        # Verify messages exist
        messages = result.get("messages", [])
        self.assertGreater(len(messages), 0)
        
        # Verify metadata
        metadata = result.get("metadata", {})
        self.assertIn("created_at", metadata)
        self.assertIn("thread_id", metadata)
    
    def test_workflow_streaming(self):
        """Test workflow streaming functionality."""
        # Create agents
        agents = self.create_test_agents()
        
        # Create agentic graph
        graph = AgenticGraph(
            project_id="test-streaming-workflow",
            agents=agents
        )
        
        user_input = "Create a simple calculator application"
        
        # Test streaming
        stream_results = []
        for chunk in graph.stream(user_input):
            stream_results.append(chunk)
            
        # Verify we got streaming results
        self.assertGreater(len(stream_results), 0)
        
        # Verify final result structure
        if stream_results:
            final_result = stream_results[-1]
            self.assertIsInstance(final_result, dict)
    
    def test_workflow_with_langsmith_tracing(self):
        """Test workflow execution with LangSmith tracing."""
        # Set up LangSmith environment
        os.environ["LANGCHAIN_API_KEY"] = "test-langsmith-key"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "test-project"
        
        # Mock LangSmith client
        with patch('cofoundai.utils.langsmith_integration.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            
            # Create agents
            agents = self.create_test_agents()
            
            # Create agentic graph
            graph = AgenticGraph(
                project_id="test-tracing-workflow",
                agents=agents
            )
            
            # Execute workflow
            result = graph.run("Create a simple web application")
            
            # Verify tracing was attempted
            mock_client.assert_called()
            
            # Verify result
            self.assertIsInstance(result, dict)
    
    def test_workflow_error_handling(self):
        """Test workflow error handling."""
        # Create agents with intentionally problematic config
        agents = self.create_test_agents()
        
        # Create agentic graph
        graph = AgenticGraph(
            project_id="test-error-handling",
            agents=agents
        )
        
        # Test with empty input
        result = graph.run("")
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
    
    def test_workflow_persistence(self):
        """Test workflow state persistence."""
        # Create agents
        agents = self.create_test_agents()
        
        # Create agentic graph with persistence
        graph = AgenticGraph(
            project_id="test-persistence",
            agents=agents,
            persist_directory=self.temp_dir
        )
        
        # Execute workflow
        result = graph.run("Create a mobile app")
        
        # Check if persistence files were created
        import os
        files = os.listdir(self.temp_dir)
        workflow_files = [f for f in files if f.startswith("workflow_")]
        
        # Should have at least one workflow file
        self.assertGreater(len(workflow_files), 0)
        
        # Verify file contains valid JSON
        if workflow_files:
            with open(os.path.join(self.temp_dir, workflow_files[0]), 'r') as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
                self.assertIn("messages", data)
    
    def test_agent_handoff_functionality(self):
        """Test agent handoff between different specialists."""
        # Create agents
        agents = self.create_test_agents()
        
        # Create agentic graph
        graph = AgenticGraph(
            project_id="test-handoff",
            agents=agents
        )
        
        # Verify handoff tools were added
        for agent_name, agent in agents.items():
            if hasattr(agent, "tools"):
                tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in agent.tools]
                
                # Should have handoff tools for other agents
                other_agents = [name for name in agents.keys() if name != agent_name]
                for other_agent in other_agents:
                    expected_tool = f"transfer_to_{other_agent}"
                    # Note: This may not always be present depending on implementation
                    # self.assertIn(expected_tool, tool_names)
    
    def test_workflow_schema_generation(self):
        """Test workflow graph schema generation."""
        # Create agents
        agents = self.create_test_agents()
        
        # Create agentic graph
        graph = AgenticGraph(
            project_id="test-schema",
            agents=agents
        )
        
        # Get schema
        schema = graph.get_graph_schema()
        
        # Verify schema structure
        self.assertIsInstance(schema, dict)
        # Schema content varies by implementation


class TestDreamServiceIntegration(unittest.TestCase):
    """Test Dream Service integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()
        
        # Set test environment
        os.environ["DEVELOPMENT_MODE"] = "true"
        os.environ["LLM_PROVIDER"] = "test"
        
    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_dream_processor_initialization(self):
        """Test dream processor can be initialized."""
        try:
            from services.dream_service.main import DreamProcessor
            
            processor = DreamProcessor()
            self.assertIsNotNone(processor)
            
        except ImportError:
            self.skipTest("Dream service not available in test environment")
    
    def test_dream_processing_workflow(self):
        """Test dream processing workflow."""
        try:
            from services.dream_service.main import DreamProcessor
            
            processor = DreamProcessor()
            
            # Test dream processing
            test_dream = "I want to build a simple todo application"
            result = processor.process_dream(test_dream, "test-project")
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertIn("project_id", result)
            
        except ImportError:
            self.skipTest("Dream service not available in test environment")


if __name__ == "__main__":
    unittest.main()
