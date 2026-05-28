import OpportunityRow from './OpportunityRow.jsx';

const COLS = [
  { key: 'posted_date',     label: 'POSTED',    sortable: true  },
  { key: 'title',           label: 'TITLE',     sortable: true  },
  { key: 'agency_short',    label: 'AGENCY',    sortable: true  },
  { key: 'notice_type',     label: 'TYPE',      sortable: true  },
  { key: 'barrier_order',   label: 'ENTRY',     sortable: true  },
  { key: 'score',           label: 'SCORE',     sortable: true  },
  { key: 'deadline_in_days',label: 'DEADLINE',  sortable: true  },
  { key: null,              label: 'LINK',      sortable: false },
];

const TH_BASE = {
  padding: '8px 10px',
  textAlign: 'left',
  fontFamily: "'Rajdhani', sans-serif",
  fontWeight: 700,
  fontSize: 10,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  background: 'var(--surface-2)',
  borderBottom: '1px solid var(--yellow)',
  boxShadow: '0 1px 8px rgba(252,227,0,0.08)',
  position: 'sticky',
  top: 0,
  zIndex: 1,
  userSelect: 'none',
  whiteSpace: 'nowrap',
  cursor: 'pointer',
};

export default function OpportunityTable({ rows, total, state, onSort, onSelect }) {
  return (
    <div style={{ paddingTop: '0.75rem' }}>
      {/* Count bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: '0.6rem',
        paddingBottom: '0.5rem',
        borderBottom: '1px solid var(--border-dim)',
      }}>
        <span style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 10,
          letterSpacing: '0.1em',
          color: 'var(--text-muted)',
        }}>
          SHOWING{' '}
          <span style={{
            color: 'var(--yellow)',
            textShadow: '0 0 6px rgba(252,227,0,0.6)',
          }}>{rows.length}</span>
          {' / '}
          {total}
        </span>
        {rows.length < total && (
          <span style={{
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 9,
            fontWeight: 600,
            letterSpacing: '0.1em',
            color: 'var(--text-subtle)',
          }}>
            — FILTERED
          </span>
        )}
      </div>

      {/* Table */}
      <div style={{
        border: '1px solid var(--border)',
        background: 'var(--surface)',
        overflow: 'hidden',
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 820 }}>
            <thead>
              <tr>
                {COLS.map(col => (
                  <th
                    key={col.label}
                    onClick={() => col.sortable && onSort(col.key)}
                    style={{
                      ...TH_BASE,
                      color: state.sortKey === col.key ? 'var(--yellow)' : 'var(--text-muted)',
                      textShadow: state.sortKey === col.key ? '0 0 6px rgba(252,227,0,0.5)' : 'none',
                      cursor: col.sortable ? 'pointer' : 'default',
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {col.sortable && <span style={{ opacity: 0.5, fontSize: 8 }}>//</span>}
                      {col.label}
                      {col.sortable && state.sortKey === col.key && (
                        <span style={{ fontSize: 8, color: 'var(--yellow)' }}>
                          {state.sortDir === 1 ? '▲' : '▼'}
                        </span>
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length > 0 ? (
                rows.map(o => (
                  <OpportunityRow
                    key={o.notice_id}
                    opportunity={o}
                    onSelect={onSelect}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan={8} style={{ padding: '3rem 1rem', textAlign: 'center' }}>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 10,
                    }}>
                      <div style={{
                        fontSize: 32,
                        color: 'var(--yellow)',
                        textShadow: '0 0 20px rgba(252,227,0,0.4)',
                        opacity: 0.4,
                        lineHeight: 1,
                      }}>
                        ◈
                      </div>
                      <div style={{
                        fontFamily: "'Rajdhani', sans-serif",
                        fontWeight: 700,
                        fontSize: 12,
                        letterSpacing: '0.15em',
                        color: 'var(--text-subtle)',
                      }}>
                        NO SIGNAL DETECTED
                      </div>
                      <div style={{
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: 10,
                        color: 'var(--text-subtle)',
                        letterSpacing: '0.06em',
                      }}>
                        ADJUST FILTERS TO RECALIBRATE
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
