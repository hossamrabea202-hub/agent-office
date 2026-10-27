"""gen_blob_splat.py: #32 phase 3 hooks in BP_JellyBlob (spec: agent-office handoffs/jelly-trail-fire DESIGN.md + PHASE2.md).
- landing (CX_26 sets LandT): TrailMgr.AddTrail(Body, 160)
- mine triggered (CX_125..CX_129, once): AddTrail(Body, 220)
- armed (CX_106 TrigT < 0), every tick: QLoc = Body; IsBurningAt; BurningOut -> Ignite(Body, 200) + DestroyActor (pops, no hatch)
Full EventGraph replace = live graph (stale export nodes dropped) + new nodes. Only external calls on the manager and an
inherited self-call (K2_DestroyActor, bSelfContext) -> nothing that the paste drops. Writes paste_blob_splat.t3d."""
import os, re, sys
W = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
sys.path.insert(0, W)
import kit2 as K
import t3dlib as T
from kit2 import G, BPC, ACTOR, VEC, link, chain
BLOB = BPC('/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob')
MGR = BPC('/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager')
EXP = 'live_BP_JellyBlob'


def reg(key, path):  # paste-format file -> t3dlib template cache
    t = open(path, encoding='utf-8', errors='ignore').read()
    cls, defs = {}, {}
    for c, n, b in re.findall(r'Begin Object Class=(\S+) Name="([^"]+)"\n(.*?)\nEnd Object', t, re.S):
        cls[n] = c; defs[n] = ('EventGraph', b)
    T._FILES[key] = (cls, defs)


reg('p_zhook', os.path.join(W, 'jellytrail', 'paste_zombie_trailhook.t3d'))
reg('p_ball', os.path.join(W, 'jellytrail', 'paste_cannonball_ignite.t3d'))

raw = open(os.path.join(W, 't3d', EXP + '.t3d'), 'rb').read()
t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
live = set(re.findall(r"Nodes\(\d+\)=\"[^']*'([^']+)'\"", t))
g = G(BLOB)
N = g.load_graph(EXP, 'EventGraph')
stale = {n for n in N if n not in live}
g.nodes = [n for n in g.nodes if n.name not in stale]
for n in g.nodes:
    for p in n.pins:
        p.links = [l for l in p.links if l[0] not in stale]
N = {n.name: n for n in g.nodes}


def body_loc(x, y):
    b = g.clone(EXP, 'CX_111', x, y)
    l = g.clone(EXP, 'CX_112', x + 180, y)
    link(b, 'Body', l, 'self')
    return l


def mgr_valid(x, y):
    """GetActorOfClass(BP_JellyTrailManager) -> Branch(IsValid). Returns (get, branch)."""
    ga = g.clone('p_zhook', 'JTZ_15', x, y)
    v = g.clone(EXP, 'CX_108', x + 250, y + 200)
    link(ga, 'ReturnValue', v, 'Object')
    br = g.branch(x + 450, y)
    chain(ga, br); link(v, 'ReturnValue', br, 'Condition')
    return ga, br


def splat(after, size, x, y):
    ga, br = mgr_valid(x, y)
    link(after, 'then', ga, 'execute')
    at = g.clone('p_zhook', 'JTZ_25', x + 700, y).default('PieceSize', '%.1f' % size)
    link(br, 'then', at, 'execute'); link(ga, 'ReturnValue', at, 'self')
    link(body_loc(x + 400, y + 350), 'ReturnValue', at, 'Loc')


# landing splat (CX_26.then is free) and trigger splat (CX_129.then is free)
assert not N['CX_26'].p('then').links and not N['CX_129'].p('then').links
splat(N['CX_26'], 160.0, N['CX_26'].x + 350, N['CX_26'].y)
splat(N['CX_129'], 220.0, N['CX_129'].x + 350, N['CX_129'].y)

# armed pop, LAST in the landed tick (so nothing touches the blob after DestroyActor):
# CX_16.else -> new Sequence: then_0 -> CX_103 (unchanged), then_1 -> Branch(TrigT < 0) -> [mgr? QLoc=Body, IsBurningAt,
# BurningOut ? Ignite + DestroyActor]
c16, c103 = N['CX_16'], N['CX_103']
assert [l[0] for l in c16.p('else').links] == ['CX_103']
c16.unlink('else')
X, Y = c103.x, c103.y - 1100
seq = g.clone(EXP, 'CX_103', X - 300, Y + 300)
link(c16, 'else', seq, 'execute'); link(seq, 'then_0', c103, 'execute')
tg = g.clone(EXP, 'CX_104', X - 150, Y + 200); lt = g.clone(EXP, 'CX_105', X, Y + 200)
link(tg, 'TrigT', lt, 'A')
armed = g.branch(X, Y)
link(seq, 'then_1', armed, 'execute'); link(lt, 'ReturnValue', armed, 'Condition')
X += 250
ga, br = mgr_valid(X, Y)
link(armed, 'then', ga, 'execute')
loc = body_loc(X + 450, Y + 400)
sq = g.vset('QLoc', 'struct', VEC, parent=MGR, x=X + 700, y=Y, external=True)
link(br, 'then', sq, 'execute'); link(ga, 'ReturnValue', sq, 'self'); link(loc, 'ReturnValue', sq, 'QLoc')
ib = g.mcall(MGR, 'IsBurningAt', [], X + 1000, Y)
chain(sq, ib); link(ga, 'ReturnValue', ib, 'self')
bo = g.vget('BurningOut', 'bool', None, parent=MGR, x=X + 1050, y=Y + 250, external=True)
link(ga, 'ReturnValue', bo, 'self')
bb = g.branch(X + 1300, Y)
chain(ib, bb); link(bo, 'BurningOut', bb, 'Condition')
ig = g.clone('p_ball', 'JTC_10', X + 1550, Y).default('Radius', '200.0')
link(bb, 'then', ig, 'execute'); link(ga, 'ReturnValue', ig, 'self'); link(loc, 'ReturnValue', ig, 'Loc')
de = g.mcall(ACTOR, 'K2_DestroyActor', [], X + 1850, Y, selfctx=True)
chain(ig, de)

n, size = g.emit(os.path.join(W, 'jellytrail', 'paste_blob_splat.t3d'))
print('nodes', n, 'chars', size, 'stale dropped', len(stale), 'live graph', len(N))
