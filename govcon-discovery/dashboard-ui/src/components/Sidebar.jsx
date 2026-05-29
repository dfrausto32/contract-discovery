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

export default function Sidebar({ opportunities, state, actions, isFiltered, activeCount, onClose }) {
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
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
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontFamily: "'Rajdhani', sans-serif", fontWeight: 700,
                fontSize: 11, letterSpacing: '0.08em',
                color: 'var(--text-muted)', padding: 0,
                transition: 'color 0.1s ease',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--yellow)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
            >
              [×]
            </button>
          )}
        </div>
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

      {/* Deadline Band */}
      <FilterSection label="DEADLINE">
        {[
          { value: '0-7',   label: '0 – 7 DAYS',   color: '#FF0055', desc: 'Urgent' },
          { value: '8-14',  label: '8 – 14 DAYS',  color: '#FF6B00', desc: 'Soon' },
          { value: '15-30', label: '15 – 30 DAYS', color: '#FCE300', desc: 'This month' },
          { value: '30+',   label: '30+ DAYS',     color: '#39FF14', desc: 'Plenty of time' },
        ].map(opt => {
          const active = state.deadlineBand === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => actions.setDeadlineBand(opt.value)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: active ? `${opt.color}12` : 'none',
                border: `1px solid ${active ? opt.color : 'rgba(255,255,255,0.06)'}`,
                cursor: 'pointer', padding: '5px 8px', textAlign: 'left', width: '100%',
                clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)',
                transition: 'all 0.1s ease', marginBottom: 5,
                boxShadow: active ? `0 0 8px ${opt.color}30` : 'none',
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.borderColor = `${opt.color}60`; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; }}
            >
              <div style={{ width: 6, height: 6, background: opt.color, flexShrink: 0, boxShadow: active ? `0 0 6px ${opt.color}` : 'none' }} />
              <div>
                <div style={{ fontFamily: "'Rajdhani', sans-serif", fontWeight: 700, fontSize: 10, letterSpacing: '0.08em', color: active ? opt.color : 'var(--text-muted)', textShadow: active ? `0 0 6px ${opt.color}60` : 'none' }}>
                  {opt.label}
                </div>
                <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 9, color: 'var(--text-subtle)', letterSpacing: '0.04em' }}>
                  {opt.desc}
                </div>
              </div>
            </button>
          );
        })}
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
      <div style={{ marginBottom: '1.1rem' }}>
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

      {/* Hide Expired toggle */}
      <FilterSection label="VISIBILITY">
        <button
          onClick={() => actions.setHideExpired(!state.hideExpired)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: state.hideExpired ? 'rgba(255,0,85,0.06)' : 'none',
            border: `1px solid ${state.hideExpired ? 'rgba(255,0,85,0.35)' : 'rgba(255,255,255,0.06)'}`,
            cursor: 'pointer', padding: '5px 8px', textAlign: 'left', width: '100%',
            clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)',
            transition: 'all 0.1s ease', marginBottom: 5,
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(255,0,85,0.35)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = state.hideExpired ? 'rgba(255,0,85,0.35)' : 'rgba(255,255,255,0.06)'; }}
        >
          <div style={{
            width: 6, height: 6, flexShrink: 0,
            background: state.hideExpired ? '#FF0055' : 'var(--text-subtle)',
            boxShadow: state.hideExpired ? '0 0 6px rgba(255,0,85,0.6)' : 'none',
            transition: 'all 0.1s ease',
          }} />
          <div>
            <div style={{ fontFamily: "'Rajdhani', sans-serif", fontWeight: 700, fontSize: 10, letterSpacing: '0.08em', color: state.hideExpired ? '#FF0055' : 'var(--text-muted)' }}>
              HIDE EXPIRED
            </div>
            <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 9, color: 'var(--text-subtle)', letterSpacing: '0.04em' }}>
              past response deadline
            </div>
          </div>
        </button>
      </FilterSection>

      {/* Show Low Signal toggle */}
      <FilterSection label="PENDING OPPS">
        <button
          onClick={() => actions.setShowLowSignal(!state.showLowSignal)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: state.showLowSignal ? 'rgba(252,227,0,0.06)' : 'none',
            border: `1px solid ${state.showLowSignal ? 'rgba(252,227,0,0.3)' : 'rgba(255,255,255,0.06)'}`,
            cursor: 'pointer',
            padding: '5px 8px',
            textAlign: 'left',
            clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)',
            transition: 'all 0.1s ease',
            width: '100%',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(252,227,0,0.3)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = state.showLowSignal ? 'rgba(252,227,0,0.3)' : 'rgba(255,255,255,0.06)'; }}
        >
          <div style={{
            width: 6, height: 6,
            background: state.showLowSignal ? 'var(--yellow)' : 'var(--text-subtle)',
            flexShrink: 0,
            boxShadow: state.showLowSignal ? '0 0 6px rgba(252,227,0,0.6)' : 'none',
            transition: 'all 0.1s ease',
          }} />
          <div>
            <div style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontWeight: 700, fontSize: 10, letterSpacing: '0.08em',
              color: state.showLowSignal ? 'var(--yellow)' : 'var(--text-muted)',
            }}>
              SHOW LOW SIGNAL
            </div>
            <div style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 9, color: 'var(--text-subtle)', letterSpacing: '0.04em',
            }}>
              dims below combined score 65
            </div>
          </div>
        </button>
      </FilterSection>
    </div>
  );
}
