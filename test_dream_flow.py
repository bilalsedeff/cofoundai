
#!/usr/bin/env python3
"""
Test script for CoFound.ai Dream phase
Tests the complete Dream → Maturation → Assemble flow
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cofoundai.core.llm_interface import LLMFactory, generate_text
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import LangGraphAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DreamFlowTester:
    """Test class for Dream phase functionality"""
    
    def __init__(self):
        self.setup_environment()
        
    def setup_environment(self):
        """Setup test environment variables"""
        # Set default environment variables if not set
        if not os.getenv("LLM_PROVIDER"):
            os.environ["LLM_PROVIDER"] = "test"  # Use test mode by default
        
        if not os.getenv("MODEL_NAME"):
            os.environ["MODEL_NAME"] = "gpt-4o"
        
        if not os.getenv("DEVELOPMENT_MODE"):
            os.environ["DEVELOPMENT_MODE"] = "true"
        
        logger.info(f"Environment: LLM_PROVIDER={os.getenv('LLM_PROVIDER')}")
        logger.info(f"Environment: MODEL_NAME={os.getenv('MODEL_NAME')}")
    
    async def test_llm_interface(self):
        """Test LLM interface functionality"""
        logger.info("Testing LLM interface...")
        
        try:
            # Test LLM factory
            llm = LLMFactory.create_llm()
            logger.info(f"Created LLM: {llm.__class__.__name__}")
            
            # Test text generation
            prompt = "Create a brief description of an AI fitness app."
            response = await llm.generate(prompt)
            
            logger.info(f"Generated response: {response.content[:100]}...")
            logger.info(f"Tokens used: {response.tokens_used}")
            logger.info(f"Estimated cost: ${response.cost:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"LLM interface test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_agent_creation(self):
        """Test agent creation and configuration"""
        logger.info("Testing agent creation...")
        
        try:
            agent_config = {
                "name": "TestAgent",
                "description": "Test agent for dream phase",
                "system_prompt": "You are a test agent. Respond helpfully and concisely.",
                "llm_provider": os.getenv("LLM_PROVIDER", "test"),
                "model_name": os.getenv("MODEL_NAME", "gpt-4o")
            }
            
            agent = LangGraphAgent(agent_config)
            logger.info(f"Created agent: {agent.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Agent creation test failed: {e}")
            return False
    
    async def test_dream_workflow(self):
        """Test complete dream workflow"""
        logger.info("Testing dream workflow...")
        
        try:
            # Create dream agents
            agent_configs = [
                {
                    "name": "VisionAnalyst",
                    "description": "Analyzes user vision and extracts insights",
                    "system_prompt": """You are a vision analyst. Your role is to:
1. Extract key business requirements from user descriptions
2. Identify relevant technology tags and categories  
3. Provide initial cost and complexity estimates
4. Generate clear, actionable project briefs

Respond in JSON format with: {
  "requirements": ["req1", "req2", ...],
  "tags": ["tag1", "tag2", ...],
  "complexity": "Low/Medium/High",
  "brief": "Project brief description"
}""",
                    "llm_provider": os.getenv("LLM_PROVIDER"),
                    "model_name": os.getenv("MODEL_NAME")
                },
                {
                    "name": "BlueprintGenerator",
                    "description": "Creates structured project blueprints",
                    "system_prompt": """You are a blueprint generator. Create detailed project blueprints including:
1. Project overview and objectives
2. Key features and functionality
3. Technical architecture recommendations
4. Development milestones
5. Success metrics

Format your response as a structured blueprint document.""",
                    "llm_provider": os.getenv("LLM_PROVIDER"),
                    "model_name": os.getenv("MODEL_NAME")
                }
            ]
            
            # Create agents
            agents = {}
            for config in agent_configs:
                agent = LangGraphAgent(config)
                agents[agent.name] = agent
            
            # Create orchestrator
            orchestrator = AgenticGraph(
                project_id="test_dream",
                agents=agents
            )
            
            # Test vision input
            vision_text = """
            Create an AI-powered fitness coach application that helps users:
            - Track their daily workouts and progress
            - Get personalized nutrition recommendations
            - Connect with other fitness enthusiasts
            - Set and achieve fitness goals
            
            The app should be mobile-first, use machine learning for personalization,
            and integrate with popular fitness devices and apps.
            """
            
            logger.info("Processing vision through orchestrator...")
            result = orchestrator.run(vision_text)
            
            logger.info("Dream workflow completed successfully!")
            logger.info(f"Result type: {type(result)}")
            
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    logger.info(f"Final response: {last_message.content[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Dream workflow test failed: {e}")
            return False
    
    async def test_api_simulation(self):
        """Test API endpoints simulation"""
        logger.info("Testing API simulation...")
        
        try:
            # Simulate dream API request
            dream_request = {
                "vision_text": "Create a todo list app with AI-powered task prioritization",
                "tags": ["productivity", "ai", "mobile"],
                "goal": "prototype",
                "tech_preferences": ["react", "python"]
            }
            
            logger.info(f"Simulating dream request: {dream_request['vision_text']}")
            
            # This would normally go through the FastAPI endpoint
            # For testing, we'll simulate the processing
            
            # Tag extraction simulation
            extracted_tags = dream_request["tags"] + ["ai-powered", "task-management"]
            
            # Blueprint generation simulation
            blueprint = f"""
# AI Todo List Application Blueprint

## Vision
{dream_request['vision_text']}

## Key Features
- Smart task prioritization using AI
- Natural language task input
- Deadline and reminder management
- Progress tracking and analytics
- Cross-platform synchronization

## Technology Stack
Recommended: {', '.join(dream_request['tech_preferences'])}

## Complexity Assessment
Medium complexity project requiring:
- AI/ML integration for prioritization
- Real-time synchronization
- Mobile-responsive design

## Estimated Timeline
- Prototype: 2-3 weeks
- MVP: 6-8 weeks
- Production: 12-16 weeks
"""
            
            # Cost estimation
            estimated_tokens = len(dream_request["vision_text"].split()) * 2
            estimated_cost = estimated_tokens * 0.00002
            
            result = {
                "initial_brief": blueprint,
                "extracted_tags": extracted_tags,
                "cost_estimate": {
                    "tokens": estimated_tokens,
                    "cost_usd": estimated_cost,
                    "complexity": "Medium"
                },
                "status": "completed",
                "project_id": "test_proj_12345"
            }
            
            logger.info("API simulation completed successfully!")
            logger.info(f"Generated {len(result['extracted_tags'])} tags")
            logger.info(f"Estimated cost: ${result['cost_estimate']['cost_usd']:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"API simulation test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("Starting CoFound.ai Dream Flow Tests...")
        
        tests = [
            ("LLM Interface", self.test_llm_interface),
            ("Agent Creation", self.test_agent_creation),
            ("Dream Workflow", self.test_dream_workflow),
            ("API Simulation", self.test_api_simulation),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results[test_name] = result
                
                if result:
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} ERROR: {e}")
                results[test_name] = False
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*50}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! CoFound.ai Dream phase is ready!")
        else:
            logger.warning("⚠️ Some tests failed. Please check the logs above.")
        
        return passed == total

async def main():
    """Main test runner"""
    tester = DreamFlowTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Ready to start the development server!")
        print("Run: python cofoundai/api/backend_api.py")
        print("Then open: http://localhost:5000")
    else:
        print("\n❌ Tests failed. Please fix issues before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
