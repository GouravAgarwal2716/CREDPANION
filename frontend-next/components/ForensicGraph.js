'use client';
import { useEffect, useRef } from 'react';

export default function ForensicGraph({ transactions = [], fraudNodes = [] }) {
    const ref = useRef(null);
    const net = useRef(null);

    useEffect(() => {
        if (!ref.current || !transactions.length) return;
        // Use standard 'vis-network' entry — works with Turbopack (no deep ESM path)
        Promise.all([
            import('vis-network'),
            import('vis-data'),
        ]).then(([visNet, visData]) => {
            const Network = visNet.Network || visNet.default?.Network;
            const DataSet = visData.DataSet || visData.default?.DataSet;
            if (!Network || !DataSet) return;

            const fraud = new Set(fraudNodes);
            const nodeMap = {};
            transactions.forEach(({ sender, receiver }) => {
                [sender, receiver].forEach(n => {
                    if (!nodeMap[n]) {
                        const f = fraud.has(n);
                        nodeMap[n] = {
                            id: n, label: n,
                            color: {
                                background: f ? '#2a0a0a' : '#1c2128', border: f ? '#f85149' : '#58a6ff',
                                highlight: { background: f ? '#3f0f0f' : '#21262d', border: f ? '#ff6b6b' : '#79c0ff' }
                            },
                            font: { color: '#e6edf3', size: 13 },
                            borderWidth: f ? 3 : 1.5, size: f ? 28 : 20,
                            shape: f ? 'hexagon' : 'ellipse',
                            shadow: f ? { enabled: true, color: '#f8514988', size: 14, x: 0, y: 0 } : false,
                            title: f ? '⚠ FRAUD NODE — Circular Trading' : n,
                        };
                    }
                });
            });
            const edgeMap = {};
            transactions.forEach(({ sender, receiver, amount }) => {
                const k = `${sender}→${receiver}`;
                if (edgeMap[k]) return;
                const fe = fraud.has(sender) && fraud.has(receiver);
                edgeMap[k] = {
                    id: k, from: sender, to: receiver,
                    color: { color: fe ? '#f85149' : '#484f58', highlight: fe ? '#ff6b6b' : '#8b949e' },
                    width: fe ? 3 : 1.5, arrows: { to: { enabled: true, scaleFactor: .8 } },
                    label: `₹${(amount / 1e5).toFixed(1)}L`, font: { color: '#8b949e', size: 10 },
                    title: `₹${amount.toLocaleString('en-IN')}`,
                    smooth: { type: 'curvedCW', roundness: .2 },
                };
            });
            if (net.current) net.current.destroy();
            net.current = new Network(
                ref.current,
                { nodes: new DataSet(Object.values(nodeMap)), edges: new DataSet(Object.values(edgeMap)) },
                {
                    physics: { solver: 'barnesHut', barnesHut: { gravitationalConstant: -9000, springLength: 190, damping: .12 }, stabilization: { iterations: 200 } },
                    interaction: { hover: true, tooltipDelay: 150 }
                }
            );
        });
        return () => { if (net.current) { net.current.destroy(); net.current = null; } };
    }, [transactions, fraudNodes]);

    if (!transactions.length) return (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, color: 'var(--text-secondary)' }}>
            No transaction data. Run an analysis first.
        </div>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '.8rem 1.2rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <span style={{ fontSize: '.8rem', color: 'var(--text-secondary)' }}>🔴 Fraud node &nbsp;|&nbsp; 🔵 Normal entity &nbsp;|&nbsp; → Flow</span>
                    <span style={{ marginLeft: 'auto', fontSize: '.75rem', color: 'var(--text-muted)' }}>{transactions.length} transaction(s)</span>
                </div>
                <div ref={ref} style={{ background: '#0d1117', height: 500 }} />
            </div>
            <div className="card">
                <div className="card-title">💳 Transaction Ledger</div>
                <table className="data-table">
                    <thead><tr><th>#</th><th>Sender</th><th>Receiver</th><th style={{ textAlign: 'right' }}>Amount</th><th>Flag</th></tr></thead>
                    <tbody>
                        {transactions.map((t, i) => {
                            const isFraud = (new Set(fraudNodes)).has(t.sender) && (new Set(fraudNodes)).has(t.receiver);
                            return (
                                <tr key={i}>
                                    <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{i + 1}</td>
                                    <td style={{ color: isFraud ? 'var(--red)' : 'var(--text-primary)' }}>{t.sender}</td>
                                    <td style={{ color: isFraud ? 'var(--red)' : 'var(--text-primary)' }}>{t.receiver}</td>
                                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{t.amount.toLocaleString('en-IN')}</td>
                                    <td>{isFraud ? <span style={{ color: 'var(--red)', fontSize: '.75rem' }}>🔴 Carousel</span> : '—'}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
