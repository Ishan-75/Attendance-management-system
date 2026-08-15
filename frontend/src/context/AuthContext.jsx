import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user_info');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const res = await authApi.getMe();
          if (res.success && res.data) {
            setUser(res.data);
            localStorage.setItem('user_info', JSON.stringify(res.data));
          }
        } catch (e) {
          // Token invalid or expired
          logout();
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [token]);

  const login = async (username_or_email, password) => {
    const res = await authApi.login(username_or_email, password);
    if (res.success && res.data) {
      const { access_token, user: userData } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_info', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return userData;
    }
    throw new Error(res.message || 'Login failed');
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // ignore
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      setToken(null);
      setUser(null);
    }
  };

  const refreshUser = async () => {
    if (token) {
      const res = await authApi.getMe();
      if (res.success && res.data) {
        setUser(res.data);
        localStorage.setItem('user_info', JSON.stringify(res.data));
      }
    }
  };

  const isAdmin = user?.role === 'ADMIN';
  const isManager = user?.role === 'MANAGER' || user?.role === 'ADMIN';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        refreshUser,
        isAuthenticated: !!token && !!user,
        isAdmin,
        isManager,
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
