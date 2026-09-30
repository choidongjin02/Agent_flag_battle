"""Anytime short-horizon search over feasible simultaneous action portfolios (HMH v2)."""
import time
import math
from hmh_geometry import Geometry
from hmh_memory import Memory
from hmh_policy import build, evaluate
from hmh_actions import Plan
from simcore.pipeline import run_turn
from hmh_features import FEATURES


def regret_matching(matrix, iterations=200):
    """Average strategies of regret matching on a zero-sum payoff matrix (row maximizes)."""
    n,m = len(matrix),len(matrix[0])
    r1,r2,s1,s2 = [0.]*n,[0.]*m,[0.]*n,[0.]*m
    def strategy(regret):
        positive = [max(r,0.) for r in regret]
        total = sum(positive)
        return [x/total for x in positive] if total > 0 else [1/len(regret)]*len(regret)
    for _ in range(iterations):
        p,q = strategy(r1),strategy(r2)
        u1 = [sum(matrix[i][j]*q[j] for j in range(m)) for i in range(n)]
        v1 = sum(p[i]*u1[i] for i in range(n))
        u2 = [-sum(p[i]*matrix[i][j] for i in range(n)) for j in range(m)]
        v2 = sum(q[j]*u2[j] for j in range(m))
        for i in range(n):
            r1[i] += u1[i]-v1
            s1[i] += p[i]
        for j in range(m):
            r2[j] += u2[j]-v2
            s2[j] += q[j]
    return [x/sum(s1) for x in s1],[x/sum(s2) for x in s2]


def transition(state, team, mine, theirs):
    return run_turn(state,mine.commands(),theirs.commands())[0] if team == 'Y' else run_turn(state,theirs.commands(),mine.commands())[0]


class HmhBot:
    """Bounded portfolio search with complete-layer iterative policy rollouts.

    Depth 4 is a continuation of three root plans against persistent opponent
    policies, NOT exhaustive minimax. Never compare different horizon lengths.
    """
    def __init__(self, search=True, budget_ms=185, max_depth=4):
        self.memory = Memory()
        self.geo = None
        self.search = search
        self.budget_ms = budget_ms
        self.max_depth = max_depth
        self.diagnostics = {}
        self.predictions = {}
        self.errors = {}
        self.predicted_turn = None
        self.profiles = ('balanced','raid','economy','cover','preserve','assault')

    def update_opponent(self, state, opp):
        # Predictions were conditioned on OUR selected action only. Compare the
        # next public snapshot, never the other player's simultaneous commands.
        if self.predicted_turn != state.turn:
            self.predictions = {}
            return
        actual = {k:n for k,n in state.units.items() if k[2] == opp}
        for profile,predicted in self.predictions.items():
            guess = {k:n for k,n in predicted.units.items() if k[2] == opp}
            loss = 0.
            for kind,weight in (('F',2.),('W',1.),('S',.5)):
                keys = {k for k in actual.keys()|guess.keys() if k[3] == kind}
                norm = 1+sum(actual.get(k,0)+guess.get(k,0) for k in keys)
                loss += weight*sum(abs(actual.get(k,0)-guess.get(k,0)) for k in keys)/norm
            loss += sum(b.owner != predicted.buildings[i].owner for i,b in state.buildings.items())/max(1,len(state.buildings))
            loss += abs(state.resources[opp]-predicted.resources[opp])/40
            self.errors[profile] = .8*self.errors.get(profile,loss)+.2*loss

    def mixture(self, profiles):
        floor = min((self.errors.get(p,0.) for p in profiles),default=0.)
        raw = [math.exp(-3*(self.errors.get(p,0.)-floor)) for p in profiles]
        total = sum(raw)
        # Nonzero floor protects against an opponent changing its policy.
        return [.75*w/total+.25/len(raw) for w in raw]

    def decide(self, view, init):
        started = time.perf_counter()
        if self.geo is None:
            self.geo = Geometry(init)
        state = self.memory.observe(view,init)
        team,opp = view.team,view.opp
        self.update_opponent(state,opp)
        deadline = started+self.budget_ms/1000
        # Soft compute limit leaves transport/parsing and OS scheduling headroom.
        max_step = .008
        def room(multiplier=1.):
            return time.perf_counter()+max(.010,max_step*multiplier)+.008 < deadline
        def timed(fn, *args, **kwargs):
            nonlocal max_step
            t=time.perf_counter(); result=fn(*args,**kwargs)
            max_step=max(max_step,time.perf_counter()-t)
            return result
        fallback = timed(build,state,team,self.geo,old_goals=self.memory.goals)
        best,depth,count = fallback,0,0
        candidates=[fallback]
        opponents=[]; labels=[]; ranked=[]
        root_states={}
        if self.search and room(3):
            # Opponent coverage includes defense/retreat/concentrated escorts.
            for profile in self.profiles:
                if not room(2): break
                opponents.append(timed(build,state,opp,self.geo,profile=profile))
                labels.append(profile)
            seen={fallback.fingerprint()}
            profiles=[('economy',None),('raid',None),('assault',None),
                      ('balanced',opponents[0].projected('W')),
                      ('cover',None),('preserve',None)] if opponents else []
            for profile,forecast in profiles:
                if not room(2): break
                plan=timed(build,state,team,self.geo,profile,self.memory.goals,forecast)
                if plan.fingerprint() not in seen:
                    seen.add(plan.fingerprint());candidates.append(plan)
            for plan in candidates:
                states=[]; values=[]
                for other in opponents:
                    if not room(): break
                    nxt=timed(transition,state,team,plan,other)
                    states.append(nxt);values.append(timed(evaluate,nxt,team,self.geo));count+=1
                if not values or len(values)!=len(opponents): break
                ranked.append((plan,states,values))
                root_states[id(plan)]=states
            prior=self.mixture(labels) if labels else []
            def rank(rows):
                if len(rows)>1:
                    _,q=regret_matching([r[2] for r in rows],iterations=80)
                else:
                    q=prior
                weights=[.75*a+.25*b for a,b in zip(q,prior)]
                return sorted(rows,key=lambda r:.85*sum(w*v for w,v in zip(weights,r[2]))+.15*min(r[2]),reverse=True)
            if ranked:
                ranked=rank(ranked);best=ranked[0][0];depth=1
                finalists=ranked[:3]
                rollout_goals={(id(r[0]),j):r[0].goals for r in finalists for j in range(len(r[1]))}
                # Only a whole layer can replace the shallower decision. Opponent
                # profile remains fixed along each trajectory; both sides replan.
                for horizon in range(2,min(self.max_depth,160-state.turn)+1):
                    layer=[]
                    for plan,states,values in finalists:
                        next_states=[];next_values=[]
                        for j,nxt in enumerate(states):
                            if abs(values[j])>=100000 or nxt.turn>=160:
                                next_states.append(nxt);next_values.append(values[j]);continue
                            if not room(3): break
                            a=timed(build,nxt,team,self.geo,
                                    profile=getattr(plan,'profile','balanced'),old_goals=rollout_goals[id(plan),j])
                            b=timed(build,nxt,opp,self.geo,profile=labels[j])
                            after=timed(transition,nxt,team,a,b);count+=1
                            rollout_goals[id(plan),j]=a.goals
                            next_states.append(after);next_values.append(timed(evaluate,after,team,self.geo))
                        if len(next_states)!=len(states): break
                        layer.append((plan,next_states,next_values))
                    if len(layer)!=len(finalists): break
                    finalists=rank(layer);best=finalists[0][0];depth=horizon
        self.predictions={p:s for p,s in zip(labels,root_states.get(id(best),[]))}
        self.predicted_turn=state.turn+1
        self.memory.goals=best.goals
        result=best.texts()
        self.diagnostics={'candidates':len(candidates),'opponents':len(opponents),
                          'transitions':count,'depth':depth,
                          'elapsed_ms':(time.perf_counter()-started)*1000,
                          'opponent_errors':dict(self.errors),
                          'changed':best.fingerprint()!=fallback.fingerprint()}
        return result
