
"""
CoFound.ai Dream Service
FastAPI microservice for handling dream phase requests
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import uuid
import json
from datetime import datetime
import asyncio
import os

from google.cloud import pubsub_v1
from google.cloud import secretmanager
import asyncpg
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class DreamRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    prompt_text: str = Field(..., description="User's dream/vision")
    goal: str = Field(default="prototype", description="Project goal")
    tags: List[str] = Field(default_factory=list, description="Industry tags")
    advanced_options: Dict[str, Any] = Field(default_factory=dict, description="Advanced options")

class DreamResponse(BaseModel):
    project_id: str
    status: str
    message: str
    blueprint_id: Optional[str] = None

class Blueprint(BaseModel):
    project_id: str
    overview: str
    features: List[str]
    tech_stack: List[str]
    timeline: str
    cost: str
    vision: str
    goal: str
    tags: List[str]

# FastAPI App
app = FastAPI(
    title="CoFound.ai Dream Service",
    description="Microservice for processing dream phase requests",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for connections
db_pool = None
redis_client = None
publisher = None

@app.on_startup
async def startup_event():
    """Initialize connections on startup"""
    global db_pool, redis_client, publisher
    
    try:
        # Initialize Pub/Sub publisher
        publisher = pubsub_v1.PublisherClient()
        
        # Get secrets
        secret_client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        environment = os.getenv("ENVIRONMENT", "dev")
        
        # Database connection
        db_secret_name = f"projects/{project_id}/secrets/db-connection-{environment}/versions/latest"
        db_secret = secret_client.access_secret_version(name=db_secret_name)
        db_config = json.loads(db_secret.payload.data.decode("UTF-8"))
        
        db_pool = await asyncpg.create_pool(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["username"],
            password=db_config["password"],
            min_size=1,
            max_size=10
        )
        
        # Redis connection
        redis_secret_name = f"projects/{project_id}/secrets/redis-connection-{environment}/versions/latest"
        redis_secret = secret_client.access_secret_version(name=redis_secret_name)
        redis_config = json.loads(redis_secret.payload.data.decode("UTF-8"))
        
        redis_client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            decode_responses=True
        )
        
        logger.info("Dream service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize dream service: {str(e)}")
        raise

@app.on_shutdown
async def shutdown_event():
    """Cleanup connections on shutdown"""
    global db_pool, redis_client
    
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "dream-service"
    }

@app.post("/api/dream", response_model=DreamResponse)
async def process_dream(request: DreamRequest, background_tasks: BackgroundTasks):
    """
    Process dream request and initiate blueprint generation
    """
    try:
        # Generate project ID if not provided
        if not request.project_id:
            request.project_id = f"proj_{int(datetime.now().timestamp())}"
        
        # Validate request
        if not request.prompt_text or len(request.prompt_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Dream description must be at least 10 characters long"
            )
        
        # Store request in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dream_requests (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    tags JSONB,
                    advanced_options JSONB,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                INSERT INTO dream_requests 
                (user_id, project_id, prompt_text, goal, tags, advanced_options)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, 
                request.user_id,
                request.project_id,
                request.prompt_text,
                request.goal,
                json.dumps(request.tags),
                json.dumps(request.advanced_options)
            )
        
        # Cache request for quick access
        cache_key = f"dream_request:{request.project_id}"
        await redis_client.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(request.dict())
        )
        
        # Publish to Pub/Sub for async processing
        background_tasks.add_task(
            publish_dream_request,
            request.project_id,
            request.dict()
        )
        
        logger.info(f"Dream request processed for project: {request.project_id}")
        
        return DreamResponse(
            project_id=request.project_id,
            status="processing",
            message="Dream request received and processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing dream request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing dream request"
        )

async def publish_dream_request(project_id: str, request_data: dict):
    """Publish dream request to Pub/Sub"""
    try:
        project_id_env = os.getenv("GOOGLE_CLOUD_PROJECT")
        environment = os.getenv("ENVIRONMENT", "dev")
        topic_path = publisher.topic_path(project_id_env, f"dream-requested-{environment}")
        
        message_data = json.dumps({
            "project_id": project_id,
            "request_data": request_data,
            "timestamp": datetime.now().isoformat()
        }).encode("utf-8")
        
        future = publisher.publish(topic_path, message_data)
        message_id = future.result()
        
        logger.info(f"Published dream request to Pub/Sub: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish dream request: {str(e)}")

@app.get("/api/dream/{project_id}/status")
async def get_dream_status(project_id: str):
    """Get dream processing status"""
    try:
        # Check cache first
        cache_key = f"dream_status:{project_id}"
        cached_status = await redis_client.get(cache_key)
        
        if cached_status:
            return json.loads(cached_status)
        
        # Check database
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT status, created_at, updated_at
                FROM dream_requests
                WHERE project_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, project_id)
            
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Dream request not found"
                )
            
            status_data = {
                "project_id": project_id,
                "status": row["status"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat()
            }
            
            # Cache for 5 minutes
            await redis_client.setex(
                cache_key,
                300,
                json.dumps(status_data)
            )
            
            return status_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dream status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error getting dream status"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
