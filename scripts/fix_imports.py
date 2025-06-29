import os
import sys

try:
    from cofoundai.orchestration.agentic_graph import AgenticGraph
    print("Import successful!")
except Exception as e:
    print(f"Import failed with error: {e}")
    
    # Try to diagnose the issue
    try:
        import cofoundai
        print("cofoundai package can be imported")
        
        import cofoundai.orchestration
        print("cofoundai.orchestration package can be imported")
        
        # Check file content for null bytes
        with open(cofoundai.orchestration.__file__, "rb") as f:
            content = f.read()
            if b"\x00" in content:
                print(f"Null bytes found in {cofoundai.orchestration.__file__}")
            else:
                print(f"No null bytes found in {cofoundai.orchestration.__file__}")
                
        try:
            # Try to read the agentic_graph.py file
            import os.path
            agentic_graph_path = os.path.join(os.path.dirname(cofoundai.orchestration.__file__), "agentic_graph.py")
            
            with open(agentic_graph_path, "rb") as f:
                content = f.read()
                if b"\x00" in content:
                    print(f"Null bytes found in {agentic_graph_path}")
                    
                    # Clean the file
                    content = content.replace(b"\x00", b"")
                    with open(agentic_graph_path, "wb") as f2:
                        f2.write(content)
                    print(f"Cleaned null bytes from {agentic_graph_path}")
                else:
                    print(f"No null bytes found in {agentic_graph_path}")
        except Exception as e2:
            print(f"Error while checking agentic_graph.py: {e2}")
    except Exception as e1:
        print(f"Error in diagnosis: {e1}")
