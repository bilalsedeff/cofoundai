"""
CoFound.ai FastAPI Agent Protocol API application.

This module makes CoFound.ai compatible with the standard Agent Protocol API.
Agent Protocol: https://github.com/AI-Engineer-Foundation/agent-protocol
"""

import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.communication.protocol import AgentProtocolAdapter
from cofoundai.utils.logger import get_logger

# Create the FastAPI application
app = FastAPI(
    title="CoFound.ai Agent Protocol API",
    description="CoFound.ai system compatible with the Agent Protocol API",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the Agent Protocol adapter
agent_protocol = AgentProtocolAdapter(app)

# Logger
logger = get_logger(__name__)

@app.get("/")
async def root():
    """API root path."""
    return {
        "name": "CoFound.ai Agent Protocol API",
        "version": "0.1.0",
        "description": "CoFound.ai system compatible with the Agent Protocol API"
    }

@app.get("/health")
async def health():
    """API health check."""
    return {"status": "ok"}

def register_agent_graph(agent_id: str, graph: AgenticGraph) -> bool:
    """
    Register the agent graph in the API adapter.
    
    Args:
        agent_id: Agent ID
        graph: Agentic Graph object
        
    Returns:
        True if the registration is successful, False otherwise
    """
    return agent_protocol.register_agent_graph(agent_id, graph)

# Custom stream response handler - when using this, we must correctly implement the async iter protocol
@app.get("/custom-stream")
async def custom_stream():
    """Example streaming API response."""
    async def generate():
        for i in range(5):
            yield f"data: Message {i}\n\n"
    
    # Correct usage of StreamingResponse:
    # Pass the async generator to StreamingResponse, return it
    return StreamingResponse(generate(), media_type="text/event-stream") 