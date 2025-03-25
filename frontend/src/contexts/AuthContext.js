import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Check if user is already logged in (via token in localStorage)
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Set the token in the API instance
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Fetch user profile to verify token validity
      api.get('/api/users/me')
        .then(response => {
          setCurrentUser(response.data);
          setIsAuthenticated(true);
        })
        .catch(() => {
          // If request fails, token is likely invalid - clear it
          localStorage.removeItem('token');
          delete api.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      setError('');
      const response = await api.post('/api/auth/login', { email, password });
      const { access_token, token_type, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('token', access_token);
      
      // Set the token in the API instance
      api.defaults.headers.common['Authorization'] = `${token_type} ${access_token}`;
      
      setCurrentUser(user);
      setIsAuthenticated(true);
      return user;
    } catch (error) {
      const message = error.response?.data?.detail || 'An error occurred during login';
      setError(message);
      throw new Error(message);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setError('');
      const response = await api.post('/api/auth/register', userData);
      return response.data;
    } catch (error) {
      const message = error.response?.data?.detail || 'An error occurred during registration';
      setError(message);
      throw new Error(message);
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    currentUser,
    isAuthenticated,
    loading,
    error,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}