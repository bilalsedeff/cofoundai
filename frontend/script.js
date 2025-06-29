// CoFound.ai Frontend JavaScript - Local Development
const API_BASE_URL = 'http://localhost:5000';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
    setupEventListeners();
});

function setupEventListeners() {
    // Enter key support for textarea
    document.getElementById('dreamInput').addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            submitDream();
        }
    });
}

async function checkSystemStatus() {
    try {
        // Check backend API
        const response = await fetch(`${API_BASE_URL}/health`);
        const status = await response.json();

        document.getElementById('backendStatus').textContent = '✅ Online';
        document.getElementById('backendStatus').className = 'status-value success';

        // Update database status based on response
        if (status.database) {
            document.getElementById('databaseStatus').textContent = '✅ Connected';
            document.getElementById('databaseStatus').className = 'status-value success';
        } else {
            document.getElementById('databaseStatus').textContent = '❌ Disconnected';
            document.getElementById('databaseStatus').className = 'status-value error';
        }

    } catch (error) {
        document.getElementById('backendStatus').textContent = '❌ Offline';
        document.getElementById('backendStatus').className = 'status-value error';
        document.getElementById('databaseStatus').textContent = '❌ Unknown';
        document.getElementById('databaseStatus').className = 'status-value error';
    }
}

async function submitDream() {
    const dreamText = document.getElementById('dreamInput').value.trim();

    if (!dreamText) {
        alert('Please enter your software project idea first!');
        return;
    }

    // Show loading state
    const button = document.getElementById('generateBtn');
    const originalText = button.textContent;
    button.textContent = 'Processing...';
    button.disabled = true;

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">🤖 CoFound.ai agents are working on your dream...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/dream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: 'local-user',
                projectId: `project-${Date.now()}`,
                promptText: dreamText
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        displayResults(result);

    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>❌ Error</h3>
                <p>Failed to process your dream: ${error.message}</p>
                <p>Make sure the backend server is running on port 5000.</p>
            </div>
        `;
    } finally {
        // Reset button
        button.textContent = originalText;
        button.disabled = false;
    }
}

function displayResults(result) {
    const resultsDiv = document.getElementById('results');

    if (result.success) {
        resultsDiv.innerHTML = `
            <div class="success">
                <h3>✅ Blueprint Generated Successfully!</h3>
                <div class="result-content">
                    <h4>📋 Project Overview:</h4>
                    <p>${result.data.vision || 'Vision generated by AI agents'}</p>

                    <h4>🎯 Objectives:</h4>
                    <ul>
                        ${(result.data.objectives || ['Objective 1', 'Objective 2']).map(obj => `<li>${obj}</li>`).join('')}
                    </ul>

                    <h4>🔧 Technical Stack:</h4>
                    <p>${result.data.tech_stack || 'Technology recommendations from AI agents'}</p>

                    <h4>📈 Next Steps:</h4>
                    <ol>
                        <li>Review and refine the blueprint</li>
                        <li>Move to Architecture phase</li>
                        <li>Begin development with AI agents</li>
                    </ol>
                </div>
            </div>
        `;
    } else {
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>❌ Processing Failed</h3>
                <p>${result.message || 'Unknown error occurred'}</p>
            </div>
        `;
    }
}

// Auto-refresh status every 30 seconds
setInterval(checkSystemStatus, 30000);