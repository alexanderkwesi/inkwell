import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Pricing({ onNavigate }) {
    const { user } = useAuth();

    const handleSelectPlan = (plan) => {
        if (!user) {
            onNavigate('signup');
            return;
        }
        
        if (plan === 'free') {
            onNavigate('dashboard');
            return;
        }

        // Navigate to payment processor redirect screen with chosen plan parameter
        onNavigate('payment', { plan });
    };

    return (
        <div className="page active" id="pricing-page">
            <div className="pricing-wrap">
                <h2>Choose your plan</h2>
                <p className="pricing-sub">Start free — upgrade anytime to unlock more books</p>
                
                <div className="pricing-grid">
                    {/* Free Plan */}
                    <div className="plan-card">
                        <div className="plan-name">Free</div>
                        <div className="plan-price">£0 <span>/ month</span></div>
                        <p className="plan-desc">Perfect for trying out the platform</p>
                        <ul className="plan-features">
                            <li><span className="check">✓</span> 4 complete books</li>
                            <li><span className="check">✓</span> AI illustrations per chapter</li>
                            <li><span className="check">✓</span> File & image upload</li>
                            <li><span className="check">✓</span> Book history</li>
                            <li style={{ color: 'var(--ink4)' }}>✗ Priority generation</li>
                            <li style={{ color: 'var(--ink4)' }}>✗ Export to PDF/EPUB</li>
                        </ul>
                        <button 
                            className="btn btn-ghost" 
                            style={{ width: '100%' }}
                            onClick={() => handleSelectPlan('free')}
                            disabled={user?.plan === 'free'}
                        >
                            {user?.plan === 'free' ? 'Current plan' : 'Select Free'}
                        </button>
                    </div>

                    {/* Pro Plan */}
                    <div className="plan-card featured">
                        <div className="popular-badge">Most Popular</div>
                        <div className="plan-name">Pro</div>
                        <div className="plan-price">£12 <span>/ month</span></div>
                        <p className="plan-desc">For serious writers and creators</p>
                        <ul className="plan-features">
                            <li><span className="check">✓</span> 10 complete books</li>
                            <li><span className="check">✓</span> HD AI illustrations</li>
                            <li><span className="check">✓</span> File & image upload</li>
                            <li><span className="check">✓</span> Full history & search</li>
                            <li><span className="check">✓</span> Priority generation</li>
                            <li><span className="check">✓</span> Export to PDF/EPUB</li>
                        </ul>
                        <button 
                            className="btn btn-gold" 
                            style={{ width: '100%' }}
                            onClick={() => handleSelectPlan('pro')}
                            disabled={user?.plan === 'pro'}
                        >
                            {user?.plan === 'pro' ? 'Current plan' : 'Upgrade to Pro'}
                        </button>
                    </div>

                    {/* Elite Plan */}
                    <div className="plan-card">
                        <div className="plan-name">Elite</div>
                        <div className="plan-price">£29 <span>/ month</span></div>
                        <p className="plan-desc">Unlimited creation for power users</p>
                        <ul className="plan-features">
                            <li><span className="check">✓</span> Unlimited books</li>
                            <li><span className="check">✓</span> Ultra-HD illustrations</li>
                            <li><span className="check">✓</span> File & image upload</li>
                            <li><span className="check">✓</span> Full history & search</li>
                            <li><span className="check">✓</span> Priority generation</li>
                            <li><span className="check">✓</span> All export formats</li>
                        </ul>
                        <button 
                            className="btn btn-dark" 
                            style={{ width: '100%' }}
                            onClick={() => handleSelectPlan('elite')}
                            disabled={user?.plan === 'elite'}
                        >
                            {user?.plan === 'elite' ? 'Current plan' : 'Get Elite'}
                        </button>
                    </div>
                </div>

                <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                    <button className="btn btn-ghost" onClick={() => onNavigate('dashboard')}>
                        ← Back to dashboard
                    </button>
                </div>

                {/* GoCardless Trust Banner */}
                <div style={{ textAlign: 'center', marginTop: '2rem', fontSize: '0.8rem', color: 'var(--ink4)' }}>
                    Payments processed securely by <strong style={{ color: 'var(--ink3)' }}>GoCardless</strong> · 
                    FCA Authorised Payment Institution · No card credentials stored on our servers
                </div>
            </div>
        </div>
    );
}
