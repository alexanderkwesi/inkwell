import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Login({ onNavigate }) {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email || !password) {
            setError('Please fill in all fields.');
            return;
        }

        setError('');
        setLoading(true);
        try {
            await login(email, password);
            onNavigate('dashboard');
        } catch (e) {
            setError(e.message || 'Login failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page active" id="login-page">
            <div className="auth-wrap">
                <div className="auth-card">
                    <h2>Welcome back</h2>
                    <p className="sub">Log in to your Inkwell account</p>
                    
                    {error && <div className="msg error">{error}</div>}
                    
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Email address</label>
                            <input 
                                type="email" 
                                value={email} 
                                onChange={(e) => setEmail(e.target.value)} 
                                placeholder="you@example.com"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input 
                                type="password" 
                                value={password} 
                                onChange={(e) => setPassword(e.target.value)} 
                                placeholder="Your password"
                                required
                            />
                        </div>
                        <div style={{ textAlign: 'right', marginBottom: '1.2rem' }}>
                            <a className="link" style={{ fontSize: '0.85rem' }} onClick={() => onNavigate('forgot')}>
                                Forgot password?
                            </a>
                        </div>
                        <button type="submit" className="btn btn-dark" style={{ width: '100%', padding: '11px' }} disabled={loading}>
                            {loading ? <span className="btn-spinner"></span> : 'Log in'}
                        </button>
                    </form>
                    
                    <div className="auth-footer">
                        Don't have an account? <a onClick={() => onNavigate('signup')}>Sign up free</a>
                    </div>
                </div>
            </div>
        </div>
    );
}
