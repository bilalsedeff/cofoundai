
import os
import json
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import glob

app = Flask(__name__)

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CoFound.ai Development Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .phase-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .phase-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .phase-title { color: #333; margin-bottom: 10px; }
        .status { padding: 5px 10px; border-radius: 5px; color: white; font-weight: bold; }
        .status.active { background: #4CAF50; }
        .status.pending { background: #FF9800; }
        .status.completed { background: #2196F3; }
        .logs { background: #1a1a1a; color: #00ff00; padding: 15px; border-radius: 5px; font-family: monospace; max-height: 300px; overflow-y: auto; }
        .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .metric-label { color: #666; margin-top: 5px; }
    </style>
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        function updateDashboard(data) {
            document.getElementById('total-projects').textContent = data.total_projects || 0;
            document.getElementById('active-sessions').textContent = data.active_sessions || 0;
            document.getElementById('completed-workflows').textContent = data.completed_workflows || 0;
            
            // Update logs
            const logsDiv = document.getElementById('logs');
            logsDiv.innerHTML = data.recent_logs?.join('\\n') || 'No recent logs';
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        setInterval(refreshData, 5000); // Refresh every 5 seconds
        window.addEventListener('load', refreshData);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CoFound.ai Development Monitor</h1>
            <p>Real-time monitoring of your multi-agent development system</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" id="total-projects">0</div>
                <div class="metric-label">Total Projects</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="active-sessions">0</div>
                <div class="metric-label">Active Sessions</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="completed-workflows">0</div>
                <div class="metric-label">Completed Workflows</div>
            </div>
        </div>
        
        <div class="phase-grid">
            <div class="phase-card">
                <h3 class="phase-title">💡 Dream Phase</h3>
                <span class="status active">ACTIVE</span>
                <p>User input processing and blueprint generation</p>
            </div>
            
            <div class="phase-card">
                <h3 class="phase-title">🌱 Maturation Phase</h3>
                <span class="status active">ACTIVE</span>
                <p>Requirements refinement and planning</p>
            </div>
            
            <div class="phase-card">
                <h3 class="phase-title">🔧 Assemble Phase</h3>
                <span class="status pending">PENDING</span>
                <p>Agent coordination and workflow setup</p>
            </div>
            
            <div class="phase-card">
                <h3 class="phase-title">🤖 LangGraph Status</h3>
                <span class="status active">RUNNING</span>
                <p>Multi-agent orchestration system</p>
            </div>
        </div>
        
        <div class="phase-card">
            <h3 class="phase-title">📊 System Logs</h3>
            <div class="logs" id="logs">
                Loading logs...
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the monitoring dashboard."""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/status')
def get_status():
    """Get system status and metrics."""
    try:
        # Count project files
        project_files = glob.glob('demos/projects/*/workflow_*.json')
        total_projects = len(set([f.split('/')[-2] for f in project_files]))
        
        # Get recent log files
        recent_logs = []
        log_files = glob.glob('logs/*.log')
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            try:
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    recent_logs = [line.strip() for line in lines[-10:]]
            except:
                recent_logs = ["Unable to read log file"]
        else:
            recent_logs = ["No log files found"]
        
        return jsonify({
            "total_projects": total_projects,
            "active_sessions": 1 if total_projects > 0 else 0,
            "completed_workflows": len(project_files),
            "recent_logs": recent_logs,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "total_projects": 0,
            "active_sessions": 0,
            "completed_workflows": 0,
            "recent_logs": [f"Error: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
