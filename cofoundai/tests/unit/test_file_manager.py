#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FileManager Test Script

This script tests the FileManager tool to verify proper functionality.
It simulates how agents would use the file system operations.
"""

import os
import sys
import json
from pathlib import Path
import tempfile
import shutil

from cofoundai.tools import FileManager
from cofoundai.utils.logger import get_logger, system_logger

# Set up logger
logger = system_logger

def run_file_manager_tests():
    """Run tests for FileManager functionality."""
    
    print("Starting FileManager tests...\n")
    
    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="cofoundai_test_"))
    print(f"Created test directory: {test_dir}")
    
    try:
        # Initialize FileManager with test directory
        file_manager = FileManager(workspace_dir=str(test_dir))
        print("Initialized FileManager")
        
        # Test creating directories
        code_dir = "src/main"
        file_manager.create_directory(code_dir)
        print(f"Created directory: {code_dir}")
        
        # Test writing files
        test_code = """
def hello_world():
    print("Hello, CoFound.ai!")
    
if __name__ == "__main__":
    hello_world()
"""
        code_file = f"{code_dir}/app.py"
        file_manager.write_file(code_file, test_code)
        print(f"Created file: {code_file}")
        
        # Test reading files
        read_content = file_manager.read_file(code_file)
        assert test_code == read_content
        print(f"Successfully read file: {code_file}")
        
        # Test listing directory
        dir_content = file_manager.list_directory(code_dir)
        assert len(dir_content) == 1
        assert dir_content[0]["name"] == "app.py"
        print(f"Successfully listed directory: {code_dir}")
        
        # Test JSON read/write
        config_data = {
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test project for FileManager"
        }
        config_file = "config.json"
        file_manager.write_json(config_file, config_data)
        print(f"Created JSON file: {config_file}")
        
        # Test reading JSON
        read_config = file_manager.read_json(config_file)
        assert read_config["name"] == config_data["name"]
        assert read_config["version"] == config_data["version"]
        print(f"Successfully read JSON file: {config_file}")
        
        # Test YAML read/write
        yaml_data = {
            "app": "test-app",
            "dependencies": ["dep1", "dep2"],
            "settings": {
                "debug": True,
                "port": 8080
            }
        }
        yaml_file = "config.yaml"
        file_manager.write_yaml(yaml_file, yaml_data)
        print(f"Created YAML file: {yaml_file}")
        
        # Test reading YAML
        read_yaml = file_manager.read_yaml(yaml_file)
        assert read_yaml["app"] == yaml_data["app"]
        assert read_yaml["settings"]["port"] == yaml_data["settings"]["port"]
        print(f"Successfully read YAML file: {yaml_file}")
        
        # Test file deletion
        file_manager.delete_file(code_file)
        try:
            file_manager.read_file(code_file)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            print(f"Successfully deleted file: {code_file}")
        
        # Test path safety
        outside_path = Path(test_dir).parent / "unauthorized.txt"
        try:
            file_manager.write_file(outside_path, "Unauthorized content")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("Path safety check passed - prevented writing outside workspace")
        
        print("\nAll FileManager tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False
    finally:
        # Clean up - remove test directory
        shutil.rmtree(test_dir)
        print(f"Cleaned up test directory: {test_dir}")

def main():
    """Main entry point for the test script."""
    print("FileManager Test Script")
    print("======================\n")
    
    success = run_file_manager_tests()
    
    if success:
        print("\nAll tests completed successfully!")
        return 0
    else:
        print("\nTests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 