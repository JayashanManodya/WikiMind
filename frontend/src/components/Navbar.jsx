import React from 'react';
import { HelpCircle, User, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab }) {
  const titles = {
    dashboard: 'Main Overview',
    upload: 'Document Ingestion',
    wiki: 'Knowledge Base Browser',
    chat: 'ChatGPT Grounded QA',
    documents: 'Document Storage Manager'
  };

  return (
    <header style={{ 
      backgroundColor: '#FFFFFF', 
      borderBottom: '1px solid var(--border-color)', 
      padding: '14px 24px',
      display: 'flex',
      alignItems: 'center',
      justify: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      {/* Title */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#09090B' }}>
          {titles[activeTab] || 'WikiMind'}
        </h3>
      </div>

      {/* Right User Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
          <ShieldCheck size={16} color="#10B981" />
          <span>Zero-Hallucination Active</span>
        </div>

        <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--border-color)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: '#09090B', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: '600' }}>
            WM
          </div>
          <span style={{ fontSize: '13px', fontWeight: '500' }}>WikiMind User</span>
        </div>
      </div>
    </header>
  );
}
