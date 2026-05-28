import { useEffect } from 'react';

const TYPE_BADGE = {
  'Solicitation':                  { bg: '#00E5FF', text: '#000' },
  'Combined Synopsis/Solicitation':{ bg: '#FCE300', text: '#000' },
  'Presolicitation':               { bg: '#FF6B00', text: '#000' },
  'Sources Sought':                { bg: '#FF0055', text: '#fff' },
};

function scoreColor(s) {
  if (s == null) return 'var(--text-subtle)';
  if (s >= 80) return '#39FF14';
  if (s >= 60) return '#FCE300';
  if (s >= 40) return '#FF6B00';
  return '#FF0055';
}

function deadlineColor(d) {
  if (d == null) return 'var(--text-muted)';
  if (d <= 7)  return '#FF0055';
  if (d <= 14) return '#FF6B00';
  if (d <= 30) return '#FCE300';
  return '#39FF14';
}

function MetaTile({ label, value, color, mono }) {
  return (
    <div style={{
      padding: '8px 10px',
      background: 'var(--surface-2)',
      borderLeft: `2px solid ${color ?? 'var(--border)'}`,
      clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
      minWidth: 0,
    }}>
      <div style={{
        fontFamily: "'Rajdhani', sans-serif",
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: '0.12em',
        color: 'var(--text-subtle)',
        marginBottom: 3,
      }}>
        // {label}
      </div>
      <div style={{
        fontFamily: mono ? "'Share Tech Mono', monospace" : "'Rajdhani', sans-serif",
        fontWeight: mono ? 400 : 600,
        fontSize: mono ? 11 : 12,
        color: color ?? 'var(--text)',
        textShadow: color ? `0 0 8px ${color}50` : 'none',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {value}
      </div>
    </div>
  );
}

export default function DetailModal({ opportunity: o, onClose }) {
  useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [onClose]);

  if (!o) return null;

  const badge   = TYPE_BADGE[o.notice_type] ?? { bg: 'var(--surface-3)', text: 'var(--text-muted)' };
  const sc      = scoreColor(o.score);
  const naics   = (o.naics ?? []).join(', ') || '—';
  const dlDays  = o.deadline_in_days;
  const dlColor = deadlineColor(dlDays);

  const deadlineVal = o.response_deadline
    ? `${o.response_deadline}${dlDays != null ? `  (${dlDays < 0 ? `${Math.abs(dlDays)}D AGO` : `${dlDays}D`})` : ''}`
    : '—';

  return (
    <div
      className="modal-backdrop"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        justifyContent: 'flex-end',
        background: 'rgba(2, 2, 4, 0.88)',
      }}
      onClick={onClose}
    >
      <div
        className="modal-panel"
        style={{
          position: 'relative',
          width: 'min(700px, 100%)',
          height: '100%',
          background: 'var(--surface)',
          borderLeft: '1px solid var(--yellow)',
          boxShadow: '-4px 0 40px rgba(252,227,0,0.08)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Scan line animation */}
        <div className="modal-scan-line" />

        {/* Sticky header */}
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border)',
          background: 'var(--surface-2)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <h2 style={{
                fontFamily: "'Rajdhani', sans-serif",
                fontWeight: 700,
                fontSize: 17,
                letterSpacing: '0.03em',
                color: 'var(--text)',
                margin: 0,
                lineHeight: 1.3,
              }}>
                {o.title}
              </h2>
            </div>
            <button
              onClick={onClose}
              style={{
                flexShrink: 0,
                background: 'none',
                border: '1px solid var(--border)',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontFamily: "'Rajdhani', sans-serif",
                fontWeight: 700,
                fontSize: 11,
                letterSpacing: '0.08em',
                padding: '4px 8px',
                clipPath: 'polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 0 100%)',
                transition: 'all 0.1s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--yellow)';
                e.currentTarget.style.color = 'var(--yellow)';
                e.currentTarget.style.boxShadow = '0 0 8px rgba(252,227,0,0.2)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.color = 'var(--text-muted)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              [×] CLOSE
            </button>
          </div>

          {/* Badges row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {o.notice_type && (
              <span style={{
                fontFamily: "'Rajdhani', sans-serif",
                fontWeight: 700,
                fontSize: 9,
                letterSpacing: '0.1em',
                padding: '2px 8px',
                background: badge.bg,
                color: badge.text,
                clipPath: 'polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 0 100%)',
              }}>
                {o.notice_type.toUpperCase()}
              </span>
            )}
            {o.score != null && (
              <span style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 10,
                color: sc,
                textShadow: `0 0 8px ${sc}80`,
              }}>
                ◈ {o.score}/100 {o.ai_generated ? '[AI]' : '[KW]'}
              </span>
            )}
          </div>
        </div>

        {/* Scrollable body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.1rem 1.25rem 2rem' }}>
          {/* Metadata grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))',
            gap: 6,
            marginBottom: '1.1rem',
          }}>
            <MetaTile label="AGENCY"    value={o.agency_short ?? '—'} />
            <MetaTile label="POSTED"    value={o.posted_date  ?? '—'} mono />
            <MetaTile
              label="DEADLINE"
              value={deadlineVal}
              color={dlDays != null ? dlColor : undefined}
              mono
            />
            <MetaTile label="NAICS"     value={naics}          mono />
            <MetaTile label="SOL. #"    value={o.solicitation_number ?? '—'} mono />
            <MetaTile
              label="RELEVANCE"
              value={o.score != null ? `${o.score} / 100` : '—'}
              color={o.score != null ? sc : undefined}
              mono
            />
          </div>

          {/* Full agency path */}
          {o.agency_full && (
            <div style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 10,
              letterSpacing: '0.04em',
              color: 'var(--text-subtle)',
              borderLeft: '2px solid var(--border)',
              paddingLeft: 10,
              marginBottom: '1.1rem',
              lineHeight: 1.6,
            }}>
              {o.agency_full}
            </div>
          )}

          {/* SAM link */}
          {o.ui_link && (
            <a
              href={o.ui_link}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                fontFamily: "'Rajdhani', sans-serif",
                fontWeight: 700,
                fontSize: 11,
                letterSpacing: '0.12em',
                color: 'var(--yellow)',
                textDecoration: 'none',
                padding: '7px 16px',
                border: '1px solid rgba(252,227,0,0.4)',
                clipPath: 'polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%)',
                background: 'var(--yellow-subtle)',
                marginBottom: '1.1rem',
                transition: 'all 0.1s ease',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(252,227,0,0.12)';
                e.currentTarget.style.boxShadow = '0 0 16px rgba(252,227,0,0.25)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--yellow-subtle)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              [ OPEN SAM.GOV → ]
            </a>
          )}

          {/* Divider */}
          <div style={{
            height: 1,
            background: 'linear-gradient(90deg, var(--yellow) 0%, transparent 100%)',
            boxShadow: '0 0 8px rgba(252,227,0,0.2)',
            marginBottom: '1.1rem',
          }} />

          {/* Intel summary header */}
          <div className="cp-label" style={{ fontSize: 11, marginBottom: 12 }}>
            INTEL SUMMARY
          </div>

          {/* Writeup */}
          {o.writeup_html ? (
            <div
              className="writeup-content"
              dangerouslySetInnerHTML={{ __html: o.writeup_html }}
            />
          ) : (
            <div style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 11,
              color: 'var(--text-subtle)',
              letterSpacing: '0.06em',
            }}>
              // NO WRITEUP AVAILABLE
            </div>
          )}

          {/* Game plan section — only rendered when present */}
          {o.gameplan_html && (
            <>
              <div style={{
                height: 1,
                background: 'linear-gradient(90deg, var(--yellow) 0%, transparent 100%)',
                boxShadow: '0 0 8px rgba(252,227,0,0.2)',
                margin: '1.4rem 0 1.1rem',
              }} />
              <div className="cp-label" style={{ fontSize: 11, marginBottom: 12 }}>
                ACTION PLAN
              </div>
              <div
                className="writeup-content"
                dangerouslySetInnerHTML={{ __html: o.gameplan_html }}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
