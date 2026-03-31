import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import DebateInterface from './components/DebateInterface';
import { api } from './api';
import './App.css';

function App() {
  const [debates, setDebates] = useState([]);
  const [currentDebateId, setCurrentDebateId] = useState(null);
  const [currentDebate, setCurrentDebate] = useState(null);
  const [isDebateLoading, setIsDebateLoading] = useState(false);

  async function loadDebates() {
    try {
      const dbs = await api.listDebates();
      setDebates(dbs);
    } catch (error) {
      console.error('Failed to load debates:', error);
    }
  }

  useEffect(() => {
    api
      .listDebates()
      .then((dbs) => setDebates(dbs))
      .catch((error) => console.error('Failed to load debates:', error));
  }, []);

  useEffect(() => {
    if (currentDebateId) {
      api
        .getDebate(currentDebateId)
        .then((db) => setCurrentDebate(db))
        .catch((error) => console.error('Failed to load debate:', error));
    }
  }, [currentDebateId]);

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
        debates={debates}
        currentDebateId={currentDebateId}
        onSelectDebate={handleSelectDebate}
        onNewDebate={handleNewDebate}
      />
      <DebateInterface
        debate={currentDebate}
        onStartDebate={handleStartDebate}
        isLoading={isDebateLoading}
      />
    </div>
  );
}

export default App;
