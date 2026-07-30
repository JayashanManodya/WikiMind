import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider } from './context/DataContext';
import LoginPage from './components/LoginPage';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import WikiPage from './pages/WikiPage';
import ChatPage from './pages/ChatPage';
import GuidePage from './pages/GuidePage';

function AppGate() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedWikiEntity, setSelectedWikiEntity] = useState(null);

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        width: '100%',
        background: 'radial-gradient(ellipse at 50% 0%, rgba(56, 189, 248, 0.45) 0%, rgba(186, 230, 253, 0.25) 45%, rgba(248, 250, 252, 0) 80%) #F8FAFC',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      }}>
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '24px',
          padding: '40px 48px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.05)',
          textAlign: 'center',
          maxWidth: '360px',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px'
        }}>
          <img 
            src="/logo-color.png" 
            alt="WikiMind Logo" 
            style={{ width: '48px', height: '48px', objectFit: 'contain' }} 
          />
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#09090B', margin: 0, letterSpacing: '-0.02em' }}>
            WikiMind
          </h2>

          <div style={{
            width: '36px',
            height: '36px',
            border: '3px solid #E2E8F0',
            borderTopColor: '#2563EB',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '8px 0 4px 0',
          }} />

          <div>
            <p style={{ margin: 0, fontSize: '0.925rem', fontWeight: '700', color: '#09090B' }}>
              Initializing WikiMind...
            </p>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: '#64748B' }}>
              Preparing knowledge base & graph engine
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="app-layout" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="main-viewport" style={{ flex: 1, width: '100%', maxWidth: '100%' }}>
        <div className="content-container">
          {activeTab === 'dashboard' && (
            <DashboardPage 
              setActiveTab={setActiveTab} 
              setSelectedWikiEntity={setSelectedWikiEntity} 
            />
          )}

          {activeTab === 'upload' && (
            <UploadPage setActiveTab={setActiveTab} />
          )}

          {activeTab === 'wiki' && (
            <WikiPage 
              selectedEntity={selectedWikiEntity} 
              setSelectedEntity={setSelectedWikiEntity} 
            />
          )}

          {activeTab === 'chat' && (
            <ChatPage 
              setActiveTab={setActiveTab} 
              setSelectedWikiEntity={setSelectedWikiEntity} 
            />
          )}

          {activeTab === 'guide' && (
            <GuidePage setActiveTab={setActiveTab} />
          )}
        </div>
      </div>

      <LoginModal />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <AppGate />
      </DataProvider>
    </AuthProvider>
  );
}

