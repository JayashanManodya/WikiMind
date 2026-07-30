import React, { useState } from 'react';
import { 
  ArrowLeft, 
  ChevronDown, 
  MessageSquare, 
  BookOpen, 
  UploadCloud, 
  LayoutDashboard,
  HelpCircle,
  LogIn, 
  LogOut, 
  History
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
      backgroundColor: 'rgba(255, 255, 255, 0.85)', 
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-color)', 
      padding: '8px 36px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 10,
      minHeight: '52px'
    }}>
      {/* Brand Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
        <img 
          src="/logo-color.png" 
          alt="WikiMind Logo" 
          style={{ width: '28px', height: '28px', objectFit: 'contain', borderRadius: '6px' }} 
        />
        <span style={{ fontSize: '15px', fontWeight: '700', color: '#09090B' }}>WikiMind</span>
      </div>

      {/* Center: Direct Top Navigation Pills */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        backgroundColor: '#F4F4F5',
        borderRadius: '9999px',
        padding: '3px',
        border: '1px solid #E4E4E7',
        gap: '2px'
      }}>
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
                padding: '6px 16px',
                borderRadius: '9999px',
                border: 'none',
                backgroundColor: isActive ? '#FFFFFF' : 'transparent',
                color: isActive ? '#09090B' : '#71717A',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                cursor: 'pointer',
                boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={14} color={isActive ? '#09090B' : '#71717A'} />
              <span>{tb.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Auth / Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button className="btn btn-outline" style={{ display: 'flex', alignItems: 'center', padding: '5px 12px', fontSize: '12.5px', gap: '6px', cursor: 'pointer' }}>
          <History size={13} color="#71717A" />
          <span>Versions</span>
        </button>

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
