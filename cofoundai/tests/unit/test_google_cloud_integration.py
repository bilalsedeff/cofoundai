#!/usr/bin/env python
"""
Unit tests for Google Cloud and LLM integration
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from cofoundai.core.llm_interface import LLMFactory, OpenAILLM
from cofoundai.utils.langsmith_integration import LangSmithTracer, get_tracer
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import LangGraphAgent


class TestGoogleCloudIntegration(unittest.TestCase):
    """Test Google Cloud integration."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()

        # Set test environment variables
        os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
        os.environ["GOOGLE_API_KEY"] = "test-api-key"
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["MODEL_NAME"] = "gpt-4o"
        os.environ["OPENAI_API_KEY"] = "test-openai-key"

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_llm_factory_creates_gpt4o(self):
        """Test LLM factory creates GPT-4o by default."""
        llm = LLMFactory.create_llm(provider="openai")

        self.assertIsInstance(llm, OpenAILLM)
        self.assertEqual(llm.model_name, "gpt-4o")
        self.assertEqual(llm.api_key, "test-openai-key")

    def test_openai_llm_initialization(self):
        """Test OpenAI LLM initialization with Google Cloud config."""
        config = {
            "model_name": "gpt-4o",
            "api_key": "test-key"
        }

        llm = OpenAILLM(config)

        self.assertEqual(llm.model_name, "gpt-4o")
        self.assertEqual(llm.api_key, "test-key")

    @patch('langsmith.Client')
    def test_langsmith_tracer_initialization(self, mock_client):
        """Test LangSmith tracer initialization."""
        os.environ["LANGCHAIN_API_KEY"] = "test-langsmith-key"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "test-project"

        tracer = LangSmithTracer()

        self.assertTrue(tracer.enabled)
        mock_client.assert_called_once()

    def test_langsmith_tracer_disabled_without_config(self):
        """Test LangSmith tracer is disabled without proper config."""
        # Remove LangSmith config
        if "LANGCHAIN_API_KEY" in os.environ:
            del os.environ["LANGCHAIN_API_KEY"]
        if "LANGCHAIN_TRACING_V2" in os.environ:
            del os.environ["LANGCHAIN_TRACING_V2"]

        tracer = LangSmithTracer()

        self.assertFalse(tracer.enabled)
        self.assertIsNone(tracer.client)

    @patch('langsmith.Client')
    def test_workflow_session_creation(self, mock_client):
        """Test workflow session creation."""
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        tracer = LangSmithTracer()
        session_id = tracer.start_workflow_session("test-project", "Test input")

        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("workflow_test-project_"))
        mock_client_instance.create_session.assert_called_once()


class TestLangGraphAgentIntegration(unittest.TestCase):
    """Test LangGraph agent integration with LLM."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()

        # Set test environment
        os.environ["LLM_PROVIDER"] = "test"
        os.environ["MODEL_NAME"] = "gpt-4o"

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_langgraph_agent_creation(self):
        """Test LangGraph agent creation with GPT-4o config."""
        config = {
            "name": "TestAgent",
            "description": "Test agent",
            "system_prompt": "You are a test agent",
            "llm_provider": "test",
            "model_name": "gpt-4o"
        }

        agent = LangGraphAgent(config)

        self.assertEqual(agent.name, "TestAgent")
        self.assertEqual(agent.description, "Test agent")
        self.assertIsNotNone(agent.llm)

    def test_agentic_graph_creation(self):
        """Test AgenticGraph creation with agents."""
        # Create test agents
        agent_configs = [
            {
                "name": "Planner",
                "system_prompt": "You are a planning agent",
                "llm_provider": "test"
            },
            {
                "name": "Developer", 
                "system_prompt": "You are a development agent",
                "llm_provider": "test"
            }
        ]

        agents = {}
        for config in agent_configs:
            agent = LangGraphAgent(config)
            agents[agent.name] = agent

        # Create graph
        graph = AgenticGraph(
            project_id="test-project",
            agents=agents
        )

        self.assertEqual(graph.project_id, "test-project")
        self.assertEqual(len(graph.agents), 2)
        self.assertIn("Planner", graph.agents)
        self.assertIn("Developer", graph.agents)


class TestMultiAgentWorkflow(unittest.TestCase):
    """Test multi-agent workflow integration."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()

        # Set test environment
        os.environ["LLM_PROVIDER"] = "test"
        os.environ["MODEL_NAME"] = "gpt-4o"
        os.environ["DEVELOPMENT_MODE"] = "true"

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_workflow_execution(self):
        """Test basic workflow execution."""
        # Create agents
        agent_configs = [
            {
                "name": "Planner",
                "system_prompt": "You are a planning agent",
                "llm_provider": "test"
            }
        ]

        agents = {}
        for config in agent_configs:
            agent = LangGraphAgent(config)
            agents[agent.name] = agent

        # Create and run workflow
        graph = AgenticGraph(
            project_id="test-workflow",
            agents=agents
        )

        result = graph.run("Create a simple web application")

        self.assertIsInstance(result, dict)
        self.assertIn("messages", result)


if __name__ == "__main__":
    unittest.main()