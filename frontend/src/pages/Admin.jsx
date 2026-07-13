import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Admin({ onNavigate }) {
    const { user, apiCall } = useAuth();
    
    const [stats, setStats] = useState(null);
    const [usersList, setUsersList] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const statsData = await apiCall('GET', '/users/admin/stats');
            setStats(statsData);

            const usersData = await apiCall('GET', '/users/admin/list');
            setUsersList(usersData.users);
        } catch (e) {
            setError(e.message || 'Failed to fetch admin dashboard metrics.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!user || !user.is_admin) {
            onNavigate('dashboard');
            return;
        }
        fetchData();
    }, [user]);

    const handleSetPlan = async (userId, plan) => {
        try {
            await apiCall('PUT', `/users/admin/${userId}/plan`, { plan });
            fetchData();
        } catch (e) {
            alert('Failed to update plan: ' + e.message);
        }
    };

    const handleDeleteUser = async (userId, email) => {
        if (!confirm(`Are you sure you want to delete user ${email}?`)) return;
        try {
            await apiCall('DELETE', `/users/admin/${userId}`);
            fetchData();
        } catch (e) {
            alert('Failed to delete user: ' + e.message);
        }
    };

    const handleResetAllBooks = async () => {
        if (!confirm('Reset all book counts to 0?')) return;
        try {
            await apiCall('POST', '/users/admin/reset-books');
            fetchData();
        } catch (e) {
            alert('Failed to reset book counts: ' + e.message);
        }
    };

    const handleExportData = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(usersList, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "inkwell_admin_export.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    };

    if (!user || !user.is_admin) {
        return <div className="page active"><p>Access Forbidden.</p></div>;
    }

    return (
        <div className="page active" id="admin-page">
            <div className="admin-wrap">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2.2rem' }}>
                    <h2>🔐 Admin Dashboard</h2>
                    <button className="btn btn-ghost" onClick={() => onNavigate('dashboard')}>
                        ← Back to Dashboard
                    </button>
                </div>

                {error && <div className="msg error">{error}</div>}

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '3rem' }}>
                        <div className="spinner"></div>
                        <p style={{ marginTop: '1rem', color: 'var(--ink3)' }}>Loading administrator panels...</p>
                    </div>
                ) : (
                    <>
                        {/* Stats Dashboard Grid */}
                        <div className="admin-grid">
                            <div className="stat-card">
                                <div className="stat-label">Total Users</div>
                                <div className="stat-val">{stats?.total_users}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Books Generated</div>
                                <div className="stat-val">{stats?.total_books}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Pro Subscribers</div>
                                <div className="stat-val">{stats?.pro_users}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Elite Subscribers</div>
                                <div className="stat-val">{stats?.elite_users}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Total Revenue</div>
                                <div className="stat-val">£{stats?.total_revenue.toFixed(2)}</div>
                            </div>
                        </div>

                        {/* All Users Table */}
                        <div className="admin-section">
                            <div className="admin-section-header">All Registered Users</div>
                            <div style={{ overflowX: 'auto' }}>
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Email</th>
                                            <th>Plan</th>
                                            <th>Books Count</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {usersList.length === 0 ? (
                                            <tr>
                                                <td colSpan="5" style={{ textAlign: 'center', color: 'var(--ink4)', padding: '2rem' }}>
                                                    No users registered yet
                                                </td>
                                            </tr>
                                        ) : (
                                            usersList.map(u => (
                                                <tr key={u.id}>
                                                    <td>{u.name}</td>
                                                    <td>{u.email}</td>
                                                    <td>
                                                        <span className={`tag ${u.plan}`}>{u.plan}</span>
                                                    </td>
                                                    <td>{u.books_used}</td>
                                                    <td style={{ display: 'flex', gap: '8px' }}>
                                                        <button 
                                                            className="btn btn-ghost" 
                                                            style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                                                            onClick={() => handleSetPlan(u.id, 'pro')}
                                                            disabled={u.plan === 'pro'}
                                                        >
                                                            → Pro
                                                        </button>
                                                        <button 
                                                            className="btn btn-ghost" 
                                                            style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                                                            onClick={() => handleSetPlan(u.id, 'elite')}
                                                            disabled={u.plan === 'elite'}
                                                        >
                                                            → Elite
                                                        </button>
                                                        <button 
                                                            className="btn btn-danger" 
                                                            style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                                                            onClick={() => handleDeleteUser(u.id, u.email)}
                                                            disabled={u.is_admin}
                                                        >
                                                            Delete
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Admin Controls */}
                        <div className="admin-section">
                            <div className="admin-section-header">Global Administrative Operations</div>
                            <div style={{ padding: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                                <button className="btn btn-dark" onClick={handleResetAllBooks}>
                                    Reset all user book counts
                                </button>
                                <button className="btn btn-outline" onClick={handleExportData}>
                                    Export users data (JSON)
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
