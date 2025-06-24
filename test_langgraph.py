
#!/usr/bin/env python3
"""
CoFound.ai LangGraph Test Script

This script tests the LangGraph multi-agent system functionality.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import (
    PlannerLangGraphAgent, 
    ArchitectLangGraphAgent, 
    DeveloperLangGraphAgent
)

def test_basic_workflow():
    """Test basic multi-agent workflow."""
    print("🚀 Testing CoFound.ai LangGraph Multi-Agent System")
    print("=" * 60)
    
    # Create agents
    print("1. Creating specialized agents...")
    
    planner_config = {
        "name": "Planner",
        "llm_provider": "test",
        "model_name": "gpt-4o"
    }
    planner = PlannerLangGraphAgent(planner_config)
    print(f"   ✅ Created {planner.name}")
    
    architect_config = {
        "name": "Architect", 
        "llm_provider": "test",
        "model_name": "gpt-4o"
    }
    architect = ArchitectLangGraphAgent(architect_config)
    print(f"   ✅ Created {architect.name}")
    
    developer_config = {
        "name": "Developer",
        "llm_provider": "test", 
        "model_name": "gpt-4o"
    }
    developer = DeveloperLangGraphAgent(developer_config)
    print(f"   ✅ Created {developer.name}")
    
    # Create agent graph
    print("\n2. Initializing AgenticGraph...")
    agents = {
        "Planner": planner,
        "Architect": architect,
        "Developer": developer
    }
    
    graph = AgenticGraph(
        project_id="test_workflow_001",
        agents=agents,
        persist_directory="demos/projects"
    )
    print(f"   ✅ Graph initialized with {len(agents)} agents")
    
    # Test workflow
    print("\n3. Running test workflow...")
    test_input = "Create a simple task management web application with user authentication"
    
    try:
        result = graph.run(test_input)
        print(f"   ✅ Workflow completed successfully")
        print(f"   📊 Status: {result.get('status', 'unknown')}")
        print(f"   📝 Messages: {len(result.get('messages', []))}")
        
        # Display results
        if result.get('messages'):
            print("\n4. Workflow Results:")
            print("-" * 40)
            for i, msg in enumerate(result['messages'][-3:], 1):
                print(f"   Message {i}: {msg.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow failed: {str(e)}")
        return False

def test_graph_schema():
    """Test graph schema generation."""
    print("\n5. Testing graph schema...")
    
    try:
        # Create minimal graph
        planner = PlannerLangGraphAgent({"name": "Planner", "llm_provider": "test"})
        graph = AgenticGraph("schema_test", agents={"Planner": planner})
        
        schema = graph.get_graph_schema()
        if schema and "status" not in schema:
            print("   ✅ Graph schema generated successfully")
            return True
        else:
            print(f"   ⚠️  Graph schema issue: {schema}")
            return False
            
    except Exception as e:
        print(f"   ❌ Schema test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("CoFound.ai LangGraph System Test")
    print("================================\n")
    
    # Run tests
    tests = [
        ("Basic Workflow", test_basic_workflow),
        ("Graph Schema", test_graph_schema)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("Test Summary:")
    print("=" * 30)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LangGraph system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
