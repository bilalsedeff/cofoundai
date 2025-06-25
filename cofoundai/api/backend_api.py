
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import asyncio
from cofoundai.core.llm_interface import LLMFactory
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import LangGraphAgent
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CoFound.ai API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class DreamRequest(BaseModel):
    vision_text: str
    tags: Optional[List[str]] = []
    goal: str = "prototype"
    tech_preferences: Optional[List[str]] = []

class DreamResponse(BaseModel):
    initial_brief: str
    extracted_tags: List[str]
    cost_estimate: Dict[str, Any]
    status: str
    project_id: str

class MaturationRequest(BaseModel):
    project_id: str
    refined_input: str
    phase: str  # "discovery", "clarity", "feasibility", "governance"

class MaturationResponse(BaseModel):
    artifacts: List[Dict[str, Any]]
    next_phase: Optional[str]
    status: str
    project_id: str

class AssembleRequest(BaseModel):
    project_id: str
    matured_brief: str

class AssembleResponse(BaseModel):
    team_composition: List[Dict[str, Any]]
    estimated_cost: Dict[str, Any]
    deployment_spec: Dict[str, Any]
    status: str

# Global variables
orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    global orchestrator
    try:
        # Initialize LLM
        logger.info("Initializing LLM interface...")
        
        # Create agents for the dream phase
        agent_configs = [
            {
                "name": "VisionAnalyst",
                "description": "Analyzes user vision and extracts key insights",
                "system_prompt": """You are a vision analyst agent. Your role is to:
1. Extract key business requirements from user descriptions
2. Identify relevant technology tags and categories
3. Provide initial cost and complexity estimates
4. Generate clear, actionable project briefs""",
                "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
                "model_name": os.getenv("MODEL_NAME", "gpt-4o")
            },
            {
                "name": "BlueprintGenerator", 
                "description": "Creates initial project blueprints",
                "system_prompt": """You are a blueprint generator agent. Your role is to:
1. Transform user visions into structured project blueprints
2. Define project scope and objectives
3. Identify key milestones and deliverables
4. Create initial architectural recommendations""",
                "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
                "model_name": os.getenv("MODEL_NAME", "gpt-4o")
            }
        ]
        
        # Create agent instances
        agents = {}
        for config in agent_configs:
            agent = LangGraphAgent(config)
            agents[agent.name] = agent
        
        # Initialize orchestrator
        orchestrator = AgenticGraph(
            project_id="system",
            agents=agents
        )
        
        logger.info("System initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cofound-ai-api"}

@app.post("/api/dream", response_model=DreamResponse)
async def dream_phase(request: DreamRequest):
    """Process user vision in the Dream phase"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="System not initialized")
        
        # Generate project ID
        import uuid
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        # Create dream processing prompt
        dream_prompt = f"""
        User Vision: {request.vision_text}
        Selected Tags: {', '.join(request.tags)}
        Goal: {request.goal}
        Tech Preferences: {', '.join(request.tech_preferences)}
        
        Please analyze this vision and provide:
        1. A refined project brief with clear objectives
        2. Extracted and additional relevant tags 
        3. Initial scope and complexity assessment
        4. Technology recommendations
        5. Cost and timeline estimates
        """
        
        # Process through orchestrator
        result = orchestrator.run(dream_prompt)
        
        # Extract information from result
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            last_message = messages[-1] if messages else None
            
            if last_message and hasattr(last_message, 'content'):
                response_content = last_message.content
            else:
                response_content = "Blueprint generated successfully"
        else:
            response_content = str(result)
        
        # Estimate tokens and cost (simplified)
        total_tokens = len(dream_prompt.split()) + len(response_content.split())
        estimated_cost = total_tokens * 0.00002  # Rough estimate
        
        return DreamResponse(
            initial_brief=response_content,
            extracted_tags=request.tags + ["AI-Generated", "CoFound.ai"],
            cost_estimate={
                "tokens": total_tokens,
                "cost_usd": estimated_cost,
                "complexity": "Medium"
            },
            status="completed",
            project_id=project_id
        )
        
    except Exception as e:
        logger.error(f"Error in dream phase: {e}")
        raise HTTPException(status_code=500, detail=f"Dream phase failed: {str(e)}")

@app.post("/api/maturation", response_model=MaturationResponse)
async def maturation_phase(request: MaturationRequest):
    """Process project through Maturation phase"""
    try:
        # Maturation logic would go here
        # For now, return a placeholder response
        artifacts = [
            {
                "name": "Refined BRD",
                "type": "document",
                "status": "generated",
                "content": "Business Requirements Document has been refined based on stakeholder input."
            },
            {
                "name": "Functional Requirements",
                "type": "specification", 
                "status": "generated",
                "content": "Detailed functional requirements have been documented."
            }
        ]
        
        next_phase_map = {
            "discovery": "clarity",
            "clarity": "feasibility", 
            "feasibility": "governance",
            "governance": None
        }
        
        return MaturationResponse(
            artifacts=artifacts,
            next_phase=next_phase_map.get(request.phase),
            status="completed",
            project_id=request.project_id
        )
        
    except Exception as e:
        logger.error(f"Error in maturation phase: {e}")
        raise HTTPException(status_code=500, detail=f"Maturation phase failed: {str(e)}")

@app.post("/api/assemble", response_model=AssembleResponse)
async def assemble_phase(request: AssembleRequest):
    """Process project through Assemble phase"""
    try:
        # Assemble logic would go here
        team_composition = [
            {
                "role": "Planner Agent",
                "count": 1,
                "estimated_tokens": 5000,
                "estimated_cost": 0.10
            },
            {
                "role": "Architect Agent", 
                "count": 1,
                "estimated_tokens": 8000,
                "estimated_cost": 0.16
            },
            {
                "role": "Developer Agent",
                "count": 2,
                "estimated_tokens": 15000,
                "estimated_cost": 0.30
            }
        ]
        
        total_cost = sum(agent["estimated_cost"] for agent in team_composition)
        
        return AssembleResponse(
            team_composition=team_composition,
            estimated_cost={
                "total_usd": total_cost,
                "currency": "USD",
                "breakdown": team_composition
            },
            deployment_spec={
                "platform": "replit",
                "services": ["api", "frontend", "database"],
                "scaling": "auto"
            },
            status="ready_for_launch"
        )
        
    except Exception as e:
        logger.error(f"Error in assemble phase: {e}")
        raise HTTPException(status_code=500, detail=f"Assemble phase failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
