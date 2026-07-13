import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function ForgotPassword({ onNavigate }) {
    const { apiCall } = useAuth();
    const [email, setEmail] = useState('');
    const [msg, setMsg] = useState({ text: '', type: '' });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email) {
            setMsg({ text: 'Please enter your email.', type: 'error' });
            return;
        }

        setMsg({ text: '', type: '' });
        setLoading(true);
        try {
            const data = await apiCall('POST', '/auth/forgot-password', { email }, false);
            setMsg({ text: data.message || 'If that email exists, a reset link has been sent.', type: 'success' });
        } catch (e) {
            setMsg({ text: e.message || 'An error occurred.', type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page active" id="forgot-page">
            <div className="auth-wrap">
                <div className="auth-card">
                    <h2>Reset password</h2>
                    <p className="sub">We'll send you a reset link by email</p>
                    
                    {msg.text && <div className={`msg ${msg.type}`}>{msg.text}</div>}
                    
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
                        <button type="submit" className="btn btn-dark" style={{ width: '100%', padding: '11px' }} disabled={loading}>
                            {loading ? <span className="btn-spinner"></span> : 'Send reset link'}
                        </button>
                    </form>
                    
                    <div className="auth-footer">
                        Remembered it? <a onClick={() => onNavigate('login')}>Back to login</a>
                    </div>
                </div>
            </div>
        </div>
    );
}
