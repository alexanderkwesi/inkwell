import React, { createContext, useState, useEffect, useContext } from 'react';

const AuthContext = createContext(null);

const API_BASE = 'http://localhost:56517/api';

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const cached = localStorage.getItem('inkwell_user');
        try {
            return cached ? JSON.parse(cached) : null;
        } catch (e) {
            return null;
        }
    });
    const [token, setToken] = useState(() => localStorage.getItem('inkwell_token'));
    const [loading, setLoading] = useState(true);

    const apiCall = async (method, path, body = null, requireAuth = true) => {
        const headers = { 'Content-Type': 'application/json' };
        if (requireAuth && token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const opts = {
            method,
            headers,
        };
        if (body) {
            opts.body = JSON.stringify(body);
        }

        const res = await fetch(`${API_BASE}${path}`, opts);
        const data = await res.json();
        
        if (!res.ok) {
            const error = new Error(data.detail || 'Request failed');
            error.status = res.status;
            throw error;
        }
        return data;
    };

    // Verify token validity on load
    useEffect(() => {
        const verifyToken = async () => {
            if (token) {
                try {
                    const data = await apiCall('GET', '/auth/me', null, true);
                    setUser(data);
                    localStorage.setItem('inkwell_user', JSON.stringify(data));
                } catch (e) {
                    // Token is invalid/expired
                    logout();
                }
            }
            setLoading(false);
        };
        verifyToken();
    }, [token]);

    const login = async (email, password) => {
        const data = await apiCall('POST', '/auth/login', { email, password }, false);
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('inkwell_token', data.token);
        localStorage.setItem('inkwell_user', JSON.stringify(data.user));
        return data.user;
    };

    const register = async (name, email, password) => {
        const data = await apiCall('POST', '/auth/register', { name, email, password }, false);
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('inkwell_token', data.token);
        localStorage.setItem('inkwell_user', JSON.stringify(data.user));
        return data.user;
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('inkwell_token');
        localStorage.removeItem('inkwell_user');
    };

    const updateProfileCache = (updatedUser) => {
        setUser(updatedUser);
        localStorage.setItem('inkwell_user', JSON.stringify(updatedUser));
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateProfileCache, apiCall }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
