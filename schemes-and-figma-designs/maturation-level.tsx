import React from 'react';
import './maturation-level.css';

const MaturationLevel: React.FC = () => {
  return (
    <div className="maturation-container">
      <div className="maturation-header">
        <h1>Step 2 — Maturation</h1>
        <p className="tagline">Refine the spark into a rock-solid brief.</p>
      </div>
      
      <div className="chat-interface">
        <div className="sidebar-left">
          <div className="project-info">
            <h3>Project: AI Fitness Coach</h3>
            <div className="scope-lock-badge">
              <span className="lock-icon">🔒</span>
              <span>Unlock Scope</span>
            </div>
          </div>
          
          <div className="risk-radar">
            <h4>Risk Radar</h4>
            <ul className="risk-items">
              <li className="risk-green">Technical feasibility ✓</li>
              <li className="risk-yellow">Payment integration ⚠</li>
              <li className="risk-red">Data compliance ⚠</li>
              <li className="risk-green">Market validation ✓</li>
            </ul>
          </div>
          
          <div className="artifacts">
            <h4>Project Assets</h4>
            <div className="artifact-item">
              <span className="file-icon">📄</span>
              <span>FigmaDesigns.pdf</span>
            </div>
            <div className="artifact-item">
              <span className="file-icon">📊</span>
              <span>UserResearch.xlsx</span>
            </div>
            <div className="artifact-drop">
              <span>+ Drop files here</span>
            </div>
          </div>
        </div>
        
        <div className="chat-area">
          <div className="chat-messages">
            <div className="message agent">
              <span className="avatar">🤖</span>
              <div className="message-content">
                <p>I see you want to build an AI fitness coach. Let's clarify some details. What kind of notifications would you prefer to implement?</p>
              </div>
            </div>
            
            <div className="quick-answers">
              <button>Push notifications</button>
              <button>SMS texts</button>
              <button>Email alerts</button>
            </div>
            
            <div className="message user">
              <div className="message-content">
                <p>Push notifications would be best for our mobile app.</p>
              </div>
              <span className="avatar">👤</span>
            </div>
            
            <div className="message agent">
              <span className="avatar">🤖</span>
              <div className="message-content">
                <p>Great choice! Push notifications will give users immediate feedback. Now, what about user data storage? This will impact our GDPR compliance strategy.</p>
              </div>
            </div>
          </div>
          
          <div className="chat-input">
            <input type="text" placeholder="Type your response..." />
            <button className="send-button">Send</button>
          </div>
        </div>
        
        <div className="sidebar-right">
          <div className="clarity-score">
            <h4>Brief Clarity</h4>
            <div className="progress-container">
              <div className="progress-bar" style={{width: '68%'}}></div>
            </div>
            <span>68% Complete</span>
          </div>
          
          <div className="generated-docs">
            <h4>Auto-Generated</h4>
            <div className="doc-item">
              <span className="doc-icon">📝</span>
              <span>BRD v0.3</span>
            </div>
            <div className="doc-item">
              <span className="doc-icon">🔄</span>
              <span>System Diagram</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="floating-help">
        <button className="ai-help">
          <span>💬</span>
        </button>
      </div>
    </div>
  );
};

export default MaturationLevel;