import { useState } from 'react';

const REPO   = 'dfrausto32/contract-discovery';
const BRANCH = 'contract-discovery';
const WORKFLOW = 'govcon-verdict.yml';

export default function VerdictButtons({ noticeId, onNeedToken }) {
  const stored = localStorage.getItem(`verdict_${noticeId}`);
  const [submitted, setSubmitted] = useState(stored || null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

  const submit = async (verdict) => {
    const pat = localStorage.getItem('gh_pat');
    if (!pat) {
      onNeedToken?.();
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${pat}`,
            'Content-Type': 'application/json',
            Accept: 'application/vnd.github+json',
          },
          body: JSON.stringify({
            ref: BRANCH,
            inputs: { notice_id: noticeId, verdict },
          }),
        }
      );

      if (res.status === 204) {
        localStorage.setItem(`verdict_${noticeId}`, verdict);
        setSubmitted(verdict);
      } else if (res.status === 401) {
        setError('Token invalid or expired — update it via the ⚙ settings button.');
      } else {
        const body = await res.text();
        setError(`GitHub API error ${res.status}: ${body.slice(0, 120)}`);
      }
    } catch (e) {
      setError(`Network error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    const isYes = submitted === 'yes';
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 12px',
        background: isYes ? 'rgba(57,255,20,0.08)' : 'rgba(255,0,85,0.06)',
        border: `1px solid ${isYes ? 'rgba(57,255,20,0.3)' : 'rgba(255,0,85,0.2)'}`,
        clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
      }}>
        <span style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 11,
          color: isYes ? '#39FF14' : '#FF0055',
          letterSpacing: '0.08em',
        }}>
          {isYes ? '✓ PURSUIT QUEUED' : '✗ PASSED'}
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-subtle)', fontFamily: "'Share Tech Mono'" }}>
          — dashboard updates after workflow completes (~2 min)
        </span>
      </div>
    );
  }

  return (
    <div>
      <div style={{
        fontFamily: "'Rajdhani', sans-serif",
        fontWeight: 700, fontSize: 10,
        letterSpacing: '0.1em', color: 'var(--text-subtle)',
        marginBottom: 8,
      }}>
        // PURSUE THIS OPPORTUNITY?
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          onClick={() => submit('yes')}
          disabled={loading}
          style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 700, fontSize: 12,
            letterSpacing: '0.1em',
            padding: '6px 20px',
            background: 'rgba(57,255,20,0.08)',
            border: '1px solid rgba(57,255,20,0.5)',
            color: '#39FF14',
            cursor: loading ? 'wait' : 'pointer',
            clipPath: 'polygon(0 0, calc(100% - 7px) 0, 100% 7px, 100% 100%, 0 100%)',
            transition: 'all 0.1s ease',
            textShadow: '0 0 6px rgba(57,255,20,0.5)',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'rgba(57,255,20,0.18)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(57,255,20,0.08)'; }}
        >
          {loading ? '…' : '[ YES — PURSUE ]'}
        </button>

        <button
          onClick={() => submit('no')}
          disabled={loading}
          style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 700, fontSize: 12,
            letterSpacing: '0.1em',
            padding: '6px 20px',
            background: 'rgba(255,0,85,0.06)',
            border: '1px solid rgba(255,0,85,0.35)',
            color: '#FF0055',
            cursor: loading ? 'wait' : 'pointer',
            clipPath: 'polygon(0 0, calc(100% - 7px) 0, 100% 7px, 100% 100%, 0 100%)',
            transition: 'all 0.1s ease',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'rgba(255,0,85,0.14)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,0,85,0.06)'; }}
        >
          {loading ? '…' : '[ NO — PASS ]'}
        </button>
      </div>

      {error && (
        <div style={{
          marginTop: 8,
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 10,
          color: '#FF6B00',
          letterSpacing: '0.04em',
        }}>
          ⚠ {error}
        </div>
      )}
    </div>
  );
}
