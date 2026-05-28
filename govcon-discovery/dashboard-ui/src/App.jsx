import { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import SummaryCards from './components/SummaryCards.jsx';
import Sidebar from './components/Sidebar.jsx';
import OpportunityTable from './components/OpportunityTable.jsx';
import DetailModal from './components/DetailModal.jsx';
import { useFilter } from './hooks/useFilter.js';

function LoadingScreen() {
  return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexDirection: 'column', gap: 16, background: 'var(--bg)',
    }}>
      <div style={{ display: 'flex', gap: 8 }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 8, height: 8,
            background: 'var(--yellow)',
            clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
            boxShadow: '0 0 10px rgba(252,227,0,0.8)',
            animation: 'bounceLoad 1s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
      <div style={{
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 11,
        letterSpacing: '0.15em',
        color: 'var(--text-muted)',
      }}>
        ESTABLISHING FEED…
      </div>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg)',
    }}>
      <div style={{
        padding: '1.5rem 2rem',
        background: 'var(--surface)',
        borderLeft: '3px solid var(--magenta)',
        clipPath: 'polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 0 100%)',
        maxWidth: 380,
      }}>
        <div style={{ fontFamily: "'Rajdhani'", fontWeight: 700, fontSize: 11, letterSpacing: '0.12em', color: 'var(--magenta)', marginBottom: 8 }}>
          // SIGNAL LOST
        </div>
        <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>Cannot load data.json</div>
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 11, color: 'var(--text-muted)' }}>{message}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [data,        setData]        = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);
  const [selectedOpp, setSelectedOpp] = useState(null);

  useEffect(() => {
    fetch('./data.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d  => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const { filtered, state, actions, isFiltered, activeCount } = useFilter(data?.opportunities ?? []);

  if (loading) return <LoadingScreen />;
  if (error)   return <ErrorScreen message={error} />;

  const summary      = data?.summary      ?? {};
  const opportunities = data?.opportunities ?? [];

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <Header summary={summary} loaded />

      {/* Summary strip */}
      <div style={{ flexShrink: 0, borderBottom: '1px solid var(--border-dim)' }}>
        <SummaryCards summary={summary} />
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Sidebar */}
        <aside style={{
          width: 'var(--sidebar-w)',
          flexShrink: 0,
          borderRight: '1px solid var(--border)',
          overflowY: 'auto',
        }}>
          <Sidebar
            opportunities={opportunities}
            state={state}
            actions={actions}
            isFiltered={isFiltered}
            activeCount={activeCount}
          />
        </aside>

        {/* Main */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '0 1.25rem 3rem' }}>
          <OpportunityTable
            rows={filtered}
            total={opportunities.length}
            state={state}
            onSort={actions.setSort}
            onSelect={setSelectedOpp}
          />
        </main>
      </div>

      {selectedOpp && (
        <DetailModal opportunity={selectedOpp} onClose={() => setSelectedOpp(null)} />
      )}
    </div>
  );
}
