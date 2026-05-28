import { useState, useMemo } from 'react';

const INITIAL = {
  search: '',
  type: '',
  agency: '',
  minScore: 0,
  sortKey: 'posted_date',
  sortDir: -1,
};

export function useFilter(opportunities) {
  const [state, setState] = useState(INITIAL);

  const actions = {
    setSearch:   (v) => setState(s => ({ ...s, search: v })),
    setType:     (v) => setState(s => ({ ...s, type: v })),
    setAgency:   (v) => setState(s => ({ ...s, agency: v })),
    setMinScore: (v) => setState(s => ({ ...s, minScore: Number(v) })),
    setSort:     (key) => setState(s => ({
      ...s,
      sortKey: key,
      sortDir: s.sortKey === key ? s.sortDir * -1 : -1,
    })),
    reset: () => setState(INITIAL),
  };

  const filtered = useMemo(() => {
    let result = (opportunities || []).filter(o => {
      if (state.type   && o.notice_type  !== state.type)   return false;
      if (state.agency && o.agency_group !== state.agency)  return false;
      if ((o.score ?? 0) < state.minScore)                  return false;
      if (state.search) {
        const q   = state.search.toLowerCase();
        const hay = `${o.title} ${o.agency_short} ${o.agency_full}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    const { sortKey: k, sortDir: dir } = state;
    return result.slice().sort((a, b) => {
      let x = a[k], y = b[k];
      if (x == null) return 1;
      if (y == null) return -1;
      if (typeof x === 'string') { x = x.toLowerCase(); y = String(y).toLowerCase(); }
      return x < y ? -dir : x > y ? dir : 0;
    });
  }, [opportunities, state]);

  const isFiltered = !!(state.search || state.type || state.agency || state.minScore > 0);
  const activeCount = [state.search, state.type, state.agency, state.minScore > 0 ? '_' : '']
    .filter(Boolean).length;

  return { filtered, state, actions, isFiltered, activeCount };
}
