import React, { useState } from 'react';
import { 
  MessageSquare, 
  BookOpen, 
  UploadCloud, 
  LayoutDashboard,
  HelpCircle,
  LogIn, 
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, isAuthenticated, openLoginModal, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  const topTabs = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'upload', label: 'Upload', icon: UploadCloud },
    { id: 'wiki', label: 'Knowledge Base', icon: BookOpen },
    { id: 'guide', label: 'Guide', icon: HelpCircle },
  ];

  return (
    <header style={{ 
      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: '1px solid #E2E8F0', 
      borderRadius: '9999px',
      padding: '8px 16px',
      margin: '8px auto 0 auto',
      width: 'min(1200px, calc(100% - 24px))',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: '8px',
      zIndex: 50,
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.04)',
      gap: '8px',
      overflowX: 'auto'
    }}>
      {/* Brand Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', flexShrink: 0 }} onClick={() => setActiveTab('dashboard')}>
        <img 
          src="/logo-color.png" 
          alt="WikiMind Logo" 
          style={{ width: '28px', height: '28px', objectFit: 'contain', borderRadius: '6px' }} 
        />
        <span style={{ fontSize: '15px', fontWeight: '700', color: '#09090B' }}>WikiMind</span>
      </div>

      {/* Center: Navigation Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {topTabs.map((tb) => {
          const Icon = tb.icon;
          const isActive = activeTab === tb.id;
          return (
            <button
              key={tb.id}
              onClick={() => setActiveTab(tb.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 16px',
                borderRadius: '9999px',
                border: 'none',
                backgroundColor: isActive ? '#F4F4F5' : 'transparent',
                color: isActive ? '#09090B' : '#64748B',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={14} color={isActive ? '#09090B' : '#64748B'} />
              <span>{tb.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Auth / Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginRight: '-4px' }}>
        {isAuthenticated && user ? (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '2px 6px',
                borderRadius: '8px'
              }}
            >
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name}
                  style={{ width: '30px', height: '30px', borderRadius: '50%', objectFit: 'cover' }}
                />
              ) : (
                <div style={{
                  width: '30px',
                  height: '30px',
                  borderRadius: '50%',
                  backgroundColor: '#09090B',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
              )}
            </button>

            {/* Dropdown */}
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
            className="btn btn-black"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', fontSize: '12.5px', cursor: 'pointer' }}
          >
            <LogIn size={14} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
}
