import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import DebateInterface from './components/DebateInterface';
import { api } from './api';
import './App.css';

function App() {
  const [mode, setMode] = useState('council'); // 'council' | 'debate'

  // Council state
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Debate state
  const [debates, setDebates] = useState([]);
  const [currentDebateId, setCurrentDebateId] = useState(null);
  const [currentDebate, setCurrentDebate] = useState(null);
  const [isDebateLoading, setIsDebateLoading] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
    loadDebates();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  // Load debate details when selected
  useEffect(() => {
    if (currentDebateId) {
      loadDebate(currentDebateId);
    }
  }, [currentDebateId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const loadDebates = async () => {
    try {
      const dbs = await api.listDebates();
      setDebates(dbs);
    } catch (error) {
      console.error('Failed to load debates:', error);
    }
  };

  const loadDebate = async (id) => {
    try {
      const db = await api.getDebate(id);
      setCurrentDebate(db);
    } catch (error) {
      console.error('Failed to load debate:', error);
    }
  };

  // ---------------------------------------------------------------------------
  // Council handlers
  // ---------------------------------------------------------------------------

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: { stage1: false, stage2: false, stage3: false },
      };

      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            loadConversations();
            break;

          case 'complete':
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Debate handlers
  // ---------------------------------------------------------------------------

  const handleNewDebate = async () => {
    try {
      const newDebate = await api.createDebate();
      setDebates([
        {
          id: newDebate.id,
          created_at: newDebate.created_at,
          title: 'New Debate',
          topic: null,
          message_count: 0,
        },
        ...debates,
      ]);
      setCurrentDebateId(newDebate.id);
      setCurrentDebate(newDebate);
    } catch (error) {
      console.error('Failed to create debate:', error);
    }
  };

  const handleSelectDebate = (id) => {
    setCurrentDebateId(id);
  };

  const handleStartDebate = async (topic) => {
    if (!currentDebateId) return;

    setIsDebateLoading(true);
    try {
      // Optimistically show the topic
      const topicMessage = { role: 'user', content: topic };
      setCurrentDebate((prev) => ({
        ...prev,
        topic,
        messages: [...(prev.messages || []), topicMessage],
      }));

      // Add a partial debate result message
      const debateMessage = {
        role: 'debate',
        stage1: null,
        stage2: null,
        stage3: null,
        stage4: null,
        loading: { stage1: false, stage2: false, stage3: false, stage4: false },
      };
      setCurrentDebate((prev) => ({
        ...prev,
        messages: [...prev.messages, debateMessage],
      }));

      await api.startDebateStream(currentDebateId, topic, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.stage1 = event.data;
              last.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.stage2 = event.data;
              last.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.stage3 = event.data;
              last.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage4_start':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.loading.stage4 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage4_complete':
            setCurrentDebate((prev) => {
              const messages = [...prev.messages];
              const last = messages[messages.length - 1];
              last.stage4 = event.data;
              last.loading.stage4 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            loadDebates();
            break;

          case 'complete':
            loadDebates();
            setIsDebateLoading(false);
            break;

          case 'error':
            console.error('Debate stream error:', event.message);
            setIsDebateLoading(false);
            break;

          default:
            console.log('Unknown debate event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to start debate:', error);
      setCurrentDebate((prev) => ({
        ...prev,
        messages: (prev.messages || []).slice(0, -2),
      }));
      setIsDebateLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="app">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        debates={debates}
        currentDebateId={currentDebateId}
        onSelectDebate={handleSelectDebate}
        onNewDebate={handleNewDebate}
      />

      {mode === 'council' ? (
        <ChatInterface
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      ) : (
        <DebateInterface
          debate={currentDebate}
          onStartDebate={handleStartDebate}
          isLoading={isDebateLoading}
        />
      )}
    </div>
  );
}

export default App;

