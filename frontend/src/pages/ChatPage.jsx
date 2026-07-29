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
  Trash2
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

export default function ChatPage({ setActiveTab, setSelectedWikiEntity }) {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('wikimind_chat_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.error("Failed to load chat history from localStorage", e);
    }
    return INITIAL_WELCOME_MESSAGE;
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Persist messages to browser localStorage cache on change
  useEffect(() => {
    try {
      localStorage.setItem('wikimind_chat_history', JSON.stringify(messages));
    } catch (e) {
      console.error("Failed to save chat history to localStorage", e);
    }
  }, [messages]);

  const handleClearChat = () => {
    setMessages(INITIAL_WELCOME_MESSAGE);
    try {
      localStorage.removeItem('wikimind_chat_history');
    } catch (e) {
      console.error("Failed to clear chat history from localStorage", e);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isAsking) return;

    const userMessage = { sender: 'user', text: inputQuery };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputQuery('');
    setIsAsking(true);

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

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: 'Error contacting backend QA engine.',
          grounded: false,
          citations: [],
          confidence: 0.0
        }
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', maxWidth: '900px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '16px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#09090B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot size={18} color="#FFFFFF" />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600' }}>ChatGPT Grounded Engine</h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Zero-hallucination factual answer model</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            className="btn btn-outline" 
            onClick={handleClearChat}
            style={{ fontSize: '12px', padding: '6px 12px', gap: '6px' }}
            title="Clear Chat History"
          >
            <Trash2 size={13} color="#71717A" />
            <span>Clear Chat</span>
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

      {/* Floating Bottom Input Bar matching Screenshot 2 */}
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
  );
}
