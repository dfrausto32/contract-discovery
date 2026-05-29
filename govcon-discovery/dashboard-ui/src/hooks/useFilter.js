import { useState, useMemo } from 'react';

const INITIAL = {
  search: '',
  type: '',
  agency: '',
  minScore: 0,
  barrier: '',
  showLowSignal: false,
  hideExpired: true,
  sortKey: 'posted_date',
  sortDir: -1,
};

// Maps notice_type → barrier sort order (1 = easiest to pursue)
const BARRIER_ORDER = {
  'Sources Sought':                 1,
  'Presolicitation':                2,
  'Combined Synopsis/Solicitation': 3,
  'Solicitation':                   4,
};

export const BARRIER_LABELS = {
  'Sources Sought':                 'EASY ENTRY',
  'Presolicitation':                'EARLY STAGE',
  'Combined Synopsis/Solicitation': 'FAST TRACK',
  'Solicitation':                   'FULL PROPOSAL',
};

function barrierOrder(notice_type) {
  return BARRIER_ORDER[notice_type] ?? 5;
}

export function useFilter(opportunities) {
  const [state, setState] = useState(INITIAL);

  const actions = {
    setSearch:   (v) => setState(s => ({ ...s, search: v })),
    setType:     (v) => setState(s => ({ ...s, type: v })),
    setAgency:   (v) => setState(s => ({ ...s, agency: v })),
    setMinScore: (v) => setState(s => ({ ...s, minScore: Number(v) })),
    setBarrier:      (v) => setState(s => ({ ...s, barrier: v })),
    setShowLowSignal:(v) => setState(s => ({ ...s, showLowSignal: v })),
    setHideExpired:  (v) => setState(s => ({ ...s, hideExpired: v })),
    setSort:     (key) => setState(s => ({
      ...s,
      sortKey: key,
      sortDir: s.sortKey === key ? s.sortDir * -1 : -1,
    })),
    reset: () => setState(INITIAL),
  };

  const filtered = useMemo(() => {
    let result = (opportunities || []).filter(o => {
      if (state.type    && o.notice_type  !== state.type)   return false;
      if (state.agency  && o.agency_group !== state.agency)  return false;
      // For pending opps, compare against combined_score; otherwise ai score
      const effectiveScore = o.in_pending ? (o.combined_score ?? 0) : (o.score ?? 0);
      if (effectiveScore < state.minScore)                   return false;
      if (state.barrier && BARRIER_LABELS[o.notice_type] !== state.barrier) return false;
      // Hide expired opps unless toggle is off
      if (state.hideExpired && o.deadline_in_days != null && o.deadline_in_days < 0) return false;
      // Hide low-signal pending rows unless toggle is on
      if (!state.showLowSignal && o.pending_low)             return false;
      if (state.search) {
        const q   = state.search.toLowerCase();
        const hay = `${o.title} ${o.agency_short} ${o.agency_full}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    const { sortKey: k, sortDir: dir } = state;
    return result.slice().sort((a, b) => {
      let x, y;
      if (k === 'barrier_order') {
        x = barrierOrder(a.notice_type);
        y = barrierOrder(b.notice_type);
      } else {
        x = a[k]; y = b[k];
      }
      if (x == null) return 1;
      if (y == null) return -1;
      if (typeof x === 'string') { x = x.toLowerCase(); y = String(y).toLowerCase(); }
      return x < y ? -dir : x > y ? dir : 0;
    });
  }, [opportunities, state]);

  const isFiltered = !!(state.search || state.type || state.agency || state.minScore > 0 || state.barrier || state.showLowSignal || !state.hideExpired);
  const activeCount = [state.search, state.type, state.agency, state.minScore > 0 ? '_' : '', state.barrier, state.showLowSignal ? '_' : '']
    .filter(Boolean).length;

  return { filtered, state, actions, isFiltered, activeCount };
}
