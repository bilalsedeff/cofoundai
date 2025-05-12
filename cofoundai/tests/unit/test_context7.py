#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Context7Adapter Test Script

This script tests the Context7Adapter tool to verify proper functionality.
It simulates how agents would use the Context7 integration to access documentation.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

from cofoundai.tools import Context7Adapter
from cofoundai.utils.logger import get_logger, system_logger

# Set up logger
logger = system_logger

def run_context7_tests():
    """Run tests for Context7Adapter functionality."""
    
    print("Starting Context7Adapter tests...\n")
    
    # Create a temporary directory for caching
    cache_dir = Path(tempfile.mkdtemp(prefix="cofoundai_context7_test_"))
    print(f"Created cache directory: {cache_dir}")
    
    try:
        # Initialize Context7Adapter
        adapter = Context7Adapter(cache_dir=str(cache_dir))
        print("Initialized Context7Adapter")
        
        # Test library ID resolution
        libraries_to_test = ["nextjs", "react", "fastapi", "tensorflow", "unknown_library"]
        
        for lib in libraries_to_test:
            lib_id = adapter.resolve_library_id(lib)
            if lib_id:
                print(f"Successfully resolved '{lib}' to '{lib_id}'")
            else:
                print(f"Could not resolve '{lib}' (expected for unknown libraries)")
        
        # Test documentation retrieval
        nextjs_id = adapter.resolve_library_id("nextjs")
        
        # Get general documentation
        docs = adapter.get_library_docs(nextjs_id)
        print(f"Retrieved general Next.js documentation: {len(docs['content'])} characters")
        
        # Get topic-specific documentation
        routing_docs = adapter.get_library_docs(nextjs_id, topic="routing")
        print(f"Retrieved Next.js routing documentation: {len(routing_docs['content'])} characters")
        
        # Test documentation search
        search_results = adapter.search_documentation("dynamic routes", [nextjs_id])
        print(f"Search found {len(search_results['results'])} results for 'dynamic routes'")
        
        # Test caching - second retrieval should be from cache
        print("Retrieving documentation again (should be from cache)...")
        before_time = import_time()
        docs_again = adapter.get_library_docs(nextjs_id, topic="routing")
        after_time = import_time()
        
        # Verify the content is the same
        assert docs_again['content'] == routing_docs['content'], "Cached content should match original"
        print(f"Cache retrieval took {(after_time - before_time)*1000:.2f}ms")
        
        # Test cache clearing
        adapter.clear_cache()
        print("Cache cleared successfully")
        
        # Verify cache files are gone
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 0, "Cache directory should be empty after clearing"
        
        print("\nAll Context7Adapter tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up - remove test directory
        try:
            shutil.rmtree(cache_dir)
            print(f"Cleaned up cache directory: {cache_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up cache directory due to: {str(e)}")
            print(f"You may need to manually remove: {cache_dir}")

def import_time():
    """Helper function to get current time for performance measurement."""
    import time
    return time.time()

def main():
    """Main entry point for the test script."""
    print("Context7Adapter Test Script")
    print("==========================\n")
    
    success = run_context7_tests()
    
    if success:
        print("\nAll tests completed successfully!")
        return 0
    else:
        print("\nTests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 