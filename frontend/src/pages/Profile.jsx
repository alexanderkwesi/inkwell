import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Profile({ onNavigate }) {
    const { user, logout, apiCall, updateProfileCache } = useAuth();
    
    const [name, setName] = useState(user?.name || '');
    const [email, setEmail] = useState(user?.email || '');
    const [profileError, setProfileError] = useState('');
    const [profileSuccess, setProfileSuccess] = useState('');
    
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [pwdError, setPwdError] = useState('');
    const [pwdSuccess, setPwdSuccess] = useState('');

    const [payments, setPayments] = useState([]);
    const [loadingPayments, setLoadingPayments] = useState(true);

    const [deleteModalOpen, setDeleteModalOpen] = useState(false);

    // Fetch billing history
    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const data = await apiCall('GET', '/payments/history');
                setPayments(data.payments);
            } catch (e) {
                console.error('Error fetching payments:', e);
            } finally {
                setLoadingPayments(false);
            }
        };
        fetchHistory();
    }, []);

    const handleSaveProfile = async (e) => {
        e.preventDefault();
        if (!name || !email) {
            setProfileError('Name and email are required.');
            return;
        }

        setProfileError('');
        setProfileSuccess('');
        try {
            const updated = await apiCall('PUT', '/users/profile', { name, email });
            updateProfileCache(updated);
            setProfileSuccess('Profile updated successfully!');
        } catch (e) {
            setProfileError(e.message || 'Profile update failed.');
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        if (!newPassword || !confirmPassword) {
            setPwdError('Please fill in both fields.');
            return;
        }
        if (newPassword !== confirmPassword) {
            setPwdError('Passwords do not match.');
            return;
        }
        if (newPassword.length < 6) {
            setPwdError('Password must be at least 6 characters.');
            return;
        }

        setPwdError('');
        setPwdSuccess('');
        try {
            await apiCall('PUT', '/users/password', { password: newPassword });
            setPwdSuccess('Password changed successfully!');
            setNewPassword('');
            setConfirmPassword('');
        } catch (e) {
            setPwdError(e.message || 'Password update failed.');
        }
    };

    const handleDeleteAccount = async () => {
        try {
            await apiCall('DELETE', '/users/account');
            logout();
            onNavigate('home');
        } catch (e) {
            alert('Failed to delete account: ' + e.message);
        }
    };

    const handleCancelSubscription = async () => {
        if (!confirm('Are you sure you want to cancel your subscription? You will be downgraded to the Free plan immediately.')) {
            return;
        }
        try {
            const res = await apiCall('POST', '/payments/cancel');
            alert(res.message);
            // Refresh me data
            const me = await apiCall('GET', '/auth/me');
            updateProfileCache(me);
        } catch (e) {
            alert('Failed to cancel subscription: ' + e.message);
        }
    };

    return (
        <div className="page active" id="profile-page">
            <div className="settings-wrap">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                    <button className="btn btn-ghost" onClick={() => onNavigate('dashboard')} style={{ padding: '7px 14px' }}>
                        ← Back to Dashboard
                    </button>
                    <h2 style={{ margin: 0 }}>Profile & Settings</h2>
                </div>

                <div className="settings-section">
                    <h3>Account Information</h3>
                    {profileError && <div className="msg error">{profileError}</div>}
                    {profileSuccess && <div className="msg success">{profileSuccess}</div>}
                    
                    <form onSubmit={handleSaveProfile}>
                        <div className="form-group">
                            <label>Full Name</label>
                            <input 
                                type="text" 
                                value={name} 
                                onChange={(e) => setName(e.target.value)} 
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Email Address</label>
                            <input 
                                type="email" 
                                value={email} 
                                onChange={(e) => setEmail(e.target.value)} 
                                required
                            />
                        </div>
                        <button type="submit" className="btn btn-dark">Save changes</button>
                    </form>
                </div>

                <div className="settings-section">
                    <h3>Change Password</h3>
                    {pwdError && <div className="msg error">{pwdError}</div>}
                    {pwdSuccess && <div className="msg success">{pwdSuccess}</div>}
                    
                    <form onSubmit={handleChangePassword}>
                        <div className="form-group">
                            <label>New Password</label>
                            <input 
                                type="password" 
                                value={newPassword} 
                                onChange={(e) => setNewPassword(e.target.value)} 
                                placeholder="New password"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Confirm New Password</label>
                            <input 
                                type="password" 
                                value={confirmPassword} 
                                onChange={(e) => setConfirmPassword(e.target.value)} 
                                placeholder="Confirm new password"
                                required
                            />
                        </div>
                        <button type="submit" className="btn btn-outline">Update password</button>
                    </form>
                </div>

                <div className="settings-section">
                    <h3>Current Plan</h3>
                    <div id="current-plan-info" style={{ fontSize: '0.95rem', color: 'var(--ink2)', marginBottom: '1.2rem', fontWeight: 500 }}>
                        Active Plan: <span className={`plan-badge ${user?.plan}`} style={{ marginLeft: '6px' }}>{user?.plan}</span>
                        {user?.plan !== 'free' && (
                            <button 
                                className="btn btn-ghost" 
                                style={{ padding: '4px 10px', fontSize: '0.75rem', marginLeft: '12px', color: 'var(--danger)', borderColor: '#f5c6c6' }}
                                onClick={handleCancelSubscription}
                            >
                                Cancel Subscription
                            </button>
                        )}
                    </div>
                    {user?.plan === 'free' ? (
                        <button className="btn btn-gold" onClick={() => onNavigate('pricing')}>Upgrade Plan</button>
                    ) : (
                        <p style={{ fontSize: '0.85rem', color: 'var(--ink3)' }}>Your billing cycles recur monthly. You can manage your Direct Debit mandate via your bank details or contact support.</p>
                    )}
                </div>

                <div className="settings-section">
                    <h3>Billing History</h3>
                    <div id="billing-history">
                        {loadingPayments ? (
                            <div>Loading history...</div>
                        ) : payments.length === 0 ? (
                            <div style={{ fontSize: '0.85rem', color: 'var(--ink4)', textAlign: 'center', padding: '1rem 0' }}>No transactions recorded</div>
                        ) : (
                            <table className="history-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Description</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {payments.map(p => (
                                        <tr key={p.id}>
                                            <td>{new Date(p.created_at).toLocaleDateString()}</td>
                                            <td>{p.plan_name ? `Inkwell ${p.plan_name.toUpperCase()} Subscription` : 'Standard payment'}</td>
                                            <td>£{p.amount.toFixed(2)}</td>
                                            <td>
                                                <span style={{ 
                                                    fontWeight: 600, 
                                                    color: p.status === 'succeeded' ? 'var(--success)' : p.status === 'pending' ? '#d97706' : 'var(--danger)' 
                                                }}>
                                                    {p.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>

                <div className="settings-section" style={{ borderColor: '#f5c6c6' }}>
                    <h3 style={{ color: 'var(--danger)' }}>Danger Zone</h3>
                    <p style={{ fontSize: '0.875rem', color: 'var(--ink3)', marginBottom: '1.2rem' }}>Permanently delete your account and all associated data. This action is irreversible.</p>
                    <button className="btn btn-danger" onClick={() => setDeleteModalOpen(true)}>Delete account</button>
                </div>
            </div>

            {/* Account Delete Confirm Modal */}
            {deleteModalOpen && (
                <div className="modal-bg" id="delete-modal">
                    <div className="modal">
                        <h3>Delete account?</h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--ink3)', marginTop: '0.5rem', lineHeight: 1.6 }}>
                            This will permanently remove your account, subscription mandates, and all generated books. This cannot be undone.
                        </p>
                        <div className="modal-actions">
                            <button className="btn btn-ghost" onClick={() => setDeleteModalOpen(false)}>Cancel</button>
                            <button className="btn btn-danger" onClick={handleDeleteAccount}>Yes, delete account</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
