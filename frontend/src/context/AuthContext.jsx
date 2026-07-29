import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginWithGoogle as loginApi, getCurrentUser } from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('wikillm_token') || null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('wikillm_token');
      if (savedToken) {
        try {
          const userData = await getCurrentUser();
          if (!userData.is_guest) {
            setUser(userData);
            setToken(savedToken);
          } else {
            // Token invalid or returned guest
            localStorage.removeItem('wikillm_token');
            setUser(null);
            setToken(null);
          }
        } catch (err) {
          console.warn("Stored auth token validation failed:", err);
          localStorage.removeItem('wikillm_token');
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const loginWithGoogleToken = async (credential) => {
    try {
      const data = await loginApi(credential);
      const { access_token, user: userData } = data;
      localStorage.setItem('wikillm_token', access_token);
      setToken(access_token);
      setUser(userData);
      setIsLoginModalOpen(false);
      return userData;
    } catch (err) {
      console.error("Google authentication error:", err);
      throw err;
    }
  };

  const loginMock = async (mockId = 'demo_user') => {
    return loginWithGoogleToken(`mock_token_${mockId}`);
  };

  const logout = () => {
    localStorage.removeItem('wikillm_token');
    setToken(null);
    setUser(null);
  };

  const openLoginModal = () => setIsLoginModalOpen(true);
  const closeLoginModal = () => setIsLoginModalOpen(false);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        isLoginModalOpen,
        openLoginModal,
        closeLoginModal,
        loginWithGoogleToken,
        loginMock,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
