import React, { useState } from 'react';
import GoogleAuthBtn from './GoogleAuthBtn';
import { useAuth } from '../context/AuthContext';
import { Shield, Sparkles, Network, AlertCircle } from 'lucide-react';
import './LoginPage.css';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1000000000000-placeholder.apps.googleusercontent.com';

export default function LoginPage() {
  const { loginWithGoogleToken } = useAuth();
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleGoogleSuccess = async (credentialResponse) => {
    setErrorMsg('');
    setIsSubmitting(true);
    try {
      if (credentialResponse.credential) {
        await loginWithGoogleToken(credentialResponse.credential);
      } else {
        setErrorMsg('Google response did not contain credential token.');
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Google sign-in failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleError = (msg) => {
    setErrorMsg(msg || 'Google Sign-In failed or popup was closed.');
  };

  return (
    <div className="login-page-container">
      <div className="login-card-wrapper">
        
        {/* Left Form Panel */}
        <div className="login-left-panel">
          
          {/* Header Brand Logo */}
          <div className="login-brand-header">
            <img
              src="/logo-color.png"
              alt="WikiMind Logo"
              className="login-brand-logo-img"
            />
          </div>

          {/* Form Content */}
          <div className="login-form-content">
            <h1 className="login-heading">Welcome to WikiMind</h1>
            <p className="login-subheading">
              Sign in with your Google account to access your private knowledge base, interactive entity graphs, and grounded AI QA.
            </p>

            {errorMsg && (
              <div style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '12px',
                padding: '12px 14px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#ef4444',
                fontSize: '0.85rem',
                textAlign: 'left'
              }}>
                <AlertCircle size={18} style={{ flexShrink: 0 }} />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Google OAuth Single Button Box */}
            <div className="login-google-container">
              <span className="login-google-badge-title">Quick & Secure Sign In</span>
              <GoogleAuthBtn
                clientId={GOOGLE_CLIENT_ID}
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
              />
            </div>

            {/* Feature Highlights */}
            <div className="login-feature-list">
              <div className="login-feature-item">
                <Shield size={16} className="login-feature-icon" />
                <span><strong>Private Knowledge Vault:</strong> Documents & entity graphs are strictly scoped to your account.</span>
              </div>
              <div className="login-feature-item">
                <Network size={16} className="login-feature-icon" />
                <span><strong>Graph-Aware QA:</strong> Traverse 1-hop relationships across your personal Wiki pages.</span>
              </div>
              <div className="login-feature-item">
                <Sparkles size={16} className="login-feature-icon" />
                <span><strong>Grounded AI Synthesis:</strong> Instant insights powered by LLM graph RAG.</span>
              </div>
            </div>

            {/* Footer Copy */}
            <p className="login-footer-copy">
              Join thousands of researchers and knowledge workers who trust WikiMind to manage, link, and query their knowledge base effortlessly.
            </p>
          </div>

          <div /> {/* Bottom spacer */}
        </div>

        {/* Right Panel with WikiMind Logo Artwork */}
        <div className="login-right-panel">
          <div className="login-graph-orb login-orb-1" />
          <div className="login-graph-orb login-orb-2" />
          
          <img
            src="/full.png"
            alt="WikiMind Logo Graphic"
            className="login-logo-artwork"
          />
        </div>

      </div>
    </div>
  );
}
