import './Sidebar.css';

export default function Sidebar({
  mode,
  onModeChange,
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  debates,
  currentDebateId,
  onSelectDebate,
  onNewDebate,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>{mode === 'debate' ? '⚖️ Debate' : '🏛️ LLM Council'}</h1>

        <div className="mode-toggle">
          <button
            className={`mode-btn ${mode === 'council' ? 'active' : ''}`}
            onClick={() => onModeChange('council')}
          >
            Council
          </button>
          <button
            className={`mode-btn ${mode === 'debate' ? 'active' : ''}`}
            onClick={() => onModeChange('debate')}
          >
            Debate
          </button>
        </div>

        {mode === 'council' ? (
          <button className="new-conversation-btn" onClick={onNewConversation}>
            + New Conversation
          </button>
        ) : (
          <button className="new-conversation-btn new-debate-btn" onClick={onNewDebate}>
            + New Debate
          </button>
        )}
      </div>

      <div className="conversation-list">
        {mode === 'council' ? (
          conversations.length === 0 ? (
            <div className="no-conversations">No conversations yet</div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`conversation-item ${
                  conv.id === currentConversationId ? 'active' : ''
                }`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="conversation-title">
                  {conv.title || 'New Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                </div>
              </div>
            ))
          )
        ) : (
          debates.length === 0 ? (
            <div className="no-conversations">No debates yet</div>
          ) : (
            debates.map((debate) => (
              <div
                key={debate.id}
                className={`conversation-item ${
                  debate.id === currentDebateId ? 'active' : ''
                }`}
                onClick={() => onSelectDebate(debate.id)}
              >
                <div className="conversation-title">
                  {debate.title || 'New Debate'}
                </div>
                {debate.topic && (
                  <div className="conversation-meta debate-topic-preview">
                    {debate.topic.length > 40
                      ? debate.topic.slice(0, 40) + '…'
                      : debate.topic}
                  </div>
                )}
              </div>
            ))
          )
        )}
      </div>
    </div>
  );
}

