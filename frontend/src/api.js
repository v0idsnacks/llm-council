/**
 * API client for the Debate backend.
 */

const API_BASE = 'http://localhost:8001';

export const api = {
  /**
   * List all debates.
   */
  async listDebates() {
    const response = await fetch(`${API_BASE}/api/debates`);
    if (!response.ok) {
      throw new Error('Failed to list debates');
    }
    return response.json();
  },

  /**
   * Create a new debate session.
   */
  async createDebate() {
    const response = await fetch(`${API_BASE}/api/debates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to create debate');
    }
    return response.json();
  },

  /**
   * Get a specific debate.
   */
  async getDebate(debateId) {
    const response = await fetch(`${API_BASE}/api/debates/${debateId}`);
    if (!response.ok) {
      throw new Error('Failed to get debate');
    }
    return response.json();
  },

  /**
   * Start a debate with streaming updates.
   * @param {string} debateId - The debate session ID
   * @param {string} topic - The debate topic/proposition
   * @param {function} onEvent - Callback: (eventType, eventData) => void
   * @returns {Promise<void>}
   */
  async startDebateStream(debateId, topic, onEvent) {
    const response = await fetch(
      `${API_BASE}/api/debates/${debateId}/start/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to start debate');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  },
};
