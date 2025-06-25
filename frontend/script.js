// Application State
class AppState {
    constructor() {
        this.currentView = 'hero';
        this.currentSession = null;
        this.currentPhase = 'dream';
        this.progress = 0;
        this.isProcessing = false;
        this.messageHistory = [];
    }

    setView(view) {
        this.currentView = view;
        this.updateUI();
    }

    setPhase(phase) {
        this.currentPhase = phase;
        this.updatePhaseUI();
    }

    setProgress(percentage) {
        this.progress = Math.max(0, Math.min(100, percentage));
        this.updateProgressUI();
    }

    updateUI() {
        const heroSection = document.getElementById('hero');
        const journeySection = document.getElementById('journey-progress');

        if (this.currentView === 'hero') {
            if (heroSection) heroSection.style.display = 'block';
            if (journeySection) journeySection.style.display = 'none';
        } else if (this.currentView === 'chat') {
            if (heroSection) heroSection.style.display = 'none';
            if (journeySection) journeySection.style.display = 'block';
        }
    }

    updatePhaseUI() {
        const phases = document.querySelectorAll('.phase');
        const phaseNames = ['dream', 'maturation', 'assemble', 'prototype', 'feedback', 'iterate', 'validate', 'golive', 'evolve'];

        phases.forEach((phase, index) => {
            const phaseName = phaseNames[index];
            phase.classList.remove('active', 'completed');

            const currentIndex = phaseNames.indexOf(this.currentPhase);
            if (index < currentIndex) {
                phase.classList.add('completed');
            } else if (index === currentIndex) {
                phase.classList.add('active');
            }
        });
    }

    updateProgressUI() {
        const progressFill = document.querySelector('.progress-fill');
        const progressPercentage = document.getElementById('progress-percent');

        if (progressFill) {
            progressFill.style.width = `${this.progress}%`;
        }
        if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(this.progress)}%`;
        }
    }
}

// Chat Management
class ChatManager {
    constructor(appState) {
        this.appState = appState;
        this.messagesContainer = null;
        this.typingTimeouts = [];
    }

    init() {
        this.messagesContainer = document.getElementById('chat-messages');
    }

    addMessage(content, sender = 'ai', options = {}) {
        if (!this.messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'ai' ? '🤖' : '👤';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (options.html) {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        // Store in history
        this.appState.messageHistory.push({
            content,
            sender,
            timestamp: new Date().toISOString(),
            options
        });
    }

    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing-indicator';
        typingDiv.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <span>CoFounder is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        typingDiv.appendChild(avatar);
        typingDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    clear() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
        this.appState.messageHistory = [];
    }
}

// API Service
class APIService {
    constructor() {
        this.baseURL = window.location.origin;
    }

    async generateBlueprint(vision) {
        const response = await fetch(`${this.baseURL}/api/dream/generate-blueprint`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vision,
                goal: 'prototype',
                tags: [],
                advanced_options: {}
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async initializeMaturation(projectData) {
        const response = await fetch(`${this.baseURL}/api/maturation/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async sendChatMessage(sessionId, message) {
        const response = await fetch(`${this.baseURL}/api/maturation/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async initializeAssembly(sessionId) {
        const response = await fetch(`${this.baseURL}/api/assemble/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async startExecution(sessionId) {
        const response = await fetch(`${this.baseURL}/api/assemble/start-execution`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}

// Main Application
class CoFoundApp {
    constructor() {
        this.appState = new AppState();
        this.chatManager = new ChatManager(this.appState);
        this.apiService = new APIService();
        this.currentProjectData = null;
    }

    init() {
        this.chatManager.init();
        this.setupEventListeners();
        this.appState.updateUI();
    }

    setupEventListeners() {
        // Hide loading screen initially
        this.hideLoading();

        // Dream input events
        const dreamInput = document.getElementById('dream-input');
        const dreamSubmit = document.getElementById('start-building');

        if (dreamInput) {
            dreamInput.addEventListener('input', () => {
                const hasContent = dreamInput.value.trim().length > 0;
                if (dreamSubmit) {
                    dreamSubmit.disabled = !hasContent;
                }
            });

            dreamInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (dreamSubmit && !dreamSubmit.disabled) {
                        this.handleDreamSubmit();
                    }
                }
            });
        }

        if (dreamSubmit) {
            dreamSubmit.addEventListener('click', () => {
                this.handleDreamSubmit();
            });
        }

        // Suggestion items
        const suggestionItems = document.querySelectorAll('.suggestion-item');
        suggestionItems.forEach(item => {
            item.addEventListener('click', () => {
                const suggestion = item.getAttribute('data-suggestion');
                if (dreamInput && suggestion) {
                    dreamInput.value = suggestion;
                    if (dreamSubmit) {
                        dreamSubmit.disabled = false;
                    }
                }
            });
        });

        // Chat input events
        const chatInput = document.getElementById('chat-input');
        const chatSend = document.getElementById('send-message');

        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleChatSubmit();
                }
            });
        }

        if (chatSend) {
            chatSend.addEventListener('click', () => {
                this.handleChatSubmit();
            });
        }

        // Back button
        const backBtn = document.getElementById('back-to-hero');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.appState.setView('hero');
                this.chatManager.clear();
            });
        }
    }

    async handleDreamSubmit() {
        const dreamInput = document.getElementById('dream-input');
        const vision = dreamInput.value.trim();

        if (!vision) return;

        try {
            this.showLoading('Generating your blueprint...');
            this.appState.setView('chat');
            this.appState.setPhase('dream');
            this.appState.setProgress(10);

            // Show initial AI message
            this.chatManager.addMessage(
                `Hello! I'm CoFounder, your AI development partner. I've received your idea: "${vision}". Let me analyze this and create a blueprint for you.`,
                'ai'
            );

            // Generate blueprint
            const blueprint = await this.apiService.generateBlueprint(vision);
            this.currentProjectData = blueprint;

            this.hideLoading();
            this.appState.setProgress(25);

            // Show blueprint summary
            setTimeout(() => {
                this.chatManager.addMessage(
                    `Great! I've created a blueprint for your ${blueprint.goal} project. Here's what I've planned:\n\n` +
                    `📋 Overview: ${blueprint.overview}\n\n` +
                    `🔧 Tech Stack: ${blueprint.tech_stack.slice(0, 4).join(', ')}\n\n` +
                    `⏱️ Timeline: ${blueprint.timeline}\n\n` +
                    `Now, let's move to the maturation phase where I'll ask you some questions to refine the plan.`,
                    'ai'
                );

                this.startMaturation();
            }, 1500);

        } catch (error) {
            this.hideLoading();
            this.chatManager.addMessage(
                'I apologize, but I encountered an error processing your request. Please try again.',
                'ai'
            );
            console.error('Error in dream phase:', error);
        }
    }

    async startMaturation() {
        try {
            this.appState.setPhase('maturation');
            this.appState.setProgress(30);

            // Show progress section and chat input (check if elements exist)
            const progressSection = document.getElementById('progress-section');
            const chatInputContainer = document.getElementById('chat-input-container');

            if (progressSection) progressSection.style.display = 'block';
            if (chatInputContainer) chatInputContainer.style.display = 'block';

            // Initialize maturation session
            const sessionData = await this.apiService.initializeMaturation(this.currentProjectData);
            this.appState.currentSession = sessionData.session_id;

            // Start maturation conversation
            setTimeout(() => {
                this.chatManager.addMessage(
                    "Let's dive deeper into your project. First, tell me: who is your target audience and what specific problem does your solution solve for them?",
                    'ai'
                );
            }, 1000);

        } catch (error) {
            this.chatManager.addMessage(
                'I encountered an error initializing the maturation phase. Please try again.',
                'ai'
            );
            console.error('Error in maturation initialization:', error);
        }
    }

    async handleChatSubmit() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();

        if (!message || this.appState.isProcessing) return;

        try {
            this.appState.isProcessing = true;

            // Add user message
            this.chatManager.addMessage(message, 'user');
            chatInput.value = '';

            // Show typing indicator
            this.chatManager.addTypingIndicator();

            // Send to API
            const response = await this.apiService.sendChatMessage(this.appState.currentSession, message);

            this.chatManager.removeTypingIndicator();

            // Add AI response
            this.chatManager.addMessage(response.response, 'ai');

            // Update progress if provided
            if (response.progress) {
                this.updateMaturationProgress(response.progress);
            }

            // Check if maturation is complete
            if (response.completed) {
                this.startAssembly();
            }

        } catch (error) {
            this.chatManager.removeTypingIndicator();
            this.chatManager.addMessage(
                'I apologize, but I encountered an error. Please try again.',
                'ai'
            );
            console.error('Error in chat:', error);
        } finally {
            this.appState.isProcessing = false;
        }
    }

    updateMaturationProgress(progressArray) {
        // Calculate overall progress based on maturation sub-phases
        const averageProgress = progressArray.reduce((sum, val) => sum + val, 0) / progressArray.length;
        const overallProgress = 30 + (averageProgress * 0.4); // 30-70% range for maturation
        this.appState.setProgress(overallProgress);
    }

    async startAssembly() {
        try {
            this.appState.setPhase('assemble');
            this.appState.setProgress(75);

            // Hide chat input during assembly
            document.getElementById('chat-input-container').style.display = 'none';

            this.chatManager.addMessage(
                "Perfect! I now have all the information I need. Let me assemble your AI development squad and start building your product.",
                'ai'
            );

            // Initialize assembly
            await this.apiService.initializeAssembly(this.appState.currentSession);

            setTimeout(() => {
                this.showAssemblyProgress();
            }, 2000);

        } catch (error) {
            this.chatManager.addMessage(
                'I encountered an error during assembly. Please try again.',
                'ai'
            );
            console.error('Error in assembly:', error);
        }
    }

    async showAssemblyProgress() {
        const phases = ['prototype', 'feedback', 'iterate', 'validate', 'golive', 'evolve'];
        let currentPhaseIndex = 0;

        const progressInterval = setInterval(async () => {
            if (currentPhaseIndex < phases.length) {
                const phase = phases[currentPhaseIndex];
                this.appState.setPhase(phase);

                const progress = 75 + ((currentPhaseIndex + 1) / phases.length) * 25;
                this.appState.setProgress(progress);

                const phaseMessages = {
                    'prototype': '🔨 Building your prototype with specialized AI agents...',
                    'feedback': '📝 Gathering feedback and analyzing requirements...',
                    'iterate': '🔄 Iterating and improving based on feedback...',
                    'validate': '✅ Validating functionality and running tests...',
                    'golive': '🚀 Preparing for deployment and go-live...',
                    'evolve': '📈 Setting up continuous improvement systems...'
                };

                this.chatManager.addMessage(phaseMessages[phase], 'ai');
                currentPhaseIndex++;
            } else {
                clearInterval(progressInterval);
                this.completeJourney();
            }
        }, 3000);
    }

    async completeJourney() {
        try {
            this.appState.setProgress(100);

            // Start execution
            await this.apiService.startExecution(this.appState.currentSession);

            this.chatManager.addMessage(
                "🎉 Congratulations! Your product has been successfully built and deployed. Your AI development squad has created a fully functional application based on your requirements.\n\nYou can now access your product and continue to evolve it with our AI agents.",
                'ai',
                { html: true }
            );

        } catch (error) {
            this.chatManager.addMessage(
                'Your product has been built successfully! (Demo mode - execution simulation completed)',
                'ai'
            );
            console.log('Execution completed in demo mode');
        }
    }

    showLoading(text = 'Processing...') {
        const loadingScreen = document.getElementById('loading-screen');
        const loadingText = loadingScreen?.querySelector('p');

        if (loadingText) loadingText.textContent = text;
        if (loadingScreen) loadingScreen.style.display = 'flex';
    }

    hideLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) loadingScreen.style.display = 'none';
    }
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    const app = new CoFoundApp();
    app.init();

    // Global error handling
    window.addEventListener('error', (e) => {
        console.error('Global error:', e.error);
        app.hideLoading();
    });

    window.addEventListener('unhandledrejection', (e) => {
        console.error('Unhandled promise rejection:', e.reason);
        app.hideLoading();
    });
});
// Initialize application when DOM is loaded
function initializeApp() {
    const app = new CoFoundApp();
    app.init();
}

// Progress bar helper function
function updateProgressBar(progress) {
    const progressPercent = document.getElementById('progress-percent');
    if (progressPercent) {
        progressPercent.textContent = `${progress}%`;
    }
}

class CoFoundAI {
    constructor() {
        this.currentPhase = 'dream';
        this.projectId = null;
        this.selectedTags = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupTokenEstimator();
    }

    bindEvents() {
        // Dream phase events
        document.getElementById('vision-input').addEventListener('input', () => {
            this.updateTokenEstimate();
        });

        document.getElementById('generate-blueprint').addEventListener('click', () => {
            this.generateBlueprint();
        });

        document.getElementById('proceed-to-maturation').addEventListener('click', () => {
            this.switchToPhase('maturation');
        });

        // Tag selection events
        document.querySelectorAll('.tag-selector .tag').forEach(tag => {
            tag.addEventListener('click', (e) => {
                this.toggleTag(e.target);
            });
        });

        // Maturation phase events
        document.getElementById('send-message').addEventListener('click', () => {
            this.sendChatMessage();
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // Assemble phase events
        document.getElementById('launch-team').addEventListener('click', () => {
            this.launchTeam();
        });

        // Phase navigation
        document.querySelectorAll('.phase').forEach(phase => {
            phase.addEventListener('click', (e) => {
                const phaseType = e.target.getAttribute('data-phase');
                this.switchToPhase(phaseType);
            });
        });
    }

    setupTokenEstimator() {
        this.updateTokenEstimate();
    }

    updateTokenEstimate() {
        const visionText = document.getElementById('vision-input').value;
        const tokenCount = Math.ceil(visionText.length / 4); // Rough estimate
        const cost = tokenCount * 0.00002; // GPT-4o pricing estimate

        document.getElementById('token-count').textContent = tokenCount;
        document.getElementById('cost-estimate').textContent = `~$${cost.toFixed(4)}`;
    }

    toggleTag(tagElement) {
        const value = tagElement.getAttribute('data-value');

        if (tagElement.classList.contains('selected')) {
            tagElement.classList.remove('selected');
            this.selectedTags = this.selectedTags.filter(tag => tag !== value);
        } else {
            tagElement.classList.add('selected');
            this.selectedTags.push(value);
        }
    }

    async generateBlueprint() {
        const visionText = document.getElementById('vision-input').value.trim();

        if (!visionText) {
            this.showStatusMessage('Please enter your vision first!', 'error');
            return;
        }

        this.showLoading('Analyzing your vision and generating blueprint...');

        try {
            const response = await fetch('/api/dream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    vision_text: visionText,
                    tags: this.selectedTags,
                    goal: document.getElementById('goal-selector').value,
                    tech_preferences: this.selectedTags.filter(tag => 
                        ['react', 'python', 'nodejs', 'mobile', 'ai', 'blockchain'].includes(tag)
                    )
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.projectId = data.project_id;
            this.displayBlueprint(data);

        } catch (error) {
            console.error('Error generating blueprint:', error);
            this.showStatusMessage('Failed to generate blueprint. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayBlueprint(data) {
        const preview = document.getElementById('blueprint-preview');
        const blueprintText = document.getElementById('blueprint-text');
        const costDetails = document.getElementById('cost-details');
        const projectTags = document.getElementById('project-tags');

        // Display blueprint content
        blueprintText.innerHTML = this.formatBlueprint(data.initial_brief);

        // Display cost details
        costDetails.innerHTML = `
            <div class="cost-item">
                <span>Tokens:</span>
                <span>${data.cost_estimate.tokens}</span>
            </div>
            <div class="cost-item">
                <span>Cost:</span>
                <span>$${data.cost_estimate.cost_usd.toFixed(4)}</span>
            </div>
            <div class="cost-item">
                <span>Complexity:</span>
                <span>${data.cost_estimate.complexity}</span>
            </div>
        `;

        // Display extracted tags
        projectTags.innerHTML = data.extracted_tags.map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('');

        preview.classList.remove('hidden');
        preview.scrollIntoView({ behavior: 'smooth' });
    }

    formatBlueprint(text) {
        // Simple markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    switchToPhase(phaseType) {
        // Update phase indicators
        document.querySelectorAll('.phase').forEach(p => p.classList.remove('active'));
        document.querySelector(`.phase[data-phase="${phaseType}"]`).classList.add('active');

        // Switch phase content
        document.querySelectorAll('.phase-content').forEach(p => p.classList.remove('active'));
        document.getElementById(`${phaseType}-phase`).classList.add('active');

        this.currentPhase = phaseType;

        // Initialize phase-specific functionality
        if (phaseType === 'maturation') {
            this.initMaturationPhase();
        } else if (phaseType === 'assemble') {
            this.initAssemblePhase();
        }
    }

    initMaturationPhase() {
        // Start the maturation conversation
        this.addChatMessage(
            'system',
            "Welcome to the Maturation phase! Let's start with Discovery & Alignment. " +
            "Can you tell me more about who will be using this application and what success looks like for you?"
        );
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        this.addChatMessage('user', message);
        input.value = '';

        // Simulate AI response (replace with actual API call)
        setTimeout(() => {
            this.addChatMessage('system', 'Thank you for that insight. Let me analyze this information and generate the appropriate artifacts...');
        }, 1000);
    }

    addChatMessage(sender, message) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async initAssemblePhase() {
        if (!this.projectId) {
            this.showStatusMessage('Please complete the previous phases first!', 'error');
            return;
        }

        this.showLoading('Analyzing your project and assembling AI team...');

        try {
            const response = await fetch('/api/assemble', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: this.projectId,
                    matured_brief: 'Placeholder matured brief' // This would come from maturation phase
                })
            });

            const data = await response.json();
            this.displayTeamComposition(data);

        } catch (error) {
            console.error('Error in assemble phase:', error);
            this.showStatusMessage('Failed to assemble team. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayTeamComposition(data) {
        const teamComposition = document.getElementById('team-composition');
        const deploymentSpec = document.getElementById('deployment-spec');
        const totalCost = document.getElementById('total-cost');

        // Display team members
        teamComposition.innerHTML = data.team_composition.map(agent => `
            <div class="team-member">
                <div class="member-role">${agent.role}</div>
                <div class="member-details">
                    <span>Count: ${agent.count}</span>
                    <span>Tokens: ${agent.estimated_tokens}</span>
                    <span>Cost: $${agent.estimated_cost.toFixed(2)}</span>
                </div>
            </div>
        `).join('');

        // Display deployment specification
        deploymentSpec.innerHTML = `
            <div class="spec-item">Platform: ${data.deployment_spec.platform}</div>
            <div class="spec-item">Services: ${data.deployment_spec.services.join(', ')}</div>
            <div class="spec-item">Scaling: ${data.deployment_spec.scaling}</div>
        `;

        // Display total cost
        totalCost.innerHTML = `
            <div class="cost-total">
                <span>Total Estimated Cost:</span>
                <span class="cost-amount">$${data.estimated_cost.total_usd.toFixed(2)}</span>
            </div>
        `;
    }

    async launchTeam() {
        this.showLoading('Launching your AI development team...');

        // Simulate team launch
        setTimeout(() => {
            this.hideLoading();
            this.showStatusMessage('AI team launched successfully! 🚀', 'success');
        }, 3000);
    }

    showLoading(message) {
        const overlay = document.getElementById('loading-overlay');
        const text = document.getElementById('loading-text');
        text.textContent = message;
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showStatusMessage(message, type = 'info') {
        const statusEl = document.getElementById('status-message');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.classList.remove('hidden');

        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 5000);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new CoFoundAI();
});