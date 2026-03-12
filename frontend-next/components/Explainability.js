'use client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine, LabelList } from 'recharts';

const FACTOR_COLORS = {
    'Base Score': '#388bfd', 'Circular Trading': '#f85149', 'Section 138 NI Act': '#f85149',
    'Revenue Inflation': '#f85149', 'Low Reality Score': '#ffa657', 'Promoter Contagion': '#f85149',
};
const AGENT_COLORS = { APPROVE: '#3fb950', REJECT: '#f85149' };

const Tip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0];
    return <div style={{ background: '#1c2128', border: '1px solid #30363d', borderRadius: 8, padding: '8px 12px', fontSize: '.8rem' }}>
        <div style={{ fontWeight: 600, color: '#e6edf3' }}>{d.name}</div>
        <div style={{ color: d.fill }}>+{d.value} pts</div>
    </div>;
};

export default function Explainability({ result }) {
    if (!result) return null;
    const rr = result.risk_results || {};
    const votes = result.committee_votes || [];
    const wt = result.committee_weighted_score || 0;

    const shapData = [
        { name: 'Base Score', value: rr.base_score || 40 },
        ...Object.entries(rr.penalties || {}).map(([k, v]) => ({ name: k, value: v })),
    ];
    const voteData = votes.map(v => ({ name: v.agent, score: v.score, vote: v.vote }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
            <div className="card">
                <div className="card-title">🧠 Risk Factor Contributions (SHAP-Style)</div>
                <p style={{ fontSize: '.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Each bar shows points added to base score of 40.
                </p>
                <ResponsiveContainer width="100%" height={Math.max(180, shapData.length * 54)}>
                    <BarChart data={shapData} layout="vertical" margin={{ top: 0, right: 60, bottom: 0, left: 165 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#30363d" horizontal={false} />
                        <XAxis type="number" tick={{ fill: '#8b949e', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis type="category" dataKey="name" tick={{ fill: '#e6edf3', fontSize: 12 }} axisLine={false} tickLine={false} width={160} />
                        <Tooltip content={<Tip />} cursor={{ fill: 'rgba(88,166,255,.06)' }} />
                        <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                            <LabelList dataKey="value" position="right" formatter={v => `+${v}`} style={{ fill: '#e6edf3', fontSize: 12, fontWeight: 600 }} />
                            {shapData.map(d => <Cell key={d.name} fill={FACTOR_COLORS[d.name] || '#388bfd'} />)}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
                <div style={{ marginTop: '1rem', padding: '.6rem 1rem', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: '.85rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <span>Base: <b style={{ color: '#388bfd' }}>{rr.base_score || 40}</b></span>
                    <span>Penalty: <b style={{ color: 'var(--red)' }}>+{(rr.total_score || 0) - (rr.base_score || 40)}</b></span>
                    <span>Total: <b style={{ color: 'var(--amber)' }}>{rr.total_score || 0}/100</b></span>
                </div>
            </div>

            {voteData.length > 0 && (
                <div className="card">
                    <div className="card-title">🏛 Committee Vote Scores</div>
                    <p style={{ fontSize: '.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                        Approval threshold: 0.70 &nbsp;|&nbsp; Actual: {wt.toFixed(4)}
                    </p>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={voteData} margin={{ top: 10, right: 30, bottom: 0, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                            <XAxis dataKey="name" tick={{ fill: '#e6edf3', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis domain={[0, 1.1]} tick={{ fill: '#8b949e', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#1c2128', border: '1px solid #30363d', borderRadius: 8, fontSize: '.8rem' }}
                                itemStyle={{ color: '#e6edf3' }} formatter={v => [v.toFixed(2), 'Score']} />
                            <ReferenceLine y={0.7} stroke="#ffa657" strokeDasharray="6 3"
                                label={{ value: 'Approval (0.70)', fill: '#ffa657', fontSize: 10, position: 'insideTopRight' }} />
                            <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                                <LabelList dataKey="score" position="top" formatter={v => v.toFixed(2)} style={{ fill: '#e6edf3', fontSize: 12, fontWeight: 600 }} />
                                {voteData.map(d => <Cell key={d.name} fill={AGENT_COLORS[d.vote] || '#58a6ff'} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}
