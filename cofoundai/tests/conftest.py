"""
Pytest configuration file for tests.

This file is automatically loaded by pytest before running tests.
It adds the project root directory to the Python path, allowing
imports of 'cofoundai' modules to work correctly.
"""

import os
import sys
from pathlib import Path
import re
import pytest

# Add project root to Python path
def pytest_configure(config):
    """
    Configure pytest environment.
    
    Adds the project root directory to sys.path so that imports
    for 'cofoundai' modules work correctly.
    """
    # Find project root (parent directory of the directory containing this file)
    project_root = Path(__file__).parent.parent.parent
    
    # Add to Python path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"Added {project_root} to Python path")

# Define custom collection rules to ignore non-test classes that look like test classes
def pytest_collection_modifyitems(config, items):
    """
    Customize test collection to ignore certain classes that start with 'Test'
    but are not actual test classes.
    """
    skip_patterns = [
        r".*TesterAgent.*", 
        r".*TestAgent.*",
    ]
    
    for item in list(items):
        nodeid = item.nodeid
        for pattern in skip_patterns:
            if re.match(pattern, nodeid):
                items.remove(item)
                break

# Setup a fixture for common test configuration
@pytest.fixture(scope="session")
def test_config():
    """
    Returns common test configuration.
    
    This can be used across tests to maintain consistent settings.
    """
    return {
        "test_mode": True,
        "workspace_dir": os.environ.get("TEST_WORKSPACE_DIR", 
                                       os.path.join(os.path.dirname(__file__), "..", "..", "test_workspace"))
    } 