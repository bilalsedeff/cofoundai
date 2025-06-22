"""
CoFound.ai LLM Interface

This module provides a unified interface for interacting with different LLM providers.
It enables easy switching between models and provides a test mode for development without LLM dependency.
"""

from typing import Dict, Any, List, Optional, Union, Type
from abc import ABC, abstractmethod
import os
import json
import logging
from datetime import datetime

# Import the config loader
from cofoundai.core.config_loader import config_loader

# Set up logging
logger = logging.getLogger(__name__)


class LLMResponse:
    """Standardized response object from LLM calls."""

    def __init__(
        self, 
        content: str, 
        role: str = "assistant", 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an LLM response.

        Args:
            content: Text content of the response
            role: Role of the responder (default: "assistant")
            metadata: Additional information about the response
        """
        self.content = content
        self.role = role
        self.metadata = metadata or {}
        self.timestamp = datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMResponse":
        """Create from dictionary."""
        response = cls(
            content=data["content"],
            role=data.get("role", "assistant"),
            metadata=data.get("metadata", {})
        )
        response.timestamp = data.get("timestamp", response.timestamp)
        return response

    def __str__(self) -> str:
        """String representation."""
        return f"LLMResponse(role={self.role}, content={self.content[:50]}{'...' if len(self.content) > 50 else ''})"


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM.

        Args:
            config: Configuration settings
        """
        self.config = config or {}
        self.model_name = self.config.get("model_name", "default")

    @abstractmethod
    def generate(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message for chat models
            messages: Optional chat history
            temperature: Optional temperature override

        Returns:
            Generated response
        """
        pass

    def is_available(self) -> bool:
        """Check if the LLM is available."""
        try:
            self.generate("Hello, are you available?")
            return True
        except Exception as e:
            logger.warning(f"LLM {self.model_name} is not available: {str(e)}")
            return False


class TestLLM(BaseLLM):
    """Mock LLM for testing without actual API calls."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the test LLM."""
        super().__init__(config)
        self.model_name = config.get("model_name", "test-model")
        self.responses = config.get("responses", {})

    def generate(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate mock responses based on patterns in the prompt.

        Args:
            prompt: Prompt text
            system_message: Ignored in test mode
            messages: Ignored in test mode
            temperature: Ignored in test mode

        Returns:
            Mock response
        """
        # Try to find a matching response from predefined patterns
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return LLMResponse(content=response)

        # Return a generic test response
        return LLMResponse(
            content=f"This is a test response to: {prompt[:50]}...",
            metadata={"test_mode": True}
        )


class AnthropicLLM(BaseLLM):
    """Interface for Anthropic's Claude models."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Anthropic LLM interface."""
        super().__init__(config)
        self.model_name = config.get("model_name", "claude-3-sonnet-20240229")

        # Get API key from config or from config_loader
        self.api_key = config.get("api_key") or config_loader.get_env("ANTHROPIC_API_KEY")

        if not self.api_key:
            logger.warning("Anthropic API key not found. Set ANTHROPIC_API_KEY in .env file or environment.")

    def generate(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate a response using Anthropic Claude.

        Args:
            prompt: The prompt to send to Claude
            system_message: Optional system message
            messages: Optional chat history
            temperature: Optional temperature setting (0-1)

        Returns:
            Generated response
        """
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        try:
            from langchain_anthropic import ChatAnthropic

            # Initialize the model
            llm = ChatAnthropic(
                model=self.model_name,
                anthropic_api_key=self.api_key,
                temperature=temperature or self.config.get("temperature", 0.7)
            )

            # Prepare messages
            chat_messages = []

            # Add system message if provided
            if system_message:
                chat_messages.append({"role": "system", "content": system_message})

            # Add chat history if provided
            if messages:
                chat_messages.extend(messages)

            # Add the current prompt
            chat_messages.append({"role": "user", "content": prompt})

            # Generate response
            response = llm.invoke(chat_messages)

            return LLMResponse(
                content=response.content,
                metadata={"model": self.model_name}
            )

        except ImportError:
            logger.error("langchain_anthropic not installed. Run: pip install langchain_anthropic")
            raise
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise


class OpenAILLM(BaseLLM):
    """Interface for OpenAI models."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the OpenAI LLM interface."""
        super().__init__(config)
        self.model_name = config.get("model_name", "gpt-4o")

        # Get API key from config or from config_loader
        self.api_key = config.get("api_key") or config_loader.get_env("OPENAI_API_KEY")

        # Google Cloud integration
        self.google_cloud_project = config_loader.get_env("GOOGLE_CLOUD_PROJECT")
        self.google_api_key = config_loader.get_env("GOOGLE_API_KEY")

        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY in .env file or environment.")

    def generate(
        self, 
        prompt: str,
        system_message: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate a response using OpenAI models.

        Args:
            prompt: The prompt to send to GPT
            system_message: Optional system message
            messages: Optional chat history
            temperature: Optional temperature setting (0-2)

        Returns:
            Generated response
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        try:
            from langchain_openai import ChatOpenAI

            # Initialize the model
            llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                temperature=temperature or self.config.get("temperature", 0.7)
            )

            # Prepare messages
            chat_messages = []

            # Add system message if provided
            if system_message:
                chat_messages.append({"role": "system", "content": system_message})

            # Add chat history if provided
            if messages:
                chat_messages.extend(messages)

            # Add the current prompt
            chat_messages.append({"role": "user", "content": prompt})

            # Generate response
            response = llm.invoke(chat_messages)

            return LLMResponse(
                content=response.content,
                metadata={"model": self.model_name}
            )

        except ImportError:
            logger.error("langchain_openai not installed. Run: pip install langchain_openai")
            raise
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise


class LLMFactory:
    """Factory for creating LLM instances."""

    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        use_dummy: bool = False
    ) -> BaseLLM:
        """
        Create an LLM instance.

        Args:
            provider: LLM provider (test, anthropic, openai)
            model_name: Name of the model to use
            config: Additional configuration
            use_dummy: Force using test/dummy LLM

        Returns:
            LLM instance
        """
        config = config or {}
        if model_name:
            config["model_name"] = model_name

        # If dummy testing is forced, use TestLLM
        if use_dummy or config_loader.is_dummy_test_mode():
            logger.info("Using dummy/test LLM as specified in configuration or CLI")
            return TestLLM(config)

        # Use provider from parameter, fallback to config or environment
        provider = provider or config_loader.get_llm_provider()
        provider = provider.lower()

        if provider == "test":
            return TestLLM(config)
        elif provider == "anthropic":
            # Merge config with any config from config_loader
            anthropic_config = config_loader.get_llm_config()
            if config:
                anthropic_config.update(config)
            return AnthropicLLM(anthropic_config)
        elif provider == "openai":
            # Merge config with any config from config_loader
            openai_config = config_loader.get_llm_config()
            if config:
                openai_config.update(config)
            # Default to GPT-4o
            if "model_name" not in openai_config:
                openai_config["model_name"] = "gpt-4o"
            return OpenAILLM(openai_config)
        else:
            logger.warning(f"Unsupported LLM provider: {provider}, falling back to test mode")
            return TestLLM(config)