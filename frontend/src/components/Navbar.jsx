import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  BookOpen, 
  UploadCloud, 
  LayoutDashboard,
  HelpCircle,
  LogIn, 
  LogOut,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, isAuthenticated, openLoginModal, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  const topTabs = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'upload', label: 'Upload', icon: UploadCloud },
    { id: 'wiki', label: 'Knowledge Base', icon: BookOpen },
    { id: 'guide', label: 'Guide', icon: HelpCircle },
  ];

  return (
    <header className="wikimind-navbar-header" style={{ 
      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: '1px solid #E2E8F0', 
      borderRadius: '9999px',
      padding: '8px 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: '8px',
      zIndex: 50,
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.04)',
      gap: '8px',
      overflow: 'visible'
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto', flexShrink: 1, padding: '2px 0' }}>
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
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap'
              }}
            >
              <Icon size={14} color={isActive ? '#09090B' : '#64748B'} />
              <span>{tb.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Auth / Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginRight: '-4px', flexShrink: 0 }}>
        {isAuthenticated && user ? (
          <div style={{ position: 'relative' }} ref={dropdownRef}>
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
                  alt={user.name || 'User'}
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
                  {user.name ? user.name.charAt(0).toUpperCase() : (user.email ? user.email.charAt(0).toUpperCase() : 'U')}
                </div>
              )}
            </button>

            {/* Dropdown */}
            {showDropdown && (
              <div style={{
                position: 'absolute',
                top: 'calc(100% + 10px)',
                right: 0,
                backgroundColor: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: '16px',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
                padding: '16px',
                width: '260px',
                zIndex: 1000,
                textAlign: 'left',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                {/* Header User Details */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name || 'User Avatar'}
                      style={{ width: '42px', height: '42px', borderRadius: '50%', objectFit: 'cover', border: '2px solid #E2E8F0', flexShrink: 0 }}
                    />
                  ) : (
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      backgroundColor: '#09090B',
                      color: '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px',
                      fontWeight: '700',
                      flexShrink: 0
                    }}>
                      {user.name ? user.name.charAt(0).toUpperCase() : (user.email ? user.email.charAt(0).toUpperCase() : 'U')}
                    </div>
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', textAlign: 'left', minWidth: 0 }}>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: '#0F172A', lineHeight: '1.2', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {user.name || 'User Account'}
                    </span>
                    <span style={{ fontSize: '12px', color: '#64748B', lineHeight: '1.3', marginTop: '3px', wordBreak: 'break-all' }}>
                      {user.email}
                    </span>
                  </div>
                </div>

                <div style={{ height: '1px', backgroundColor: '#F1F5F9', margin: '0 -16px' }} />

                {/* Quick Navigation / Account Items */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <button
                    onClick={() => {
                      setShowDropdown(false);
                      setActiveTab('dashboard');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 10px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#334155',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      borderRadius: '8px',
                      textAlign: 'left',
                      transition: 'background-color 0.15s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8FAFC'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <LayoutDashboard size={15} color="#64748B" />
                    <span>Dashboard</span>
                  </button>

                  <button
                    onClick={() => {
                      setShowDropdown(false);
                      setActiveTab('guide');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 10px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#334155',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      borderRadius: '8px',
                      textAlign: 'left',
                      transition: 'background-color 0.15s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8FAFC'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <BookOpen size={15} color="#64748B" />
                    <span>User Guide & Docs</span>
                  </button>
                </div>

                <div style={{ height: '1px', backgroundColor: '#F1F5F9', margin: '0 -16px' }} />

                {/* Sign Out Button */}
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    logout();
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '9px 12px',
                    border: 'none',
                    backgroundColor: '#FEF2F2',
                    color: '#DC2626',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    borderRadius: '8px',
                    textAlign: 'left',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#FEE2E2';
                    e.currentTarget.style.color = '#B91C1C';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#FEF2F2';
                    e.currentTarget.style.color = '#DC2626';
                  }}
                >
                  <LogOut size={16} />
                  <span>Sign Out Account</span>
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
