import React, { useState } from 'react';
import GoogleAuthBtn from './GoogleAuthBtn';
import { useAuth } from '../context/AuthContext';
import { LogIn, X, Shield, UserCheck, AlertCircle } from 'lucide-react';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1000000000000-placeholder.apps.googleusercontent.com';

export default function LoginModal() {
  const { isLoginModalOpen, closeLoginModal, loginWithGoogleToken, loginMock } = useAuth();
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isLoginModalOpen) return null;

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
      setErrorMsg('Failed to log in with test account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
    }}>
      <div style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '16px',
        width: '90%',
        maxWidth: '440px',
        padding: '28px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        color: '#f8fafc',
        position: 'relative',
      }}>
        {/* Close Button */}
        <button
          onClick={closeLoginModal}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '8px',
          }}
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <img 
            src="/logo-color.png" 
            alt="WikiMind Logo" 
            style={{ height: '52px', objectFit: 'contain', marginBottom: '12px' }} 
          />
          <h2 style={{ fontSize: '1.4rem', fontWeight: '600', margin: '0 0 8px 0', color: '#f8fafc' }}>
            Sign In to WikiMind
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0, lineHeight: 1.5 }}>
            Log in with your Google account to keep your documents, Wiki Knowledge pages, and AI context private and unique to you.
          </p>
        </div>

        {errorMsg && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '10px 14px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: '#fca5a5',
            fontSize: '0.85rem'
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
          <span>Or Quick Dev Sign-In</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#334155' }} />
        </div>

        {/* Developer / Demo Quick Login buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button
            onClick={() => handleMockLogin('alice')}
            disabled={isSubmitting}
            style={{
              padding: '10px 16px',
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background-color 0.2s',
            }}
          >
            <UserCheck size={16} color="#60a5fa" />
            Continue as User Alice (Demo A)
          </button>
          
          <button
            onClick={() => handleMockLogin('bob')}
            disabled={isSubmitting}
            style={{
              padding: '10px 16px',
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0',
              fontWeight: 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background-color 0.2s',
            }}
          >
            <UserCheck size={16} color="#a78bfa" />
            Continue as User Bob (Demo B)
          </button>
        </div>
      </div>
    </div>
  );
}
