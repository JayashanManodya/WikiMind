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
  Search,
  Check,
  Database,
  ShieldCheck,
  Sparkles,
  Cpu
} from 'lucide-react';
import { askQuestion, getSessionMessages, deleteChatSession } from '../api/client';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';

const renderFormattedMarkdown = (text) => {
  if (!text) return null;

  const lines = text.split('\n');

  return lines.map((line, lIdx) => {
    // Process bold (**text**) and italic (*text*) tokens
    const parts = line.split(/(\*\*.*?\*\*|\*.*?\*)/g);

    const formattedParts = parts.map((part, pIdx) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
        return (
          <strong key={pIdx} style={{ fontWeight: '700', color: '#0F172A' }}>
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
        return <em key={pIdx}>{part.slice(1, -1)}</em>;
      }
      return part;
    });

    // Check if line is a bullet item
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      return (
        <div key={lIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', margin: '4px 0 4px 8px' }}>
          <span style={{ color: '#4F46E5', fontWeight: 'bold', lineHeight: '1.6' }}>•</span>
          <div style={{ flex: 1 }}>{formattedParts}</div>
        </div>
      );
    }

    return (
      <div key={lIdx} style={{ minHeight: line.trim() === '' ? '12px' : 'auto' }}>
        {formattedParts}
      </div>
    );
  });
};

const INITIAL_WELCOME_MESSAGE = [
  {
    sender: 'bot',
    text: 'Hello! Ask me any question grounded strictly in your ingested knowledge base.',
    grounded: true,
    citations: [],
    confidence: 1.0
  }
];

const GENERATION_PIPELINE = [
  { id: 1, label: 'Analyzing question intent & query parameters', icon: Search, color: '#2563EB' },
  { id: 2, label: 'Searching grounded Wiki knowledge base & vectors', icon: Database, color: '#10B981' },
  { id: 3, label: 'Verifying factual citations & context snippets', icon: ShieldCheck, color: '#8B5CF6' },
  { id: 4, label: 'Synthesizing zero-hallucination answer', icon: Sparkles, color: '#EC4899' }
];

const createDefaultSession = () => ({
  id: `session_${Date.now()}`,
  title: 'New Conversation',
  createdAt: new Date().toISOString(),
  messages: INITIAL_WELCOME_MESSAGE
});

export default function ChatPage({ setActiveTab, setSelectedWikiEntity }) {
  const { user } = useAuth();
  const { chatSessions: cachedSessions, loadChatSessions } = useData();
  const [sessions, setSessions] = useState([createDefaultSession()]);
  const [activeSessionId, setActiveSessionId] = useState(sessions[0]?.id);
  const [inputQuery, setInputQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 768 : false);
  const [showSidebar, setShowSidebar] = useState(typeof window !== 'undefined' ? window.innerWidth >= 768 : false);
  const [searchConv, setSearchConv] = useState('');
  const [showSearchInput, setShowSearchInput] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const chatEndRef = useRef(null);

  // Monitor window resize for responsive layout
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Cycle generation pipeline steps while asking
  useEffect(() => {
    let interval;
    if (isAsking) {
      setGenerationStep(0);
      interval = setInterval(() => {
        setGenerationStep(prev => (prev < 3 ? prev + 1 : prev));
      }, 2000);
    } else {
      setGenerationStep(0);
    }
    return () => clearInterval(interval);
  }, [isAsking]);

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
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 100px)', width: '100%', gap: '20px', position: 'relative' }}>
      
      {/* Mobile Dark Backdrop Overlay */}
      {isMobile && showSidebar && (
        <div 
          onClick={() => setShowSidebar(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(9, 9, 11, 0.4)',
            backdropFilter: 'blur(4px)',
            WebkitBackdropFilter: 'blur(4px)',
            zIndex: 99
          }}
        />
      )}

      {/* Sessions Left Panel / Sidebar */}
      {showSidebar && (
        <div style={{
          position: isMobile ? 'fixed' : 'relative',
          top: isMobile ? '70px' : 'auto',
          left: isMobile ? '12px' : 'auto',
          zIndex: isMobile ? 100 : 1,
          width: isMobile ? 'calc(100% - 24px)' : '290px',
          maxWidth: '320px',
          maxHeight: isMobile ? 'calc(100vh - 90px)' : '820px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '28px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.12)',
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
                  onClick={() => {
                    setActiveSessionId(sess.id);
                    if (isMobile) setShowSidebar(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '16px',
                    backgroundColor: isActive ? '#EEF2FF' : '#F8FAFC',
                    border: isActive ? '1px solid #C7D2FE' : '1px solid #E2E8F0',
                    color: isActive ? '#4F46E5' : '#0F172A',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden', flex: 1, paddingRight: '6px' }}>
                    <MessageSquare size={16} color={isActive ? '#4F46E5' : '#64748B'} style={{ flexShrink: 0 }} />
                    
                    {isEditing ? (
                      <div 
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', width: '100%' }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input 
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => { 
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleSaveRename(sess.id);
                            }
                          }}
                          autoFocus
                          style={{
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #4F46E5',
                            borderRadius: '6px',
                            fontSize: '12.5px',
                            padding: '3px 8px',
                            color: '#09090B',
                            width: '100%',
                            outline: 'none'
                          }}
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSaveRename(sess.id);
                          }}
                          title="Save title"
                          style={{
                            backgroundColor: '#4F46E5',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '4px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justify: 'center',
                            flexShrink: 0
                          }}
                        >
                          <Check size={13} color="#FFFFFF" />
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: '13.5px', fontWeight: isActive ? '600' : '500', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {sess.title}
                      </span>
                    )}
                  </div>

                  {/* Action Buttons (Edit & Delete) & Active Indicator */}
                  {!isEditing && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: '#FFFFFF', padding: '3px 6px', borderRadius: '10px', border: '1px solid #E2E8F0', boxShadow: '0 2px 4px rgba(0,0,0,0.03)' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingSessionId(sess.id);
                            setEditingTitle(sess.title);
                          }}
                          title="Rename Conversation"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                        >
                          <Pencil size={12} color="#64748B" />
                        </button>

                        <button 
                          onClick={(e) => handleDeleteSession(sess.id, e)}
                          title="Delete Conversation"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                        >
                          <Trash2 size={12} color="#EF4444" />
                        </button>
                      </div>

                      {/* Active Indicator Blue Dot */}
                      {isActive && (
                        <div style={{
                          width: '7px',
                          height: '7px',
                          borderRadius: '50%',
                          backgroundColor: '#4F46E5',
                          boxShadow: '0 0 6px rgba(79, 70, 229, 0.6)'
                        }} />
                      )}
                    </div>
                  )}
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
              onClick={() => setShowSidebar(!showSidebar)} 
              style={{ background: 'none', border: 'none', padding: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '6px' }}
              title={showSidebar ? 'Hide Sidebar' : 'Show Sidebar'}
            >
              {showSidebar ? <ChevronLeft size={18} color="#09090B" /> : <ChevronRight size={18} color="#09090B" />}
            </button>

            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', flexShrink: 0 }}>
              <img src="/full.png" alt="WikiMind Logo" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%', display: 'block' }} />
            </div>
            <div>
              <h3 style={{ fontSize: '15.5px', fontWeight: '600' }}>{activeSession?.title || 'WikiMind Grounded Engine'}</h3>
              <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Zero-hallucination factual answer model</p>
            </div>
          </div>
        </div>

        {/* Messages Feed */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isUser ? 'flex-end' : 'flex-start',
                  gap: '6px',
                  maxWidth: isUser ? '75%' : '82%',
                  marginLeft: isUser ? 'auto' : '0',
                  marginRight: isUser ? '0' : 'auto'
                }}
              >
                {/* Header Avatar & Sender Info */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {!isUser && (
                    <div style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #E2E8F0',
                      display: 'flex',
                      alignItems: 'center',
                      justify: 'center',
                      overflow: 'hidden',
                      flexShrink: 0,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.06)'
                    }}>
                      <img src="/full.png" alt="WikiMind" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%', display: 'block' }} />
                    </div>
                  )}

                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#64748B' }}>
                    {isUser ? 'You' : 'WikiMind Assistant'}
                  </span>

                  {isUser && (
                    user && user.picture ? (
                      <img
                        src={user.picture}
                        alt={user.name || 'User'}
                        style={{ width: '28px', height: '28px', borderRadius: '50%', objectFit: 'cover', border: '1px solid #E2E8F0', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}
                      />
                    ) : (
                      <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: '#09090B', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: '700' }}>
                        {user && user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                      </div>
                    )
                  )}
                </div>

                {/* Message Bubble */}
                <div style={{
                  backgroundColor: isUser ? '#FFFFFF' : '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                  padding: '14px 18px',
                  color: '#0F172A',
                  boxShadow: '0 4px 14px rgba(0, 0, 0, 0.03)',
                  fontSize: '14.5px',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                  width: '100%'
                }}>
                  <div style={{ margin: 0, color: '#0F172A' }}>{renderFormattedMarkdown(msg.text)}</div>

                  {/* Source Citations */}
                  {!isUser && msg.citations && msg.citations.length > 0 && (
                    <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', color: '#64748B', fontWeight: '600' }}>Citations:</span>
                      {msg.citations.map((cite, cIdx) => {
                        let rawStr = typeof cite === 'string' 
                          ? cite 
                          : (cite.entity_name || cite.name || cite.title || cite.file || cite.source || 'Wiki Article');
                        
                        // Extract filename if full path
                        if (typeof rawStr === 'string') {
                          rawStr = rawStr.split('/').pop().split('\\').pop();
                          rawStr = rawStr.replace(/\.[a-zA-Z0-9]+$/i, ''); // Strip .md, .pdf, etc.
                          rawStr = rawStr.replace(/_/g, ' ').trim(); // Replace underscores with spaces
                        }

                        const cleanWikiName = rawStr || 'Wiki Article';

                        return (
                          <span 
                            key={cIdx} 
                            className="badge-clean"
                            style={{ cursor: 'pointer' }}
                            title={`View Wiki Article: ${cleanWikiName}`}
                            onClick={() => {
                              if (setSelectedWikiEntity && cleanWikiName) {
                                setSelectedWikiEntity(cleanWikiName);
                                setActiveTab('wiki');
                              }
                            }}
                          >
                            <BookOpen size={11} color="#2563EB" />
                            {cleanWikiName}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isAsking && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px', marginLeft: '2px' }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                display: 'flex',
                alignItems: 'center',
                justify: 'center',
                overflow: 'hidden',
                flexShrink: 0
              }}>
                <img src="/full.png" alt="WikiMind" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%', display: 'block' }} />
              </div>

              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 12px',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '16px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
              }}>
                <Loader2 className="spin" size={13} color={GENERATION_PIPELINE[generationStep]?.color || '#2563EB'} style={{ flexShrink: 0, animation: 'spin 1s linear infinite' }} />
                <span style={{ fontSize: '12.5px', color: '#0F172A', fontWeight: '500' }}>
                  {GENERATION_PIPELINE[generationStep]?.label || 'Generating response...'}
                </span>
              </div>
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
            gap: '10px',
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '9999px',
            padding: '6px 8px 6px 16px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.03)',
            overflow: 'hidden'
          }}
        >
          <Paperclip size={18} color="#71717A" style={{ cursor: 'pointer' }} />

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
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: inputQuery.trim() ? '#09090B' : '#F4F4F5',
              border: 'none',
              padding: 0,
              margin: 0,
              display: 'inline-flex',
              alignItems: 'center',
              justify: 'center',
              cursor: inputQuery.trim() ? 'pointer' : 'default',
              transition: 'all 0.15s ease',
              flexShrink: 0,
              outline: 'none'
            }}
          >
            <Send size={15} color={inputQuery.trim() ? '#FFFFFF' : '#A1A1AA'} style={{ display: 'block', margin: 'auto' }} />
          </button>
        </form>

      </div>

    </div>
  );
}
