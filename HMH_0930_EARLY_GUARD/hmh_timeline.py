"""Per-target arrival timelines (E1) from public state only.

Counts are per-target upper bounds: each target independently assumes the
side sends everything that can reach it, but the production budget is added
once per target (not once per production site).
"""
from simcore.pipeline import unit_cost


def _units(state, team, kind):
    return {(x,y):n for (x,y,t,k),n in state.units.items() if t == team and k == kind and n > 0}


def w_reach(state, team, geo, cells, horizon):
    """reach[cell][t-1] = team W able to stand on cell after t turns (t=1..horizon)."""
    ws = _units(state,team,'W')
    sites = [state.bases[team]]+[b.pos for b in state.buildings.values()
                                  if b.owner == team and b.btype == 'HOSPITAL']
    budget = state.resources[team]//unit_cost(state,team,'W')
    stations = [b.pos for b in state.buildings.values() if b.owner == team and b.btype == 'STATION']
    tele = max([min(5,n) for p,n in ws.items() if p in stations] or [0]) if len(stations) >= 2 else 0
    result = {}
    for cell in cells:
        row = []
        spawn_d = min((geo.distance(s,cell) for s in sites),default=999)
        for t in range(1,horizon+1):
            n = sum(c for p,c in ws.items() if geo.distance(p,cell) <= t)
            if spawn_d <= t:
                n += budget
            if tele and any(geo.distance(s,cell) <= t-1 for s in stations):
                n += tele
            row.append(n)
        result[cell] = row
    return result


def f_arrival(state, team, geo, cells):
    fs = _units(state,team,'F')
    return {cell:min((geo.distance(p,cell) for p in fs),default=999) for cell in cells}


def defense_demands(state, team, geo, horizon=2, margin=0):
    """Warn early for economic buildings; keep other warning horizons unchanged.

    Returns (pos, need, deadline): `need` W must stand on pos by `deadline`
    turns so that an arriving enemy F dies (W >= enemy W + 1).
    """
    opp = 'K' if team == 'Y' else 'Y'
    owned = [b for b in state.buildings.values() if b.owner == team]
    cells = [b.pos for b in owned]
    fa = f_arrival(state,opp,geo,cells)
    # Economic losses affect all later production. Give distant defenders
    # four turns to arrive, while retaining the policy's existing troop cap.
    warning_horizons = {b.pos: max(4,horizon) if b.btype in ('ENG','HALL') else horizon
                        for b in owned}
    if not cells:
        return []
    reach = w_reach(state,opp,geo,cells,max(warning_horizons.values()))
    demands = []
    for b in owned:
        d = fa[b.pos]
        if d > warning_horizons[b.pos]:
            continue
        t = max(1,d)
        need = reach[b.pos][t-1]+1+margin
        demands.append((b.pos,need,t))
    return demands
