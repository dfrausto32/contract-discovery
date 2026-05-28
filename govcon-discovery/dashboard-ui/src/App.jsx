import { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import SummaryCards from './components/SummaryCards.jsx';
import Sidebar from './components/Sidebar.jsx';
import OpportunityTable from './components/OpportunityTable.jsx';
import DetailModal from './components/DetailModal.jsx';
import { useFilter } from './hooks/useFilter.js';

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);
  useEffect(() => {
    const fn = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', fn);
    return () => window.removeEventListener('resize', fn);
  }, []);
  return isMobile;
}

function LoadingScreen() {
  return (
    <div style={{
      height: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center',
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
      height: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center',
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    fetch('./data.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d  => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  // Close sidebar when switching to desktop
  useEffect(() => { if (!isMobile) setSidebarOpen(false); }, [isMobile]);

  const { filtered, state, actions, isFiltered, activeCount } = useFilter(data?.opportunities ?? []);

  if (loading) return <LoadingScreen />;
  if (error)   return <ErrorScreen message={error} />;

  const summary       = data?.summary      ?? {};
  const opportunities = data?.opportunities ?? [];

  return (
    <div style={{
      height: isMobile ? 'auto' : '100vh',
      minHeight: isMobile ? '100dvh' : undefined,
      display: 'flex',
      flexDirection: 'column',
      overflow: isMobile ? 'visible' : 'hidden',
    }}>
      <Header summary={summary} loaded />

      {/* Summary strip */}
      <div style={{ flexShrink: 0, borderBottom: '1px solid var(--border-dim)' }}>
        <SummaryCards summary={summary} />
      </div>

      {/* Body */}
      <div style={{
        flex: 1,
        display: 'flex',
        overflow: isMobile ? 'visible' : 'hidden',
        position: 'relative',
      }}>
        {/* Mobile backdrop */}
        {isMobile && sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(6,6,8,0.75)',
              zIndex: 29,
              animation: 'backdropIn 0.2s ease forwards',
            }}
          />
        )}

        {/* Sidebar — always visible on desktop, drawer on mobile */}
        <aside
          className={isMobile ? `sidebar-mobile${sidebarOpen ? ' sidebar-open' : ''}` : undefined}
          style={isMobile ? undefined : {
            width: 'var(--sidebar-w)',
            flexShrink: 0,
            borderRight: '1px solid var(--border)',
            overflowY: 'auto',
          }}
        >
          <Sidebar
            opportunities={opportunities}
            state={state}
            actions={actions}
            isFiltered={isFiltered}
            activeCount={activeCount}
            onClose={isMobile ? () => setSidebarOpen(false) : undefined}
          />
        </aside>

        {/* Main content */}
        <main style={{
          flex: 1,
          overflowY: isMobile ? 'visible' : 'auto',
          padding: isMobile ? '0 0.75rem 3rem' : '0 1.25rem 3rem',
          minWidth: 0,
        }}>
          {/* Mobile filter toggle */}
          {isMobile && (
            <div style={{
              position: 'sticky',
              top: 'var(--header-h)',
              zIndex: 10,
              background: 'var(--bg)',
              paddingTop: '0.5rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid var(--border-dim)',
              marginBottom: '0.5rem',
            }}>
              <button
                onClick={() => setSidebarOpen(true)}
                style={{
                  background: activeCount > 0 ? 'var(--yellow-subtle)' : 'none',
                  border: `1px solid ${activeCount > 0 ? 'rgba(252,227,0,0.4)' : 'rgba(255,255,255,0.08)'}`,
                  color: activeCount > 0 ? 'var(--yellow)' : 'var(--text-muted)',
                  fontFamily: "'Rajdhani', sans-serif",
                  fontWeight: 700,
                  fontSize: 11,
                  letterSpacing: '0.1em',
                  padding: '6px 14px',
                  cursor: 'pointer',
                  clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  textShadow: activeCount > 0 ? '0 0 6px rgba(252,227,0,0.5)' : 'none',
                }}
              >
                <span style={{ opacity: 0.6, fontSize: 9 }}>//</span>
                FILTERS
                {activeCount > 0 && (
                  <span style={{ color: 'var(--yellow)', textShadow: '0 0 6px rgba(252,227,0,0.8)' }}>
                    [{activeCount}]
                  </span>
                )}
              </button>
            </div>
          )}

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
