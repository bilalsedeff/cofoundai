
#!/usr/bin/env python3
"""
Backend startup script for CoFound.ai
Ensures proper Python path configuration before starting the API server
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for development
os.environ.setdefault("LLM_PROVIDER", "test")
os.environ.setdefault("DEVELOPMENT_MODE", "true")
os.environ.setdefault("MODEL_NAME", "gpt-4o")

if __name__ == "__main__":
    import uvicorn
    from cofoundai.api.backend_api import app
    
    port = int(os.getenv("PORT", 5000))
    print(f"Starting CoFound.ai backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
