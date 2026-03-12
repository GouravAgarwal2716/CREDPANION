'use client';
import { useState, useRef, useCallback } from 'react';

const TABS = [
    { id: 'summary', label: '📊 Executive Summary' },
    { id: 'graph', label: '🕸 Forensic Graph' },
    { id: 'reality', label: '🏭 Operational Reality' },
    { id: 'explain', label: '🧠 Explainability' },
    { id: 'whatif', label: '🔮 What-If' },
    { id: 'report', label: '📄 CAM Report' },
];

const DEMO_INFO = {
    CleanCorp: { badge: 'approve', label: '✅ Low Risk → APPROVE', desc: 'Healthy borrower — clean records, active factory.' },
    FraudCo: { badge: 'reject', label: '🚨 High Risk → REJECT', desc: 'Carousel fraud + inflated revenue + idle plant.' },
    LitigationLtd: { badge: 'reject', label: '⚖️ Medium Risk → REJECT', desc: 'Legal disputes — S.138 cases + labour conflict.' },
    CustomCase: { badge: 'analyze', label: '📄 Custom Analysis', desc: 'AI analyzing user-uploaded documents.' },
};

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function runAnalysis(company) {
    const form = new FormData();
    form.append('company', company);
    const r = await fetch(`${API}/analyze`, { method: 'POST', body: form, signal: AbortSignal.timeout(120000) });
    if (!r.ok) throw new Error(`API ${r.status}`);
    return r.json();
}

function getFraudNodes(transactions) {
    const adj = {};
    transactions.forEach(({ sender, receiver }) => {
        (adj[sender] = adj[sender] || []).push(receiver);
    });
    const visited = new Set(), inStack = new Set(), fraud = new Set();
    function dfs(n, path) {
        if (inStack.has(n)) { path.forEach(x => fraud.add(x)); return; }
        if (visited.has(n)) return;
        visited.add(n); inStack.add(n);
        (adj[n] || []).forEach(nb => dfs(nb, [...path, n]));
        inStack.delete(n);
    }
    Object.keys(adj).forEach(n => dfs(n, [n]));
    return [...fraud];
}

// ── Lazy-loaded tab components (avoid SSR issues with vis-network/recharts)
import dynamic from 'next/dynamic';
const ExecutiveSummary = dynamic(() => import('./ExecutiveSummary'), { ssr: false });
const ForensicGraph = dynamic(() => import('./ForensicGraph'), { ssr: false });
const OperationalReality = dynamic(() => import('./OperationalReality'), { ssr: false });
const Explainability = dynamic(() => import('./Explainability'), { ssr: false });
const WhatIfSimulator = dynamic(() => import('./WhatIfSimulator'), { ssr: false });
const CamReport = dynamic(() => import('./CamReport'), { ssr: false });
const AiCopilot = dynamic(() => import('./AiCopilot'), { ssr: false });


export default function Dashboard() {
    const [tab, setTab] = useState('summary');
    const [company, setCompany] = useState('CleanCorp');
    const [customName, setCustomName] = useState('Custom Company');
    const [files, setFiles] = useState({ gst: [], bank: [], photos: [] });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [trail, setTrail] = useState([]);
    const trailRef = useRef(null);

    const addLine = useCallback((line) => {
        setTrail(p => [...p, line]);
        setTimeout(() => { if (trailRef.current) trailRef.current.scrollTop = trailRef.current.scrollHeight; }, 50);
    }, []);

    const handleFileChange = useCallback((key, fileList) => {
        if (fileList && fileList.length > 0) {
            setFiles(prev => ({ ...prev, [key]: Array.from(fileList) }));
            setCompany('CustomCase'); // Automatically switch to Custom Case
        }
    }, []);

    const handleRun = async () => {
        setLoading(true); setResult(null); setTrail([]);

        const isCustom = company === 'CustomCase';
        const runCompany = isCustom ? customName || 'Custom Company' : company;

        try {
            if (isCustom) {
                addLine(`📤 Uploading custom documents...`);
                const upForm = new FormData();
                files.gst.forEach(f => upForm.append('gst_files', f));
                files.bank.forEach(f => upForm.append('bank_files', f));
                files.photos.forEach(f => upForm.append('photo_files', f));
                const upRes = await fetch(`${API}/upload`, { method: 'POST', body: upForm });
                if (!upRes.ok) throw new Error('Failed to upload files');
                addLine(`✅ Files uploaded successfully.`);
            } else {
                // If demo case, push empty form to clear backend upload cache
                await fetch(`${API}/upload`, { method: 'POST', body: new FormData() });
            }

            addLine(`🔄 Starting analysis for ${runCompany}...`);
            const data = await runAnalysis(runCompany);
            const lines = data.audit_trail || [];
            lines.forEach((l, i) => setTimeout(() => addLine(l), i * 55));
            setTimeout(() => {
                setResult(data);
                const dec = data.risk_results?.decision;
                addLine(`${dec === 'APPROVE' ? '✅' : '❌'} Committee: Final vote → ${dec}`);
                setLoading(false);
            }, lines.length * 55 + 300);
        } catch (e) {
            addLine(`❌ Error: ${e.message}`);
            setLoading(false);
        }
    };

    const info = DEMO_INFO[company] || {};
    const txns = result?.transactions || [];
    const fraud = txns.length ? getFraudNodes(txns) : [];
    const rr = result?.risk_results || {};

    return (
        <div className="app-shell">
            {/* ══ SIDEBAR ══ */}
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <div className="sidebar-logo-icon">🏦</div>
                    <div>
                        <h2>Credpanion</h2>
                        <span>Agentic Credit Intelligence</span>
                    </div>
                </div>

                <div className="sidebar-section">
                    <div className="sidebar-section-title">📂 Upload Documents</div>
                    {[['📄', 'GST Returns (PDF)', '.pdf', 'gst'], ['🏦', 'Bank Statements (PDF)', '.pdf', 'bank'], ['📷', 'Factory Photos', 'image/*', 'photos']].map(([e, l, a, key]) => (
                        <div className="upload-zone" key={l}>
                            <label>
                                {e} <span style={{ flex: 1, color: files[key]?.length ? 'var(--blue)' : 'inherit' }}>
                                    {files[key]?.length ? `${files[key].length} file(s) attached` : l}
                                </span>
                                <input type="file" accept={a} multiple onChange={(ev) => handleFileChange(key, ev.target.files)} />
                            </label>
                        </div>
                    ))}
                </div>

                <div className="sidebar-section">
                    <div className="sidebar-section-title">🎯 Analysis Case</div>
                    <select className="demo-select" value={company}
                        onChange={ev => { setCompany(ev.target.value); setResult(null); setTrail([]); }}>
                        <option>CleanCorp</option>
                        <option>FraudCo</option>
                        <option>LitigationLtd</option>
                        <option value="CustomCase">Custom Upload</option>
                    </select>
                    {company === 'CustomCase' && (
                        <input
                            type="text"
                            value={customName}
                            onChange={(e) => setCustomName(e.target.value)}
                            placeholder="Enter Company Name"
                            style={{ width: '100%', marginTop: '8px', padding: '6px 8px', background: '#0d1117', color: 'white', border: '1px solid var(--border)', borderRadius: '4px', fontSize: '0.8rem' }}
                        />
                    )}
                    <div style={{ marginTop: 6 }}>
                        <span className={`demo-badge badge-${info.badge}`}>{info.label}</span>
                    </div>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.5 }}>{info.desc}</p>
                </div>

                <div className="sidebar-section">
                    <button className={`run-btn${loading ? ' loading' : ''}`} onClick={handleRun} disabled={loading}>
                        {loading ? '⏳ Analysing...' : '🚀 Run Committee Analysis'}
                    </button>
                </div>

                <div className="sidebar-section">
                    <div className="sidebar-section-title">📡 Live Agent Transcript</div>
                </div>
                <div className="audit-trail" ref={trailRef}>
                    {trail.length === 0
                        ? <div className="audit-line" style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Awaiting pipeline...</div>
                        : trail.map((line, i) => (
                            <div key={i} className={`audit-line${line.includes('⚠') || line.includes('⛔') ? ' warn' : line.includes('✅') || line.includes('APPROVE') ? ' ok' : line.includes('❌') || line.includes('REJECT') || line.includes('Hard block') ? ' err' : ''}`}>
                                {line}
                            </div>
                        ))
                    }
                </div>
            </aside>

            {/* ══ MAIN ══ */}
            <div className="main-content">
                <header className="header">
                    <span className="header-title">Credpanion Credit Intelligence</span>
                    <span className="header-sub">— Agentic Multi-Agent Credit Committee</span>
                    <div className="header-pills">
                        {result && (<>
                            <span className="pill" style={{ background: rr.decision === 'APPROVE' ? 'var(--green-bg)' : 'var(--red-bg)', color: rr.decision === 'APPROVE' ? 'var(--green)' : 'var(--red)', border: `1px solid ${rr.decision === 'APPROVE' ? 'var(--green-border)' : 'var(--red-border)'}` }}>{rr.decision}</span>
                            <span className="pill" style={{ background: 'var(--amber-bg)', color: 'var(--amber)', border: '1px solid rgba(255,166,87,0.4)' }}>Score: {rr.total_score}/100</span>
                            <span className="pill" style={{ background: 'rgba(88,166,255,0.1)', color: 'var(--blue)', border: '1px solid var(--blue-glow)' }}>{result.company_name}</span>
                        </>)}
                    </div>
                </header>

                <nav className="tab-bar">
                    {TABS.map(t => (
                        <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
                            {t.label}
                        </button>
                    ))}
                </nav>

                <main className="tab-content">
                    {loading && (
                        <div className="spinner-row">
                            <div className="spinner" />
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Running 8-agent credit pipeline...</span>
                        </div>
                    )}

                    {!result && !loading && (
                        <div className="landing">
                            <div>
                                <div style={{ fontSize: '3.5rem', marginBottom: '0.5rem' }}>⚡</div>
                                <h2 style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--blue)' }}>Credpanion Credit Intelligence</h2>
                                <p style={{ color: 'var(--text-secondary)', marginTop: '0.6rem', fontSize: '0.95rem' }}>
                                    Select a demo case and click <strong>Run Committee Analysis</strong> to start the 8-agent pipeline.
                                </p>
                            </div>
                            <div className="landing-cards">
                                {[['🔍', '8 AI Agents', 'Extractor → CAM'], ['📊', 'Fraud Detection', 'Carousel + Inflation'], ['🏛️', 'Credit Committee', 'Weighted Voting'], ['🔮', 'Counterfactuals', 'What-If Explorer'], ['📄', 'CAM Report', 'Downloadable .docx']].map(([icon, title, sub]) => (
                                    <div className="landing-card" key={title}>
                                        <div style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>{icon}</div>
                                        <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{title}</div>
                                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: 2 }}>{sub}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {result && tab === 'summary' && <ExecutiveSummary result={result} />}
                    {result && tab === 'graph' && <ForensicGraph transactions={txns} fraudNodes={fraud} />}
                    {result && tab === 'reality' && <OperationalReality visionResults={result.vision_results || []} realityScore={result.reality_score || 0} />}
                    {result && tab === 'explain' && <Explainability result={result} />}
                    {result && tab === 'whatif' && <WhatIfSimulator counterfactuals={result.counterfactual_analysis || []} currentScore={rr.total_score || 0} />}
                    {result && tab === 'report' && <CamReport result={result} />}
                </main>
            </div>

            {/* Global AI Copilot */}
            <AiCopilot />
        </div>
    );
}
