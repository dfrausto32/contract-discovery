const BAND_COLORS = {
  '90-100': '#39FF14',
  '70-89':  '#FCE300',
  '50-69':  '#FF6B00',
  '<50':    '#FF0055',
};

function Card({ glyph, label, children }) {
  return (
    <div className="cp-card" style={{ padding: '0.75rem 0.9rem', minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
        <span style={{
          fontSize: 10,
          color: 'var(--yellow)',
          textShadow: '0 0 6px rgba(252,227,0,0.6)',
          userSelect: 'none',
        }}>
          {glyph}
        </span>
        <span className="cp-label">{label}</span>
      </div>
      {children}
    </div>
  );
}

function DataRow({ label, value, color }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      margin: '3px 0',
      gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        {color && (
          <div style={{
            width: 5,
            height: 5,
            background: color,
            flexShrink: 0,
            boxShadow: `0 0 4px ${color}`,
          }} />
        )}
        <span style={{
          fontSize: 12,
          fontWeight: 500,
          color: 'var(--text-muted)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {label}
        </span>
      </div>
      <span style={{
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 12,
        color: color ?? 'var(--text)',
        flexShrink: 0,
        textShadow: color ? `0 0 6px ${color}70` : 'none',
      }}>
        {value}
      </span>
    </div>
  );
}

export default function SummaryCards({ summary }) {
  const total     = summary.total_kept      ?? 0;
  const evaluated = summary.evaluated_total ?? 0;
  const byType    = summary.by_notice_type  ?? {};
  const byBand    = summary.by_score_band   ?? {};
  const agencies  = (summary.top_agencies  ?? []).slice(0, 4);
  const dl        = summary.deadlines_within ?? {};
  const pct       = evaluated > 0 ? Math.min(100, (total / evaluated) * 100) : 0;

  return (
    <div className="summary-grid" style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(185px, 1fr))',
      gap: '0.6rem',
      padding: '0.75rem 1.25rem',
    }}>
      {/* Total kept */}
      <Card glyph="◈" label="Total Kept">
        <div style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: '1.9rem',
          fontWeight: 400,
          lineHeight: 1,
          color: 'var(--yellow)',
          textShadow: '0 0 12px rgba(252,227,0,0.8), 0 0 24px rgba(252,227,0,0.4)',
          marginBottom: 5,
        }}>
          {total}
        </div>
        <div style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 10,
          color: 'var(--text-muted)',
          letterSpacing: '0.04em',
          marginBottom: 8,
        }}>
          / {evaluated.toLocaleString()} EVALUATED
        </div>
        <div style={{ height: 2, background: 'var(--border-dim)' }}>
          <div style={{
            width: `${pct}%`,
            height: '100%',
            background: 'linear-gradient(90deg, var(--yellow) 0%, #ffe94d 100%)',
            boxShadow: '0 0 6px rgba(252,227,0,0.6)',
            transition: 'width 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
          }} />
        </div>
      </Card>

      {/* Score bands */}
      <Card glyph="▸" label="Score Band">
        {Object.entries(byBand).sort((a, b) => b[1] - a[1]).map(([band, count]) => (
          <DataRow key={band} label={band} value={count} color={BAND_COLORS[band]} />
        ))}
        {!Object.keys(byBand).length && <span style={{ fontSize: 11, color: 'var(--text-subtle)' }}>NO DATA</span>}
      </Card>

      {/* Notice type */}
      <Card glyph="◆" label="Notice Type">
        {Object.entries(byType).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
          <DataRow key={type} label={type} value={count} />
        ))}
        {!Object.keys(byType).length && <span style={{ fontSize: 11, color: 'var(--text-subtle)' }}>NO DATA</span>}
      </Card>

      {/* Deadlines */}
      <Card glyph="◉" label="Deadlines">
        <DataRow label="WITHIN 7D"  value={dl['7']  ?? 0} color={(dl['7']  ?? 0) > 0 ? '#FF0055' : undefined} />
        <DataRow label="WITHIN 14D" value={dl['14'] ?? 0} color={(dl['14'] ?? 0) > 0 ? '#FF6B00' : undefined} />
        <DataRow label="WITHIN 30D" value={dl['30'] ?? 0} color={(dl['30'] ?? 0) > 0 ? '#FCE300' : undefined} />
      </Card>

      {/* Top agencies */}
      <Card glyph="▸" label="Top Agencies">
        {agencies.map(a => (
          <DataRow key={a.name} label={a.name} value={a.count} />
        ))}
        {!agencies.length && <span style={{ fontSize: 11, color: 'var(--text-subtle)' }}>NO DATA</span>}
      </Card>
    </div>
  );
}
