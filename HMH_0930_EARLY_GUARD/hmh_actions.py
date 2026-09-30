"""Shared production, source-pool and TELE reservations."""
from collections import defaultdict
from simcore.commands import Spawn, Move, Tele, Priority
from simcore.pipeline import unit_cost


class Plan:
    def __init__(self, state, team, geo):
        self.state, self.team, self.geo = state, team, geo
        self.base = state.bases[team]
        self.pool = {(x,y,k): n for (x,y,t,k),n in state.units.items() if t == team}
        self.arrivals = defaultdict(int)
        self.resource = state.resources[team]
        self.spawns, self.moves, self.priority = [], [], []
        self.goals = []
        self.tele_used = False
        self.moving = False
        self._commands = None
        self.stations = {b.pos for b in state.buildings.values() if b.owner == team and b.btype == 'STATION'}

    def spawn(self, kind, n, pos):
        self._commands = None
        assert not self.moving
        valid = pos == self.base or any(b.pos == pos and b.owner == self.team and b.btype == 'HOSPITAL'
                                         for b in self.state.buildings.values())
        assert valid
        cost = unit_cost(self.state, self.team, kind)
        n = min(n, self.resource//cost)
        if n > 0:
            self.resource -= cost*n
            self.pool[(*pos,kind)] = self.pool.get((*pos,kind),0)+n
            self.spawns.append(Spawn(kind,n) if pos == self.base else Spawn(kind,n,*pos))
        return n

    def reachable(self, src, dst):
        return src == dst or dst in self.geo.adj[src] or (
            not self.tele_used and src in self.stations and dst in self.stations)

    def options(self, src):
        opts = self.geo.choices(src, self.base)
        if not self.tele_used and src in self.stations:
            opts += sorted(self.stations-set(opts),key=lambda p:self.geo.key(p,self.base))
        return opts

    def send(self, src, kind, n, dst):
        self._commands = None
        self.moving = True
        key = (*src,kind)
        assert 0 <= n <= self.pool.get(key,0) and self.reachable(src,dst)
        if not n:
            return
        self.pool[key] -= n
        self.arrivals[(*dst,kind)] += n
        if src == dst:
            return
        if dst not in self.geo.adj[src]:
            assert n <= 5 and not self.tele_used
            self.tele_used = True
            self.moves.append(Tele(*src,kind,n,*dst))
        else:
            dx,dy = dst[0]-src[0],dst[1]-src[1]
            direction = {(0,-1):'U',(0,1):'D',(-1,0):'L',(1,0):'R'}[(dx,dy)]
            self.moves.append(Move(*src,kind,n,direction))

    def support(self, dst):
        # At most ONE remote station source may use TELE.
        direct, remote = 0, 0
        for (x,y,k),n in self.pool.items():
            if k != 'W' or n <= 0:
                continue
            src = (x,y)
            if src == dst or dst in self.geo.adj[src]:
                direct += n
            elif self.reachable(src,dst):
                remote = max(remote,min(5,n))
        return direct+remote+self.arrivals.get((*dst,'W'),0)

    def escort(self, dst, need):
        need = max(0,need-self.arrivals.get((*dst,'W'),0))
        sources = sorted([(x,y) for (x,y,k),n in self.pool.items() if k == 'W' and n > 0],
                         key=lambda s:(s != dst, self.geo.distance(s,dst),self.geo.key(s,self.base)))
        for src in sources:
            if not need:
                break
            if self.reachable(src,dst):
                n = min(need,self.pool[(*src,'W')])
                if src != dst and dst not in self.geo.adj[src]:
                    n = min(n,5)
                self.send(src,'W',n,dst)
                need -= n
        return need == 0

    def commands(self):
        # Plans are frozen after build() returns.
        if self._commands is not None:
            return self._commands
        # Same source/kind/direction splits are merged into one line.
        merged, index = [], {}
        for c in self.moves:
            if isinstance(c,Move):
                k = (c.x,c.y,c.kind,c.direction)
                if k in index:
                    merged[index[k]] = Move(c.x,c.y,c.kind,merged[index[k]].count+c.count,c.direction)
                    continue
                index[k] = len(merged)
            merged.append(c)
        self._commands = self.spawns+merged+([Priority(self.priority)] if self.priority else [])
        return self._commands

    def texts(self):
        result = []
        for c in self.commands():
            if isinstance(c,Spawn):
                result.append(f'SPAWN {c.kind} {c.count}'+(f' {c.x} {c.y}' if c.x is not None else ''))
            elif isinstance(c,Move):
                result.append(f'MOVE {c.x} {c.y} {c.kind} {c.count} {c.direction}')
            elif isinstance(c,Tele):
                result.append(f'TELE {c.x} {c.y} {c.kind} {c.count} {c.tx} {c.ty}')
            else:
                result.append('PRIORITY '+' '.join(str(v) for p in c.coords for v in p))
        return result

    def fingerprint(self):
        # Order matters for moves (notably TELE), production and priorities.
        return tuple(self.texts())

    def projected(self, kind):
        result = defaultdict(int)
        for source in (self.pool,self.arrivals):
            for (x,y,k),n in source.items():
                if k == kind and n > 0:
                    result[(x,y)] += n
        return result
