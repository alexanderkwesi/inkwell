import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Signup({ onNavigate }) {
    const { register } = useAuth();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name || !email || !password) {
            setError('Please fill in all fields.');
            return;
        }
        if (password.length < 6) {
            setError('Password must be at least 6 characters.');
            return;
        }

        setError('');
        setLoading(true);
        try {
            await register(name, email, password);
            onNavigate('dashboard');
        } catch (e) {
            setError(e.message || 'Sign up failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page active" id="signup-page">
            <div className="auth-wrap">
                <div className="auth-card">
                    <h2>Create account</h2>
                    <p className="sub">Start generating books for free today</p>
                    
                    {error && <div className="msg error">{error}</div>}
                    
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Full name</label>
                            <input 
                                type="text" 
                                value={name} 
                                onChange={(e) => setName(e.target.value)} 
                                placeholder="Your name"
                                required
                            />
                        </div>
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
                                placeholder="Min. 6 characters"
                                required
                            />
                            <div className="form-hint">At least 6 characters</div>
                        </div>
                        <button type="submit" className="btn btn-gold" style={{ width: '100%', padding: '11px' }} disabled={loading}>
                            {loading ? <span className="btn-spinner"></span> : 'Create free account'}
                        </button>
                    </form>
                    
                    <div className="auth-footer">
                        Already have an account? <a onClick={() => onNavigate('login')}>Log in</a>
                    </div>
                </div>
            </div>
        </div>
    );
}
