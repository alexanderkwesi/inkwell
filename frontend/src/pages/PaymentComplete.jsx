import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function PaymentComplete({ onNavigate }) {
    const { apiCall, updateProfileCache } = useAuth();
    
    const [cancelled, setCancelled] = useState(false);
    const [statusText, setStatusText] = useState('Confirming your payment…');
    const [description, setDescription] = useState('Please wait while we verify your payment with GoCardless. This usually takes a few seconds.');
    const [statusMsg, setStatusMsg] = useState('');
    const [loading, setLoading] = useState(true);
    const [showDashboardBtn, setShowDashboardBtn] = useState(false);

    useEffect(() => {
        const query = new URLSearchParams(window.location.search);
        const isCancelled = query.get('cancelled') === '1';
        const subId = query.get('sub_id');
        const brId = query.get('br_id');

        if (isCancelled) {
            setCancelled(true);
            setLoading(false);
            setStatusText('Payment cancelled');
            setDescription('No charge has been made. You can try again or choose a different plan.');
            return;
        }

        if (!subId || !brId) {
            setLoading(false);
            setStatusText('Missing payment parameters');
            setDescription('We could not identify the billing reference parameters in the URL redirect.');
            return;
        }

        // Start polling
        let polls = 0;
        const maxPolls = 12; // 12 * 5s = 60s
        
        const poll = async () => {
            polls++;
            setStatusMsg(`Checking… (${polls}/${maxPolls})`);
            
            try {
                const data = await apiCall('POST', '/payments/complete', {
                    billing_request_id: brId,
                    subscription_id: subId
                });

                if (data.status === 'active') {
                    setLoading(false);
                    setStatusText('🎉 Payment confirmed!');
                    setDescription(`You're now on the ${data.plan?.toUpperCase() || 'upgraded'} plan. Welcome!`);
                    setStatusMsg('');
                    setShowDashboardBtn(true);
                    
                    // Refresh user plan cache
                    if (data.user) {
                        updateProfileCache(data.user);
                    }

                    // Auto-redirect to dashboard after 3s
                    setTimeout(() => {
                        // Clear URL query parameters cleanly
                        window.history.replaceState({}, document.title, window.location.pathname);
                        onNavigate('dashboard');
                    }, 3000);
                    return;
                }

                if (data.status === 'pending' && polls < maxPolls) {
                    setTimeout(poll, 5000);
                } else if (polls >= maxPolls) {
                    setLoading(false);
                    setStatusText('Payment processing');
                    setDescription('GoCardless is processing your payment. Your plan will upgrade within a few minutes. You can safely close this page.');
                    setStatusMsg('');
                    setShowDashboardBtn(true);
                }
            } catch (e) {
                if (polls < maxPolls) {
                    setTimeout(poll, 5000);
                } else {
                    setLoading(false);
                    setStatusText('Something went wrong');
                    setDescription(e.message || 'Network error occurred verifying payment.');
                    setStatusMsg('');
                    setShowDashboardBtn(true);
                }
            }
        };

        // Initial delay before polling
        setTimeout(poll, 2000);
    }, []);

    const handleBack = () => {
        // Clear query parameters
        window.history.replaceState({}, document.title, window.location.pathname);
        onNavigate(cancelled ? 'pricing' : 'dashboard');
    };

    return (
        <div className="page active" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)' }}>
            <div className="settings-section" style={{ maxWidth: '480px', width: '90%', textAlign: 'center', padding: '3rem 2rem', margin: 0 }}>
                {cancelled ? (
                    <div style={{ fontSize: '3rem', marginBottom: '1.2rem', color: 'var(--danger)' }}>✕</div>
                ) : loading ? (
                    <div className="spinner" style={{ marginBottom: '1.5rem' }}></div>
                ) : (
                    <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🎉</div>
                )}

                <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.8rem', marginBottom: '0.8rem' }}>
                    {statusText}
                </h1>
                <p style={{ color: 'var(--ink3)', lineHeight: 1.6, marginBottom: '1.5rem', fontSize: '0.95rem' }}>
                    {description}
                </p>
                
                {statusMsg && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--ink4)', marginBottom: '1rem' }}>
                        {statusMsg}
                    </div>
                )}

                {showDashboardBtn || cancelled ? (
                    <div>
                        <button className="btn btn-gold" onClick={handleBack}>
                            {cancelled ? 'Back to plans' : 'Go to dashboard'}
                        </button>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
