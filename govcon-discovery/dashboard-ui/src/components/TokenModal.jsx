import { useState } from 'react';

export default function TokenModal({ onClose }) {
  const [val, setVal] = useState(localStorage.getItem('gh_pat') || '');
  const [saved, setSaved] = useState(false);

  const save = () => {
    if (val.trim()) {
      localStorage.setItem('gh_pat', val.trim());
      setSaved(true);
      setTimeout(() => onClose(), 800);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(2,2,4,0.92)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: 'min(480px, 90vw)',
          background: 'var(--surface)',
          border: '1px solid var(--yellow)',
          clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)',
          boxShadow: '0 0 40px rgba(252,227,0,0.12)',
          padding: '1.5rem 1.5rem 1.75rem',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <span style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 700, fontSize: 13,
            letterSpacing: '0.12em', color: 'var(--yellow)',
          }}>
            // GITHUB TOKEN SETUP
          </span>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', fontFamily: "'Rajdhani'",
            fontWeight: 700, fontSize: 12, letterSpacing: '0.08em',
          }}>
            [×]
          </button>
        </div>

        <p style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 11, color: 'var(--text-muted)',
          letterSpacing: '0.04em', lineHeight: 1.6,
          marginBottom: '1rem',
        }}>
          Enter a GitHub Personal Access Token with <strong style={{ color: 'var(--text)' }}>workflow</strong> scope
          to enable YES / NO decisions from this dashboard.
          The token is stored in your browser only — never sent to any server.
        </p>

        <a
          href="https://github.com/settings/tokens/new?scopes=workflow&description=GovCon+Dashboard"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            fontFamily: "'Share Tech Mono'", fontSize: 10,
            color: 'var(--cyan)', letterSpacing: '0.06em',
            marginBottom: '1rem', textDecoration: 'underline',
          }}
        >
          Create a token on GitHub →
        </a>

        <input
          type="password"
          className="cp-input"
          placeholder="ghp_xxxxxxxxxxxx"
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && save()}
          style={{ width: '100%', boxSizing: 'border-box', marginBottom: '0.75rem' }}
          autoFocus
        />

        <button
          onClick={save}
          disabled={!val.trim()}
          style={{
            width: '100%',
            fontFamily: "'Rajdhani', sans-serif",
            fontWeight: 700, fontSize: 12,
            letterSpacing: '0.1em',
            padding: '8px 0',
            background: saved ? 'rgba(57,255,20,0.12)' : 'var(--yellow-subtle)',
            border: `1px solid ${saved ? '#39FF14' : 'rgba(252,227,0,0.5)'}`,
            color: saved ? '#39FF14' : 'var(--yellow)',
            cursor: val.trim() ? 'pointer' : 'not-allowed',
            clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
            transition: 'all 0.15s ease',
          }}
        >
          {saved ? '✓ SAVED' : 'SAVE TOKEN'}
        </button>
      </div>
    </div>
  );
}
