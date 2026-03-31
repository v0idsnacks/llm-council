import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import DebateStage1 from './DebateStage1';
import DebateStage2 from './DebateStage2';
import DebateStage3 from './DebateStage3';
import DebateStage4 from './DebateStage4';
import './DebateInterface.css';

export default function DebateInterface({
  debate,
  onStartDebate,
  isLoading,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [debate]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onStartDebate(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!debate) {
    return (
      <div className="debate-interface">
        <div className="empty-state">
          <h2>⚖️ Multi-Agent Debate</h2>
          <p>Create a new debate to get started</p>
        </div>
      </div>
    );
  }

  const hasMessages = debate.messages && debate.messages.length > 0;

  return (
    <div className="debate-interface">
      <div className="messages-container">
        {!hasMessages ? (
          <div className="empty-state">
            <h2>⚖️ Start a Debate</h2>
            <p>Enter a proposition below — a Pro Agent and an Against Agent will argue both sides, then a Judge will deliver a verdict.</p>
            <div className="debate-example-topics">
              <p className="example-label">Example topics:</p>
              <ul>
                <li>"Artificial intelligence will create more jobs than it destroys"</li>
                <li>"Remote work is better than office work for most employees"</li>
                <li>"Nuclear energy should be a major part of the clean energy transition"</li>
              </ul>
            </div>
          </div>
        ) : (
          debate.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">Debate Topic</div>
                  <div className="message-content">
                    <div className="topic-text markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="debate-message">
                  <div className="message-label">⚖️ Debate</div>

                  {/* Stage 1 – Opening Arguments */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 1: Collecting opening arguments…</span>
                    </div>
                  )}
                  {msg.stage1 && <DebateStage1 stage1={msg.stage1} />}

                  {/* Stage 2 – Rebuttals */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 2: Generating rebuttals…</span>
                    </div>
                  )}
                  {msg.stage2 && <DebateStage2 stage2={msg.stage2} />}

                  {/* Stage 3 – Final Statements */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 3: Preparing final statements…</span>
                    </div>
                  )}
                  {msg.stage3 && <DebateStage3 stage3={msg.stage3} />}

                  {/* Stage 4 – Judge Verdict */}
                  {msg.loading?.stage4 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 4: Judge is evaluating…</span>
                    </div>
                  )}
                  {msg.stage4 && <DebateStage4 stage4={msg.stage4} />}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && !hasMessages && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Preparing the debate arena…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {!hasMessages && (
        <form className="input-form" onSubmit={handleSubmit}>
          <textarea
            className="message-input"
            placeholder="Enter a debate proposition… (Shift+Enter for new line, Enter to submit)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={3}
          />
          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || isLoading}
          >
            Start Debate
          </button>
        </form>
      )}
    </div>
  );
}
