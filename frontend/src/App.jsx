import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Pricing from './pages/Pricing';
import Payment from './pages/Payment';
import PaymentComplete from './pages/PaymentComplete';
import Admin from './pages/Admin';

export default function App() {
    const { user, loading, logout } = useAuth();
    
    // State-based routing with params
    const [nav, setNav] = useState({ page: 'home', params: {} });
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const onNavigate = (page, params = {}) => {
        setNav({ page, params });
        setMobileMenuOpen(false);
        window.scrollTo(0, 0);
    };

    // Detect URL query redirect parameters from GoCardless payment returns
    useEffect(() => {
        const query = new URLSearchParams(window.location.search);
        if (query.get('sub_id') || query.get('cancelled') === '1') {
            onNavigate('payment-complete');
        }
    }, []);

    if (loading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--paper)' }}>
                <div className="spinner"></div>
            </div>
        );
    }

    const renderPage = () => {
        switch (nav.page) {
            case 'home':
                return <Home onNavigate={onNavigate} />;
            case 'login':
                return <Login onNavigate={onNavigate} />;
            case 'signup':
                return <Signup onNavigate={onNavigate} />;
            case 'forgot':
                return <ForgotPassword onNavigate={onNavigate} />;
            case 'dashboard':
                return user ? <Dashboard onNavigate={onNavigate} /> : <Login onNavigate={onNavigate} />;
            case 'profile':
                return user ? <Profile onNavigate={onNavigate} /> : <Login onNavigate={onNavigate} />;
            case 'pricing':
                return <Pricing onNavigate={onNavigate} />;
            case 'payment':
                return user ? <Payment onNavigate={onNavigate} params={nav.params} /> : <Login onNavigate={onNavigate} />;
            case 'payment-complete':
                return <PaymentComplete onNavigate={onNavigate} />;
            case 'admin':
                return user?.is_admin ? <Admin onNavigate={onNavigate} /> : <Home onNavigate={onNavigate} />;
            default:
                return <Home onNavigate={onNavigate} />;
        }
    };

    return (
        <div>
            {/* Global Navigation Header Bar */}
            {nav.page !== 'dashboard' && (
                <nav>
                    <div className="nav-logo" onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>
                        ✦ <span>Inkwell</span> AI
                    </div>
                    
                    {/* Desktop Navigation links */}
                    <div className="nav-right">
                        {user ? (
                            <>
                                {user.is_admin && (
                                    <button className="btn btn-ghost" onClick={() => onNavigate('admin')}>
                                        🔐 Admin
                                    </button>
                                )}
                                <button className="btn btn-ghost" onClick={() => onNavigate('dashboard')}>
                                    Dashboard
                                </button>
                                <button className="btn btn-ghost" onClick={() => onNavigate('profile')}>
                                    ⚙ {user.name.split(' ')[0]}
                                </button>
                                <button className="btn btn-ghost" onClick={logout}>
                                    Log out
                                </button>
                            </>
                        ) : (
                            <>
                                <button className="btn btn-ghost" onClick={() => onNavigate('login')}>
                                    Log in
                                </button>
                                <button className="btn btn-gold" onClick={() => onNavigate('signup')}>
                                    Get started
                                </button>
                            </>
                        )}
                    </div>

                    {/* Mobile Hamburger toggle */}
                    <button 
                        className={`nav-hamburger ${mobileMenuOpen ? 'open' : ''}`} 
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    >
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                </nav>
            )}

            {/* Mobile slide-down menu */}
            {mobileMenuOpen && nav.page !== 'dashboard' && (
                <div className="mobile-menu open">
                    {user ? (
                        <>
                            {user.is_admin && (
                                <button className="btn btn-ghost" onClick={() => onNavigate('admin')}>
                                    🔐 Admin Dashboard
                                </button>
                            )}
                            <button className="btn btn-ghost" onClick={() => onNavigate('dashboard')}>
                                Dashboard
                            </button>
                            <button className="btn btn-ghost" onClick={() => onNavigate('profile')}>
                                ⚙ Settings ({user.name.split(' ')[0]})
                            </button>
                            <button className="btn btn-danger" onClick={logout}>
                                Log out
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="btn btn-ghost" onClick={() => onNavigate('login')}>
                                Log in
                            </button>
                            <button className="btn btn-gold" onClick={() => onNavigate('signup')}>
                                Get started
                            </button>
                        </>
                    )}
                </div>
            )}

            {/* Page Content area */}
            {renderPage()}
        </div>
    );
}
