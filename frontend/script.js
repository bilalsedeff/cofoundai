
// Global state management
let currentStep = 'dream';
let projectData = {};
let currentSession = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up navigation
    setupNavigation();
    
    // Set up event listeners
    setupEventListeners();
    
    // Show initial step
    showStep('dream');
}

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const step = this.getAttribute('href').substring(1);
            showStep(step);
        });
    });
}

function setupEventListeners() {
    // Tag selection
    const tags = document.querySelectorAll('.tag');
    tags.forEach(tag => {
        tag.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });
    
    // Chat input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

function showStep(step) {
    // Hide all sections
    document.querySelectorAll('.step-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(step).classList.add('active');
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[href="#${step}"]`).classList.add('active');
    
    currentStep = step;
}

function toggleAdvancedOptions() {
    const button = document.querySelector('.toggle-advanced');
    const content = document.querySelector('.advanced-content');
    
    if (content.style.display === 'none' || !content.style.display) {
        content.style.display = 'block';
        button.classList.add('active');
    } else {
        content.style.display = 'none';
        button.classList.remove('active');
    }
}

async function generateBlueprint() {
    const visionInput = document.getElementById('vision-input').value;
    const goalSelector = document.getElementById('goal-selector').value;
    const selectedTags = Array.from(document.querySelectorAll('.tag.active')).map(tag => tag.getAttribute('data-tag'));
    
    if (!visionInput.trim()) {
        alert('Please describe your vision first.');
        return;
    }
    
    // Show loading
    showLoading('Generating your blueprint...');
    
    try {
        // Prepare request data
        const requestData = {
            vision: visionInput,
            goal: goalSelector,
            tags: selectedTags,
            advanced_options: getAdvancedOptions()
        };
        
        // Call backend API
        const response = await fetch('/api/dream/generate-blueprint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            const result = await response.json();
            displayBlueprint(result);
            projectData = result;
        } else {
            throw new Error('Failed to generate blueprint');
        }
    } catch (error) {
        console.error('Error generating blueprint:', error);
        alert('Failed to generate blueprint. Please try again.');
    } finally {
        hideLoading();
    }
}

function getAdvancedOptions() {
    const advancedContent = document.querySelector('.advanced-content');
    if (advancedContent.style.display === 'none') {
        return {};
    }
    
    const inputs = advancedContent.querySelectorAll('input, select');
    const options = {};
    
    inputs.forEach(input => {
        if (input.value) {
            const key = input.previousElementSibling.textContent.toLowerCase().replace(/\s+/g, '_');
            options[key] = input.value;
        }
    });
    
    return options;
}

function displayBlueprint(data) {
    const preview = document.getElementById('blueprint-preview');
    
    // Update content
    document.getElementById('project-overview').textContent = data.overview || 'Generated based on your vision and requirements.';
    
    const featuresList = document.getElementById('key-features');
    featuresList.innerHTML = '';
    (data.features || []).forEach(feature => {
        const li = document.createElement('li');
        li.textContent = feature;
        featuresList.appendChild(li);
    });
    
    const techStack = document.getElementById('tech-stack');
    techStack.innerHTML = '';
    (data.tech_stack || []).forEach(tech => {
        const span = document.createElement('span');
        span.textContent = tech;
        techStack.appendChild(span);
    });
    
    document.getElementById('timeline-estimate').textContent = data.timeline || '4-6 weeks';
    document.getElementById('cost-estimate').textContent = data.cost || '2,500 tokens';
    
    // Show preview
    preview.style.display = 'block';
}

function editBlueprint() {
    const preview = document.getElementById('blueprint-preview');
    preview.style.display = 'none';
}

async function proceedToMaturation() {
    if (!projectData || !projectData.overview) {
        alert('Please generate a blueprint first.');
        return;
    }
    
    showLoading('Initializing maturation process...');
    
    try {
        // Initialize maturation session
        const response = await fetch('/api/maturation/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });
        
        if (response.ok) {
            const result = await response.json();
            currentSession = result.session_id;
            showStep('maturation');
            initializeMaturationChat();
        } else {
            throw new Error('Failed to initialize maturation');
        }
    } catch (error) {
        console.error('Error initializing maturation:', error);
        alert('Failed to start maturation process. Please try again.');
    } finally {
        hideLoading();
    }
}

function initializeMaturationChat() {
    const chatMessages = document.getElementById('chat-messages');
    
    // Add initial CoFounder message
    setTimeout(() => {
        addChatMessage(
            "Hello! I'm your CoFounder agent. I've reviewed your initial blueprint and I have some questions to help clarify and strengthen your concept. Let's work together to turn your idea into a solid, executable plan.\n\nFirst, let me ask: Who is your primary target audience, and what specific problem does your solution solve for them?",
            'agent'
        );
    }, 1000);
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send message to backend
        const response = await fetch('/api/maturation/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSession,
                message: message
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add agent response
            addChatMessage(result.response, 'agent');
            
            // Update progress if provided
            if (result.progress) {
                updateMaturationProgress(result.progress);
            }
            
            // Check if maturation is complete
            if (result.completed) {
                document.getElementById('proceed-assemble').disabled = false;
            }
        } else {
            throw new Error('Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'agent');
    }
}

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message agent-message typing-indicator';
    typingDiv.innerHTML = '<div class="message-content">CoFounder is typing...</div>';
    typingDiv.id = 'typing-indicator';
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function updateMaturationProgress(progress) {
    const metrics = document.querySelectorAll('.metric');
    
    metrics.forEach((metric, index) => {
        const progressBar = metric.querySelector('.progress-fill');
        const progressText = metric.querySelector('.progress-text');
        
        if (progress[index] !== undefined) {
            progressBar.style.width = `${progress[index]}%`;
            progressText.textContent = `${progress[index]}%`;
        }
    });
}

async function proceedToAssemble() {
    if (!currentSession) {
        alert('Please complete the maturation process first.');
        return;
    }
    
    showLoading('Assembling your AI squad...');
    
    try {
        const response = await fetch('/api/assemble/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSession
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showStep('assemble');
            animateAssemblyProcess();
        } else {
            throw new Error('Failed to initialize assembly');
        }
    } catch (error) {
        console.error('Error initializing assembly:', error);
        alert('Failed to start assembly process. Please try again.');
    } finally {
        hideLoading();
    }
}

function animateAssemblyProcess() {
    const steps = document.querySelectorAll('.progress-step');
    let currentStepIndex = 0;
    
    const animateStep = () => {
        if (currentStepIndex < steps.length) {
            // Mark current step as active
            steps[currentStepIndex].classList.add('active');
            
            // Mark previous step as completed
            if (currentStepIndex > 0) {
                steps[currentStepIndex - 1].classList.remove('active');
                steps[currentStepIndex - 1].classList.add('completed');
            }
            
            currentStepIndex++;
            
            // Continue animation
            setTimeout(animateStep, 2000);
        } else {
            // All steps completed
            steps[steps.length - 1].classList.remove('active');
            steps[steps.length - 1].classList.add('completed');
            
            // Update status
            const statusIndicator = document.querySelector('.status-indicator');
            statusIndicator.innerHTML = '<span class="status-dot" style="background: #10b981;"></span><span>Squad Ready!</span>';
            
            // Enable start execution button
            document.getElementById('start-execution').disabled = false;
            
            // Show success message
            setTimeout(() => {
                alert('Your AI squad is assembled and ready to execute your project!');
            }, 500);
        }
    };
    
    // Start animation
    setTimeout(animateStep, 1000);
}

async function startExecution() {
    showLoading('Starting project execution...');
    
    try {
        const response = await fetch('/api/assemble/start-execution', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSession
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Project execution started! You will receive updates as your AI team works on your project.');
            
            // Could redirect to a monitoring dashboard
            // window.location.href = '/dashboard';
        } else {
            throw new Error('Failed to start execution');
        }
    } catch (error) {
        console.error('Error starting execution:', error);
        alert('Failed to start execution. Please try again.');
    } finally {
        hideLoading();
    }
}

// Navigation functions
function backToDream() {
    showStep('dream');
}

function backToMaturation() {
    showStep('maturation');
}

// Utility functions
function showLoading(text = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    loadingText.textContent = text;
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'none';
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    hideLoading();
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    hideLoading();
});
