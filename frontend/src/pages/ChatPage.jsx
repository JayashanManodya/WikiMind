import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  BookOpen, 
  Paperclip,
  Mic,
  Trash2,
  Plus,
  MessageSquare,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { askQuestion } from '../api/client';

const INITIAL_WELCOME_MESSAGE = [
  {
    sender: 'bot',
    text: 'Hello! Ask me any question grounded strictly in your ingested knowledge base.',
    grounded: true,
    citations: [],
    confidence: 1.0
  }
];

const createDefaultSession = () => ({
  id: `session_${Date.now()}`,
  title: 'New Conversation',
  createdAt: new Date().toISOString(),
  messages: INITIAL_WELCOME_MESSAGE
});

export default function ChatPage({ setActiveTab, setSelectedWikiEntity }) {
  // Multi-chat sessions state loaded from localStorage
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('wikimind_multi_chat_sessions_v1');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.error("Failed to load multi-chat sessions from localStorage", e);
    }
    return [createDefaultSession()];
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    try {
      const savedActive = localStorage.getItem('wikimind_active_session_id');
      if (savedActive && sessions.some(s => s.id === savedActive)) {
        return savedActive;
      }
    } catch (e) {
      console.error("Failed to load active session ID", e);
    }
    return sessions[0]?.id || `session_${Date.now()}`;
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const chatEndRef = useRef(null);

  // Active session object
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const messages = activeSession ? activeSession.messages : INITIAL_WELCOME_MESSAGE;

  // Auto-scroll on new message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAsking]);

  // Read pre-filled query if user clicked prompt chip on Overview
  useEffect(() => {
    try {
      const prefill = localStorage.getItem('wikimind_prefill_query');
      if (prefill) {
        setInputQuery(prefill);
        localStorage.removeItem('wikimind_prefill_query');
      }
    } catch (e) {}
  }, []);

  // Persist sessions and active session ID to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('wikimind_multi_chat_sessions_v1', JSON.stringify(sessions));
      if (activeSessionId) {
        localStorage.setItem('wikimind_active_session_id', activeSessionId);
      }
    } catch (e) {
      console.error("Failed to save sessions to localStorage", e);
    }
  }, [sessions, activeSessionId]);

  // Create new chat session
  const handleNewChat = () => {
    const newSess = createDefaultSession();
    setSessions(prev => [newSess, ...prev]);
    setActiveSessionId(newSess.id);
    setInputQuery('');
  };

  // Delete chat session
  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== sessionId);
      if (filtered.length === 0) {
        const fallback = createDefaultSession();
        setActiveSessionId(fallback.id);
        return [fallback];
      }
      if (activeSessionId === sessionId) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  // Clear messages in current session
  const handleClearCurrentSession = () => {
    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        return { ...s, messages: INITIAL_WELCOME_MESSAGE };
      }
      return s;
    }));
  };

  // Send message
  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isAsking) return;

    const userMessage = { sender: 'user', text: inputQuery };
    const queryText = inputQuery;
    setInputQuery('');
    setIsAsking(true);

    // Auto-generate chat title from first user query
    const isFirstUserMsg = !activeSession.messages.some(m => m.sender === 'user');
    const autoTitle = isFirstUserMsg 
      ? (queryText.length > 28 ? queryText.slice(0, 28) + '...' : queryText) 
      : activeSession.title;

    // Update active session messages with user query
    const updatedMessages = [...activeSession.messages, userMessage];
    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        return { 
          ...s, 
          title: s.title === 'New Conversation' ? autoTitle : s.title,
          messages: updatedMessages 
        };
      }
      return s;
    }));

    try {
      const res = await askQuestion(userMessage.text, updatedMessages);
      
      const botMessage = {
        sender: 'bot',
        text: res.answer,
        grounded: res.grounded,
        citations: res.citations || [],
        confidence: res.confidence_score,
        status: res.status,
        contextSummary: res.context_summary
      };

      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, botMessage] };
        }
        return s;
      }));
    } catch (err) {
      const errorMsg = {
        sender: 'bot',
        text: 'Error contacting backend QA engine.',
        grounded: false,
        citations: [],
        confidence: 0.0
      };
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, errorMsg] };
        }
        return s;
      }));
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 120px)', maxWidth: '1100px', margin: '0 auto', gap: '16px' }}>
      
      {/* Sessions Left Panel / Sidebar */}
      {showSidebar && (
        <div style={{
          width: '260px',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#FFFFFF',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '14px',
          gap: '12px'
        }}>
          {/* New Chat Button */}
          <button 
            className="btn btn-black" 
            onClick={handleNewChat}
            style={{ width: '100%', justifyContent: 'center', fontSize: '13px', padding: '10px 14px' }}
          >
            <Plus size={16} />
            <span>New Chat</span>
          </button>

          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', tracking: '0.5px', marginTop: '4px' }}>
            Recent Conversations ({sessions.length})
          </div>

          {/* Sessions List */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {sessions.map((sess) => {
              const isActive = sess.id === activeSessionId;
              return (
                <div 
                  key={sess.id}
                  onClick={() => setActiveSessionId(sess.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    backgroundColor: isActive ? '#09090B' : '#F4F4F5',
                    color: isActive ? '#FFFFFF' : '#09090B',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    <MessageSquare size={14} color={isActive ? '#FFFFFF' : '#71717A'} style={{ shrink: 0 }} />
                    <span style={{ fontSize: '13px', fontWeight: isActive ? '600' : '500', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                      {sess.title}
                    </span>
                  </div>

                  <button 
                    onClick={(e) => handleDeleteSession(sess.id, e)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '2px',
                      color: isActive ? '#A1A1AA' : '#A1A1AA',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title="Delete Chat"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Chat Interface */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#FFFFFF', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '20px' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '14px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              className="btn btn-outline" 
              onClick={() => setShowSidebar(!showSidebar)} 
              style={{ padding: '6px', borderRadius: '6px' }}
              title={showSidebar ? 'Hide Sidebar' : 'Show Sidebar'}
            >
              {showSidebar ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            </button>

            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#09090B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={18} color="#FFFFFF" />
            </div>
            <div>
              <h3 style={{ fontSize: '15.5px', fontWeight: '600' }}>{activeSession?.title || 'ChatGPT Grounded Engine'}</h3>
              <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Zero-hallucination factual answer model</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              className="btn btn-outline" 
              onClick={handleClearCurrentSession}
              style={{ fontSize: '12px', padding: '6px 12px', gap: '6px' }}
              title="Clear Current Chat"
            >
              <Trash2 size={13} color="#71717A" />
              <span>Clear Current</span>
            </button>
            <span className="badge-clean">Ver 4.0 Mar 14</span>
          </div>
        </div>

        {/* Messages Feed */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={idx}
                className={isUser ? 'chat-user-msg' : 'chat-bot-msg'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  {isUser ? (
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: '#27272A', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px' }}>
                      U
                    </div>
                  ) : (
                    <div style={{ width: '22px', height: '22px', borderRadius: '4px', backgroundColor: '#09090B', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Bot size={12} color="#FFF" />
                    </div>
                  )}
                  
                  <span style={{ fontSize: '12px', fontWeight: '600' }}>
                    {isUser ? 'You' : 'ChatGPT Assistant'}
                  </span>

                  {!isUser && msg.grounded !== undefined && (
                    <span className="badge-clean" style={{ marginLeft: 'auto', fontSize: '10px' }}>
                      {msg.grounded ? <CheckCircle2 size={11} color="#10B981" /> : <XCircle size={11} color="#EF4444" />}
                      {msg.grounded ? 'Grounded' : 'Refused / No Knowledge'}
                    </span>
                  )}
                </div>

                <p style={{ fontSize: '14.5px', whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{msg.text}</p>

                {/* Source Citations */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Citations:</span>
                    {msg.citations.map((cite, cIdx) => (
                      <span 
                        key={cIdx} 
                        className="badge-clean" 
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
                          const entityName = cite.replace('.md', '').replace(/_/g, ' ');
                          if (setSelectedWikiEntity) setSelectedWikiEntity(entityName);
                          setActiveTab('wiki');
                        }}
                      >
                        <BookOpen size={10} />
                        {cite}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {isAsking && (
            <div className="chat-bot-msg" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Loader2 className="spin" size={16} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: '13.5px', color: 'var(--text-muted)' }}>Searching grounded documents & generating response...</span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <form 
          onSubmit={handleSend}
          style={{
            marginTop: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#FFFFFF',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '8px 12px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
          }}
        >
          <Paperclip size={18} color="#71717A" style={{ cursor: 'pointer', marginLeft: '4px' }} />

          <input 
            type="text" 
            placeholder="Send a message or query knowledge base..." 
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isAsking}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: '14px',
              color: 'var(--text-main)',
              backgroundColor: 'transparent',
              padding: '8px 4px'
            }}
          />

          <Mic size={18} color="#71717A" style={{ cursor: 'pointer' }} />

          <button 
            type="submit" 
            disabled={!inputQuery.trim() || isAsking}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: inputQuery.trim() ? '#09090B' : '#E4E4E7',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justify: 'center',
              cursor: inputQuery.trim() ? 'pointer' : 'default',
              transition: 'background-color 0.15s ease'
            }}
          >
            <Send size={15} color={inputQuery.trim() ? '#FFFFFF' : '#A1A1AA'} />
          </button>
        </form>

      </div>

    </div>
  );
}
