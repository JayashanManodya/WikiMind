import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Wrench, 
  BookOpen, 
  MessageSquare, 
  UploadCloud,
  Zap, 
  HelpCircle, 
  Settings,
  Activity,
  Plus,
  FileText,
  Trash2,
  Folder,
  Layers,
  Network
} from 'lucide-react';
import { getHealth } from '../api/client';

export default function Sidebar({ activeTab, setActiveTab }) {
  const [healthStatus, setHealthStatus] = useState('checking');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await getHealth();
        if (res.status === 'ok' || res.status === 'healthy') {
          setHealthStatus('healthy');
        } else {
          setHealthStatus('degraded');
        }
      } catch (err) {
        setHealthStatus('offline');
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="sidebar" style={{ width: '230px', padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Contextual Header based on activeTab */}
      <div style={{ paddingBottom: '10px', borderBottom: '1px solid var(--border-color)' }}>
        <p style={{ fontSize: '11px', fontWeight: '700', color: '#71717A', textTransform: 'uppercase', tracking: '0.5px' }}>
          {activeTab === 'chat' && '💬 Chat Conversations Menu'}
          {activeTab === 'wiki' && '📚 Wiki Knowledge Base Menu'}
          {activeTab === 'upload' && '📤 Document Ingestion Menu'}
          {activeTab === 'dashboard' && '📊 Agent Overview Menu'}
        </p>
      </div>

      {/* Contextual Navigation Menu */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        
        {/* MENU 1: CHAT MENU */}
        {activeTab === 'chat' && (
          <>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Select or switch between active conversation sessions below.
            </div>

            <button 
              className="btn btn-outline" 
              onClick={() => setActiveTab('wiki')}
              style={{ justifyContent: 'center', fontSize: '12.5px', padding: '8px 12px', gap: '6px' }}
            >
              <BookOpen size={14} color="#09090B" />
              <span>Browse Knowledge Base</span>
            </button>
          </>
        )}

        {/* MENU 2: WIKI KNOWLEDGE BASE MENU */}
        {activeTab === 'wiki' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              onClick={() => setActiveTab('wiki')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: '8px',
                backgroundColor: '#F4F4F5',
                color: '#09090B',
                fontSize: '13px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <Folder size={15} color="#09090B" />
              <span>All Wiki Entities</span>
            </button>

            <button
              onClick={() => setActiveTab('wiki')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: '8px',
                backgroundColor: 'transparent',
                color: '#3F3F46',
                fontSize: '13px',
                fontWeight: '500',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <Network size={15} color="#71717A" />
              <span>Knowledge Graph View</span>
            </button>

            <div style={{ marginTop: '10px', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
              <p style={{ fontSize: '11px', fontWeight: '600', color: '#A1A1AA', textTransform: 'uppercase', marginBottom: '6px' }}>
                Entity Categories
              </p>
              {['SYSTEM', 'PERSON', 'CONCEPT', 'PRODUCT', 'COMPONENT', 'HARDWARE'].map((cat) => (
                <div key={cat} style={{ fontSize: '12px', color: '#52525B', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>
                  • {cat}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* MENU 3: UPLOAD INGESTION MENU */}
        {activeTab === 'upload' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              Ingestion Pipeline Stages:
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#09090B', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={14} color="#71717A" />
                <span>1. Layout Parsing</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#09090B', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={14} color="#71717A" />
                <span>2. LLM Extraction</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#09090B', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={14} color="#71717A" />
                <span>3. SQL DB Record Save</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#09090B', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={14} color="#71717A" />
                <span>4. Vector DB Indexing</span>
              </div>
            </div>
          </div>
        )}

        {/* MENU 4: OVERVIEW DASHBOARD MENU */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              onClick={() => setActiveTab('dashboard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: '8px',
                backgroundColor: '#F4F4F5',
                color: '#09090B',
                fontSize: '13px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              <Sparkles size={15} color="#09090B" />
              <span>Prompt Guidelines</span>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: '8px',
                backgroundColor: 'transparent',
                color: '#3F3F46',
                fontSize: '13px',
                fontWeight: '500',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              <Wrench size={15} color="#71717A" />
              <span>Tools & Engines</span>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 10px',
                borderRadius: '8px',
                backgroundColor: 'transparent',
                color: '#3F3F46',
                fontSize: '13px',
                fontWeight: '500',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              <Zap size={15} color="#71717A" />
              <span>Auto Ingestion Triggers</span>
            </button>
          </div>
        )}

      </div>

      {/* Bottom Footer Items */}
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '6px 10px',
            borderRadius: '6px',
            background: 'none',
            border: 'none',
            color: '#3F3F46',
            fontSize: '12.5px',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          <Settings size={15} color="#71717A" />
          <span>Advanced</span>
        </button>

        <button
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '6px 10px',
            borderRadius: '6px',
            background: 'none',
            border: 'none',
            color: '#3F3F46',
            fontSize: '12.5px',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          <HelpCircle size={15} color="#71717A" />
          <span>Need help?</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)', padding: '6px 10px', marginTop: '4px' }}>
          <Activity size={12} color={healthStatus === 'healthy' ? '#10B981' : '#EF4444'} />
          <span>{healthStatus === 'healthy' ? 'API Online' : 'API Offline'}</span>
        </div>
      </div>
    </aside>
  );
}
