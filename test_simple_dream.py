
#!/usr/bin/env python3
"""
Simple test for Dream phase without complex dependencies
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for test mode
os.environ["LLM_PROVIDER"] = "test"
os.environ["DEVELOPMENT_MODE"] = "true"

from cofoundai.core.llm_interface import LLMFactory, LLMResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dream_basic():
    """Test basic dream functionality"""
    
    print("🚀 CoFound.ai Dream Phase Test")
    print("=" * 40)
    
    try:
        # Test LLM creation
        print("1. Creating LLM instance...")
        llm = LLMFactory.create_llm()
        print(f"✅ Created: {llm.__class__.__name__}")
        
        # Test vision processing
        print("\n2. Processing user vision...")
        vision_text = """
        Create an AI-powered fitness coach application that helps users:
        - Track their daily workouts and progress
        - Get personalized nutrition recommendations  
        - Connect with other fitness enthusiasts
        - Set and achieve fitness goals
        
        The app should be mobile-first, use machine learning for personalization,
        and integrate with popular fitness devices and apps.
        """
        
        response = await llm.generate(vision_text)
        print(f"✅ Generated {response.tokens_used} tokens")
        print(f"💰 Cost: ${response.cost:.4f}")
        
        # Display result
        print("\n3. Generated Blueprint:")
        print("-" * 40)
        print(response.content)
        print("-" * 40)
        
        print("\n🎉 Dream phase test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    success = await test_dream_basic()
    
    if success:
        print("\n✅ Ready for next steps!")
        print("Run: python cofoundai/api/backend_api.py")
        print("Then: open http://localhost:5000")
    else:
        print("\n❌ Please fix issues before proceeding")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
