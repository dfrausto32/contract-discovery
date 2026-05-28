import { BARRIER_LABELS } from '../hooks/useFilter.js';

const BARRIER_OPTIONS = [
  { value: 'EASY ENTRY',   label: 'EASY ENTRY',   color: '#39FF14', desc: 'Capabilities statement only' },
  { value: 'EARLY STAGE',  label: 'EARLY STAGE',  color: '#00E5FF', desc: 'Pre-RFP engagement window' },
  { value: 'FAST TRACK',   label: 'FAST TRACK',   color: '#FCE300', desc: 'Combined notice, faster timeline' },
  { value: 'FULL PROPOSAL',label: 'FULL PROPOSAL', color: '#FF6B00', desc: 'Full proposal required' },
];

function FilterSection({ label, children }) {
  return (
    <div style={{ marginBottom: '1.1rem' }}>
      <div className="cp-label" style={{ marginBottom: 7 }}>{label}</div>
      {children}
    </div>
  );
}

export default function Sidebar({ opportunities, state, actions, isFiltered, activeCount }) {
  const types    = [...new Set((opportunities ?? []).map(o => o.notice_type).filter(Boolean))].sort();
  const agencies = [...new Set((opportunities ?? []).map(o => o.agency_group).filter(Boolean))].sort();

  return (
    <div style={{ padding: '1rem 1rem 2rem' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.1rem',
        paddingBottom: '0.6rem',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="cp-label" style={{ fontSize: 11 }}>FILTERS</span>
          {activeCount > 0 && (
            <span style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 10,
              color: 'var(--yellow)',
              textShadow: '0 0 6px rgba(252,227,0,0.6)',
            }}>
              [{activeCount}]
            </span>
          )}
        </div>
        {isFiltered && (
          <button
            onClick={actions.reset}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 600,
              fontSize: 11,
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
              padding: 0,
              transition: 'color 0.1s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--yellow)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            [×] RESET
          </button>
        )}
      </div>

      {/* Search */}
      <FilterSection label="SEARCH">
        <input
          type="search"
          className="cp-input"
          placeholder="TITLE OR AGENCY…"
          value={state.search}
          onChange={e => actions.setSearch(e.target.value)}
        />
      </FilterSection>

      {/* Notice Type */}
      <FilterSection label="NOTICE TYPE">
        <select
          className="cp-input"
          value={state.type}
          onChange={e => actions.setType(e.target.value)}
        >
          <option value="">ALL TYPES</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </FilterSection>

      {/* Agency */}
      <FilterSection label="AGENCY">
        <select
          className="cp-input"
          value={state.agency}
          onChange={e => actions.setAgency(e.target.value)}
        >
          <option value="">ALL AGENCIES</option>
          {agencies.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </FilterSection>

      {/* Entry Barrier */}
      <FilterSection label="ENTRY BARRIER">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {BARRIER_OPTIONS.map(opt => {
            const active = state.barrier === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => actions.setBarrier(active ? '' : opt.value)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  background: active ? `${opt.color}12` : 'none',
                  border: `1px solid ${active ? opt.color : 'rgba(255,255,255,0.06)'}`,
                  cursor: 'pointer',
                  padding: '5px 8px',
                  textAlign: 'left',
                  clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)',
                  transition: 'all 0.1s ease',
                  boxShadow: active ? `0 0 8px ${opt.color}30` : 'none',
                }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.borderColor = `${opt.color}60`; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; }}
              >
                <div style={{
                  width: 6,
                  height: 6,
                  background: opt.color,
                  flexShrink: 0,
                  boxShadow: active ? `0 0 6px ${opt.color}` : 'none',
                }} />
                <div>
                  <div style={{
                    fontFamily: "'Rajdhani', sans-serif",
                    fontWeight: 700,
                    fontSize: 10,
                    letterSpacing: '0.08em',
                    color: active ? opt.color : 'var(--text-muted)',
                    textShadow: active ? `0 0 6px ${opt.color}60` : 'none',
                  }}>
                    {opt.label}
                  </div>
                  <div style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: 9,
                    color: 'var(--text-subtle)',
                    letterSpacing: '0.04em',
                  }}>
                    {opt.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </FilterSection>

      {/* Min Score */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div className="cp-label">MIN SCORE</div>
          <span style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 11,
            color: state.minScore > 0 ? 'var(--yellow)' : 'var(--text-subtle)',
            textShadow: state.minScore > 0 ? '0 0 6px rgba(252,227,0,0.7)' : 'none',
            transition: 'all 0.15s ease',
          }}>
            {state.minScore}
          </span>
        </div>
        <input
          type="range"
          min="0" max="100" step="5"
          value={state.minScore}
          onChange={e => actions.setMinScore(e.target.value)}
          style={{
            background: state.minScore > 0
              ? `linear-gradient(to right, var(--yellow) ${state.minScore}%, var(--border-dim) ${state.minScore}%)`
              : 'var(--border-dim)',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3 }}>
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 9, color: 'var(--text-subtle)' }}>0</span>
          <span style={{ fontFamily: "'Share Tech Mono'", fontSize: 9, color: 'var(--text-subtle)' }}>100</span>
        </div>
      </div>
    </div>
  );
}
