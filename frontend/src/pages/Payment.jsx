import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Payment({ onNavigate, params }) {
    const { apiCall } = useAuth();
    const plan = params?.plan || 'pro';
    const amount = plan === 'pro' ? 12 : 29;

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [redirectUrl, setRedirectUrl] = useState('');

    useEffect(() => {
        const initiateFlow = async () => {
            try {
                const data = await apiCall('POST', '/payments/initiate', { plan });
                setRedirectUrl(data.payment_url);
                setLoading(false);
                
                // Optional: Auto redirect to GoCardless hosted page
                // window.location.href = data.payment_url;
            } catch (e) {
                setError(e.message || 'Failed to initialize payment flow. Please try again.');
                setLoading(false);
            }
        };
        initiateFlow();
    }, [plan]);

    const handleRedirect = () => {
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    };

    return (
        <div className="page active" id="payment-page">
            <div className="auth-wrap">
                <div className="auth-card" style={{ maxWidth: '480px' }}>
                    <h2>Complete payment</h2>
                    <p className="sub" id="payment-plan-label">
                        Upgrading to {plan.charAt(0).toUpperCase() + plan.slice(1)} — £{amount}/month
                    </p>

                    <div className="gc-info">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2d5a8e" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 16v-4M12 8h.01"/>
                        </svg>
                        <div>
                            You will be redirected to <strong>GoCardless</strong> — a UK FCA-authorised payment provider — to enter your bank/DD details securely. We never store or see your bank credentials.
                            <br />
                            <span className="gc-badge">🔒 Secured by GoCardless</span>
                        </div>
                    </div>

                    {loading ? (
                        <div id="payment-loading" style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                            <div className="spinner"></div>
                            <p style={{ color: 'var(--ink3)', fontSize: '0.9rem', marginTop: '1rem' }}>
                                Preparing your secure payment page…
                            </p>
                        </div>
                    ) : error ? (
                        <div className="msg error" style={{ margin: '1rem 0' }}>{error}</div>
                    ) : (
                        <div id="payment-actions">
                            <button 
                                className="btn btn-gold" 
                                style={{ width: '100%', padding: '12px', fontSize: '1rem' }} 
                                onClick={handleRedirect}
                            >
                                Pay securely via GoCardless ✦
                            </button>
                        </div>
                    )}

                    <div className="auth-footer" style={{ marginTop: '1.5rem' }}>
                        <a onClick={() => onNavigate('pricing')}>← Back to plans</a>
                    </div>
                </div>
            </div>
        </div>
    );
}
