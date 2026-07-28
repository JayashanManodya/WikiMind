import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Upload, 
  BookOpen, 
  MessageSquare, 
  Bot,
  Activity
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

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload & Ingest', icon: Upload },
    { id: 'wiki', label: 'Wiki Browser & Graph', icon: BookOpen },
    { id: 'chat', label: 'AI QA Chat', icon: MessageSquare },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 4px 20px 4px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#09090B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Bot size={18} color="#FFFFFF" />
        </div>
        <div>
          <h2 style={{ fontSize: '17px', fontWeight: '700', lineHeight: '1.2' }}>WikiLLM</h2>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Grounded Knowledge System</p>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        <p style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-subtle)', textTransform: 'uppercase', padding: '0 8px 8px 8px' }}>
          Navigation
        </p>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive ? '#09090B' : 'transparent',
                color: isActive ? '#FFFFFF' : 'var(--text-main)',
                fontSize: '13.5px',
                fontWeight: isActive ? '600' : '400',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={17} color={isActive ? '#FFFFFF' : '#71717A'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Status Card */}
      <div className="clean-card" style={{ padding: '12px', marginTop: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '12px', fontWeight: '600' }}>WikiLLM Engine</span>
          <span className="badge-clean" style={{ fontSize: '10px' }}>v2.0</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <Activity size={12} color={healthStatus === 'healthy' ? '#10B981' : '#EF4444'} />
          <span>{healthStatus === 'healthy' ? 'API Online' : 'API Offline'}</span>
        </div>
      </div>
    </aside>
  );
}
