import React, { useState } from 'react';
import { ShieldCheck, LogIn, LogOut, User, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab }) {
  const { user, isAuthenticated, openLoginModal, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

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
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      {/* Title */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#09090B', margin: 0 }}>
          {titles[activeTab] || 'WikiMind'}
        </h3>
      </div>

      {/* Right Auth / User Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
          <ShieldCheck size={16} color="#10B981" />
          <span>User-Isolated Knowledge Active</span>
        </div>

        <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--border-color)' }} />

        {isAuthenticated && user ? (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '8px',
                transition: 'background-color 0.2s',
              }}
            >
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name}
                  style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover' }}
                />
              ) : (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#2563eb',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: '600'
                }}>
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
              )}
              
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#09090B' }}>
                  {user.name || 'Google User'}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>
                  {user.email || 'Google Account'}
                </div>
              </div>
            </button>

            {/* User Dropdown Menu */}
            {showDropdown && (
              <div style={{
                position: 'absolute',
                top: '110%',
                right: 0,
                backgroundColor: '#FFFFFF',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '8px',
                width: '200px',
                zIndex: 20,
              }}>
                <div style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', fontSize: '12px', color: '#64748b' }}>
                  Logged in as <strong style={{ color: '#0f172a' }}>{user.email}</strong>
                </div>
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    logout();
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    marginTop: '4px',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: '#ef4444',
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: 'pointer',
                    borderRadius: '6px',
                    textAlign: 'left',
                  }}
                >
                  <LogOut size={16} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={openLoginModal}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: '#2563eb',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)',
            }}
          >
            <LogIn size={16} />
            Sign In with Google
          </button>
        )}
      </div>
    </header>
  );
}
