import { useState, useEffect, useCallback } from 'react';

const ENRICH_REPO     = 'dfrausto32/contract-discovery';
const ENRICH_BRANCH   = 'contract-discovery';
const ENRICH_WORKFLOW = 'govcon-enrich.yml';

function scoreColor(s) {
  if (s == null) return 'var(--text-subtle)';
  if (s >= 80) return '#39FF14';
  if (s >= 65) return '#FCE300';
  if (s >= 50) return '#FF6B00';
  return '#FF0055';
}

function deadlineLabel(d) {
  if (d == null) return { text: 'NO DEADLINE', color: 'var(--text-subtle)' };
  if (d < 0)  return { text: `EXPIRED ${Math.abs(d)}D AGO`, color: '#c0504d' };
  if (d <= 7)  return { text: `${d}D — URGENT`,  color: '#FF0055' };
  if (d <= 14) return { text: `${d}D — SOON`,    color: '#FF6B00' };
  if (d <= 30) return { text: `${d}D`,            color: '#FCE300' };
  return { text: `${d}D`, color: '#39FF14' };
}

const TYPE_COLOR = {
  'Solicitation':                   '#00E5FF',
  'Combined Synopsis/Solicitation': '#FCE300',
  'Presolicitation':                '#FF6B00',
  'Sources Sought':                 '#A855F7',
};

export default function TriagePanel({ opportunities, onClose, onNeedToken }) {
  const opps = opportunities.filter(o => o.in_pending);

  const [index,      setIndex]      = useState(0);
  const [enrichSet,  setEnrichSet]  = useState(new Set());
  const [dismissSet, setDismissSet] = useState(new Set());
  const [phase,      setPhase]      = useState('triage'); // 'triage' | 'confirm' | 'done'
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  const current = opps[index];
  const total   = opps.length;

  const advance = useCallback(() => {
    if (index < total - 1) setIndex(i => i + 1);
    else setPhase('confirm');
  }, [index, total]);

  const doEnrich  = useCallback(() => { setEnrichSet(s  => new Set([...s,  current.notice_id])); advance(); }, [current, advance]);
  const doDismiss = useCallback(() => { setDismissSet(s => new Set([...s,  current.notice_id])); advance(); }, [current, advance]);
  const doSkip    = useCallback(() => advance(), [advance]);

  useEffect(() => {
    const fn = e => {
      if (phase !== 'triage') return;
      if (e.key === 'y' || e.key === 'Y') doEnrich();
      if (e.key === 'n' || e.key === 'N') doDismiss();
      if (e.key === 's' || e.key === 'S' || e.key === ' ') { e.preventDefault(); doSkip(); }
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [phase, doEnrich, doDismiss, doSkip, onClose]);

  const dispatch = async () => {
    const pat = localStorage.getItem('gh_pat');
    if (!pat) { onNeedToken(); return; }
    setLoading(true);
    setError(null);

    const enrichIds  = [...enrichSet].join(',');
    const dismissIds = [...dismissSet].join(',');

    if (!enrichIds && !dismissIds) { setPhase('done'); setLoading(false); return; }

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
          body: JSON.stringify({
            ref: ENRICH_BRANCH,
            inputs: {
              notice_ids:  enrichIds,
              dismiss_ids: dismissIds,
              limit: '0',
            },
          }),
        }
      );
      if (res.status === 204) {
        setPhase('done');
      } else if (res.status === 401) {
        setError('Token invalid — update via ⚙');
      } else {
        const body = await res.text();
        setError(`GitHub ${res.status}: ${body.slice(0, 100)}`);
      }
    } catch (e) {
      setError(`Network error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const progress = total > 0 ? ((index) / total) * 100 : 0;

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 60,
        background: 'rgba(2,2,4,0.94)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: 'min(640px, 92vw)',
        display: 'flex', flexDirection: 'column', gap: 0,
      }}>
        {/* Header bar */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 12,
        }}>
          <span style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 11, letterSpacing: '0.12em', color: 'var(--yellow)' }}>
            // TRIAGE QUEUE
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {phase === 'triage' && (
              <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-subtle)' }}>
                {index + 1} / {total}
                {enrichSet.size > 0 && <span style={{ color: '#39FF14', marginLeft: 8 }}>✓{enrichSet.size}</span>}
                {dismissSet.size > 0 && <span style={{ color: '#FF0055', marginLeft: 6 }}>✗{dismissSet.size}</span>}
              </span>
            )}
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 11, letterSpacing: '0.08em', color: 'var(--text-muted)', padding: 0 }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--yellow)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
            >[×] CLOSE</button>
          </div>
        </div>

        {/* Progress bar */}
        {phase === 'triage' && (
          <div style={{ height: 2, background: 'var(--border-dim)', marginBottom: 16, position: 'relative' }}>
            <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${progress}%`, background: 'var(--yellow)', boxShadow: '0 0 8px rgba(252,227,0,0.6)', transition: 'width 0.2s ease' }} />
          </div>
        )}

        {/* ── TRIAGE PHASE ── */}
        {phase === 'triage' && total === 0 && (
          <div style={{ textAlign: 'center', fontFamily: "'Share Tech Mono'", fontSize: 12, color: 'var(--text-subtle)', padding: '3rem 0' }}>
            // NO PENDING OPPS TO TRIAGE
          </div>
        )}

        {phase === 'triage' && current && (
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)',
            padding: '1.25rem 1.5rem 1.5rem',
          }}>
            {/* Type badge + score */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              {current.notice_type && (
                <span style={{
                  fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 9, letterSpacing: '0.1em',
                  padding: '2px 7px', background: TYPE_COLOR[current.notice_type] ?? 'var(--surface-3)',
                  color: '#000', clipPath: 'polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 0 100%)',
                }}>
                  {current.notice_type.toUpperCase()}
                </span>
              )}
              {current.combined_score != null && (
                <span style={{
                  fontFamily: "'Share Tech Mono'", fontSize: 10,
                  color: scoreColor(current.combined_score),
                  textShadow: `0 0 8px ${scoreColor(current.combined_score)}80`,
                }}>
                  ◈ {current.combined_score}/100 [S2]
                </span>
              )}
              <span style={{
                fontFamily: "'Share Tech Mono'", fontSize: 10,
                color: deadlineLabel(current.deadline_in_days).color,
              }}>
                {deadlineLabel(current.deadline_in_days).text}
              </span>
            </div>

            {/* Title */}
            <h2 style={{
              fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 18,
              letterSpacing: '0.04em', color: 'var(--text)',
              margin: '0 0 6px', lineHeight: 1.3,
            }}>
              {current.title}
            </h2>

            {/* Agency */}
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-subtle)', marginBottom: 14 }}>
              {current.agency_full || current.agency_short || '—'}
            </div>

            {/* Description excerpt */}
            <div style={{
              borderLeft: '2px solid var(--border)',
              paddingLeft: 12,
              fontFamily: "'Barlow', sans-serif",
              fontSize: 13, color: 'var(--text-muted)',
              lineHeight: 1.65,
              minHeight: 80,
              maxHeight: 180,
              overflowY: 'auto',
            }}>
              {current.description_excerpt || <span style={{ color: 'var(--text-subtle)', fontFamily: "'Share Tech Mono'", fontSize: 10 }}>// NO DESCRIPTION</span>}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button
                onClick={doEnrich}
                style={{
                  flex: 1,
                  fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 13, letterSpacing: '0.1em',
                  padding: '9px 0',
                  background: 'rgba(57,255,20,0.08)', border: '1px solid rgba(57,255,20,0.5)',
                  color: '#39FF14', cursor: 'pointer',
                  clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
                  transition: 'all 0.1s ease', textShadow: '0 0 6px rgba(57,255,20,0.5)',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(57,255,20,0.16)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(57,255,20,0.08)'}
              >
                [ Y — ENRICH ]
              </button>
              <button
                onClick={doSkip}
                style={{
                  flex: '0 0 auto',
                  fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 13, letterSpacing: '0.1em',
                  padding: '9px 18px',
                  background: 'none', border: '1px solid rgba(255,255,255,0.1)',
                  color: 'var(--text-subtle)', cursor: 'pointer',
                  clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
                  transition: 'all 0.1s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.25)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}
              >
                [ S — SKIP ]
              </button>
              <button
                onClick={doDismiss}
                style={{
                  flex: 1,
                  fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 13, letterSpacing: '0.1em',
                  padding: '9px 0',
                  background: 'rgba(255,0,85,0.06)', border: '1px solid rgba(255,0,85,0.4)',
                  color: '#FF0055', cursor: 'pointer',
                  clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
                  transition: 'all 0.1s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,0,85,0.14)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,0,85,0.06)'}
              >
                [ N — DISMISS ]
              </button>
            </div>

            <div style={{ marginTop: 8, textAlign: 'center', fontFamily: "'Share Tech Mono'", fontSize: 9, color: 'var(--text-subtle)', letterSpacing: '0.06em' }}>
              Y = enrich &nbsp;·&nbsp; S / SPACE = skip &nbsp;·&nbsp; N = dismiss
            </div>
          </div>
        )}

        {/* ── CONFIRM PHASE ── */}
        {phase === 'confirm' && (
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)',
            padding: '1.5rem',
          }}>
            <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 12, letterSpacing: '0.12em', color: 'var(--yellow)', marginBottom: 16 }}>
              // TRIAGE COMPLETE
            </div>

            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
              <div style={{ flex: 1, padding: '10px 14px', background: 'rgba(57,255,20,0.06)', border: '1px solid rgba(57,255,20,0.25)', clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)' }}>
                <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 22, color: '#39FF14', textShadow: '0 0 12px rgba(57,255,20,0.6)' }}>{enrichSet.size}</div>
                <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 10, letterSpacing: '0.1em', color: 'rgba(57,255,20,0.7)', marginTop: 2 }}>QUEUED FOR AI</div>
              </div>
              <div style={{ flex: 1, padding: '10px 14px', background: 'rgba(255,0,85,0.06)', border: '1px solid rgba(255,0,85,0.2)', clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)' }}>
                <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 22, color: '#FF0055', textShadow: '0 0 12px rgba(255,0,85,0.5)' }}>{dismissSet.size}</div>
                <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 10, letterSpacing: '0.1em', color: 'rgba(255,0,85,0.7)', marginTop: 2 }}>TO DISMISS</div>
              </div>
              <div style={{ flex: 1, padding: '10px 14px', background: 'var(--surface-2)', border: '1px solid var(--border-dim)', clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)' }}>
                <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 22, color: 'var(--text-muted)' }}>{total - enrichSet.size - dismissSet.size}</div>
                <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 10, letterSpacing: '0.1em', color: 'var(--text-subtle)', marginTop: 2 }}>SKIPPED</div>
              </div>
            </div>

            {enrichSet.size === 0 && dismissSet.size === 0 ? (
              <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 11, color: 'var(--text-subtle)', marginBottom: 16 }}>
                // Nothing to dispatch — all skipped.
              </div>
            ) : (
              <button
                onClick={dispatch}
                disabled={loading}
                style={{
                  width: '100%',
                  fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 13, letterSpacing: '0.12em',
                  padding: '10px 0',
                  background: 'var(--yellow-subtle)', border: '1px solid rgba(252,227,0,0.5)',
                  color: 'var(--yellow)', cursor: loading ? 'wait' : 'pointer',
                  clipPath: 'polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%)',
                  transition: 'all 0.1s ease',
                  textShadow: '0 0 6px rgba(252,227,0,0.4)',
                  marginBottom: error ? 8 : 0,
                }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'rgba(252,227,0,0.12)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'var(--yellow-subtle)'; }}
              >
                {loading ? '…' : '[ DISPATCH ENRICHMENT ]'}
              </button>
            )}

            {error && (
              <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: '#FF6B00', marginTop: 6 }}>⚠ {error}</div>
            )}

            <button onClick={() => { setIndex(0); setPhase('triage'); }} style={{ marginTop: 12, background: 'none', border: 'none', cursor: 'pointer', fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-subtle)', padding: 0, letterSpacing: '0.06em' }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--text-muted)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-subtle)'}
            >
              ← back to triage
            </button>
          </div>
        )}

        {/* ── DONE PHASE ── */}
        {phase === 'done' && (
          <div style={{
            background: 'var(--surface)', border: '1px solid rgba(57,255,20,0.4)',
            clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)',
            padding: '1.5rem', textAlign: 'center',
          }}>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 14, color: '#39FF14', textShadow: '0 0 10px rgba(57,255,20,0.6)', marginBottom: 8, letterSpacing: '0.08em' }}>
              ✓ DISPATCHED
            </div>
            <div style={{ fontFamily: "'Share Tech Mono'", fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              {enrichSet.size > 0 && <div>◈ {enrichSet.size} opps queued for AI enrichment</div>}
              {dismissSet.size > 0 && <div>✗ {dismissSet.size} opps will be dismissed</div>}
              <div style={{ marginTop: 8, color: 'var(--text-subtle)' }}>Dashboard updates in ~5 min</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
