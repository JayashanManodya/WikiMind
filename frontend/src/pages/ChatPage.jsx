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
  ChevronRight,
  Pencil,
  Search
} from 'lucide-react';
import { askQuestion, getSessionMessages, deleteChatSession } from '../api/client';
import { useData } from '../context/DataContext';

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
  const { chatSessions: cachedSessions, loadChatSessions } = useData();
  const [sessions, setSessions] = useState([createDefaultSession()]);
  const [activeSessionId, setActiveSessionId] = useState(sessions[0]?.id);
  const [inputQuery, setInputQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchConv, setSearchConv] = useState('');
  const [showSearchInput, setShowSearchInput] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const chatEndRef = useRef(null);

  // Load chat sessions from DataContext cache/fetch on mount
  useEffect(() => {
    const loadRemoteSessions = async () => {
      try {
        const resSessions = await loadChatSessions();
        if (resSessions && resSessions.length > 0) {
          const formatted = resSessions.map(s => ({
            id: s.id,
            title: s.title,
            createdAt: s.created_at,
            messages: []
          }));
          setSessions(formatted);
          setActiveSessionId(formatted[0].id);
        }
      } catch (err) {
        console.warn("Using local fallback sessions", err);
      }
    };
    loadRemoteSessions();
  }, [loadChatSessions]);


  // Fetch messages for active session when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) return;
    const loadMessages = async () => {
      try {
        const res = await getSessionMessages(activeSessionId);
        if (res.messages && res.messages.length > 0) {
          const formattedMsgs = res.messages.map(m => ({
            sender: m.role === 'user' ? 'user' : 'bot',
            text: m.content,
            grounded: true,
            citations: m.sources || []
          }));
          setSessions(prev => prev.map(s => {
            if (s.id === activeSessionId) {
              return { ...s, messages: formattedMsgs };
            }
            return s;
          }));
        } else {
          setSessions(prev => prev.map(s => {
            if (s.id === activeSessionId && s.messages.length === 0) {
              return { ...s, messages: INITIAL_WELCOME_MESSAGE };
            }
            return s;
          }));
        }
      } catch (err) {
        console.warn("Failed to load messages for session", activeSessionId, err);
      }
    };
    loadMessages();
  }, [activeSessionId]);

  // Active session object
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0] || createDefaultSession();
  const messages = activeSession.messages && activeSession.messages.length > 0 
    ? activeSession.messages 
    : INITIAL_WELCOME_MESSAGE;

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

  // Create new chat session
  const handleNewChat = () => {
    const newSess = createDefaultSession();
    setSessions(prev => [newSess, ...prev]);
    setActiveSessionId(newSess.id);
    setInputQuery('');
  };

  // Delete chat session
  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await deleteChatSession(sessionId);
    } catch (err) {}

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

  // Clear all conversation sessions
  const handleClearAllSessions = () => {
    if (window.confirm('Are you sure you want to clear all chat conversations?')) {
      const fresh = createDefaultSession();
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
    }
  };

  // Rename session title
  const handleSaveRename = (sessionId) => {
    if (!editingTitle.trim()) return;
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: editingTitle.trim() } : s));
    setEditingSessionId(null);
    setEditingTitle('');
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

    const isFirstUserMsg = !activeSession.messages.some(m => m.sender === 'user');
    const autoTitle = isFirstUserMsg 
      ? (queryText.length > 28 ? queryText.slice(0, 28) + '...' : queryText) 
      : activeSession.title;

    const updatedMessages = [...(activeSession.messages || []), userMessage];
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
      const res = await askQuestion(userMessage.text, updatedMessages, activeSessionId);
      
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

  const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(searchConv.toLowerCase()));

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 100px)', width: '100%', gap: '20px' }}>
      
      {/* Sessions Left Panel / Sidebar (Matching Screenshot UI) */}
      {showSidebar && (
        <div style={{
          width: '290px',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '28px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.03)',
          padding: '24px 20px',
          gap: '18px'
        }}>
          {/* Top Actions Row: New Chat Pill + Circular Search Button */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              onClick={handleNewChat}
              style={{
                flex: 1,
                backgroundColor: '#4F46E5', // Indigo blue matching screenshot
                color: '#FFFFFF',
                border: 'none',
                padding: '12px 20px',
                borderRadius: '9999px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 14px rgba(79, 70, 229, 0.25)',
                transition: 'all 0.15s ease'
              }}
            >
              <Plus size={18} />
              <span>New chat</span>
            </button>

            <button
              onClick={() => setShowSearchInput(!showSearchInput)}
              title="Search Conversations"
              style={{
                width: '42px',
                height: '42px',
                padding: 0,
                margin: 0,
                borderRadius: '50%',
                backgroundColor: '#09090B',
                border: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                flexShrink: 0,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <Search size={17} color="#FFFFFF" />
            </button>
          </div>

          {/* Collapsible Search Input */}
          {showSearchInput && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '8px 12px',
              gap: '8px'
            }}>
              <Search size={14} color="#64748B" />
              <input 
                type="text" 
                placeholder="Search conversations..." 
                value={searchConv}
                onChange={(e) => setSearchConv(e.target.value)}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  outline: 'none',
                  fontSize: '12.5px',
                  color: '#09090B',
                  width: '100%'
                }}
              />
            </div>
          )}

          {/* Subheader: Your conversations + Clear All */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #F1F5F9', paddingBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500', color: '#64748B' }}>
              Your conversations
            </span>
            <button
              onClick={handleClearAllSessions}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: '#4F46E5',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                padding: 0
              }}
            >
              Clear All
            </button>
          </div>

          {/* Conversations List (Matching Screenshot UI) */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '2px' }}>
            {filteredSessions.map((sess) => {
              const isActive = sess.id === activeSessionId;
              const isEditing = editingSessionId === sess.id;

              return (
                <div 
                  key={sess.id}
                  onClick={() => setActiveSessionId(sess.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '12px 14px',
                    borderRadius: '16px',
                    backgroundColor: isActive ? '#EEF2FF' : 'transparent',
                    color: isActive ? '#4F46E5' : '#0F172A',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden', flex: 1, paddingRight: '6px' }}>
                    <MessageSquare size={16} color={isActive ? '#4F46E5' : '#0F172A'} style={{ flexShrink: 0 }} />
                    
                    {isEditing ? (
                      <input 
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleSaveRename(sess.id)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleSaveRename(sess.id); }}
                        autoFocus
                        style={{
                          backgroundColor: '#FFFFFF',
                          border: '1px solid #4F46E5',
                          borderRadius: '4px',
                          fontSize: '13px',
                          padding: '2px 6px',
                          color: '#09090B',
                          width: '100%',
                          outline: 'none'
                        }}
                      />
                    ) : (
                      <span style={{ fontSize: '13.5px', fontWeight: isActive ? '600' : '500', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {sess.title}
                      </span>
                    )}
                  </div>

                  {/* Actions & Active Blue Indicator Dot */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                    {isActive && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#FFFFFF', padding: '4px 8px', borderRadius: '12px', boxShadow: '0 2px 6px rgba(0,0,0,0.05)' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingSessionId(sess.id);
                            setEditingTitle(sess.title);
                          }}
                          title="Rename Chat"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
                        >
                          <Pencil size={13} color="#64748B" />
                        </button>

                        <button 
                          onClick={(e) => handleDeleteSession(sess.id, e)}
                          title="Delete Chat"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
                        >
                          <Trash2 size={13} color="#64748B" />
                        </button>
                      </div>
                    )}

                    {/* Active Indicator Blue Dot */}
                    {isActive && (
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: '#4F46E5',
                        boxShadow: '0 0 8px rgba(79, 70, 229, 0.6)'
                      }} />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Chat Interface */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '28px', boxShadow: '0 8px 30px rgba(0,0,0,0.02)', padding: '28px' }}>
        
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
              <h3 style={{ fontSize: '15.5px', fontWeight: '600' }}>{activeSession?.title || 'WikiMind Grounded Engine'}</h3>
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
            <span className="badge-clean">WikiMind v1.0</span>
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
                    {isUser ? 'You' : 'WikiMind Assistant'}
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
                    {msg.citations.map((cite, cIdx) => {
                      const citeStr = typeof cite === 'string' 
                        ? cite 
                        : (cite.file || cite.name || cite.source || (cite.snippet ? (cite.snippet.substring(0, 35) + '...') : 'Source Document'));
                      const entityName = citeStr.replace('.md', '').replace(/_/g, ' ');

                      return (
                        <span 
                          key={cIdx} 
                          className="badge-clean" 
                          style={{ cursor: 'pointer' }}
                          title={typeof cite === 'object' && cite.snippet ? cite.snippet : citeStr}
                          onClick={() => {
                            if (setSelectedWikiEntity && entityName && !entityName.includes('...')) {
                              setSelectedWikiEntity(entityName);
                              setActiveTab('wiki');
                            }
                          }}
                        >
                          <BookOpen size={10} />
                          {citeStr}
                        </span>
                      );
                    })}
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
