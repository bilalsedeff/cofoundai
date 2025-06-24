from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cofoundai.communication.protocol import register_agent_protocol_routes
from cofoundai.orchestration.agentic_graph import AgenticGraph
from cofoundai.agents.langgraph_agent import LangGraphAgent

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)

# Register Agent Protocol routes
register_agent_protocol_routes(app)

# Global session storage (in production, use Redis or database)
sessions = {}

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "CoFound.ai Backend API"})

@app.route('/api/dream/generate-blueprint', methods=['POST'])
def generate_blueprint():
    """Generate blueprint from user vision."""
    try:
        data = request.get_json()
        vision = data.get('vision', '')

        # Create project ID
        project_id = f"proj_{int(datetime.now().timestamp())}"

        # Create simple blueprint response
        blueprint = {
            "project_id": project_id,
            "vision": vision,
            "goal": data.get('goal', 'web_application'),
            "overview": f"Creating a {data.get('goal', 'web application')} based on: {vision[:100]}...",
            "tech_stack": ["Python", "Flask", "JavaScript", "HTML/CSS", "SQLite"],
            "timeline": "2-4 weeks estimated development time",
            "status": "blueprint_generated"
        }

        return jsonify(blueprint)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/maturation/initialize', methods=['POST'])
def initialize_maturation():
    """Initialize maturation session."""
    try:
        data = request.get_json()
        project_id = data.get('project_id', f"proj_{int(datetime.now().timestamp())}")

        # Create session
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Store session
        sessions[session_id] = {
            "project_id": project_id,
            "phase": "maturation",
            "progress": [25, 0, 0, 0],  # Discovery, Definition, Technical, Governance
            "created_at": datetime.now().isoformat(),
            "data": data
        }

        return jsonify({
            "session_id": session_id,
            "status": "initialized",
            "phase": "maturation"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/maturation/chat', methods=['POST'])
def maturation_chat():
    """Handle maturation phase chat."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message', '')

        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        session = sessions[session_id]

        # Simple response logic
        response_text = f"Thank you for that information: '{message}'. "

        if "target audience" in message.lower() or "users" in message.lower():
            response_text += "Great! Now tell me about the core features you envision. What are the 3-5 most important things users should be able to do?"
            session["progress"][0] = 50
        elif "feature" in message.lower() or "function" in message.lower():
            response_text += "Excellent! Now let's discuss the technical requirements. Do you have any preferences for technology stack, performance requirements, or integration needs?"
            session["progress"][1] = 75
        elif "technical" in message.lower() or "technology" in message.lower():
            response_text += "Perfect! We have enough information to move to the assembly phase. Your maturation is complete!"
            session["progress"] = [100, 100, 100, 100]
            completed = True
        else:
            response_text += "Can you provide more details about your target users and what problems this solves for them?"

        # Check if completed
        completed = all(p >= 75 for p in session["progress"])

        return jsonify({
            "response": response_text,
            "progress": session["progress"],
            "completed": completed,
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/assemble/initialize', methods=['POST'])
def initialize_assembly():
    """Initialize assembly phase."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        session = sessions[session_id]
        session["phase"] = "assembly"

        return jsonify({
            "status": "assembly_initialized",
            "agents": ["Planner", "Architect", "Developer", "Tester", "Reviewer", "Documentor"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/assemble/start-execution', methods=['POST'])
def start_execution():
    """Start execution phase."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        session = sessions[session_id]
        session["phase"] = "execution"
        session["status"] = "completed"

        return jsonify({
            "status": "execution_started",
            "message": "Multi-agent workflow initiated successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible externally
    app.run(host='0.0.0.0', port=5000, debug=True)