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
