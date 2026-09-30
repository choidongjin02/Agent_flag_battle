"""Persistent public history; no map seed or spectator score inputs."""
from collections import defaultdict
from protocol import BALANCE
from simcore.state import Building, GameState


class Memory:
    def __init__(self):
        self.known = {}
        self.claimed = defaultdict(set)
        self.occupation = defaultdict(int)
        self.previous_turn = None
        self.goals = []
        self.enemy_revealed = set()

    def observe(self, view, init):
        opp = view.opp
        for b in view.buildings:
            if b.get('score',-1) >= 0:
                self.known[(b['x'],b['y'])] = b['score']
                self.known[(init.width-1-b['x'],init.height-1-b['y'])] = b['score']
            if b['type'] == 'DEPOT' and b['owner'] != 'N':
                self.claimed[b['id']].add(b['owner'])
            if b['owner'] == opp:
                self.enemy_revealed.add(b['id'])
            if self.previous_turn != view.turn and view.turn > 1 and b['owner'] != 'N':
                self.occupation[(b['owner'],b['id'])] += 1
        for u in view.units:
            if u['team'] != opp:
                continue
            radius = 2 if u['kind'] == 'S' else 0
            for b in view.buildings:
                if max(abs(u['x']-b['x']),abs(u['y']-b['y'])) <= radius:
                    self.enemy_revealed.add(b['id'])
        for watch in view.buildings:
            if watch['owner'] == opp and watch['type'] == 'WATCH':
                for b in view.buildings:
                    if max(abs(watch['x']-b['x']),abs(watch['y']-b['y'])) <= 3:
                        self.enemy_revealed.add(b['id'])
        self.previous_turn = view.turn
        buildings = {}
        for b in view.buildings:
            pos = b['x'],b['y']
            estimate = 3 if b['type'] == 'PLAZA' or 5 <= b['x'] <= 9 else 2
            buildings[b['id']] = Building(b['id'],*pos,b['type'],self.known.get(pos,estimate),b['owner'],b['stage'])
        revealed = {view.team:{b['id'] for b in view.buildings if b.get('score',-1) >= 0},
                    opp:set(self.enemy_revealed)}
        occupation = {t:sum(n*buildings[i].score for (owner,i),n in self.occupation.items() if owner == t)
                      for t in ('Y','K')}
        return GameState(BALANCE,init.terrain,buildings,init.bases,
                         {view.team:view.my_resource,opp:view.opp_resource},
                         {(u['x'],u['y'],u['team'],u['kind']):u['count'] for u in view.units},
                         view.turn-1,{i:set(v) for i,v in self.claimed.items()},revealed,occupation)
