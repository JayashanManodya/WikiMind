import React, { useState } from 'react';
import GoogleAuthBtn from './GoogleAuthBtn';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, UserCheck, AlertCircle, Sparkles, Database, MessageSquare } from 'lucide-react';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1000000000000-placeholder.apps.googleusercontent.com';

export default function LoginPage() {
  const { loginWithGoogleToken, loginMock } = useAuth();
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

  const handleMockLogin = async (id) => {
    setErrorMsg('');
    setIsSubmitting(true);
    try {
      await loginMock(id);
    } catch (err) {
      setErrorMsg('Failed to log in with demo account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#f8fafc',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'radial-gradient(circle at top, #1e293b 0%, #0f172a 100%)',
    }}>
      <div style={{
        maxWidth: '480px',
        width: '100%',
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '20px',
        padding: '36px 32px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        textAlign: 'center',
      }}>
        {/* Header Logo */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
          <div style={{
            padding: '14px',
            borderRadius: '16px',
            backgroundColor: 'rgba(37, 99, 235, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Lock size={36} color="#60a5fa" />
          </div>
        </div>

        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', margin: '0 0 8px 0', color: '#f8fafc' }}>
          Sign In Required
        </h1>
        <p style={{ fontSize: '0.9rem', color: '#94a3b8', margin: '0 0 24px 0', lineHeight: 1.5 }}>
          Welcome to <strong>WikiMind</strong>. To access document ingestion, knowledge graph browsing, and grounded AI QA, please sign in.
        </p>

        {/* Feature Cards */}
        <div style={{
          backgroundColor: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '24px',
          textAlign: 'left',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <Shield size={18} color="#10b981" style={{ flexShrink: 0 }} />
            <span><strong>Private Knowledge Vault:</strong> Your uploaded documents and generated wiki graphs are strictly scoped to your account.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <Database size={18} color="#60a5fa" style={{ flexShrink: 0 }} />
            <span><strong>Graph-Aware QA:</strong> Traverse 1-hop relationships across your personal Wiki pages.</span>
          </div>
        </div>

        {errorMsg && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: '#fca5a5',
            fontSize: '0.85rem',
            textAlign: 'left',
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Google OAuth Login Button */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <GoogleAuthBtn
            clientId={GOOGLE_CLIENT_ID}
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
          />
        </div>

        {/* Divider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          margin: '20px 0',
          color: '#64748b',
          fontSize: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#334155' }} />
          <span>Or Quick Dev Demo Access</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#334155' }} />
        </div>

        {/* Quick Dev Demo Sign-In Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button
            onClick={() => handleMockLogin('alice')}
            disabled={isSubmitting}
            style={{
              padding: '12px 16px',
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#e2e8f0',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              transition: 'all 0.2s ease',
            }}
          >
            <UserCheck size={18} color="#60a5fa" />
            <span>Continue as <strong>Alice</strong> (Demo Account A)</span>
          </button>
          
          <button
            onClick={() => handleMockLogin('bob')}
            disabled={isSubmitting}
            style={{
              padding: '12px 16px',
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#e2e8f0',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              transition: 'all 0.2s ease',
            }}
          >
            <UserCheck size={18} color="#a78bfa" />
            <span>Continue as <strong>Bob</strong> (Demo Account B)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
