'use client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

const sc = s => s <= 40 ? '#3fb950' : s <= 70 ? '#ffa657' : '#f85149';

export default function WhatIfSimulator({ counterfactuals = [], currentScore = 0 }) {
    if (!counterfactuals.length) return (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-secondary)', fontSize: '.9rem' }}>
            No counterfactual data. Run the analysis first.
        </div>
    );

    const chartData = counterfactuals.map(c => ({
        name: c.scenario.replace('Remove ', '').replace('Resolve ', '').replace('Improve ', '').replace(' (All Risks Resolved)', ' 🏆'),
        score: c.score_if_removed,
        delta: c.delta,
    }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
            <div className="card">
                <div className="card-title">🔮 What-If Scenario Chart</div>
                <p style={{ fontSize: '.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Current score: <b style={{ color: sc(currentScore) }}>{currentScore}/100</b>. Bars show score if each factor is resolved.
                </p>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 80, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                        <XAxis dataKey="name" tick={{ fill: '#8b949e', fontSize: 10, angle: -25, textAnchor: 'end' }} axisLine={false} tickLine={false} interval={0} />
                        <YAxis domain={[0, 105]} tick={{ fill: '#8b949e', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={{ background: '#1c2128', border: '1px solid #30363d', borderRadius: 8, fontSize: '.8rem' }}
                            itemStyle={{ color: '#e6edf3' }} formatter={(v, _, p) => [`${v}/100 (saves -${p.payload.delta} pts)`, 'Score']} />
                        <ReferenceLine y={currentScore} stroke="#484f58" strokeDasharray="4 3"
                            label={{ value: `Current: ${currentScore}`, fill: '#8b949e', fontSize: 10, position: 'insideTopRight' }} />
                        <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                            {chartData.map(d => <Cell key={d.name} fill={sc(d.score)} />)}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="card">
                <div className="card-title">📋 Scenario Breakdown</div>
                <table className="data-table">
                    <thead><tr><th>Scenario</th><th style={{ textAlign: 'center' }}>Score If Resolved</th><th style={{ textAlign: 'center' }}>Reduction</th><th>Recommendation</th></tr></thead>
                    <tbody>
                        {counterfactuals.map((c, i) => (
                            <tr key={i}>
                                <td style={{ fontWeight: 500 }}>{c.scenario}</td>
                                <td style={{ textAlign: 'center' }}><span style={{ color: sc(c.score_if_removed), fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{c.score_if_removed}/100</span></td>
                                <td style={{ textAlign: 'center' }}>{c.delta > 0 ? <span className="delta-chip">–{c.delta} pts</span> : '—'}</td>
                                <td style={{ color: 'var(--text-secondary)', fontSize: '.8rem' }}>{c.description}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
