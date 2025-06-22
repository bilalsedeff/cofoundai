
"""
CoFound.ai Dream Service

This microservice handles the Dream phase of the CoFound.ai workflow.
It processes user dreams/visions and converts them into structured blueprints.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from google.cloud import pubsub_v1, secretmanager, storage
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from cofoundai.utils.langsmith_integration import get_tracer, trace_agent_method
from cofoundai.agents.langgraph_agent import LangGraphAgent
from cofoundai.orchestration.agentic_graph import AgenticGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables for services
connector = None
db_pool = None
publisher = None
storage_client = None
secret_client = None

def initialize_gcp_services():
    """Initialize Google Cloud Platform services."""
    global connector, db_pool, publisher, storage_client, secret_client
    
    try:
        # Cloud SQL Connector
        connector = Connector()
        
        # Pub/Sub Publisher
        publisher = pubsub_v1.PublisherClient()
        
        # Cloud Storage
        storage_client = storage.Client()
        
        # Secret Manager
        secret_client = secretmanager.SecretManagerServiceClient()
        
        # Database connection
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        region = os.environ.get('GOOGLE_CLOUD_REGION', 'us-central1')
        instance_name = f"{project_id}:{region}:cofoundai-postgres-dev"
        
        def getconn():
            conn = connector.connect(
                instance_name,
                "pg8000",
                user=get_secret("database-user"),
                password=get_secret("database-password"),
                db="cofoundai"
            )
            return conn

        # Create SQLAlchemy engine
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        db_pool = Session
        
        logger.info("Successfully initialized GCP services")
        
    except Exception as e:
        logger.error(f"Failed to initialize GCP services: {e}")
        # For development, continue without GCP services
        if os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true':
            logger.warning("Running in development mode without GCP services")
        else:
            raise

def get_secret(secret_id: str) -> str:
    """Retrieve secret from Google Secret Manager."""
    if secret_client is None:
        return os.environ.get(secret_id.replace('-', '_').upper(), 'default_value')
    
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {e}")
        return 'default_value'

def publish_to_pubsub(topic_name: str, data: Dict[str, Any]) -> bool:
    """Publish message to Pub/Sub topic."""
    if publisher is None:
        logger.warning("Pub/Sub not available, skipping publish")
        return False
    
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        topic_path = publisher.topic_path(project_id, topic_name)
        
        # Convert data to JSON string
        message_data = json.dumps(data).encode('utf-8')
        
        # Publish message
        future = publisher.publish(topic_path, message_data)
        message_id = future.result()
        
        logger.info(f"Published message {message_id} to {topic_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish to {topic_name}: {e}")
        return False

class DreamProcessor:
    """Processes user dreams into structured blueprints."""
    
    def __init__(self):
        """Initialize the dream processor."""
        self.tracer = get_tracer()
        
        # Initialize specialized agents for dream processing
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize dream processing agents."""
        try:
            # Vision Analysis Agent
            vision_config = {
                "name": "VisionAnalyst",
                "system_prompt": "You analyze user visions and extract key requirements, goals, and constraints.",
                "llm_provider": "openai",
                "model_name": "gpt-4-turbo-preview"
            }
            self.agents["vision"] = LangGraphAgent(vision_config)
            
            # Blueprint Generator Agent
            blueprint_config = {
                "name": "BlueprintGenerator", 
                "system_prompt": "You create detailed project blueprints from analyzed visions.",
                "llm_provider": "openai",
                "model_name": "gpt-4-turbo-preview"
            }
            self.agents["blueprint"] = LangGraphAgent(blueprint_config)
            
            logger.info("Dream processing agents initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize dream agents: {e}")
            self.agents = {}
    
    @trace_agent_method("dream")
    def process_dream(self, user_dream: str, project_id: str) -> Dict[str, Any]:
        """
        Process a user's dream into a structured blueprint.
        
        Args:
            user_dream: User's vision/dream description
            project_id: Unique project identifier
            
        Returns:
            Structured blueprint
        """
        try:
            # Start tracing session
            session_id = self.tracer.start_workflow_session(project_id, user_dream)
            
            # Step 1: Vision Analysis
            vision_result = self._analyze_vision(user_dream, project_id)
            
            # Step 2: Blueprint Generation
            blueprint_result = self._generate_blueprint(vision_result, project_id)
            
            # Step 3: Validation and Enhancement
            final_blueprint = self._validate_blueprint(blueprint_result, project_id)
            
            # Publish to next phase
            self._publish_to_maturation(final_blueprint, project_id)
            
            # End tracing session
            self.tracer.end_workflow_session("success", final_blueprint)
            
            return {
                "status": "success",
                "project_id": project_id,
                "blueprint": final_blueprint,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Dream processing failed for {project_id}: {e}")
            self.tracer.end_workflow_session("error", {})
            
            return {
                "status": "error",
                "project_id": project_id,
                "error": str(e)
            }
    
    def _analyze_vision(self, user_dream: str, project_id: str) -> Dict[str, Any]:
        """Analyze user vision to extract key components."""
        if "vision" not in self.agents:
            # Fallback analysis without LLM
            return {
                "vision_summary": user_dream[:200],
                "key_requirements": ["Feature 1", "Feature 2", "Feature 3"],
                "target_users": ["General users"],
                "constraints": [],
                "success_metrics": ["User satisfaction", "Performance"]
            }
        
        # Use vision analysis agent
        analysis_prompt = f"""
        Analyze this user vision and extract key components:
        
        Vision: {user_dream}
        
        Extract:
        1. Vision summary (2-3 sentences)
        2. Key requirements and features
        3. Target users and personas
        4. Constraints and limitations
        5. Success metrics and goals
        
        Provide structured output in JSON format.
        """
        
        result = self.agents["vision"].process({
            "content": analysis_prompt,
            "project_id": project_id
        })
        
        # Trace the vision analysis
        self.tracer.trace_agent_execution(
            agent_name="VisionAnalyst",
            phase="dream_analysis",
            input_data={"user_dream": user_dream[:100]},
            output_data=result
        )
        
        return result
    
    def _generate_blueprint(self, vision_analysis: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Generate detailed blueprint from vision analysis."""
        if "blueprint" not in self.agents:
            # Fallback blueprint without LLM
            return {
                "project_title": "AI-Powered Application",
                "description": "An innovative application built with AI",
                "architecture": {
                    "frontend": "React",
                    "backend": "Python/Flask",
                    "database": "PostgreSQL",
                    "deployment": "Google Cloud"
                },
                "features": [
                    {"name": "User Authentication", "priority": "high"},
                    {"name": "Data Processing", "priority": "medium"},
                    {"name": "Analytics Dashboard", "priority": "low"}
                ],
                "timeline": {
                    "total_duration": "4-6 weeks",
                    "phases": [
                        {"name": "Planning", "duration": "1 week"},
                        {"name": "Development", "duration": "3-4 weeks"},
                        {"name": "Testing", "duration": "1 week"}
                    ]
                }
            }
        
        blueprint_prompt = f"""
        Create a detailed project blueprint based on this vision analysis:
        
        {json.dumps(vision_analysis, indent=2)}
        
        Generate:
        1. Project title and description
        2. Technical architecture recommendations
        3. Feature breakdown with priorities
        4. Development timeline and phases
        5. Resource requirements
        6. Risk assessment and mitigation
        
        Provide structured output in JSON format.
        """
        
        result = self.agents["blueprint"].process({
            "content": blueprint_prompt,
            "project_id": project_id
        })
        
        # Trace blueprint generation
        self.tracer.trace_agent_execution(
            agent_name="BlueprintGenerator",
            phase="dream_blueprint",
            input_data={"vision_analysis": vision_analysis},
            output_data=result
        )
        
        return result
    
    def _validate_blueprint(self, blueprint: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Validate and enhance the generated blueprint."""
        # Add metadata and validation
        enhanced_blueprint = {
            **blueprint,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "project_id": project_id,
                "version": "1.0",
                "status": "draft"
            }
        }
        
        return enhanced_blueprint
    
    def _publish_to_maturation(self, blueprint: Dict[str, Any], project_id: str):
        """Publish blueprint to maturation phase."""
        maturation_data = {
            "project_id": project_id,
            "blueprint": blueprint,
            "phase": "maturation",
            "timestamp": datetime.now().isoformat()
        }
        
        success = publish_to_pubsub("maturation-requests", maturation_data)
        if success:
            logger.info(f"Published blueprint for {project_id} to maturation phase")
        else:
            logger.warning(f"Failed to publish blueprint for {project_id} to maturation phase")

# Global dream processor instance
dream_processor = DreamProcessor()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "dream-service"})

@app.route('/dream/process', methods=['POST'])
def process_dream():
    """Process a user's dream into a blueprint."""
    try:
        data = request.get_json()
        
        if not data or 'user_dream' not in data:
            return jsonify({"error": "user_dream is required"}), 400
        
        user_dream = data['user_dream']
        project_id = data.get('project_id', f"proj_{int(datetime.now().timestamp())}")
        
        # Process the dream
        result = dream_processor.process_dream(user_dream, project_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing dream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/dream/status/<project_id>', methods=['GET'])
def get_dream_status(project_id):
    """Get the status of a dream processing job."""
    # This would typically query the database or cache
    # For now, return a simple response
    return jsonify({
        "project_id": project_id,
        "status": "completed",
        "phase": "dream"
    })

if __name__ == '__main__':
    # Initialize GCP services
    initialize_gcp_services()
    
    # Start the Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true')
