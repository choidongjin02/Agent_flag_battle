"""Global capture assignment and joint destination-level F/W allocation."""
import math
from collections import defaultdict
from hmh_actions import Plan
from hmh_geometry import assignment
from simcore.pipeline import unit_cost


def enemy(team):
    return 'K' if team == 'Y' else 'Y'


def units(state, team, kind):
    return {(x,y):n for (x,y,t,k),n in state.units.items() if t == team and k == kind and n > 0}


def value(state, team, b, profile='balanced'):
    horizon = min(1.,max(0,160-state.turn)/24)
    owns = {q.btype for q in state.buildings.values() if q.owner == team}
    bonus = 0
    if b.btype == 'ENG' and 'ENG' not in owns:
        bonus = 20
    elif b.btype == 'HALL':
        bonus = 15
    elif b.btype == 'HOSPITAL':
        bonus = 13
    elif b.btype == 'LIBRARY' and 'LIBRARY' not in owns:
        bonus = 5
    elif b.btype == 'DEPOT' and team not in state.depot_claimed.get(b.id,set()):
        bonus = 9
    elif b.btype == 'STATION':
        bonus = 4 if 'STATION' in owns else 2
    if profile == 'economy':
        bonus *= 1.35
    score = 8*b.score + bonus*horizon
    return score*(1.25 if b.owner == enemy(team) else 1)


def threat(state, team, geo):
    """Per-cell upper envelopes, NOT a simultaneous joint opponent move."""
    reach = defaultdict(int)
    ew = units(state,team,'W')
    stations = {b.pos for b in state.buildings.values() if b.owner == team and b.btype == 'STATION'}
    for src,n in ew.items():
        for dst in [src]+geo.adj[src]:
            reach[dst] += n
    for dst in stations:
        if len(stations) >= 2:
            reach[dst] += max([min(5,n) for src,n in ew.items()
                               if src in stations and src != dst and dst not in geo.adj[src]] or [0])
    spawn_cells = set()
    sites = [state.bases[team]]+[b.pos for b in state.buildings.values() if b.owner == team and b.btype == 'HOSPITAL']
    for site in sites:
        spawn_cells.update([site]+geo.adj[site])
    budget = state.resources[team]//unit_cost(state,team,'W')
    for dst in spawn_cells:
        reach[dst] += budget
    return reach


def build(state, team, geo, profile='balanced', old_goals=(), forecast=None):
    plan = Plan(state,team,geo)
    opp,base = enemy(team),state.bases[team]
    key = lambda p: geo.key(p,base)
    buildings = sorted(state.buildings.values(),key=lambda b:key(b.pos))
    at = {b.pos:b for b in buildings}
    targets = [b for b in buildings if b.owner != team]
    ef,ew = units(state,opp,'F'),units(state,opp,'W')
    envelope = threat(state,opp,geo)
    risk = envelope if forecast is None else {p:math.ceil(.25*envelope.get(p,0)+.75*forecast.get(p,0))
                                             for p in set(envelope)|set(forecast)}
    own_f = sum(units(state,team,'F').values())
    own_w = sum(units(state,team,'W').values())
    sites = sorted({base}|{b.pos for b in buildings if b.owner == team and b.btype == 'HOSPITAL'},key=key)
    wanted = min(7,max(2,len(targets)))
    if profile == 'raid':
        wanted = min(4,wanted)
    if state.turn >= 150:
        wanted = min(wanted,own_f+1)
    viable = [b for b in targets if any(geo.distance(s,b.pos) <= 160-state.turn for s in sites)]
    extra = min(max(0,wanted-own_f),plan.resource//5) if viable else 0
    if own_f >= 3 and state.turn > 2:
        extra = min(extra,1)
    for _ in range(extra):
        f_here = plan.projected('F')
        def spawn_value(site):
            best = max((value(state,team,b,profile)/(3+geo.distance(site,b.pos))
                        - 1.2*sum(1 for p,n in f_here.items() if geo.distance(p,b.pos) <= geo.distance(site,b.pos))
                        for b in viable),default=0)
            return best-2*max(0,risk.get(site,0)-plan.support(site))
        plan.spawn('F',1,max(sites,key=spawn_value))
    slots = [p for p,n in sorted(plan.projected('F').items(),key=lambda a:key(a[0])) for _ in range(min(n,17))][:17]
    defend = [b for b in buildings if b.owner == team and any(geo.distance(p,b.pos) <= 2 for p in ef)]
    tasks = targets+defend
    previous = defaultdict(list)
    for pos,bid in old_goals:
        previous[tuple(pos)].append(bid)
    costs = []
    for src in slots:
        row = []
        for b in tasks:
            d = geo.distance(src,b.pos)
            score = value(state,team,b,profile)/(3+d)
            if b.owner == team:
                score *= .55
            if d > 160-state.turn:
                score = -1000
            score -= .6*max(0,ew.get(b.pos,0)-own_w)/(1+d)
            if b.id in previous[src]:
                score += .65
            if src == b.pos and b.owner != team:
                score += 2
            row.append(score)
        costs.append(row+[0.]*len(slots))
    matched = assignment(costs)
    jobs = [(src,tasks[j] if j < len(tasks) else None) for src,j in zip(slots,matched)]
    lib = any(b.owner == team and b.btype == 'LIBRARY' for b in buildings)
    capture_reserve = sum(max(1,(4 if b.btype == 'PLAZA' else 2)-int(lib))
                          for src,b in jobs if b and b.owner != team and geo.distance(src,b.pos) <= 1)
    spendable = min(plan.resource,max(0,plan.resource+10-capture_reserve))
    nw = spendable//unit_cost(state,team,'W')
    if nw:
        fronts = [b.pos for src,b in jobs if b is not None]+list(ef)
        def site_value(site):
            distances = sorted(geo.distance(site,p) for p in fronts)
            dist = sum(distances[:3])/max(1,min(3,len(distances)))
            return -dist+3*sum(1 for p in ef if geo.distance(site,p) <= 2)
        site = max(sites,key=site_value)
        for loc in sorted(sites,key=lambda p:-(risk.get(p,0)-plan.support(p))):
            if loc == site or not nw:
                continue
            deficit = risk.get(loc,0)-plan.support(loc)
            if deficit > 0 and any(geo.distance(loc,p) <= 1 for p in plan.projected('F')):
                n = min(nw,deficit)
                plan.spawn('W',n,loc)
                nw -= n
        plan.spawn('W',nw,site)
    jobs.sort(key=lambda job:-(value(state,team,job[1],profile)/(1+geo.distance(job[0],job[1].pos))
                              if job[1] else 0))
    assigned_dest = set()
    for src,b in jobs:
        if plan.pool.get((*src,'F'),0) <= 0:
            continue
        goal = b.pos if b else src
        def endpoint(dst):
            need,support = risk.get(dst,0),plan.support(dst)
            if src != dst and dst not in geo.adj[src]:
                support = plan.arrivals.get((*dst,'W'),0)+sum(n for (x,y,k),n in plan.pool.items()
                          if k == 'W' and ((x,y) == dst or dst in geo.adj[(x,y)]))
            score = -1.5*geo.distance(dst,goal)-12*max(0,need-support)-.12*need
            if dst in assigned_dest:
                score -= 1.0
            if dst == goal and b and b.owner != team:
                score += 2
            if dst == src and b and b.owner != team and dst == goal:
                score += 1
            if dst in ef and support <= ew.get(dst,0):
                score -= 2
            return score
        dst = max(plan.options(src),key=endpoint)
        need = risk.get(dst,0)
        if dst in ef:
            need = max(need,ew.get(dst,0)+1)
        plan.send(src,'F',1,dst)
        if plan.support(dst) >= need:
            plan.escort(dst,need)
        assigned_dest.add(dst)
        if b:
            plan.goals.append((dst,b.id))
    for (x,y,k),n in list(plan.pool.items()):
        if k == 'F' and n > 0:
            src = (x,y)
            dst = min(geo.choices(src,base),key=lambda p:(max(0,risk.get(p,0)-plan.support(p)),p != src))
            plan.send(src,'F',n,dst)
    for b in sorted(defend,key=lambda b:-value(state,team,b)):
        if any(geo.distance(p,b.pos) <= 1 for p in ef):
            need = risk.get(b.pos,0)+1
            if plan.support(b.pos) >= need:
                plan.escort(b.pos,need)
    attack_tasks = []
    for p,n in ef.items():
        b = at.get(p)
        gain = 18+min(n,4)*3+(value(state,team,b)*.5 if b else 0)
        attack_tasks.append((p,gain*(1.45 if profile == 'raid' else 1)))
    for src,b in jobs:
        if b:
            attack_tasks.append((b.pos,12+value(state,team,b)*.35))
    for b in defend:
        attack_tasks.append((b.pos,20+value(state,team,b)*.6))
    if not attack_tasks:
        attack_tasks = [(b.pos,value(state,team,b)) for b in targets] or [(base,1)]
    committed = defaultdict(int)
    sources = sorted([(x,y) for (x,y,k),n in plan.pool.items() if k == 'W' and n > 0],key=key)
    for src in sources:
        n = plan.pool.get((*src,'W'),0)
        if not n:
            continue
        target = max(attack_tasks,key=lambda task: task[1]/(2+geo.distance(src,task[0]))
                     -.15*max(0,committed[task[0]]-envelope.get(task[0],0)-4))[0]
        dst = min(plan.options(src),key=lambda p:(geo.distance(p,target),p != target,key(p)))
        committed[target] += n
        if src != dst and dst not in geo.adj[src]:
            moved = min(n,5)
            plan.send(src,'W',moved,dst)
            n -= moved
            if n:
                nxt = min(geo.choices(src,base),key=lambda p:(geo.distance(p,target),key(p)))
                plan.send(src,'W',n,nxt)
        else:
            plan.send(src,'W',n,dst)
    for (x,y,k),n in list(plan.pool.items()):
        if k == 'S' and n:
            src = (x,y)
            dst = min(geo.choices(src,base),key=lambda p:(risk.get(p,0),geo.distance(p,base)))
            plan.send(src,k,n,dst)
    projected_f = plan.projected('F')
    caps = [b for b in buildings if b.owner != team and projected_f.get(b.pos,0)]
    plan.priority = [b.pos for b in sorted(caps,key=lambda b:-value(state,team,b,profile))]
    return plan


def evaluate(state, team, geo):
    """Lexicographic terminal objective. Hidden scores stay estimated in rollouts."""
    opp = enemy(team)
    scores = {t:sum(b.score for b in state.buildings.values() if b.owner == t) for t in (team,opp)}
    total = sum(b.score for b in state.buildings.values())
    if scores[opp] == 0 and scores[team]*2 > total:
        return 100000.
    if scores[team] == 0 and scores[opp]*2 > total:
        return -100000.
    if state.turn >= 160:
        material = {t:sum(n*{'F':5,'W':3,'S':2}[k] for (x,y,s,k),n in state.units.items() if s == t) for t in (team,opp)}
        a = (scores[team],state.occupation_score_turns[team],material[team])
        b = (scores[opp],state.occupation_score_turns[opp],material[opp])
        return 100000. if a > b else -100000. if a < b else 0.
    remaining = 160-state.turn
    future = min(1.,remaining/20)
    def side(t):
        fs,ws = units(state,t,'F'),units(state,t,'W')
        ef = units(state,enemy(t),'F')
        result = 8*scores[t]+.22*state.resources[t]+.70*sum(ws.values())+3.5*min(9,sum(fs.values()))
        owned = [b for b in state.buildings.values() if b.owner == t]
        kinds = {b.btype for b in owned}
        result += future*(20*('ENG' in kinds)+15*sum(b.btype == 'HALL' for b in owned)
                          +10*sum(b.btype == 'HOSPITAL' for b in owned)+4*('LIBRARY' in kinds))
        for b in state.buildings.values():
            if b.owner != t and fs:
                d = min(geo.distance(p,b.pos) for p in fs)
                if d <= remaining:
                    result += .70*value(state,t,b)/(2+d)
        for p,n in ws.items():
            if ef:
                d = min(geo.distance(p,q) for q in ef)
                result += .12*min(n,20)*max(0,10-d)/10
        ew = units(state,enemy(t),'W')
        for p,n in fs.items():
            nearby = max([w for q,w in ew.items() if geo.distance(q,p) <= 1] or [0])
            if nearby > ws.get(p,0):
                result -= min(n,3)*2
        return result
    return side(team)-side(opp)
