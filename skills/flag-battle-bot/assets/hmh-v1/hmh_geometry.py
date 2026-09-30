"""Cached graph distances and rectangular maximum-weight assignment."""
from collections import deque


class Geometry:
    def __init__(self, init):
        self.width, self.height = init.width, init.height
        self.cells = [(x, y) for y in range(init.height) for x in range(init.width) if init.passable(x, y)]
        self.adj = {p: [(p[0]+dx, p[1]+dy) for dx, dy in ((0,-1),(0,1),(-1,0),(1,0))
                        if init.passable(p[0]+dx, p[1]+dy)] for p in self.cells}
        self.dist = {}
        for p in self.cells:
            ds = {p: 0}
            q = deque([p])
            while q:
                v = q.popleft()
                for w in self.adj[v]:
                    if w not in ds:
                        ds[w] = ds[v] + 1
                        q.append(w)
            self.dist[p] = ds

    def distance(self, a, b):
        return self.dist.get(a, {}).get(b, 999)

    def key(self, p, base):
        x, y = p
        return (self.height-1-y, self.width-1-x) if base[0]*2 > self.width-1 else (y, x)

    def choices(self, p, base):
        return [p] + sorted(self.adj[p], key=lambda q: self.key(q, base))


def assignment(weights):
    """Hungarian algorithm; one distinct column per row, rows <= columns.

    Dummy columns encode waiting; this optimizes assignment only, not combat.
    """
    if not weights:
        return []
    n, m = len(weights), len(weights[0])
    assert n <= m
    u, v, p, way = [0.]*(n+1), [0.]*(m+1), [0]*(m+1), [0]*(m+1)
    for i in range(1, n+1):
        p[0] = i
        j0 = 0
        minimum = [float('inf')]*(m+1)
        used = [False]*(m+1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], float('inf'), 0
            for j in range(1, m+1):
                if not used[j]:
                    cur = -weights[i0-1][j-1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j], way[j] = cur, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(m+1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if not j0:
                break
    result = [-1]*n
    for j in range(1, m+1):
        if p[j]:
            result[p[j]-1] = j-1
    return result
