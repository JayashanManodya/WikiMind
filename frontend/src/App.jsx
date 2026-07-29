import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import WikiPage from './pages/WikiPage';
import ChatPage from './pages/ChatPage';

function AppGate() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedWikiEntity, setSelectedWikiEntity] = useState(null);

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        fontFamily: 'sans-serif',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid #334155',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px auto',
          }} />
          <p style={{ margin: 0, fontSize: '0.9rem' }}>Initializing WikiMind...</p>
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
        </div>
      </div>

      <LoginModal />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppGate />
    </AuthProvider>
  );
}
