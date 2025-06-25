"""
LLM Interface for CoFound.ai
Supports OpenAI, Anthropic, and Google Cloud Vertex AI with GPU acceleration
"""

import os
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json

# Import LLM libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google.cloud import aiplatform
    from vertexai.language_models import TextGenerationModel
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Standard response format for all LLM interactions"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseLLM(ABC):
    """Base class for all LLM implementations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "gpt-4o")
        self.api_key = config.get("api_key")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM"""
        pass

    @abstractmethod
    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for prompt and response"""
        pass

class OpenAILLM(BaseLLM):
    """OpenAI GPT implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")

        self.client = openai.AsyncOpenAI(api_key=self.api_key)

        # Token pricing (per 1K tokens)
        self.pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Add system message if provided
            if "system_prompt" in kwargs:
                messages.insert(0, {"role": "system", "content": kwargs["system_prompt"]})

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            cost = self.estimate_cost(prompt, content)

            return LLMResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                cost=cost,
                metadata={"provider": "openai"}
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost based on token usage"""
        model = self.model_name
        if model not in self.pricing:
            model = "gpt-4o"  # Default fallback

        # Rough token estimation (1 token ≈ 4 characters)
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        input_cost = (input_tokens / 1000) * self.pricing[model]["input"]
        output_cost = (output_tokens / 1000) * self.pricing[model]["output"]

        return input_cost + output_cost

class VertexAILLM(BaseLLM):
    """Google Cloud Vertex AI implementation with GPU support"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Vertex AI library not available. Install with: pip install google-cloud-aiplatform")

        self.project_id = config.get("project_id", os.getenv("GOOGLE_CLOUD_PROJECT"))
        self.region = config.get("region", "us-central1")

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.region)

        # Initialize the model
        if "gemini" in self.model_name.lower():
            self.model = GenerativeModel(self.model_name)
        else:
            self.model = TextGenerationModel.from_pretrained(self.model_name)

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Vertex AI"""
        try:
            if hasattr(self.model, 'generate_content'):
                # Gemini model
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": kwargs.get("temperature", self.temperature),
                        "max_output_tokens": kwargs.get("max_tokens", self.max_tokens)
                    }
                )
                content = response.text
            else:
                # PaLM model
                response = self.model.predict(
                    prompt,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_output_tokens=kwargs.get("max_tokens", self.max_tokens)
                )
                content = response.text

            cost = self.estimate_cost(prompt, content)

            return LLMResponse(
                content=content,
                model=self.model_name,
                tokens_used=None,  # Vertex AI doesn't always provide token counts
                cost=cost,
                metadata={"provider": "vertex_ai", "project": self.project_id}
            )

        except Exception as e:
            logger.error(f"Vertex AI error: {e}")
            raise

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for Vertex AI (simplified pricing)"""
        # Rough estimation - actual pricing varies by model
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        # Gemini Pro pricing (approximate)
        input_cost = (input_tokens / 1000) * 0.0005
        output_cost = (output_tokens / 1000) * 0.0015

        return input_cost + output_cost

class AnthropicLLM(BaseLLM):
    """Anthropic Claude implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")

        self.client = Anthropic(api_key=self.api_key)

        # Pricing per 1M tokens
        self.pricing = {
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25}
        }

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self.estimate_cost(prompt, content)

            return LLMResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                cost=cost,
                metadata={"provider": "anthropic"}
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost based on token usage"""
        model = self.model_name
        if model not in self.pricing:
            model = "claude-3-sonnet"  # Default fallback

        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        input_cost = (input_tokens / 1000000) * self.pricing[model]["input"]
        output_cost = (output_tokens / 1000000) * self.pricing[model]["output"]

        return input_cost + output_cost

class TestLLM(BaseLLM):
    """Test LLM implementation for development without API keys"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {"model_name": "test-gpt-4o", "api_key": None})

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock response for testing"""

        # Generate contextual responses based on prompt keywords
        if "fitness" in prompt.lower():
            content = """
# AI Fitness Coach Application Blueprint

## Project Overview
An intelligent fitness coaching application that provides personalized workout plans, nutrition guidance, and progress tracking using AI technology.

## Key Features
- Personalized workout plans based on user goals and fitness level
- AI-powered nutrition recommendations and meal planning
- Progress tracking with visual analytics and insights
- Social features for community support and challenges
- Integration with fitness devices and health apps

## Technical Architecture
**Frontend**: React Native for cross-platform mobile app
**Backend**: Python FastAPI with PostgreSQL database
**AI/ML**: OpenAI GPT-4 for personalized recommendations
**Analytics**: Real-time progress tracking with charts

## Complexity Assessment
Medium complexity - Requires AI integration, real-time data processing, and device integrations.

## Estimated Timeline
- Prototype: 3-4 weeks
- MVP: 8-10 weeks  
- Production: 16-20 weeks
"""

        elif "todo" in prompt.lower() or "task" in prompt.lower():
            content = """
# AI-Powered Todo List Application Blueprint

## Project Overview
Smart task management application with AI-powered prioritization and natural language processing for task creation.

## Key Features
- Natural language task input with AI parsing
- Intelligent task prioritization based on deadlines and importance
- Smart scheduling and time blocking
- Progress analytics and productivity insights
- Cross-device synchronization

## Technical Architecture
**Frontend**: React with Material-UI
**Backend**: Python Flask with SQLite/PostgreSQL
**AI**: OpenAI API for natural language processing
**Sync**: Real-time updates with WebSocket

## Complexity Assessment
Medium complexity - AI integration for NLP and smart prioritization.

## Estimated Timeline
- Prototype: 2-3 weeks
- MVP: 6-8 weeks
- Production: 12-16 weeks
"""

        else:
            content = f"""
# Project Blueprint

Based on your vision: "{prompt[:100]}..."

## Project Analysis
This appears to be a software development project requiring careful planning and execution.

## Key Requirements
- Modern technology stack
- User-focused design
- Scalable architecture
- Quality testing and documentation

## Recommended Approach
1. Requirements analysis and planning
2. Architecture design and prototyping
3. Iterative development with testing
4. Deployment and monitoring

## Complexity Assessment
Medium complexity project requiring professional development practices.

## Next Steps
- Detailed requirements gathering
- Technology stack selection
- Development timeline planning
- Resource allocation and team formation
"""

        return LLMResponse(
            content=content.strip(),
            model="test-gpt-4o",
            tokens_used=len(prompt.split()) * 3,
            cost=0.0001,
            metadata={"mode": "test", "timestamp": "2024-01-26"}
        )

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        return 0.001  # Mock cost

class LLMFactory:
    """Factory class for creating LLM instances"""

    @staticmethod
    def create_llm(provider: str = None, config: Dict[str, Any] = None) -> BaseLLM:
        """Create LLM instance based on provider"""

        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "openai")

        if config is None:
            config = LLMFactory.get_default_config(provider)

        provider = provider.lower()

        # Check if in development/test mode
        if provider == "test" or os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
            logger.info("Using test LLM (no API key required)")
            return TestLLM(config)

        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not available. Install with: pip install openai")
            api_key = config.get("api_key")
            if not api_key:
                logger.warning("OpenAI API key not found, falling back to test mode")
                return TestLLM(config)
            return OpenAILLM(config)

        elif provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic library not available. Install with: pip install anthropic")
            api_key = config.get("api_key")
            if not api_key:
                logger.warning("Anthropic API key not found, falling back to test mode")
                return TestLLM(config)
            return AnthropicLLM(config)

        elif provider == "vertex_ai" or provider == "google":
            if not VERTEX_AI_AVAILABLE:
                raise ImportError("Vertex AI library not available. Install with: pip install google-cloud-aiplatform")
            project_id = config.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                logger.warning("Google Cloud Project ID not found, falling back to test mode")
                return TestLLM(config)
            return VertexAILLM(config)

        elif provider == "test":
            return TestLLM(config)

        else:
            logger.warning(f"Unsupported LLM provider: {provider}, falling back to test mode")
            return TestLLM(config)

    @staticmethod
    def get_default_config(provider: str) -> Dict[str, Any]:
        """Get default configuration for provider"""

        base_config = {
            "temperature": 0.7,
            "max_tokens": 4000
        }

        if provider == "openai":
            base_config.update({
                "model_name": os.getenv("MODEL_NAME", "gpt-4o"),
                "api_key": os.getenv("OPENAI_API_KEY")
            })
        elif provider == "anthropic":
            base_config.update({
                "model_name": os.getenv("MODEL_NAME", "claude-3-sonnet-20240229"),
                "api_key": os.getenv("ANTHROPIC_API_KEY")
            })
        elif provider in ["vertex_ai", "google"]:
            base_config.update({
                "model_name": os.getenv("MODEL_NAME", "gemini-pro"),
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "region": os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
            })
        elif provider == "test":
            base_config.update({
                "model_name": "test-model"
            })

        return base_config

# Convenience function for quick LLM usage
async def generate_text(prompt: str, provider: str = None, **kwargs) -> str:
    """Quick text generation function"""
    llm = LLMFactory.create_llm(provider)
    response = await llm.generate(prompt, **kwargs)
    return response.content

# Export main classes
__all__ = [
    "BaseLLM",
    "OpenAILLM", 
    "VertexAILLM",
    "AnthropicLLM",
    "TestLLM",
    "LLMFactory",
    "LLMResponse",
    "generate_text"
]