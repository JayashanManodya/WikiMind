import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import WikiPage from './pages/WikiPage';
import ChatPage from './pages/ChatPage';

function MainAppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedWikiEntity, setSelectedWikiEntity] = useState(null);

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="main-viewport">
        <Navbar activeTab={activeTab} />
        
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
      <MainAppContent />
    </AuthProvider>
  );
}
