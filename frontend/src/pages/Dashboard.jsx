import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Dashboard({ onNavigate }) {
    const { user, logout, apiCall, updateProfileCache } = useAuth();
    
    const [books, setBooks] = useState([]);
    const [selectedBook, setSelectedBook] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [attachedFiles, setAttachedFiles] = useState([]);
    
    const [loadingHistory, setLoadingHistory] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const fileInputRef = useRef(null);
    const imageInputRef = useRef(null);
    const promptRef = useRef(null);
    const messagesEndRef = useRef(null);

    // Fetch book history
    const fetchHistory = async () => {
        try {
            const data = await apiCall('GET', '/books');
            setBooks(data.books);
        } catch (e) {
            console.error('Error fetching book history:', e);
        } finally {
            setLoadingHistory(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    // Scroll chat area
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [selectedBook, generating]);

    const selectBook = async (bookId) => {
        try {
            const data = await apiCall('GET', `/books/${bookId}`);
            setSelectedBook(data);
            setSidebarOpen(false);
        } catch (e) {
            alert('Failed to load book: ' + e.message);
        }
    };

    const deleteBook = async (bookId, e) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this book?')) return;
        try {
            await apiCall('DELETE', `/books/${bookId}`);
            if (selectedBook && selectedBook.id === bookId) {
                setSelectedBook(null);
            }
            fetchHistory();
            // Refresh user cache since books_used decremented
            const userMe = await apiCall('GET', '/auth/me');
            updateProfileCache(userMe);
        } catch (e) {
            alert('Failed to delete book: ' + e.message);
        }
    };

    const handleFileUpload = async (e, type) => {
        const file = e.target.files[0];
        if (!file) return;

        const maxBytes = 20 * 1024 * 1024;
        if (file.size > maxBytes) {
            alert('File too large. Maximum is 20 MB.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        setUploading(true);
        try {
            // We use direct fetch because of multipart/form-data
            const token = localStorage.getItem('inkwell_token');
            const res = await fetch('http://localhost:8000/api/files/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Upload failed');
            
            setAttachedFiles(prev => [...prev, data]);
        } catch (e) {
            alert('Upload failed: ' + e.message);
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const removeAttachedFile = async (fileId, idx) => {
        try {
            await apiCall('DELETE', `/files/${fileId}`);
            setAttachedFiles(prev => prev.filter((_, i) => i !== idx));
        } catch (e) {
            alert('Failed to delete file: ' + e.message);
        }
    };

    const generateBook = async () => {
        if (!prompt.trim() || generating) return;

        const limit = user.plan === 'free' ? 4 : user.plan === 'pro' ? 10 : Infinity;
        if (user.books_used >= limit) {
            alert(`You've reached your ${limit}-book limit on the ${user.plan} plan. Please upgrade to continue.`);
            onNavigate('pricing');
            return;
        }

        setGenerating(true);
        setSelectedBook({
            prompt: prompt,
            title: 'Generating book...',
            synopsis: 'Claude is writing your narrative prose, structuring chapters, and outlining illustrations...',
            chapters: [],
            isPlaceholder: true
        });
        
        try {
            const data = await apiCall('POST', '/books/generate', { prompt });
            setSelectedBook(data);
            fetchHistory();
            
            // Refresh user stats
            const userMe = await apiCall('GET', '/auth/me');
            updateProfileCache(userMe);
            setPrompt('');
            setAttachedFiles([]);
        } catch (e) {
            alert('Book generation failed: ' + e.message);
            setSelectedBook(null);
        } finally {
            setGenerating(false);
        }
    };

    const newChat = () => {
        setSelectedBook(null);
        setAttachedFiles([]);
        setPrompt('');
    };

    const copyBookToClipboard = (book) => {
        if (!book) return;
        let text = `${book.title}\n\nSynopsis:\n${book.synopsis}\n\n`;
        book.chapters.forEach(ch => {
            text += `Chapter ${ch.chapter_number}: ${ch.title}\n\nContent:\n${ch.content}\n\nIllustration Prompt:\n${ch.image_description}\n\n`;
        });
        navigator.clipboard.writeText(text).then(() => {
            alert('Book text copied to clipboard!');
        });
    };

    const fillPrompt = (txt) => {
        setPrompt(txt);
        if (promptRef.current) {
            promptRef.current.focus();
        }
    };

    const autoResize = (e) => {
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            generateBook();
        }
    };

    const escHtml = (str) => {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    };

    return (
        <div className="page active" id="dashboard-page" style={{ display: 'flex' }}>
            {/* Sidebar toggle button (Mobile) */}
            <button className="sidebar-toggle" id="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
                ☰
            </button>

            {/* Sidebar Overlay (Mobile) */}
            {sidebarOpen && (
                <div className="sidebar-overlay open" onClick={() => setSidebarOpen(false)}></div>
            )}

            {/* Sidebar */}
            <div className={`sidebar ${sidebarOpen ? 'mobile-open' : ''}`}>
                <div className="sidebar-top">
                    <div className="user-info">
                        <div className="avatar">{(user?.name || 'U').charAt(0).toUpperCase()}</div>
                        <div>
                            <div className="user-name">{user?.name}</div>
                            <div className="user-plan">
                                <span className={`plan-badge ${user?.plan}`}>{user?.plan}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="sidebar-new-chat">
                    <button className="new-chat-btn" onClick={newChat}>
                        <span>✦</span> New Book
                    </button>
                </div>

                <div className="sidebar-nav">
                    <div className="sidebar-section">Recent Books</div>
                    <div id="history-items">
                        {loadingHistory ? (
                            <div className="history-empty">Loading history...</div>
                        ) : books.length === 0 ? (
                            <div className="history-empty">No books yet</div>
                        ) : (
                            books.map(b => (
                                <div 
                                    key={b.id} 
                                    className={`chat-item ${selectedBook?.id === b.id ? 'active' : ''}`}
                                    onClick={() => selectBook(b.id)}
                                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                >
                                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        📖 {b.title}
                                    </span>
                                    <button 
                                        onClick={(e) => deleteBook(b.id, e)} 
                                        style={{ background: 'none', color: '#888', border: 'none', cursor: 'pointer', padding: '2px' }}
                                        title="Delete Book"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="sidebar-bottom">
                    <button className="sidebar-action" onClick={() => onNavigate('profile')}>⚙ Profile & Settings</button>
                    <button className="sidebar-action" onClick={() => onNavigate('pricing')}>💎 Upgrade Plan</button>
                    <button className="sidebar-action" onClick={logout}>→ Log out</button>
                </div>
            </div>

            {/* Main content area */}
            <div className="main-content">
                <div className="chat-area" id="chat-area">
                    {!selectedBook ? (
                        <div className="welcome-center" id="welcome-screen">
                            <div style={{ fontSize: '2.5rem' }}>Readable</div>
                            <h2>What book shall we write?</h2>
                            <p>Describe your idea — genre, characters, setting — and Claude will generate a structured multi-chapter illustrated outline.</p>
                            <div className="suggestion-chips">
                                <div className="chip" onClick={() => fillPrompt('A mystery novel set in Victorian London with a detective and a stolen diamond')}>🔍 Mystery Novel</div>
                                <div className="chip" onClick={() => fillPrompt("A children's picture book about a brave little cloud who wants to make rain")}>☁️ Children's Book</div>
                                <div className="chip" onClick={() => fillPrompt("A sci-fi epic about humanity's first contact with an alien civilization in 2150")}>🚀 Sci-Fi Epic</div>
                                <div className="chip" onClick={() => fillPrompt('A fantasy adventure with dragons, a reluctant hero, and an ancient prophecy')}>🐉 Fantasy Adventure</div>
                            </div>
                        </div>
                    ) : (
                        <div className="messages-wrapper">
                            {/* User input prompt bubble */}
                            <div className="user-msg">
                                <div className="user-bubble">{selectedBook.prompt}</div>
                            </div>

                            {/* Book card */}
                            <div className="book-card" id={selectedBook.id || 'temp-book'}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                                    <div>
                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--gold)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                            ✦ Generated Book Outline
                                        </div>
                                        <div className="book-title">{selectedBook.title}</div>
                                        <div style={{ fontSize: '0.9rem', color: 'var(--ink3)', lineHeight: 1.6, marginTop: '0.4rem' }}>
                                            {selectedBook.synopsis}
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="divider"></div>

                                {selectedBook.chapters.length === 0 && generating && (
                                    <div className="typing-indicator">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <span style={{ fontSize: '0.85rem', marginLeft: '8px' }}>Claude is thinking...</span>
                                    </div>
                                )}

                                {selectedBook.chapters.map(ch => (
                                    <div key={ch.id || ch.chapter_number} className="book-chapter">
                                        <h4>Chapter {ch.chapter_number}: {ch.title}</h4>
                                        
                                        {ch.image_description && (
                                            <div className="book-image-placeholder">
                                                <span style={{ fontSize: '1.5rem' }}>🎨</span>
                                                <span>{ch.image_description}</span>
                                                <span style={{ fontSize: '0.75rem', color: 'var(--ink4)' }}>(Illustrations can be generated using this visual description)</span>
                                            </div>
                                        )}
                                        
                                        <p dangerouslySetInnerHTML={{ __html: escHtml(ch.content).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') }}></p>
                                    </div>
                                ))}

                                {!selectedBook.isPlaceholder && (
                                    <div className="book-actions">
                                        <button className="btn btn-outline" onClick={() => copyBookToClipboard(selectedBook)}>📋 Copy text</button>
                                        <button className="btn btn-ghost" onClick={newChat}>✦ New book</button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Usage limit indicator */}
                {user && user.plan !== 'elite' && (
                    <div id="books-used-bar" style={{ padding: '6px 1.5rem', backgroundColor: 'var(--gold3)', textAlign: 'center', fontSize: '0.82rem', color: '#7a5c10', borderTop: '1px solid var(--gold2)' }}>
                        📚 {user.books_used}/{user.plan === 'free' ? 4 : 10} books used on {user.plan} plan. {user.books_used >= (user.plan === 'free' ? 4 : 10) ? 'Upgrade to generate more!' : ''}
                    </div>
                )}

                {/* Uploaded files attachment list */}
                {attachedFiles.length > 0 && (
                    <div className="uploaded-files">
                        {attachedFiles.map((file, idx) => (
                            <div key={file.id} className="file-chip">
                                {file.file_type === 'image' ? '🖼' : '📄'} {file.filename}
                                <button onClick={() => removeAttachedFile(file.id, idx)}>✕</button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Input Prompt bar */}
                <div className="prompt-bar">
                    <div className="prompt-inner">
                        <textarea 
                            ref={promptRef}
                            className="prompt-textarea" 
                            placeholder="Describe your book idea... (e.g. Victorian mystery novel, character names, tone)" 
                            rows="2" 
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onInput={autoResize}
                            disabled={generating}
                        ></textarea>
                        
                        <div className="prompt-actions">
                            <div className="prompt-left">
                                <button className="upload-btn" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                                    {uploading ? 'Uploading...' : '📎 Attach document'}
                                </button>
                                <button className="upload-btn" onClick={() => imageInputRef.current?.click()} disabled={uploading}>
                                    📎 Attach image
                                </button>
                                <input 
                                    type="file" 
                                    ref={fileInputRef} 
                                    style={{ display: 'none' }}
                                    onChange={(e) => handleFileUpload(e, 'file')} 
                                    accept=".pdf,.txt,.md,.docx"
                                />
                                <input 
                                    type="file" 
                                    ref={imageInputRef} 
                                    style={{ display: 'none' }}
                                    onChange={(e) => handleFileUpload(e, 'image')}
                                    accept="image/*"
                                />
                            </div>
                            <button 
                                className="send-btn" 
                                onClick={generateBook} 
                                disabled={!prompt.trim() || generating || uploading}
                            >
                                {generating ? 'Generating...' : 'Generate ✦'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div ref={messagesEndRef} />
        </div>
    );
}
