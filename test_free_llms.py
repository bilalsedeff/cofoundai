
#!/usr/bin/env python3
"""
Test script for free LLM alternatives in CoFound.ai
Tests HuggingFace and local models without API costs
"""

import os
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cofoundai.core.llm_interface import LLMFactory

async def test_huggingface_llm():
    """Test HuggingFace free tier models"""
    print("\n🤗 Testing HuggingFace Free Models...")
    
    # Set environment for HuggingFace
    os.environ["LLM_PROVIDER"] = "huggingface"
    os.environ["MODEL_NAME"] = "microsoft/DialoGPT-medium"
    os.environ["HUGGINGFACE_API_KEY"] = "hf_demo"  # Demo key
    
    try:
        llm = LLMFactory.create_llm("huggingface")
        
        prompt = "Create a simple Python function that calculates fibonacci numbers:"
        response = await llm.generate(prompt)
        
        print(f"✅ HuggingFace Model: {response.model}")
        print(f"✅ Response: {response.content[:200]}...")
        print(f"✅ Cost: ${response.cost}")
        
    except Exception as e:
        print(f"❌ HuggingFace test failed: {e}")

async def test_local_models():
    """Test local model fallback"""
    print("\n🏠 Testing Local Model Fallback...")
    
    # Test without API keys - should fallback to test mode
    os.environ["LLM_PROVIDER"] = "test"
    
    try:
        llm = LLMFactory.create_llm("test")
        
        prompt = "Create a web application for task management"
        response = await llm.generate(prompt)
        
        print(f"✅ Test Model: {response.model}")
        print(f"✅ Response: {response.content[:200]}...")
        print(f"✅ Cost: ${response.cost}")
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")

async def test_openai_with_key():
    """Test OpenAI if API key is provided"""
    print("\n🔑 Testing OpenAI (if API key provided)...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⏭️  Skipping OpenAI test - no API key provided")
        print("   Set OPENAI_API_KEY environment variable to test")
        return
    
    try:
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["MODEL_NAME"] = "gpt-4o-mini"  # Cheapest GPT-4 model
        
        llm = LLMFactory.create_llm("openai")
        
        prompt = "Explain how to use Google Cloud Compute Engine for hosting a Python web app"
        response = await llm.generate(prompt)
        
        print(f"✅ OpenAI Model: {response.model}")
        print(f"✅ Response: {response.content[:200]}...")
        print(f"✅ Tokens: {response.tokens_used}")
        print(f"✅ Estimated Cost: ${response.cost:.4f}")
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")

async def main():
    """Run all LLM tests"""
    print("🧪 CoFound.ai Free LLM Alternatives Test")
    print("=" * 50)
    
    # Test free alternatives
    await test_local_models()
    await test_huggingface_llm() 
    await test_openai_with_key()
    
    print("\n" + "=" * 50)
    print("💡 Setup Instructions:")
    print("1. For OpenAI: Set OPENAI_API_KEY in .env file")
    print("2. For HuggingFace: Get free API key from https://huggingface.co/settings/tokens")
    print("3. For local models: Install Ollama (completely free)")
    print("4. Test mode works without any API keys")

if __name__ == "__main__":
    asyncio.run(main())
