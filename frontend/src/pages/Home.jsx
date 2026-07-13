import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Home({ onNavigate }) {
    const { user } = useAuth();

    return (
        <div className="page active" id="home-page">
            <div className="inkwell-hero">
                <div className="inkwell-badge">
                    <svg viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    Claude-powered generation
                </div>
                <h1>Write books with <span className="accent">precision</span> & clarity</h1>
                <p className="subhead">From outline to illustrated chapters — a complete book in minutes. No emoji, just professional prose and structured narrative.</p>
                
                <div className="hero-cta">
                    {user ? (
                        <button className="btn btn-dark" style={{ padding: '12px 32px', fontSize: '1rem' }} onClick={() => onNavigate('dashboard')}>
                            Go to Dashboard
                        </button>
                    ) : (
                        <>
                            <button className="btn btn-dark" style={{ padding: '12px 32px', fontSize: '1rem' }} onClick={() => onNavigate('signup')}>
                                Start writing
                            </button>
                            <button className="btn btn-ghost" style={{ padding: '12px 28px', fontSize: '1rem' }} onClick={() => onNavigate('pricing')}>
                                View plans
                            </button>
                        </>
                    )}
                </div>

                <div className="hero-stats">
                    <div className="stat-item">
                        <span className="stat-text"><strong>12k+</strong> books generated</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-text"><strong>4.8★</strong> writer rating</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-text"><strong>3 min</strong> avg completion</span>
                    </div>
                </div>
            </div>

            <div className="inkwell-features">
                <div className="features-grid">
                    <div className="feature-item">
                        <div className="feature-icon-svg">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
                                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
                            </svg>
                        </div>
                        <div className="feature-text">
                            <h3>Structured chapters</h3>
                            <p>Consistent narrative voice, multi‑chapter outlines, and flowing prose — all generated from a single prompt.</p>
                        </div>
                    </div>
                    <div className="feature-item">
                        <div className="feature-icon-svg">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 16v-4M12 8h.01"/>
                            </svg>
                        </div>
                        <div className="feature-text">
                            <h3>Contextual illustrations</h3>
                            <p>Each chapter receives a detailed image description, ready for AI image tools — no emoji, only descriptive prompts.</p>
                        </div>
                    </div>
                    <div className="feature-item">
                        <div className="feature-icon-svg">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
                                <polyline points="13 2 13 9 20 9"/>
                            </svg>
                        </div>
                        <div className="feature-text">
                            <h3>Upload reference files</h3>
                            <p>Attach documents or style guides — the AI builds upon your existing material for truly custom output.</p>
                        </div>
                    </div>
                    <div className="feature-item">
                        <div className="feature-icon-svg">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M2 12h20M12 2v20"/>
                            </svg>
                        </div>
                        <div className="feature-text">
                            <h3>Full revision history</h3>
                            <p>Every book is automatically saved. Revisit, edit, or continue any project from where you left off.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="inkwell-showcase">
                <div className="showcase-header">
                    <h2>Recently generated</h2>
                    <p>Stories crafted by writers like you</p>
                </div>
                <div className="showcase-grid">
                    <div className="showcase-card">
                        <div className="card-meta"><span>Victorian mystery</span><span>3 chapters</span></div>
                        <div className="card-title">The Lambeth Fog</div>
                        <div className="card-desc">A detective's hunt for a vanished heiress weaves through London's darkest alleys, with a twist that echoes through generations.</div>
                        <div className="card-tags"><span className="tag2">suspense</span><span class="tag2">historical</span></div>
                    </div>
                    <div className="showcase-card">
                        <div className="card-meta"><span>Hard sci‑fi</span><span>5 chapters</span></div>
                        <div className="card-title">Aurora Rising</div>
                        <div className="card-desc">First contact near Jupiter’s orbit unravels a conspiracy that could redefine humanity’s place in the cosmos.</div>
                        <div className="card-tags"><span className="tag2">space</span><span class="tag2">thriller</span></div>
                    </div>
                    <div className="showcase-card">
                        <div className="card-meta"><span>Literary fiction</span><span>4 chapters</span></div>
                        <div className="card-title">The Architect's Silence</div>
                        <div className="card-desc">An aging architect reflects on love, ambition, and the one building he never designed — his own life.</div>
                        <div className="card-tags"><span className="tag2">drama</span><span class="tag2">character study</span></div>
                    </div>
                </div>
            </div>

            <div className="inkwell-cta-bar">
                <div className="cta-content">
                    <h3>Turn your idea into a book</h3>
                    <p>No fluff, no emoji — just clean, intelligent prose. Start with a free account.</p>
                    <button className="btn btn-dark" style={{ background: '#fff', color: '#0d0d0d' }} onClick={() => onNavigate(user ? 'dashboard' : 'signup')}>
                        Create free account
                    </button>
                </div>
            </div>
        </div>
    );
}
