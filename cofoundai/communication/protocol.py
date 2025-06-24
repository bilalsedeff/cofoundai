"""
Agent Protocol adapter.

This module contains the adapter class that allows CoFound.ai to work with the Agent Protocol (AP).
Agent Protocol is a standard API that allows different agents to communicate with each other and with humans.

"""

import json
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse

from cofoundai.communication.message import Message, MessageContent
from cofoundai.communication.agent_command import Command, CommandType, CommandTarget
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.utils.logger import get_logger

# Logger
logger = get_logger(__name__)

# Agent Protocol Models

class Content(BaseModel):
    """Agent Protocol Content model."""
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class APMessage(BaseModel):
    """Agent Protocol Message model."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    role: str
    content: List[Content]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Thread(BaseModel):
    """Agent Protocol Thread model."""
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ThreadState(BaseModel):
    """Agent Protocol Thread State model."""
    thread_id: str
    state: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ThreadPatch(BaseModel):
    """Agent Protocol Thread Patch model."""
    metadata: Optional[Dict[str, Any]] = None
    
class ThreadSearchRequest(BaseModel):
    """Agent Protocol Thread Search Request model."""
    thread_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    limit: Optional[int] = None

class RunCreate(BaseModel):
    """Agent Protocol Run creation model."""
    thread_id: Optional[str] = None
    agent_id: Optional[str] = None
    input: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = False
    config: Optional[Dict[str, Any]] = None

class Run(BaseModel):
    """Agent Protocol Run model."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    agent_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RunSearchRequest(BaseModel):
    """Agent Protocol Run Search Request model."""
    run_ids: Optional[List[str]] = None
    thread_ids: Optional[List[str]] = None
    agent_ids: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    limit: Optional[int] = None

class Item(BaseModel):
    """Store Item model."""
    key: str
    namespace: List[str]
    value: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StorePutRequest(BaseModel):
    """Store Item add/update request."""
    namespace: List[str]
    key: str
    value: Dict[str, Any]

class StoreDeleteRequest(BaseModel):
    """Store Item delete request."""
    namespace: List[str]
    key: str

class StoreSearchRequest(BaseModel):
    """Store Item search request."""
    namespace: Optional[List[str]] = None
    query: Optional[str] = None
    
class SearchItemsResponse(BaseModel):
    """Store Item search result."""
    items: List[Item]

class StoreListNamespacesRequest(BaseModel):
    """Store Namespaces list request."""
    pass

class AgentSchema(BaseModel):
    """Agent schema model."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class RunWaitResponse(BaseModel):
    """Run wait response."""
    run: Run
    messages: List[APMessage] = []

# CoFound.ai and Agent Protocol conversion functions

def convert_to_ap_message(message: Message, thread_id: str) -> APMessage:
    """Convert CoFound.ai Message to AP Message."""
    content = [
        Content(
            type="text",
            text=message.content.text if hasattr(message.content, "text") else str(message.content),
            data=message.content.data if hasattr(message.content, "data") else {}
        )
    ]
    
    return APMessage(
        thread_id=thread_id,
        role=message.sender,
        content=content,
        metadata=message.metadata
    )

def convert_from_ap_message(ap_message: APMessage) -> Message:
    """Convert AP Message to CoFound.ai Message."""
    content_text = ""
    content_data = {}
    
    if ap_message.content:
        for content in ap_message.content:
            if content.type == "text" and content.text:
                content_text += content.text
            if content.data:
                content_data.update(content.data)
    
    return Message(
        sender=ap_message.role,
        recipient="system",  # Default recipient
        content=MessageContent(text=content_text, data=content_data),
        metadata=ap_message.metadata or {},
        message_id=ap_message.message_id
    )

# Flask Route Registration Function

def register_agent_protocol_routes(flask_app):
    """
    Register Agent Protocol routes with a Flask application.
    
    Args:
        flask_app: Flask application instance
    """
    from flask import request, jsonify
    
    # Create adapter instance
    adapter = AgentProtocolAdapter()
    
    # Health endpoint
    @flask_app.route('/ap/health')
    def ap_health():
        return jsonify({"status": "ok", "service": "Agent Protocol"})
    
    # Agent endpoints
    @flask_app.route('/ap/agents/<agent_id>')
    def get_agent(agent_id):
        try:
            import asyncio
            result = asyncio.run(adapter.get_agent(agent_id))
            return jsonify(result.dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 404
    
    # Run endpoints
    @flask_app.route('/ap/runs', methods=['POST'])
    def create_run():
        try:
            data = request.get_json()
            run_create = RunCreate(**data)
            import asyncio
            result = asyncio.run(adapter.create_run(run_create))
            return jsonify(result.dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @flask_app.route('/ap/runs/<run_id>')
    def get_run(run_id):
        try:
            import asyncio
            result = asyncio.run(adapter.get_run(run_id))
            return jsonify(result.dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 404
    
    logger.info("Agent Protocol routes registered with Flask app")
    return adapter

# Agent Protocol API Adapter

class AgentProtocolAdapter:
    """
    Adapter that makes CoFound.ai compatible with the Agent Protocol.
    
    This class makes the CoFound.ai agentic_graph structure compatible with the Agent Protocol API standards.
    """
    
    def __init__(self, app: FastAPI = None):
        """
        Initialize the adapter.
        
        Args:
            app: FastAPI application (optional)
        """
        self.app = app
        self.graphs: Dict[str, AgenticGraph] = {}
        self.runs: Dict[str, Run] = {}
        self.threads: Dict[str, Thread] = {}
        self.thread_states: Dict[str, ThreadState] = {}
        self.store: Dict[str, Dict[str, Item]] = {}
        
        if app:
            self._register_routes()
            logger.info("Agent Protocol API routes registered")
    
    def _register_routes(self):
        """Register API routes."""
        # Agent API
        self.app.get("/agents/{agent_id}")(self.get_agent)
        self.app.get("/agents/{agent_id}/schemas")(self.get_agent_schemas)
        self.app.post("/agents/search")(self.search_agents)
        
        # Runs API
        self.app.post("/runs", response_model=Run)(self.create_run)
        self.app.get("/runs/{run_id}", response_model=Run)(self.get_run)
        self.app.post("/runs/stream")(self.create_and_stream_run)
        self.app.post("/runs/wait", response_model=RunWaitResponse)(self.create_and_wait_run)
        self.app.get("/runs/{run_id}/stream")(self.stream_run)
        self.app.post("/runs/search")(self.search_runs)
        
        # Threads API
        self.app.post("/threads", response_model=Thread)(self.create_thread)
        self.app.get("/threads/{thread_id}", response_model=Thread)(self.get_thread)
        self.app.patch("/threads/{thread_id}", response_model=Thread)(self.patch_thread)
        self.app.get("/threads/{thread_id}/state")(self.get_thread_state)
        self.app.post("/threads/{thread_id}/runs", response_model=Run)(self.create_run_in_thread)
        self.app.post("/threads/search")(self.search_threads)
        
        # Store API
        self.app.put("/store/items")(self.put_item)
        self.app.get("/store/items/{key}")(self.get_item)
        self.app.delete("/store/items")(self.delete_item)
        self.app.post("/store/items/search", response_model=SearchItemsResponse)(self.search_items)
        self.app.post("/store/namespaces", response_model=List[List[str]])(self.list_namespaces)
    
    def register_agent_graph(self, agent_id: str, graph: AgenticGraph):
        """
        Save the agent graph.
        
        Args:
            agent_id: Agent ID
            graph: Agentic Graph object
        """
        self.graphs[agent_id] = graph
        logger.info(f"Agent ID {agent_id} graph saved")
        return True
    
    # Agent API implementations
    async def get_agent(self, agent_id: str):
        """Get agent information."""
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        graph = self.graphs[agent_id]
        
        # Create agent schema
        return AgentSchema(
            name=agent_id,
            description=f"Agentic graph for {agent_id}",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            output_schema={"type": "object"}
        )
    
    async def get_agent_schemas(self, agent_id: str):
        """Get agent schemas."""
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Simple input/output schemas
        input_schema = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Input message for the agent"
                }
            }
        }
        
        output_schema = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Output message from the agent"
                },
                "status": {
                    "type": "string",
                    "description": "Status of the agent execution"
                }
            }
        }
        
        return {
            "input_schema": input_schema,
            "output_schema": output_schema
        }
    
    async def search_agents(self, request: dict = Body(...)):
        """Search agents."""
        agent_list = []
        
        for agent_id, graph in self.graphs.items():
            agent_list.append({
                "agent_id": agent_id,
                "name": agent_id,
                "description": f"Agentic graph for {agent_id}"
            })
            
        return {"agents": agent_list}
    
    # Runs API implementations
    async def create_run(self, run_create: RunCreate):
        """Create a new run."""
        agent_id = run_create.agent_id
        if agent_id not in self.graphs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Create or use thread
        thread_id = run_create.thread_id
        if not thread_id:
            thread = Thread()
            self.threads[thread.thread_id] = thread
            thread_id = thread.thread_id
        elif thread_id not in self.threads:
            thread = Thread(thread_id=thread_id)
            self.threads[thread_id] = thread
        
        # Create run
        run = Run(
            agent_id=agent_id,
            thread_id=thread_id,
            input=run_create.input,
            metadata=run_create.metadata
        )
        self.runs[run.run_id] = run
        
        # Start asynchronous processing
        asyncio.create_task(self._execute_run(run))
        
        return run
    
    async def _execute_run(self, run: Run):
        """Execute the run."""
        try:
            # Update status
            run.status = "running"
            run.started_at = datetime.now()
            
            # Get user input
            user_input = run.input.get("message", "")
            if isinstance(user_input, dict) and "content" in user_input:
                user_input = user_input["content"]
            
            # Run the graph
            graph = self.graphs[run.agent_id]
            result = graph.run(user_input)
            
            # Save output
            run.output = result
            run.status = "completed"
            run.completed_at = datetime.now()
            
        except Exception as e:
            # On error
            logger.error(f"Run execution error: {str(e)}")
            run.status = "failed"
            run.output = {"error": str(e)}
            run.completed_at = datetime.now()
    
    async def get_run(self, run_id: str):
        """Get run information."""
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        return self.runs[run_id]
    
    async def create_and_stream_run(self, run_stream: Dict[str, Any] = Body(...)):
        """Create a new run and stream it."""
        # Convert to RunCreate object
        run_create = RunCreate(
            agent_id=run_stream.get("agent_id"),
            thread_id=run_stream.get("thread_id"),
            input=run_stream.get("input", {}),
            metadata=run_stream.get("metadata", {}),
            stream=True
        )
        
        # Create run
        run = await self.create_run(run_create)
        
        # Return streaming response - new approach
        async def stream_gen():
            async for chunk in self.stream_run(run.run_id):
                yield chunk
                
        return StreamingResponse(stream_gen(), media_type="text/event-stream")
    
    async def create_and_wait_run(self, run_create: RunCreate):
        """Create a new run and wait for completion."""
        # Create run
        run = await self.create_run(run_create)
        
        # Wait for completion
        for _ in range(100):  # Maximum 100 seconds wait
            current_run = self.runs[run.run_id]
            if current_run.status in ["completed", "failed"]:
                # Get messages
                messages = []  # In real implementation, get messages from the thread
                
                return RunWaitResponse(run=current_run, messages=messages)
            
            await asyncio.sleep(1)
        
        # Timeout status
        run.status = "failed"
        run.output = {"error": "Run timeout"}
        self.runs[run.run_id] = run
        
        return RunWaitResponse(run=run, messages=[])
    
    async def stream_run(self, run_id: str):
        """Get run output as a stream."""
        if run_id not in self.runs:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        run = self.runs[run_id]
        if run.status != "running":
            # Already completed or failed run
            yield json.dumps({"status": run.status, "output": run.output})
            return
        
        # Generate stream response
        graph = self.graphs[run.agent_id]
        user_input = run.input.get("message", "")
        
        # Note: This is an asynchronous generator function
        # Instead of returning StreamingResponse, we run the generator ourselves
        try:
            for chunk in graph.stream(user_input):
                # Convert chunk to JSON format
                if isinstance(chunk, dict):
                    yield json.dumps(chunk) + "\n"
                else:
                    yield json.dumps({"chunk": str(chunk)}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
    
    async def search_runs(self, search_request: RunSearchRequest):
        """Search runs."""
        filtered_runs = []
        
        for run_id, run in self.runs.items():
            include = True
            
            # Filter by run ID
            if search_request.run_ids and run_id not in search_request.run_ids:
                include = False
                
            # Filter by thread ID
            if include and search_request.thread_ids and run.thread_id not in search_request.thread_ids:
                include = False
                
            # Filter by agent ID
            if include and search_request.agent_ids and run.agent_id not in search_request.agent_ids:
                include = False
                
            # Filter by status
            if include and search_request.statuses and run.status not in search_request.statuses:
                include = False
                
            # Filter by creation time
            if include and search_request.created_after and run.created_at < search_request.created_after:
                include = False
                
            if include and search_request.created_before and run.created_at > search_request.created_before:
                include = False
                
            # Filter by metadata
            if include and search_request.metadata:
                for key, value in search_request.metadata.items():
                    if not run.metadata or key not in run.metadata or run.metadata[key] != value:
                        include = False
                        break
            
            if include:
                filtered_runs.append(run)
                
        # Apply limit
        if search_request.limit and len(filtered_runs) > search_request.limit:
            filtered_runs = filtered_runs[:search_request.limit]
                
        return {"runs": filtered_runs}
    
    # Threads API implementations
    async def create_thread(self, thread: Thread = Body(...)):
        """Create a new thread."""
        self.threads[thread.thread_id] = thread
        return thread
    
    async def get_thread(self, thread_id: str):
        """Get thread information."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        return self.threads[thread_id]
    
    async def patch_thread(self, thread_id: str, thread_patch: ThreadPatch):
        """Update thread information."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        thread = self.threads[thread_id]
        
        # Update metadata
        if thread_patch.metadata:
            if not thread.metadata:
                thread.metadata = {}
            thread.metadata.update(thread_patch.metadata)
        
        return thread
    
    async def get_thread_state(self, thread_id: str):
        """Get thread state."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # If thread state exists, get it, otherwise create it
        if thread_id in self.thread_states:
            return self.thread_states[thread_id]
        
        # Default empty state
        thread_state = ThreadState(
            thread_id=thread_id,
            state={}
        )
        self.thread_states[thread_id] = thread_state
        return thread_state
    
    async def create_run_in_thread(self, thread_id: str, run_create: RunCreate):
        """Create a new run in a thread."""
        if thread_id not in self.threads:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        # Add thread ID
        run_create.thread_id = thread_id
        
        # Create run
        return await self.create_run(run_create)
    
    async def search_threads(self, search_request: ThreadSearchRequest):
        """Search threads."""
        filtered_threads = []
        
        for thread_id, thread in self.threads.items():
            include = True
            
            # Filter by thread ID
            if search_request.thread_ids and thread_id not in search_request.thread_ids:
                include = False
                
            # Filter by creation time
            if include and search_request.created_after and thread.created_at < search_request.created_after:
                include = False
                
            if include and search_request.created_before and thread.created_at > search_request.created_before:
                include = False
                
            # Filter by metadata
            if include and search_request.metadata:
                for key, value in search_request.metadata.items():
                    if not thread.metadata or key not in thread.metadata or thread.metadata[key] != value:
                        include = False
                        break
            
            if include:
                filtered_threads.append(thread)
                
        # Apply limit
        if search_request.limit and len(filtered_threads) > search_request.limit:
            filtered_threads = filtered_threads[:search_request.limit]
                
        return {"threads": filtered_threads}
    
    # Store API implementations
    async def put_item(self, request: StorePutRequest):
        """Add an item to the store."""
        namespace_key = "/".join(request.namespace)
        
        if namespace_key not in self.store:
            self.store[namespace_key] = {}
        
        # Create or update item
        item = Item(
            key=request.key,
            namespace=request.namespace,
            value=request.value,
            updated_at=datetime.now()
        )
        
        if request.key in self.store[namespace_key]:
            # Update existing item, keep creation time
            item.created_at = self.store[namespace_key][request.key].created_at
        
        self.store[namespace_key][request.key] = item
        return {"status": "success"}
    
    async def get_item(self, key: str, namespace: List[str] = None):
        """Get an item from the store."""
        namespace = namespace or []
        namespace_key = "/".join(namespace)
        
        if namespace_key not in self.store or key not in self.store[namespace_key]:
            raise HTTPException(status_code=404, detail=f"Item {key} not found in namespace {namespace}")
        
        return self.store[namespace_key][key]
    
    async def delete_item(self, request: StoreDeleteRequest):
        """Delete an item from the store."""
        namespace_key = "/".join(request.namespace)
        
        if namespace_key in self.store and request.key in self.store[namespace_key]:
            del self.store[namespace_key][request.key]
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail=f"Item {request.key} not found in namespace {request.namespace}")
    
    async def search_items(self, request: StoreSearchRequest):
        """Search items in the store."""
        items = []
        namespaces = []
        
        if request.namespace:
            # Search in specific namespaces
            for ns in request.namespace:
                ns_key = "/".join(ns if isinstance(ns, list) else [ns])
                if ns_key in self.store:
                    namespaces.append(ns_key)
        else:
            # Search in all namespaces
            namespaces = list(self.store.keys())
        
        for namespace_key in namespaces:
            for key, item in self.store[namespace_key].items():
                # Simple search, if query exists, search in key
                if not request.query or request.query.lower() in key.lower():
                    items.append(item)
        
        return SearchItemsResponse(items=items)
    
    async def list_namespaces(self, request: StoreListNamespacesRequest):
        """List namespaces."""
        namespaces = []
        
        for namespace_key in self.store.keys():
            if namespace_key:
                # Convert namespace_key string to list format
                ns_parts = namespace_key.split("/")
                namespaces.append(ns_parts)
                
        return namespaces 