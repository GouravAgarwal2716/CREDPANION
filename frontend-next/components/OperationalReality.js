'use client';
import RiskGauge from './RiskGauge';

export default function OperationalReality({ visionResults = [], realityScore = 0 }) {
    const vr = visionResults[0] || {};
    const pct = Math.round(realityScore * 100);
    const isOk = realityScore >= 0.5;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
            <div className="grid-2" style={{ alignItems: 'start' }}>
                {/* Gauge */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                    <div className="card-title">Operational Reality Score</div>
                    <RiskGauge score={pct} category={pct <= 40 ? 'High' : pct <= 70 ? 'Medium' : 'Low'} />
                    <div style={{
                        padding: '.55rem 1.2rem', borderRadius: 'var(--radius-md)', fontWeight: 700, fontSize: '.88rem',
                        background: isOk ? 'var(--green-bg)' : 'var(--red-bg)',
                        color: isOk ? 'var(--green)' : 'var(--red)',
                        border: `1px solid ${isOk ? 'var(--green-border)' : 'var(--red-border)'}`
                    }}>
                        {isOk ? '✅ Satisfactory Utilisation' : '⚠️ Idle Machinery Detected'}
                    </div>
                    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' }}>
                            <span style={{ color: 'var(--green)' }}>● Active: {vr.active_assets || 0}</span>
                            <span style={{ color: 'var(--red)' }}>● Idle: {vr.idle_assets || 0}</span>
                        </div>
                        <div className="factory-status-bar">
                            <div className="factory-status-fill" style={{
                                width: `${pct}%`,
                                background: isOk ? 'linear-gradient(90deg,#1a7f37,#3fb950)' : 'linear-gradient(90deg,#8a2222,#f85149)'
                            }} />
                        </div>
                        <div style={{ fontSize: '.74rem', color: 'var(--text-muted)', textAlign: 'center' }}>{pct}% operational utilisation</div>
                    </div>
                </div>

                {/* Assessment */}
                <div className="card">
                    <div className="card-title">Factory Site Assessment</div>
                    <div style={{
                        height: 200, borderRadius: 'var(--radius-md)', marginBottom: '1rem',
                        background: isOk ? 'linear-gradient(135deg,#0d2818,#1a3a22)' : 'linear-gradient(135deg,#200a0a,#3a1219)',
                        border: `2px dashed ${isOk ? 'var(--green)' : 'var(--red)'}`,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '.5rem',
                    }}>
                        <span style={{ fontSize: '3.5rem' }}>{isOk ? '🏭' : '🏚️'}</span>
                        <b style={{ color: isOk ? 'var(--green)' : 'var(--red)', fontSize: '1rem' }}>
                            {isOk ? 'Active Production Site' : 'Predominantly Idle Facility'}
                        </b>
                        <span style={{ color: 'var(--text-muted)', fontSize: '.78rem', textAlign: 'center', padding: '0 1rem' }}>
                            {isOk ? 'Equipment operational, activity consistent with declared turnover' : 'Significant idle machinery — inconsistent with stated financials'}
                        </span>
                    </div>
                    {visionResults.map((r, i) => (
                        <div key={i} style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', padding: '.7rem 1rem', fontSize: '.8rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '.4rem' }}>
                            <span>📷 Image {i + 1}</span>
                            <span style={{ color: 'var(--green)' }}>Active: {r.active_assets}</span>
                            <span style={{ color: 'var(--red)' }}>Idle: {r.idle_assets}</span>
                            <span style={{ color: 'var(--blue)', fontFamily: 'var(--font-mono)' }}>Score: {(r.reality_score || 0).toFixed(2)}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="card">
                <div className="card-title">📌 Analyst Interpretation</div>
                <p style={{ fontSize: '.85rem', color: 'var(--text-secondary)', lineHeight: 1.75 }}>
                    {isOk
                        ? `The operational reality score of ${pct}% indicates the borrower's production activity is consistent with observed factory conditions. Physical verification risk is LOW.`
                        : `The operational reality score of ${pct}% is below the 50% threshold. Idle machinery detected — INCONSISTENT with declared revenue. A deeper physical inspection is recommended before disbursement.`
                    }
                </p>
            </div>
        </div>
    );
}
