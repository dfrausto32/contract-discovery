// notice_type → badge color + tooltip description
const TYPE_BADGE = {
  'Solicitation': {
    bg: '#00E5FF', text: '#000',
    tip: 'Solicitation (RFP/RFQ) — Formal request for proposals. Full proposal required. Most competitive pursuit.',
  },
  'Combined Synopsis/Solicitation': {
    bg: '#FCE300', text: '#000',
    tip: 'Combined Synopsis/Solicitation — Combines the market notice and RFP in one posting. Full proposal required but faster timeline.',
  },
  'Presolicitation': {
    bg: '#FF6B00', text: '#000',
    tip: 'Presolicitation — Early notice before the formal RFP. Good window to introduce yourself to the CO and shape requirements.',
  },
  'Sources Sought': {
    bg: '#A855F7', text: '#fff',
    tip: 'Sources Sought — Market research only. No contract is awarded. Submit a capabilities statement to get on the agency\'s radar. Lowest commitment.',
  },
};

// notice_type → barrier-to-entry indicator
const BARRIER = {
  'Sources Sought':                 { label: 'EASY ENTRY',    color: '#39FF14' },
  'Presolicitation':                { label: 'EARLY STAGE',   color: '#00E5FF' },
  'Combined Synopsis/Solicitation': { label: 'FAST TRACK',    color: '#FCE300' },
  'Solicitation':                   { label: 'FULL PROPOSAL', color: '#FF6B00' },
};

function scoreColor(s) {
  if (s == null) return 'var(--text-subtle)';
  if (s >= 80) return '#39FF14';
  if (s >= 60) return '#FCE300';
  if (s >= 40) return '#FF6B00';
  return '#FF0055';
}

function scoreBand(s) {
  if (s == null) return '';
  if (s >= 80) return 'band-high';
  if (s >= 60) return 'band-good';
  if (s >= 40) return 'band-mid';
  return 'band-low';
}

function deadlineColor(d) {
  if (d == null) return null;
  if (d <= 7)  return '#FF0055';
  if (d <= 14) return '#FF6B00';
  if (d <= 30) return '#FCE300';
  return '#39FF14';
}

const TD = {
  padding: '8px 10px',
  borderBottom: '1px solid var(--border-dim)',
  verticalAlign: 'middle',
};

export default function OpportunityRow({ opportunity: o, onSelect }) {
  const badge   = TYPE_BADGE[o.notice_type] ?? { bg: 'var(--surface-3)', text: 'var(--text-muted)', tip: '' };
  const barrier = BARRIER[o.notice_type];
  // For pending opps, use combined_score for color; for enriched use ai score
  const displayScore = o.in_pending ? o.combined_score : o.score;
  const sc      = scoreColor(displayScore);
  const band    = scoreBand(displayScore);
  const dlColor = deadlineColor(o.deadline_in_days);
  const expired = o.deadline_in_days != null && o.deadline_in_days < 0;

  let rowStyle;
  if (o.pending_low)  rowStyle = { opacity: 0.5 };
  else if (expired)   rowStyle = { opacity: 0.55 };
  else if (o.in_review) rowStyle = { borderLeft: '2px solid #FF9500' };

  return (
    <tr
      className={`opp-row ${band}${expired ? ' opp-expired' : ''}`}
      onClick={() => onSelect(o)}
      style={rowStyle}
    >
      {/* Posted */}
      <td className="col-hide-mobile" style={TD}>
        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {o.posted_date ?? '—'}
        </span>
      </td>

      {/* Title */}
      <td style={{ ...TD, maxWidth: 280 }}>
        <span title={o.title} style={{
          fontFamily: "'Rajdhani', sans-serif",
          fontWeight: 500,
          fontSize: 13,
          display: 'block',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: expired ? '#c0504d' : 'var(--text)',
          textDecoration: expired ? 'line-through' : 'none',
          textDecorationColor: '#c0504d80',
        }}>
          {o.title ?? '—'}
        </span>
        {expired && (
          <span style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 9,
            letterSpacing: '0.06em',
            color: '#c0504d',
          }}>
            EXPIRED
          </span>
        )}
      </td>

      {/* Agency */}
      <td className="col-hide-mobile" style={{ ...TD, maxWidth: 140 }}>
        <span title={o.agency_full} style={{
          fontFamily: "'Rajdhani', sans-serif",
          fontSize: 12,
          fontWeight: 500,
          color: 'var(--text-muted)',
          display: 'block',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {o.agency_short ?? '—'}
        </span>
      </td>

      {/* Type */}
      <td style={TD}>
        {o.notice_type ? (
          <span
            title={badge.tip}
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700,
              fontSize: 10,
              letterSpacing: '0.06em',
              padding: '2px 7px',
              background: badge.bg,
              color: badge.text,
              clipPath: 'polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 0 100%)',
              whiteSpace: 'nowrap',
              display: 'inline-block',
              cursor: 'help',
            }}
          >
            {o.notice_type.toUpperCase()}
          </span>
        ) : <span style={{ color: 'var(--text-subtle)' }}>—</span>}
      </td>

      {/* Entry barrier */}
      <td className="col-hide-mobile" style={TD}>
        {barrier ? (
          <span style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 700,
            fontSize: 9,
            letterSpacing: '0.07em',
            color: barrier.color,
            textShadow: `0 0 6px ${barrier.color}50`,
            whiteSpace: 'nowrap',
          }}>
            ▸ {barrier.label}
          </span>
        ) : <span style={{ color: 'var(--text-subtle)' }}>—</span>}
      </td>

      {/* Score hex */}
      <td style={TD}>
        {o.in_pending ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div
              className="hex-score"
              style={{
                background: displayScore != null ? `${sc}15` : 'var(--surface-2)',
                color: 'var(--text-subtle)',
                fontSize: 9,
                border: `1px solid var(--border-dim)`,
              }}
            >
              {displayScore ?? '—'}
            </div>
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 9,
              color: o.pending_low ? 'var(--text-subtle)' : 'rgba(252,227,0,0.5)',
              letterSpacing: '0.04em',
            }}>
              {o.pending_low ? '//LOW' : '◈'}
            </span>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div
              className="hex-score"
              style={{
                background: o.score != null ? `${sc}20` : 'var(--surface-2)',
                color: sc,
                textShadow: o.score != null ? `0 0 8px ${sc}` : 'none',
                fontSize: o.score != null ? 11 : 10,
              }}
            >
              {o.score ?? '—'}
            </div>
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 9,
              letterSpacing: '0.04em',
              color: o.ai_generated ? '#39FF14' : '#FF6B00',
              textShadow: o.ai_generated ? '0 0 4px rgba(57,255,20,0.6)' : 'none',
            }}>
              [{o.ai_generated ? 'AI' : 'KW'}]
            </span>
          </div>
        )}
      </td>

      {/* Deadline */}
      <td style={TD}>
        {o.response_deadline ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 11,
              color: expired ? '#c0504d' : (dlColor ?? 'var(--text-muted)'),
              textShadow: !expired && dlColor ? `0 0 6px ${dlColor}60` : 'none',
            }}>
              {o.response_deadline}
            </span>
            {o.deadline_in_days != null && (
              <span style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 9,
                letterSpacing: '0.06em',
                color: expired ? '#c0504d' : (dlColor ?? 'var(--text-subtle)'),
              }}>
                {expired
                  ? `${Math.abs(o.deadline_in_days)}D AGO`
                  : `${o.deadline_in_days}D`}
              </span>
            )}
          </div>
        ) : (
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 11, color: 'var(--text-subtle)' }}>—</span>
        )}
      </td>

      {/* SAM link */}
      <td style={TD} onClick={e => e.stopPropagation()}>
        {o.ui_link ? (
          <a
            href={o.ui_link}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700,
              fontSize: 10,
              letterSpacing: '0.08em',
              color: 'var(--yellow)',
              textDecoration: 'none',
              padding: '3px 8px',
              border: '1px solid rgba(252,227,0,0.3)',
              clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)',
              background: 'var(--yellow-subtle)',
              display: 'inline-block',
              transition: 'all 0.1s ease',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'rgba(252,227,0,0.12)';
              e.currentTarget.style.boxShadow = '0 0 8px rgba(252,227,0,0.3)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'var(--yellow-subtle)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            [→ SAM]
          </a>
        ) : (
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 11, color: 'var(--text-subtle)' }}>—</span>
        )}
      </td>
    </tr>
  );
}