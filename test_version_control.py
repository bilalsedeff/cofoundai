#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VersionControl Test Script

This script tests the VersionControl tool to verify proper functionality.
It simulates how agents would use Git version control operations
for user-specific projects.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import uuid
import time  # Add time for sleep

from cofoundai.tools import VersionControl, FileManager
from cofoundai.utils.logger import get_logger, system_logger

# Set up logger
logger = system_logger

def run_version_control_tests():
    """Run tests for VersionControl functionality."""
    
    print("Starting VersionControl tests...\n")
    
    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="cofoundai_git_test_"))
    print(f"Created test directory: {test_dir}")
    
    try:
        # Create unique project ID
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        
        # Initialize VersionControl with test directory as workspace
        version_control = VersionControl(
            project_id=project_id,
            workspace_dir=str(test_dir)
        )
        
        # Test repository initialization
        print("\n1. Testing repository initialization...")
        init_result = version_control.init_repo()
        if init_result["status"] == "success":
            print("✅ Repository initialization successful")
            print(f"   Message: {init_result['message']}")
        else:
            print("❌ Repository initialization failed")
            print(f"   Error: {init_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test creating and writing to a file
        print("\n2. Testing file creation...")
        project_dir = test_dir / project_id
        file_manager = FileManager(workspace_dir=str(project_dir))
        test_file_content = "# Test File\n\nThis is a test file created for Git testing."
        file_manager.write_file("README.md", test_file_content)
        
        if os.path.exists(project_dir / "README.md"):
            print("✅ File creation successful")
        else:
            print("❌ File creation failed")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test adding files to staging
        print("\n3. Testing adding files to staging...")
        add_result = version_control.add_files(["README.md"])
        if add_result["status"] == "success":
            print("✅ Files added to staging successfully")
        else:
            print("❌ Adding files failed")
            print(f"   Error: {add_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test committing changes
        print("\n4. Testing commit...")
        commit_result = version_control.commit("Initial commit with README")
        if commit_result["status"] == "success":
            print("✅ Commit successful")
            print(f"   Message: {commit_result['message']}")
        else:
            print("❌ Commit failed")
            print(f"   Error: {commit_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test getting status
        print("\n5. Testing repository status...")
        status_result = version_control.get_status()
        if status_result["status"] == "success":
            print("✅ Status check successful")
            print(f"   Current branch: {status_result['current_branch']}")
            print(f"   Has changes: {status_result['has_changes']}")
        else:
            print("❌ Status check failed")
            print(f"   Error: {status_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test creating and checking out a branch
        print("\n6. Testing branch creation and checkout...")
        branch_result = version_control.checkout_branch("feature-branch", create=True)
        if branch_result["status"] == "success":
            print("✅ Branch creation and checkout successful")
            print(f"   Message: {branch_result['message']}")
        else:
            print("❌ Branch operation failed")
            print(f"   Error: {branch_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test listing branches
        print("\n7. Testing branch listing...")
        branches_result = version_control.list_branches()
        if branches_result["status"] == "success":
            print("✅ Branch listing successful")
            print(f"   Branches: {', '.join(branches_result['branches'])}")
            print(f"   Current branch: {branches_result['current_branch']}")
        else:
            print("❌ Branch listing failed")
            print(f"   Error: {branches_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test file modification and diffing
        print("\n8. Testing file modification and diffing...")
        modified_content = test_file_content + "\n\nThis line was added in the feature branch."
        file_manager.write_file("README.md", modified_content)
        
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        diff_result = version_control.get_diff("README.md")
        if diff_result["status"] == "success" and diff_result["diff"]:
            print("✅ Diff successful")
            print("   Diff preview:")
            print(f"   {diff_result['diff'].split('\\n')[0]}...")
        else:
            print("❌ Diff failed or no changes detected")
            print(f"   Result: {diff_result}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test creating a snapshot
        print("\n9. Testing project snapshot creation...")
        snapshot_result = version_control.create_project_snapshot("Feature branch snapshot")
        if snapshot_result["status"] == "success":
            print("✅ Snapshot creation successful")
            print(f"   Snapshot ID: {snapshot_result.get('snapshot_id', 'Unknown')}")
        else:
            print("❌ Snapshot creation failed")
            print(f"   Error: {snapshot_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test listing snapshots
        print("\n10. Testing snapshot listing...")
        snapshots_result = version_control.list_snapshots()
        if snapshots_result["status"] == "success":
            print("✅ Snapshot listing successful")
            print(f"   Found {len(snapshots_result['snapshots'])} snapshots")
            if snapshots_result['snapshots']:
                first_snapshot = snapshots_result['snapshots'][0]
                print(f"   Latest snapshot: {first_snapshot.get('description')} ({first_snapshot.get('timestamp')})")
        else:
            print("❌ Snapshot listing failed")
            print(f"   Error: {snapshots_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Return to master branch (not main)
        print("\n11. Testing branch switching...")
        master_branch_result = version_control.checkout_branch("master")
        if master_branch_result["status"] == "success":
            print("✅ Branch switch successful")
            print(f"   Message: {master_branch_result['message']}")
        else:
            print("❌ Branch switch failed")
            print(f"   Error: {master_branch_result.get('message', 'Unknown error')}")
            return
            
        time.sleep(0.5)  # Add sleep to avoid file locking issues
        
        # Test commit log
        print("\n12. Testing commit log...")
        log_result = version_control.log(n=5)
        if log_result["status"] == "success":
            print("✅ Log retrieval successful")
            print(f"   Found {len(log_result['commits'])} commits")
            if log_result['commits']:
                first_commit = log_result['commits'][0]
                print(f"   Latest commit: {first_commit.get('message')} by {first_commit.get('author')}")
        else:
            print("❌ Log retrieval failed")
            print(f"   Error: {log_result.get('message', 'Unknown error')}")
            return
        
        print("\nAll VersionControl tests completed successfully! 🎉")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        raise
    finally:
        # Give Windows time to release file locks before cleanup
        time.sleep(1.0)
        
        # Try to remove the test directory, with retries
        for attempt in range(3):
            try:
                shutil.rmtree(test_dir)
                print(f"\nRemoved test directory: {test_dir}")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"Cleanup attempt {attempt+1} failed: {str(e)}")
                    time.sleep(2.0)  # Wait longer before retrying
                else:
                    print(f"\nWarning: Could not remove test directory: {str(e)}")
                    print(f"You may need to manually delete: {test_dir}")

if __name__ == "__main__":
    run_version_control_tests() 