'use client';
import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, X, MessageSquareText } from 'lucide-react';
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AiCopilot() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'ai', content: "Hello. I am the Credpanion AI Copilot. I'm actively monitoring this loan application. What would you like to know?" }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const endOfMessagesRef = useRef(null);

    // Auto-scroll on new message
    useEffect(() => {
        endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        // Add a temporary empty AI message that we will stream text into
        setMessages(prev => [...prev, { role: 'ai', content: '' }]);

        try {
            const response = await fetch(`${API}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMsg })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to connect to Copilot');
            }

            // Stream reading
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value, { stream: true });

                if (chunkValue) {
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        const last = newMsgs[newMsgs.length - 1];
                        if (last.role === 'ai') last.content += chunkValue;
                        return newMsgs;
                    });
                }
            }
        } catch (error) {
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs[newMsgs.length - 1].content = `⚠️ Error: ${error.message}. Ensure you have run an application analysis first.`;
                return newMsgs;
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 100 }}>
            {/* The Chat Window */}
            {isOpen && (
                <div style={{
                    position: 'absolute', bottom: '100%', right: '0',
                    width: '380px', height: '520px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-lg)',
                    boxShadow: '0 12px 30px rgba(0,0,0,0.5)',
                    display: 'flex', flexDirection: 'column',
                    marginBottom: '1rem',
                    overflow: 'hidden'
                }}>
                    {/* Header */}
                    <div style={{ padding: '1.2rem', background: 'var(--bg-base)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                            <div style={{ background: 'rgba(37,99,235,0.2)', color: 'var(--blue)', padding: '0.4rem', borderRadius: '50%' }}>
                                <Bot size={20} />
                            </div>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-primary)' }}>AI Co-Pilot</h3>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Real-time case intelligence</div>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                            <X size={20} />
                        </button>
                    </div>

                    {/* Chat Area */}
                    <div style={{ flex: 1, padding: '1.2rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {messages.map((m, i) => (
                            <div key={i} style={{
                                display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
                                flexDirection: m.role === 'user' ? 'row-reverse' : 'row'
                            }}>
                                <div style={{
                                    background: m.role === 'user' ? 'var(--blue)' : 'var(--bg-base)',
                                    color: m.role === 'user' ? '#fff' : 'var(--blue)',
                                    padding: '0.4rem', borderRadius: '50%', flexShrink: 0
                                }}>
                                    {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>
                                <div style={{
                                    background: m.role === 'user' ? 'var(--blue)' : 'var(--bg-base)',
                                    color: m.role === 'user' ? '#fff' : 'var(--text-primary)',
                                    padding: '0.8rem 1rem', borderRadius: 'var(--radius-md)',
                                    fontSize: '0.84rem', lineHeight: '1.5',
                                    border: m.role === 'ai' ? '1px solid var(--border)' : 'none',
                                    whiteSpace: 'pre-wrap'
                                }}>
                                    {m.content}
                                </div>
                            </div>
                        ))}
                        <div ref={endOfMessagesRef} />
                    </div>

                    {/* Input */}
                    <form onSubmit={handleSubmit} style={{ padding: '1rem', borderTop: '1px solid var(--border)', background: 'var(--bg-base)', display: 'flex', gap: '0.5rem' }}>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about this loan case..."
                            disabled={isLoading}
                            style={{
                                flex: 1, padding: '0.8rem', borderRadius: 'var(--radius-md)',
                                border: '1px solid var(--border)', background: 'var(--bg-app)',
                                color: 'var(--text-primary)', outline: 'none', fontSize: '0.85rem'
                            }}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            style={{
                                background: 'var(--blue)', color: '#fff', border: 'none',
                                borderRadius: 'var(--radius-md)', padding: '0 1rem',
                                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                opacity: (isLoading || !input.trim()) ? 0.5 : 1
                            }}
                        >
                            <Send size={18} />
                        </button>
                    </form>
                </div>
            )}

            {/* Floating FAB Toggle */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    background: 'var(--blue)', color: '#fff', border: 'none',
                    width: '60px', height: '60px', borderRadius: '50%',
                    boxShadow: '0 8px 20px rgba(37,99,235,0.4)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'transform 0.2s',
                    transform: isOpen ? 'scale(0.9)' : 'scale(1)'
                }}
            >
                {isOpen ? <X size={24} /> : <MessageSquareText size={24} />}
            </button>
        </div>
    );
}
