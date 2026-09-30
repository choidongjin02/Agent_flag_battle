"""Anytime short-horizon search over feasible simultaneous action portfolios."""
import time
from hmh_geometry import Geometry
from hmh_memory import Memory
from hmh_policy import build, evaluate
from hmh_actions import Plan
from simcore.pipeline import run_turn


def transition(state, team, mine, theirs):
    return run_turn(state,mine.commands(),theirs.commands())[0] if team == 'Y' else run_turn(state,theirs.commands(),mine.commands())[0]


class HmhBot:
    def __init__(self, search=True, budget_ms=135):
        self.memory = Memory()
        self.geo = None
        self.search = search
        self.budget_ms = budget_ms
        self.diagnostics = {}

    def decide(self, view, init):
        started = time.perf_counter()
        if self.geo is None:
            self.geo = Geometry(init)
        state = self.memory.observe(view,init)
        deadline = started+self.budget_ms/1000
        team,opp = view.team,view.opp
        fallback = build(state,team,self.geo,old_goals=self.memory.goals)
        best,count = fallback,0
        candidates = [fallback]
        if self.search and time.perf_counter() < deadline-.035:
            opponents = [build(state,opp,self.geo,profile=p) for p in ('balanced','raid','economy')]
            opponents.append(Plan(state,opp,self.geo))
            seen = {fallback.fingerprint()}
            for profile,forecast in [('economy',None),('raid',None),('balanced',opponents[0].projected('W'))]:
                if time.perf_counter() >= deadline-.020:
                    break
                plan = build(state,team,self.geo,profile,self.memory.goals,forecast)
                if plan.fingerprint() not in seen:
                    seen.add(plan.fingerprint())
                    candidates.append(plan)
            best_value,ranked = -float('inf'),[]
            for plan in candidates:
                values,states = [],[]
                for other in opponents:
                    if time.perf_counter() >= deadline-.010:
                        break
                    nxt = transition(state,team,plan,other)
                    states.append(nxt)
                    values.append(evaluate(nxt,team,self.geo))
                if len(values) != len(opponents):
                    break
                score = .60*sum(values)/len(values)+.40*min(values)
                ranked.append((score,plan,states))
                count += len(values)
                if score > best_value:
                    best_value,best = score,plan
            finalists = sorted(ranked,key=lambda r:r[0],reverse=True)[:2]
            deep = []
            if len(finalists) == 2:
                for score,plan,states in finalists:
                    values = []
                    for index,nxt in enumerate(states):
                        if time.perf_counter() >= deadline-.020:
                            break
                        v = evaluate(nxt,team,self.geo)
                        if abs(v) >= 100000:
                            values.append(v)
                            continue
                        a = build(nxt,team,self.geo,old_goals=plan.goals)
                        b = build(nxt,opp,self.geo,profile=('balanced','raid','economy','balanced')[index])
                        values.append(evaluate(transition(nxt,team,a,b),team,self.geo))
                        count += 1
                    if len(values) != len(states):
                        break
                    deep.append((.60*sum(values)/len(values)+.40*min(values),plan))
                if len(deep) == 2:
                    best = max(deep,key=lambda x:x[0])[1]
        self.memory.goals = best.goals
        self.diagnostics = {'candidates':len(candidates),'transitions':count,
                            'elapsed_ms':(time.perf_counter()-started)*1000,
                            'changed':best.fingerprint() != fallback.fingerprint()}
        return best.texts()
