'use client';
// SVG Arc Risk Gauge

function polar(cx, cy, r, deg) {
    const rad = ((deg - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}
function arc(cx, cy, r, s, e) {
    if (Math.abs(e - s) >= 360) e -= 0.01;
    const st = polar(cx, cy, r, s), en = polar(cx, cy, r, e);
    return `M ${st.x} ${st.y} A ${r} ${r} 0 ${e - s > 180 ? 1 : 0} 1 ${en.x} ${en.y}`;
}

const CAT_COLOR = { Low: '#3fb950', Medium: '#ffa657', High: '#f85149' };

export default function RiskGauge({ score = 0, category = 'Low' }) {
    const color = CAT_COLOR[category] || '#58a6ff';
    const min = -140, max = 140;
    const ang = min + (score / 100) * (max - min);
    const cx = 120, cy = 120, r = 88, sw = 14;
    const nr = ((ang - 90) * Math.PI) / 180;
    const nx = cx + 72 * Math.cos(nr), ny = cy + 72 * Math.sin(nr);

    return (
        <div className="gauge-wrap">
            <svg width="240" height="175" viewBox="0 0 240 175" style={{ overflow: 'visible' }}>
                <path d={arc(cx, cy, r, min, max)} fill="none" stroke="#1c2128" strokeWidth={sw} strokeLinecap="round" />
                <path d={arc(cx, cy, r, min, min + 0.4 * (max - min))} fill="none" stroke="rgba(63,185,80,0.22)" strokeWidth={sw} strokeLinecap="round" />
                <path d={arc(cx, cy, r, min + 0.4 * (max - min), min + 0.7 * (max - min))} fill="none" stroke="rgba(255,166,87,0.22)" strokeWidth={sw} strokeLinecap="round" />
                <path d={arc(cx, cy, r, min + 0.7 * (max - min), max)} fill="none" stroke="rgba(248,81,73,0.22)" strokeWidth={sw} strokeLinecap="round" />
                <path d={arc(cx, cy, r, min, ang)} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 8px ${color}99)`, transition: 'all 1s ease' }} />
                <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#e6edf3" strokeWidth="2.5" strokeLinecap="round"
                    style={{ transition: 'all 1s ease' }} />
                <circle cx={cx} cy={cy} r="5" fill={color} />
                <text x={cx - r - 4} y={cy + 24} fill="#484f58" fontSize="10" textAnchor="middle">0</text>
                <text x={cx + r + 4} y={cy + 24} fill="#484f58" fontSize="10" textAnchor="middle">100</text>
                <text x={cx} y={cy + 48} fill={color} fontSize="36" fontWeight="800" textAnchor="middle"
                    fontFamily="JetBrains Mono,monospace" style={{ transition: 'fill 1s ease' }}>{score}</text>
                <text x={cx} y={cy + 64} fill="#8b949e" fontSize="11" textAnchor="middle">{category} Risk</text>
            </svg>
        </div>
    );
}
