'use client';
import RiskGauge from './RiskGauge';

const AGENT_ICONS = { Auditor: '📊', Sleuth: '⚖️', Vision: '📷', Adversarial: '🔥' };

export default function ExecutiveSummary({ result }) {
    if (!result) return null;
    const rr = result.risk_results || {};
    const score = rr.total_score || 0;
    const category = rr.category || 'N/A';
    const decision = rr.decision || 'N/A';
    const votes = result.committee_votes || [];
    const forensic = result.forensic_report || [];
    const gst = result.gst_sales || 0;
    const bank = result.bank_credits || 0;
    const reality = result.reality_score || 0;
    const legal = result.legal_flags || [];
    const fmt = n => n >= 1e6 ? `₹${(n / 1e6).toFixed(1)}M` : `₹${n.toLocaleString('en-IN')}`;
    const CAT_COLOR = { Low: '#3fb950', Medium: '#ffa657', High: '#f85149' };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.6rem' }}>
            {/* ── Top row ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '1.4rem' }}>
                {/* Gauge */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="card-title">Risk Score</div>
                    <RiskGauge score={score} category={category} />
                </div>
                {/* Metrics */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div className={`decision-banner ${decision === 'APPROVE' ? 'decision-approve' : 'decision-reject'}`}>
                        <div className="decision-icon">{decision === 'APPROVE' ? '✅' : '❌'}</div>
                        <div>
                            <div className="decision-label" style={{ color: decision === 'APPROVE' ? 'var(--green)' : 'var(--red)' }}>{decision}</div>
                            <div className="decision-sub">
                                {decision === 'APPROVE' ? 'Committee recommends approval' : 'Committee recommends rejection'}&nbsp;·&nbsp;
                                Weighted: {(result.committee_weighted_score || 0).toFixed(4)}
                            </div>
                        </div>
                    </div>
                    <div className="grid-4">
                        {[
                            { label: 'GST Sales', v: fmt(gst), c: 'var(--blue)' },
                            { label: 'Bank Credits', v: fmt(bank), c: 'var(--blue)' },
                            { label: 'Reality Score', v: `${Math.round(reality * 100)}%`, c: reality >= 0.5 ? 'var(--green)' : 'var(--red)' },
                            { label: 'Legal Flags', v: legal.length, c: legal.length === 0 ? 'var(--green)' : 'var(--red)' },
                        ].map(({ label, v, c }) => (
                            <div className="metric-tile" key={label}>
                                <div className="metric-label">{label}</div>
                                <div className="metric-value" style={{ color: c }}>{v}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Committee Votes ── */}
            <div className="card">
                <div className="card-title">🏛 Credit Committee Votes</div>
                {votes.length > 0 ? (
                    <div className="vote-grid">
                        {votes.map(v => (
                            <div key={v.agent} className={`vote-card ${v.vote === 'APPROVE' ? 'approve' : 'reject'}`}>
                                <div className="vote-icon">{AGENT_ICONS[v.agent] || '🤖'}</div>
                                <div className="vote-agent">{v.agent}</div>
                                <div className="vote-verdict" style={{ color: v.vote === 'APPROVE' ? 'var(--green)' : 'var(--red)' }}>{v.vote}</div>
                                <div className="vote-score">score: {v.score.toFixed(2)}</div>
                                <div className="vote-rat">{v.rationale}</div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Hard block — committee bypassed. Routed directly to Risk Engine.</p>
                )}
            </div>

            {/* ── Forensic Flags ── */}
            {forensic.length > 0 && (
                <div className="card">
                    <div className="card-title" style={{ color: 'var(--red)' }}>🚨 Forensic Red Flags</div>
                    <div className="flag-list">
                        {forensic.map((f, i) => (
                            <div key={i} className="flag-item"><span style={{ color: 'var(--red)' }}>⚠</span><span>{f}</span></div>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Penalties ── */}
            {Object.keys(rr.penalties || {}).length > 0 && (
                <div className="card">
                    <div className="card-title">⚡ Penalty Breakdown</div>
                    <table className="data-table">
                        <thead><tr><th>Factor</th><th>Points</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>Base Score</td>
                                <td><span className="delta-chip" style={{ background: 'rgba(88,166,255,0.1)', color: 'var(--blue)', borderColor: 'var(--blue-glow)' }}>+{rr.base_score || 40}</span></td>
                            </tr>
                            {Object.entries(rr.penalties || {}).map(([k, v]) => (
                                <tr key={k}>
                                    <td>{k}</td>
                                    <td><span className="delta-chip" style={{ background: 'var(--red-bg)', color: 'var(--red)', borderColor: 'var(--red-border)' }}>+{v}</span></td>
                                </tr>
                            ))}
                            <tr style={{ fontWeight: 700 }}>
                                <td>Total Score</td>
                                <td style={{ color: CAT_COLOR[category] || 'var(--amber)' }}>{score}/100 — {category} Risk</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
