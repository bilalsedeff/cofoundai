
#!/usr/bin/env python
"""
Test runner for CoFound.ai project
"""

import sys
import os
import subprocess
import unittest

def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    
    # Set test environment
    os.environ["DEVELOPMENT_MODE"] = "true"
    os.environ["LLM_PROVIDER"] = "test"
    
    # Run unit tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "cofoundai/tests/unit/", 
        "-v", "--tb=short"
    ], cwd=".")
    
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    
    # Set test environment
    os.environ["DEVELOPMENT_MODE"] = "true"
    os.environ["LLM_PROVIDER"] = "test"
    
    # Run integration tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "cofoundai/tests/integration/", 
        "-v", "--tb=short"
    ], cwd=".")
    
    return result.returncode == 0

def run_all_tests():
    """Run all tests."""
    print("Running all CoFound.ai tests...")
    
    # Set test environment
    os.environ["DEVELOPMENT_MODE"] = "true"
    os.environ["LLM_PROVIDER"] = "test"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
    
    success = True
    
    # Run unit tests
    if not run_unit_tests():
        success = False
        print("❌ Unit tests failed!")
    else:
        print("✅ Unit tests passed!")
    
    # Run integration tests
    if not run_integration_tests():
        success = False
        print("❌ Integration tests failed!")
    else:
        print("✅ Integration tests passed!")
    
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "unit":
            success = run_unit_tests()
        elif test_type == "integration":
            success = run_integration_tests()
        elif test_type == "all":
            success = run_all_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python run_tests.py [unit|integration|all]")
            sys.exit(1)
    else:
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
