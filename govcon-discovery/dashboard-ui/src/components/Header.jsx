export default function Header({ summary, loaded, onSettings }) {
  const total       = summary.total_kept      ?? 0;
  const evaluated   = summary.evaluated_total ?? 0;
  const updated     = summary.last_updated    ?? '—';
  const reviewCount = summary.review_count    ?? 0;

  return (
    <header style={{
      height: 'var(--header-h)',
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.25rem',
      background: 'var(--surface)',
      borderBottom: '1px solid var(--yellow)',
      boxShadow: '0 1px 16px rgba(252, 227, 0, 0.12)',
      position: 'relative',
      zIndex: 20,
    }}>
      {/* Left */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <span style={{
            color: 'var(--yellow)',
            fontSize: 18,
            lineHeight: 1,
            textShadow: '0 0 10px rgba(252,227,0,0.7)',
            userSelect: 'none',
          }}>◈</span>
          <span
            className="glitch-title"
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700,
              fontSize: 18,
              letterSpacing: '0.12em',
              color: 'var(--yellow)',
              textShadow: '0 0 8px rgba(252,227,0,0.5)',
              textTransform: 'uppercase',
              cursor: 'default',
              userSelect: 'none',
            }}
          >
            GOVCON INTEL FEED
          </span>
        </div>
        {loaded && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 10,
            color: 'var(--text-muted)',
            letterSpacing: '0.06em',
          }}>
            <span>// {total} OPP · EVALUATED {evaluated.toLocaleString()} · {updated}</span>
            {reviewCount > 0 && (
              <span style={{
                color: '#FF9500',
                textShadow: '0 0 6px rgba(255,149,0,0.7)',
                letterSpacing: '0.08em',
              }}>
                ⚑ {reviewCount} PENDING REVIEW
              </span>
            )}
          </div>
        )}
      </div>

      {/* Right: settings + LIVE badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {loaded && (
          <button
            onClick={onSettings}
            title="GitHub token settings"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-subtle)', fontSize: 14,
              lineHeight: 1, padding: 2,
              transition: 'color 0.1s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--yellow)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-subtle)'}
          >
            ⚙
          </button>
        )}
        {loaded && (
          <div style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 600,
            fontSize: 11,
            letterSpacing: '0.14em',
            color: 'var(--yellow)',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            animation: 'flicker 6s ease-in-out infinite',
            userSelect: 'none',
          }}>
            <span style={{ color: 'var(--text-muted)' }}>[</span>
            <span style={{
              fontSize: 9,
              textShadow: '0 0 6px rgba(252,227,0,0.9)',
            }}>◉</span>
            LIVE
            <span style={{ color: 'var(--text-muted)' }}>]</span>
          </div>
        )}
      </div>
    </header>
  );
}
