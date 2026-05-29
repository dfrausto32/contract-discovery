import { useState, useRef, useEffect } from 'react';

const ENRICH_REPO     = 'dfrausto32/contract-discovery';
const ENRICH_BRANCH   = 'contract-discovery';
const ENRICH_WORKFLOW = 'govcon-enrich.yml';

function EnrichPanel({ pendingCount, onNeedToken, onClose }) {
  const [limit,     setLimit]     = useState(Math.min(pendingCount || 30, 50));
  const [loading,   setLoading]   = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error,     setError]     = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    const fn = e => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    document.addEventListener('mousedown', fn);
    return () => document.removeEventListener('mousedown', fn);
  }, [onClose]);

  const dispatch = async () => {
    const pat = localStorage.getItem('gh_pat');
    if (!pat) { onNeedToken(); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `https://api.github.com/repos/${ENRICH_REPO}/actions/workflows/${ENRICH_WORKFLOW}/dispatches`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${pat}`,
            'Content-Type': 'application/json',
            Accept: 'application/vnd.github+json',
          },
          body: JSON.stringify({ ref: ENRICH_BRANCH, inputs: { limit: String(limit) } }),
        }
      );
      if (res.status === 204) {
        setSubmitted(true);
        setTimeout(onClose, 2000);
      } else if (res.status === 401) {
        setError('Token invalid — update via ⚙');
      } else {
        const body = await res.text();
        setError(`GitHub ${res.status}: ${body.slice(0, 80)}`);
      }
    } catch (e) {
      setError(`Network error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      ref={ref}
      style={{
        position: 'absolute',
        top: 'calc(100% + 6px)',
        right: 0,
        width: 230,
        background: 'var(--surface-2)',
        border: '1px solid var(--yellow)',
        clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%)',
        boxShadow: '0 4px 24px rgba(252,227,0,0.12)',
        padding: '0.9rem 1rem',
        zIndex: 100,
      }}
    >
      <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 10, letterSpacing: '0.12em', color: 'var(--yellow)', marginBottom: 10 }}>
        // BATCH AI ENRICHMENT
      </div>

      <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-muted)', marginBottom: 10, lineHeight: 1.5 }}>
        {pendingCount} opps pending.<br />Enrich top:
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <input
          type="number"
          min={1}
          max={pendingCount || 200}
          value={limit}
          onChange={e => setLimit(Math.max(1, Math.min(Number(e.target.value), pendingCount || 200)))}
          className="cp-input"
          style={{ width: 60, textAlign: 'center', padding: '4px 6px' }}
        />
        <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-subtle)' }}>
          by score
        </span>
      </div>

      {submitted ? (
        <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: '#39FF14', textShadow: '0 0 6px rgba(57,255,20,0.5)', letterSpacing: '0.06em' }}>
          ✓ QUEUED — ~5 min to complete
        </div>
      ) : (
        <>
          <button
            onClick={dispatch}
            disabled={loading}
            style={{
              width: '100%',
              fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 12,
              letterSpacing: '0.1em',
              padding: '6px 0',
              background: 'var(--yellow-subtle)',
              border: '1px solid rgba(252,227,0,0.5)',
              color: 'var(--yellow)',
              cursor: loading ? 'wait' : 'pointer',
              clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
              transition: 'all 0.1s ease',
              textShadow: '0 0 6px rgba(252,227,0,0.4)',
            }}
            onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'rgba(252,227,0,0.12)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'var(--yellow-subtle)'; }}
          >
            {loading ? '…' : '[ RUN ENRICHMENT ]'}
          </button>
          {error && (
            <div style={{ marginTop: 7, fontFamily: "'Share Tech Mono'", fontSize: 9, color: '#FF6B00', lineHeight: 1.4 }}>
              ⚠ {error}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function Header({ summary, loaded, onSettings, onNeedToken, onTriage }) {
  const total        = summary.total_kept      ?? 0;
  const evaluated    = summary.evaluated_total ?? 0;
  const updated      = summary.last_updated    ?? '—';
  const reviewCount  = summary.review_count    ?? 0;
  const pendingCount = summary.pending_count   ?? 0;
  const [showEnrich, setShowEnrich] = useState(false);

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
            color: 'var(--yellow)', fontSize: 18, lineHeight: 1,
            textShadow: '0 0 10px rgba(252,227,0,0.7)', userSelect: 'none',
          }}>◈</span>
          <span
            className="glitch-title"
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700, fontSize: 18, letterSpacing: '0.12em',
              color: 'var(--yellow)', textShadow: '0 0 8px rgba(252,227,0,0.5)',
              textTransform: 'uppercase', cursor: 'default', userSelect: 'none',
            }}
          >
            GOVCON INTEL FEED
          </span>
        </div>
        {loaded && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em',
          }}>
            <span>// {total} OPP · EVALUATED {evaluated.toLocaleString()} · {updated}</span>
            {reviewCount > 0 && (
              <span style={{ color: '#FF9500', textShadow: '0 0 6px rgba(255,149,0,0.7)', letterSpacing: '0.08em' }}>
                ⚑ {reviewCount} PENDING REVIEW
              </span>
            )}
          </div>
        )}
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Triage button — shown when there are pending opps */}
        {loaded && pendingCount > 0 && onTriage && (
          <button
            onClick={onTriage}
            title="Swipe through pending opps to queue for AI or dismiss"
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700, fontSize: 10,
              letterSpacing: '0.1em',
              padding: '4px 10px',
              background: 'none',
              border: '1px solid rgba(0,229,255,0.25)',
              color: 'var(--cyan)',
              cursor: 'pointer',
              clipPath: 'polygon(0 0, calc(100% - 7px) 0, 100% 7px, 100% 100%, 0 100%)',
              transition: 'all 0.1s ease',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,229,255,0.08)'; e.currentTarget.style.borderColor = 'rgba(0,229,255,0.5)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.borderColor = 'rgba(0,229,255,0.25)'; }}
          >
            <span style={{ fontSize: 9, opacity: 0.7 }}>▸</span>
            TRIAGE
          </button>
        )}

        {/* Enrich button — shown when there are pending opps */}
        {loaded && pendingCount > 0 && (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowEnrich(v => !v)}
              title={`${pendingCount} opps awaiting AI enrichment`}
              style={{
                fontFamily: "'Rajdhani', sans-serif",
                fontWeight: 700, fontSize: 10,
                letterSpacing: '0.1em',
                padding: '4px 10px',
                background: showEnrich ? 'rgba(252,227,0,0.1)' : 'var(--yellow-subtle)',
                border: `1px solid ${showEnrich ? 'rgba(252,227,0,0.6)' : 'rgba(252,227,0,0.3)'}`,
                color: 'var(--yellow)',
                cursor: 'pointer',
                clipPath: 'polygon(0 0, calc(100% - 7px) 0, 100% 7px, 100% 100%, 0 100%)',
                transition: 'all 0.1s ease',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(252,227,0,0.1)'; }}
              onMouseLeave={e => { if (!showEnrich) e.currentTarget.style.background = 'var(--yellow-subtle)'; }}
            >
              <span style={{ fontSize: 9, opacity: 0.7 }}>◈</span>
              ENRICH
              <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 9, color: 'rgba(252,227,0,0.7)' }}>
                [{pendingCount}]
              </span>
            </button>

            {showEnrich && (
              <EnrichPanel
                pendingCount={pendingCount}
                onNeedToken={() => { setShowEnrich(false); onNeedToken?.(); }}
                onClose={() => setShowEnrich(false)}
              />
            )}
          </div>
        )}

        {/* Settings gear */}
        {loaded && (
          <button
            onClick={onSettings}
            title="GitHub token settings"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-subtle)', fontSize: 14,
              lineHeight: 1, padding: 2, transition: 'color 0.1s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--yellow)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-subtle)'}
          >
            ⚙
          </button>
        )}

        {/* LIVE badge */}
        {loaded && (
          <div style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 600, fontSize: 11, letterSpacing: '0.14em',
            color: 'var(--yellow)',
            display: 'flex', alignItems: 'center', gap: 6,
            animation: 'flicker 6s ease-in-out infinite',
            userSelect: 'none',
          }}>
            <span style={{ color: 'var(--text-muted)' }}>[</span>
            <span style={{ fontSize: 9, textShadow: '0 0 6px rgba(252,227,0,0.9)' }}>◉</span>
            LIVE
            <span style={{ color: 'var(--text-muted)' }}>]</span>
          </div>
        )}
      </div>
    </header>
  );
}
