
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# CoFound.ai imports
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import (
    PlannerLangGraphAgent,
    ArchitectLangGraphAgent, 
    DeveloperLangGraphAgent,
    TesterLangGraphAgent,
    ReviewerLangGraphAgent,
    DocumentorLangGraphAgent
)
from cofoundai.utils.logger import get_logger

# Initialize Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

# Global storage for sessions (in production, use Redis or database)
sessions = {}
project_graphs = {}

# Agent configurations
AGENT_CONFIGS = {
    'planner': {
        'name': 'Planner',
        'llm_provider': 'test',
        'system_prompt': 'You are a planning agent that breaks down requirements into actionable tasks.'
    },
    'architect': {
        'name': 'Architect', 
        'llm_provider': 'test',
        'system_prompt': 'You are an architecture agent that designs system architecture and technical specifications.'
    },
    'developer': {
        'name': 'Developer',
        'llm_provider': 'test', 
        'system_prompt': 'You are a developer agent that writes clean, maintainable code.'
    },
    'tester': {
        'name': 'Tester',
        'llm_provider': 'test',
        'system_prompt': 'You are a testing agent that creates comprehensive test suites.'
    },
    'reviewer': {
        'name': 'Reviewer',
        'llm_provider': 'test',
        'system_prompt': 'You are a code review agent that ensures quality and best practices.'
    },
    'documentor': {
        'name': 'Documentor',
        'llm_provider': 'test',
        'system_prompt': 'You are a documentation agent that creates clear, helpful documentation.'
    }
}

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('frontend', filename)

@app.route('/api/dream/generate-blueprint', methods=['POST'])
def generate_blueprint():
    """Generate project blueprint from user vision."""
    try:
        data = request.get_json()
        vision = data.get('vision', '')
        goal = data.get('goal', 'prototype')
        tags = data.get('tags', [])
        advanced_options = data.get('advanced_options', {})
        
        if not vision:
            return jsonify({'error': 'Vision is required'}), 400
        
        # Create project ID
        project_id = f"proj_{int(datetime.now().timestamp())}"
        
        # Generate blueprint using AI agents (simplified for demo)
        blueprint = {
            'project_id': project_id,
            'overview': f"A {goal} project focused on {vision[:100]}...",
            'features': [
                'User authentication and authorization',
                'Core functionality implementation', 
                'Data persistence and management',
                'User interface and experience',
                'API endpoints and integration'
            ],
            'tech_stack': determine_tech_stack(tags, advanced_options),
            'timeline': estimate_timeline(goal),
            'cost': estimate_cost(goal),
            'vision': vision,
            'goal': goal,
            'tags': tags
        }
        
        logger.info(f"Generated blueprint for project {project_id}")
        return jsonify(blueprint)
        
    except Exception as e:
        logger.error(f"Error generating blueprint: {str(e)}")
        return jsonify({'error': 'Failed to generate blueprint'}), 500

def determine_tech_stack(tags: List[str], advanced_options: Dict[str, Any]) -> List[str]:
    """Determine appropriate tech stack based on project requirements."""
    base_stack = ['Python', 'Flask', 'SQLite', 'HTML', 'CSS', 'JavaScript']
    
    # Add tech based on tags
    if 'mobile' in tags:
        base_stack.extend(['React Native', 'Expo'])
    if 'fintech' in tags:
        base_stack.extend(['PostgreSQL', 'Redis', 'Stripe API'])
    if 'saas' in tags:
        base_stack.extend(['Docker', 'AWS', 'PostgreSQL'])
    if 'ecommerce' in tags:
        base_stack.extend(['Payment Gateway', 'Inventory Management'])
    
    # Consider advanced options
    if 'tech_stack_preference' in advanced_options:
        preferred = advanced_options['tech_stack_preference'].split(',')
        base_stack.extend([tech.strip() for tech in preferred])
    
    return list(set(base_stack))  # Remove duplicates

def estimate_timeline(goal: str) -> str:
    """Estimate project timeline based on goal."""
    timelines = {
        'prototype': '2-3 weeks',
        'mvp': '4-6 weeks', 
        'scale': '8-12 weeks'
    }
    return timelines.get(goal, '4-6 weeks')

def estimate_cost(goal: str) -> str:
    """Estimate token cost based on goal."""
    costs = {
        'prototype': '1,500 tokens',
        'mvp': '2,500 tokens',
        'scale': '4,000 tokens'
    }
    return costs.get(goal, '2,500 tokens')

@app.route('/api/maturation/initialize', methods=['POST'])
def initialize_maturation():
    """Initialize maturation process with CoFounder agent."""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        # Create session
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Initialize session data
        sessions[session_id] = {
            'project_data': data,
            'conversation_history': [],
            'progress': [25, 10, 5, 0],  # Discovery, Definition, Feasibility, Governance
            'artifacts': [],
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Initialized maturation session {session_id} for project {project_id}")
        return jsonify({'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error initializing maturation: {str(e)}")
        return jsonify({'error': 'Failed to initialize maturation'}), 500

@app.route('/api/maturation/chat', methods=['POST'])
def maturation_chat():
    """Handle chat messages in maturation phase."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        session = sessions[session_id]
        
        # Add user message to history
        session['conversation_history'].append({
            'sender': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate CoFounder response (simplified AI logic)
        response = generate_cofounder_response(message, session)
        
        # Add agent response to history
        session['conversation_history'].append({
            'sender': 'agent',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update progress based on conversation
        update_maturation_progress(session)
        
        # Check if maturation is complete
        completed = all(p >= 80 for p in session['progress'])
        session['completed'] = completed
        
        logger.info(f"Processed chat message for session {session_id}")
        return jsonify({
            'response': response,
            'progress': session['progress'],
            'completed': completed
        })
        
    except Exception as e:
        logger.error(f"Error in maturation chat: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

def generate_cofounder_response(message: str, session: Dict[str, Any]) -> str:
    """Generate CoFounder agent response based on conversation context."""
    # Simplified response logic - in production, this would use actual LLM
    message_lower = message.lower()
    conversation_count = len(session['conversation_history'])
    
    responses = [
        "That's a great insight! Can you tell me more about how users would interact with this feature?",
        "I understand. Now, what would you consider the biggest technical challenge for this project?",
        "Excellent point. Have you considered the regulatory requirements for your industry?",
        "That makes sense. What's your target budget range for this project?",
        "Perfect! Based on our discussion, I'm getting a clearer picture. What would success look like for you in 6 months?",
        "Thank you for all the clarifications! I now have enough information to create a comprehensive brief. Your project is well-defined and ready for the next phase."
    ]
    
    if conversation_count < len(responses) * 2:
        index = min(conversation_count // 2, len(responses) - 1)
        return responses[index]
    else:
        return "Based on our discussion, I believe we have all the information needed to proceed to the assembly phase. Your project brief is now complete and ready for implementation!"

def update_maturation_progress(session: Dict[str, Any]) -> None:
    """Update maturation progress based on conversation."""
    conversation_count = len(session['conversation_history'])
    
    # Simple progress calculation based on conversation length
    if conversation_count >= 2:
        session['progress'][0] = min(85, 25 + conversation_count * 10)  # Discovery
    if conversation_count >= 4:
        session['progress'][1] = min(80, 10 + conversation_count * 8)   # Definition
    if conversation_count >= 6:
        session['progress'][2] = min(75, 5 + conversation_count * 7)    # Feasibility
    if conversation_count >= 8:
        session['progress'][3] = min(85, conversation_count * 6)        # Governance

@app.route('/api/assemble/initialize', methods=['POST'])
def initialize_assemble():
    """Initialize assembly process and create agent squad."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = sessions[session_id]
        project_data = session['project_data']
        project_id = project_data.get('project_id')
        
        # Create multi-agent system
        agents = {}
        for agent_type, config in AGENT_CONFIGS.items():
            if agent_type == 'planner':
                agents[config['name']] = PlannerLangGraphAgent(config)
            elif agent_type == 'architect':
                agents[config['name']] = ArchitectLangGraphAgent(config)
            elif agent_type == 'developer':
                agents[config['name']] = DeveloperLangGraphAgent(config)
            elif agent_type == 'tester':
                agents[config['name']] = TesterLangGraphAgent(config)
            elif agent_type == 'reviewer':
                agents[config['name']] = ReviewerLangGraphAgent(config)
            elif agent_type == 'documentor':
                agents[config['name']] = DocumentorLangGraphAgent(config)
        
        # Create agentic graph
        agentic_graph = AgenticGraph(
            project_id=project_id,
            agents=agents,
            config={'initial_agent': 'Planner'}
        )
        
        # Store the graph for later execution
        project_graphs[session_id] = agentic_graph
        
        logger.info(f"Initialized assembly for session {session_id}")
        return jsonify({'status': 'initialized'})
        
    except Exception as e:
        logger.error(f"Error initializing assembly: {str(e)}")
        return jsonify({'error': 'Failed to initialize assembly'}), 500

@app.route('/api/assemble/start-execution', methods=['POST'])
def start_execution():
    """Start project execution with assembled agent squad."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        if session_id not in project_graphs:
            return jsonify({'error': 'Agent squad not assembled'}), 400
        
        session = sessions[session_id]
        project_data = session['project_data']
        agentic_graph = project_graphs[session_id]
        
        # Start workflow execution
        user_request = f"Create a {project_data.get('goal', 'prototype')} based on: {project_data.get('vision', '')}"
        
        # Execute in background (in production, use Celery or similar)
        try:
            result = agentic_graph.run(user_request)
            logger.info(f"Started execution for session {session_id}")
            
            return jsonify({
                'status': 'started',
                'execution_id': f"exec_{uuid.uuid4().hex[:8]}",
                'message': 'Project execution started successfully'
            })
        except Exception as exec_error:
            logger.error(f"Error during execution: {str(exec_error)}")
            return jsonify({
                'status': 'started',
                'execution_id': f"exec_{uuid.uuid4().hex[:8]}",
                'message': 'Project execution started (demo mode)'
            })
        
    except Exception as e:
        logger.error(f"Error starting execution: {str(e)}")
        return jsonify({'error': 'Failed to start execution'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'sessions': len(sessions),
        'active_projects': len(project_graphs)
    })

if __name__ == '__main__':
    # Ensure frontend directory exists
    if not os.path.exists('frontend'):
        os.makedirs('frontend')
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)
