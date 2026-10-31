# #381 Realm vision v2 (adjustedfilm, 2026-10-31 late): whole EventGraph of BP_RealmVision (replaces the 379-node v1 of #379).
#   "<blender python>" -I gen_realmvision381.py  ->  BP_RealmVision_v2_graph.txt, VARIABLES_v2_BPVar.txt (only the NEW variables)
# Owner's Play test of v1: "fade in the visuals between the realms ... the feeling of being absorbed in or consumed in rather than
# just 1 frame world next frame realm" + "more distortion dreamlike state, pinkish orange semi scary fantasy comfortable yet
# unsettling dream" + "your realm is very very dark".
#   RvTick (every 0.05 s): v1's inside test against the real mesh (3 rays, crossings, majority) + Dist = distance from the camera
#     to the nearest membrane hit along 6 directions. A change of Inside starts the crossing one-shot (CrossT0, CrossDir +1 / -1).
#   Tick (every frame, DeltaSeconds):
#     target = inside ? PullMax + (1 - PullMax) * smooth(Dist / DeepDist) : PullMax * smooth(1 - Dist / PullDist)
#              (outside 10 m -> 0 m: 0 -> 0.35 "pull"; inside 0 -> 8 m: 0.35 -> 1; continuous at the membrane)
#     W = FInterpTo(W, target, dt, FadeSpeed); weight = W * (1 - BreathAmt * pulse(BreathHz))
#     Cross = one-shot envelope sin(pi * sqrt(t / dur)), dur = EnterTime 1.5 s (swallowed) or ExitTime 0.8 s (peel back)
#     -> Vision.BlendWeight, MPC_RealmDream: Amount, Cross, CrossDir, BreathHz (the dream post-process and the jelly bubble read it)
import math, os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))          # bpkit's import overwrites HERE

PPC, SMC, PCM = CLS('PostProcessComponent'), CLS('StaticMeshComponent'), CLS('PlayerCameraManager')
MATL, MPC_CLS = CLS('KismetMaterialLibrary'), CLS('MaterialParameterCollection')
MPC = '/Game/CastleDefender/Gameplay/Realm/MPC_RealmDream.MPC_RealmDream'
STEPS, DT, FAR = 8, 0.05, '1000000.0'
RAYS = (('Up', ('0.0', '0.0', '1.0')), ('Fwd', ('1.0', '0.0', '0.0')), ('Left', ('0.0', '-1.0', '0.0')))
PROBES = (('Down', ('0.0', '0.0', '-1.0')), ('Back', ('-1.0', '0.0', '0.0')), ('Right', ('0.0', '1.0', '0.0')))   # distance only

G = Graph(); b = B(G, 'rw')
g = lambda var, pin, x, y: b.get(var, pin, x, y)
DBLV, BOOLV, OBJV = D('v', default='0.0'), bo('v', default='false'), lambda c: ob('v', c)
mesh = lambda x, y: g('BubbleMesh', OBJV(PRIM), x, y)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}


def mpc_set(param, val, x, y):
    n = b.name('Mpc' + param)
    callfn(G, n, MATL, 'SetScalarParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', param),
           fl('ParameterValue', default='0.0')], x=x, y=y, self_hidden=True)
    b.wire(val, n, 'ParameterValue'); return n


def fn1(m, a, x, y): return b.math(m, [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
def mul(a, c, x, y, db='1.0'): return b.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
def add(a, c, x, y, db='0.0'): return b.d2('Add_DoubleDouble', a, c, x, y, db=db)
def sub(a, c, x, y, da='0.0', db='0.0'): return b.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
def div(a, c, x, y, db='1.0'): return b.d2('Divide_DoubleDouble', a, c, x, y, db=db)
def sat(v, x, y): return b.clamp(v, '0.0', '1.0', x, y)
def smooth(v, x, y):          # v*v*(3-2v) on a saturated v
    return mul(mul(v, v, x, y), sub(None, mul(v, None, x, y + 100, db='2.0'), x + 150, y + 100, da='3.0'), x + 300, y)


def trace(start, end, x, y, tag):
    tr = b.call(PRIM, 'K2_LineTraceComponent', [V('TraceStart'), V('TraceEnd'), bo('bTraceComplex', default='true'), bo('bShowTrace', default='false'),
                bo('bPersistentShowTrace', default='false'), V('HitLocation', out=True), V('HitNormal', out=True), {'name': 'BoneName', 'cat': 'name', 'out': True},
                st('OutHit', HITRES, out=True), bo('ReturnValue', out=True, default='false')], x, y, target=mesh(x - 150, y + 300), tag=tag)
    b.wire(start, tr, 'TraceStart'); b.wire(end, tr, 'TraceEnd')
    return tr


# ================================================================================================= BeginPlay (as v1)
b.override('BP', 'ReceiveBeginPlay', 0, 0)
gc = b.call(ACT, 'K2_GetComponentsByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Script/Engine.StaticMeshComponent'),
            arr(ob('ReturnValue', SMC, out=True))], 250, 250, target=g('Bubble', OBJV(ACT), 0, 250), pure=True, const=True, tag='BubbleMeshes')
it0 = b.name('FirstMesh')
G.node(it0, 'K2Node_GetArrayItem', [], [arr(ob('Array', SMC)), it('Dimension 1', default='0'), ob('Output', SMC, out=True)], 500, 250)
b.wire((gc, 'ReturnValue'), it0, 'Array')
vb = b.branch(b.valid(g('Bubble', OBJV(ACT), 300, 100), 450, 100), 300, 0, tag='IfBubble'); G.link('BP', 'then', vb, 'execute')
sm = b.set('BubbleMesh', OBJV(PRIM), (it0, 'Output'), 600, 0); G.link(vb, 'then', sm, 'execute')
sd = b.set('Dist', DBLV, None, 750, 0); G.nodes[-1][3][2]['default'] = FAR
st0 = b.set('CrossT0', DBLV, None, 900, 0); G.nodes[-1][3][2]['default'] = '-100.0'
w0 = b.setm('BlendWeight', PPC, fl('v', default='0.0'), None, g('Vision', OBJV(PPC), 1000, 300), 1050, 0)
tm = b.timer('RvTick', 1300, 0, dtime=repr(DT), loop=True)
b.chain(sm, sd, st0, w0, tm)

# ================================================================================================= RvTick: inside + distance
Y0 = 1200
b.event('RvTick', [], 0, Y0)
pcm = b.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], 0, Y0 + 300, pure=True, tag='CamMgr')
camn = b.call(PCM, 'GetCameraLocation', [V('ReturnValue', out=True)], 250, Y0 + 300, target=(pcm, 'ReturnValue'), pure=True, const=True, tag='CamLoc')
cam = (camn, 'ReturnValue')
bnd = b.lib(KSL, 'GetComponentBounds', [ob('Component', SCENE), V('Origin', out=True), V('BoxExtent', out=True), fl('SphereRadius', out=True, default='0.0')],
            0, Y0 + 500, pure=True, tag='Bounds')
b.wire(mesh(-200, Y0 + 500), bnd, 'Component')
org, ext = (bnd, 'Origin'), (bnd, 'BoxExtent')
vis = b.call(SCENE, 'IsVisible', [bo('ReturnValue', out=True, default='false')], 250, Y0 + 700, target=mesh(0, Y0 + 700), pure=True, const=True, tag='BubbleVis')
alive = b.b2('BooleanAND', b.valid(mesh(0, Y0 + 850), 250, Y0 + 850), (vis, 'ReturnValue'), 450, Y0 + 750)
d = b.brk(b.v2('Subtract_VectorVector', cam, org, 450, Y0 + 400), 650, Y0 + 400)
e = b.brk(ext, 650, Y0 + 550)
near = None
for i, c in enumerate('XYZ'):           # within the bounds + the 10 m pull zone + 2 m
    t = b.dcmp('LessEqual_DoubleDouble', fn1('Abs', d[c], 850, Y0 + 350 + 100 * i), add(e[c], None, 850, Y0 + 650 + 100 * i, db='1200.0'), 1050, Y0 + 400 + 100 * i)
    near = t if near is None else b.b2('BooleanAND', near, t, 1250, Y0 + 400 + 100 * i)
bn = b.branch(b.b2('BooleanAND', alive, near, 1450, Y0 + 500), 300, Y0, tag='IfNear'); G.link('RvTick', 'then', bn, 'execute')
# far / gone: outside, no distance (the cross one-shot still fires when the bubble vanishes around you)
offd = b.set('Dist', DBLV, None, 600, Y0 - 400); G.nodes[-1][3][2]['default'] = FAR
G.link(bn, 'else', offd, 'execute')

reach = add(mul(b.math('VSize', [(V('A'), ext)], D('ReturnValue', out=True), 850, Y0 + 1000), None, 1050, Y0 + 1000, db='2.0'), None, 1250, Y0 + 1000, db='1000.0')
last, X, votes, dists = None, 600, [], []
two = g('TwoSided', BOOLV, 600, Y0 + 1200)


def ray_dir(dvec, x, y):
    dirv = b.vec(None, None, None, x, y, *dvec)
    far = b.v2('Add_VectorVector', cam, b.math('Multiply_VectorFloat', [(V('A'), dirv), (D('B', default='1.0'), reach)], V('ReturnValue', out=True), x, y + 150), x + 200, y + 100)
    return dirv, far


def hitdist(tr, x, y):        # distance to the hit, or FAR
    dd = b.math('VSize', [(V('A'), b.v2('Subtract_VectorVector', (tr, 'HitLocation'), cam, x, y))], D('ReturnValue', out=True), x + 150, y)
    return b.self_(dd, None, (tr, 'ReturnValue'), x + 300, y, db=FAR)


for rname, dvec in RAYS:
    dirv, far = ray_dir(dvec, X, Y0 + 1100)
    counts = []
    for way, (start0, end, sign) in enumerate(((cam, far, '2.0'), (far, cam, '-2.0'))):
        step = b.math('Multiply_VectorFloat', [(V('A'), dirv), (D('B', default=sign), None)], V('ReturnValue', out=True), X, Y0 + 1400 + 150 * way)
        start, hits = start0, []
        for k in range(STEPS):
            tr = trace(start, end, X, Y0 + 200 * way, 'Ray%s%s%d' % (rname, 'Out' if way == 0 else 'In', k))
            if last is None: G.link(bn, 'then', tr, 'execute')
            else: b.chain(last, tr)
            last = tr
            if way == 0 and k == 0: dists.append(hitdist(tr, X + 150, Y0 + 3600))       # nearest wall along this ray
            hit = (tr, 'ReturnValue')
            hits.append(b.math('Conv_BoolToInt', [(bo('InBool', default='false'), hit)], it('ReturnValue', out=True), X + 150, Y0 + 2000 + 100 * k + 900 * way))
            nxt = b.v2('Add_VectorVector', (tr, 'HitLocation'), step, X + 150, Y0 + 1700 + 150 * way)
            start = b.selvec(nxt, end, hit, X + 300, Y0 + 1700 + 150 * way)
            X += 450
        acc = hits[0]
        for h in hits[1:]: acc = b.i2('Add_IntInt', acc, h, X, Y0 + 2000 + 900 * way)
        counts.append(acc)
    both = b.i2('Add_IntInt', counts[0], counts[1], X, Y0 + 3000)
    n_ = b.math('SelectInt', [(it('A', default='0'), counts[0]), (it('B', default='0'), both), (bo('bPickA', default='false'), two)], it('ReturnValue', out=True), X + 200, Y0 + 3000)
    votes.append(b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', n_, None, X + 400, Y0 + 3000, db='2'), None, X + 600, Y0 + 3000, db='1'))
for pname, dvec in PROBES:                 # 3 more single traces, for the distance only
    dirv, far = ray_dir(dvec, X, Y0 + 1100)
    tr = trace(cam, far, X, Y0, 'Probe' + pname); b.chain(last, tr); last = tr
    dists.append(hitdist(tr, X + 150, Y0 + 3600)); X += 450
r1, r2, r3 = votes
maj = b.b2('BooleanOR', b.b2('BooleanOR', b.b2('BooleanAND', r1, r2, X, Y0 + 3200), b.b2('BooleanAND', r1, r3, X, Y0 + 3300), X + 200, Y0 + 3250),
           b.b2('BooleanAND', r2, r3, X, Y0 + 3400), X + 400, Y0 + 3300)
dmin = dists[0]
for dd in dists[1:]: dmin = b.d2('FMin', dmin, dd, X + 600, Y0 + 3600)
sdst = b.set('Dist', DBLV, dmin, X + 200, Y0); b.chain(last, sdst)
newin = b.b2('BooleanAND', maj, alive, X + 600, Y0 + 3400)
# bubble far / gone joins here with newin = false
mg = b.seq('AfterTest', 1, X + 450, Y0); G.link(sdst, 'then', mg, 'execute'); G.link(offd, 'then', mg, 'execute')
newin2 = b.b2('BooleanAND', newin, near, X + 800, Y0 + 3400)
# a change of Inside starts the crossing one-shot
chg = b.math('NotEqual_BoolBool', [(bo('A', default='false'), newin2), (bo('B', default='false'), g('Inside', BOOLV, X + 800, Y0 + 3550))], bo('ReturnValue', out=True), X + 1000, Y0 + 3500)
bc = b.branch(chg, X + 700, Y0, tag='IfCross'); G.link(mg, 'then_0', bc, 'execute')
sct = b.set('CrossT0', DBLV, b.now(X + 900, Y0 - 300), X + 1000, Y0 - 200)
scd = b.set('CrossDir', DBLV, b.self_(None, None, newin2, X + 1100, Y0 - 350, da='1.0', db='-1.0'), X + 1250, Y0 - 200)
G.link(bc, 'then', sct, 'execute'); b.chain(sct, scd)
mg2 = b.seq('AfterCross', 1, X + 1500, Y0); G.link(bc, 'else', mg2, 'execute'); G.link(scd, 'then', mg2, 'execute')
si = b.set('Inside', BOOLV, newin2, X + 1800, Y0); G.link(mg2, 'then_0', si, 'execute')

# ================================================================================================= Tick: weight, crossing, MPC
TY = Y0 + 4600
G.node('TK', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveTick")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveTick")' % ACT}, ex('then', True),
        fl('DeltaSeconds', out=True, default='0.0')], 0, TY)
dt = ('TK', 'DeltaSeconds')
dist = lambda x, y: g('Dist', DBLV, x, y)
pull = g('PullMax', DBLV, 300, TY + 900)
out_t = mul(pull, smooth(sat(sub(None, div(dist(300, TY + 400), g('PullDist', DBLV, 300, TY + 500), 500, TY + 450), 700, TY + 450, da='1.0'), 900, TY + 450), 1100, TY + 450), 1500, TY + 500)
in_t = add(pull, mul(sub(None, pull, 700, TY + 800, da='1.0'), smooth(sat(div(dist(300, TY + 700), g('DeepDist', DBLV, 300, TY + 800), 500, TY + 750), 900, TY + 750), 1100, TY + 750),
                     1500, TY + 750), 1700, TY + 700)
tgt = b.self_(in_t, out_t, g('Inside', BOOLV, 1700, TY + 900), 1900, TY + 650)
wi = b.math('FInterpTo', [(D('Current', default='0.0'), g('W', DBLV, 1900, TY + 450)), (D('Target', default='0.0'), tgt), (D('DeltaTime', default='0.0'), None),
            (D('InterpSpeed', default='3.0'), g('FadeSpeed', DBLV, 1900, TY + 850))], D('ReturnValue', out=True), 2100, TY + 550)
b.wire(b.math('Conv_FloatToDouble', [(fl('InFloat', default='0.0'), dt)], D('ReturnValue', out=True), 1900, TY + 750), wi[0], 'DeltaTime')
sw = b.set('W', DBLV, wi, 300, TY); G.link('TK', 'then', sw, 'execute')
now = b.now(300, TY + 1200)
pulse = add(mul(fn1('Sin', mul(mul(now, g('BreathHz', DBLV, 300, TY + 1300), 500, TY + 1250), None, 700, TY + 1250, db=repr(2 * math.pi)), 900, TY + 1250), None, 1100, TY + 1250, db='0.5'),
            None, 1300, TY + 1250, db='0.5')
wf = sat(mul(g('W', DBLV, 1300, TY + 1100), sub(None, mul(g('BreathAmt', DBLV, 1300, TY + 1400), pulse, 1500, TY + 1350), 1700, TY + 1300, da='1.0'), 1900, TY + 1200), 2100, TY + 1200)
# crossing envelope: sin(pi * sqrt(t / dur)) for 0 <= t < dur
cdir = g('CrossDir', DBLV, 300, TY + 1700)
dur = b.self_(g('EnterTime', DBLV, 300, TY + 1800), g('ExitTime', DBLV, 300, TY + 1900), b.dcmp('Greater_DoubleDouble', cdir, None, 500, TY + 1700, db='0.0'), 700, TY + 1800)
ct = div(sub(b.now(300, TY + 1600), g('CrossT0', DBLV, 300, TY + 1650), 500, TY + 1600), b.d2('FMax', dur, None, 900, TY + 1800, db='0.05'), 1100, TY + 1650)
live = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', ct, None, 1300, TY + 1550, db='0.0'), b.dcmp('Less_DoubleDouble', ct, None, 1300, TY + 1650, db='1.0'), 1500, TY + 1600)
env = b.self_(fn1('Sin', mul(fn1('Sqrt', sat(ct, 1300, TY + 1750), 1500, TY + 1750), None, 1700, TY + 1750, db=repr(math.pi)), 1900, TY + 1750), None, live, 2100, TY + 1650)
sbw = b.setm('BlendWeight', PPC, fl('v', default='0.0'), wf, g('Vision', OBJV(PPC), 2200, TY + 300), 600, TY)
m1 = mpc_set('Amount', wf, 900, TY)
m2 = mpc_set('Cross', env, 1200, TY)
m3 = mpc_set('CrossDir', cdir, 1500, TY)
m4 = mpc_set('BreathHz', g('BreathHz', DBLV, 1500, TY + 300), 1800, TY)
b.chain(sw, sbw, m1, m2, m3, m4)

# ================================================================================================= checks + output
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]
dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate node names: %s' % sorted(dup)[:10])
open(os.path.join(HERE, 'BP_RealmVision_v2_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_RealmVision v2: nodes %d, links %d' % (len(G.nodes), len(G.links)))


def bpvar(name, vt, default, flags):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Realm Vision"),PropertyFlags=%d,DefaultValue="%s")' % (
        name, uuid.uuid5(uuid.NAMESPACE_URL, 'realmvision376/' + name).hex.upper(), vt, name, flags, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
EDIT, HIDDEN = 5, 4 | 0x10000
NEW = [('PullDist', REAL, '1000.0', EDIT), ('DeepDist', REAL, '800.0', EDIT), ('PullMax', REAL, '0.35', EDIT),
       ('EnterTime', REAL, '1.5', EDIT), ('ExitTime', REAL, '0.8', EDIT),
       ('Dist', REAL, FAR, HIDDEN), ('CrossT0', REAL, '-100.0', HIDDEN), ('CrossDir', REAL, '1.0', HIDDEN)]
used = {p for n in G.nodes for p in n[2] if 'VariableReference' in p}
for v in [n for n, *_ in NEW] + ['Bubble', 'TwoSided', 'FadeSpeed', 'BreathHz', 'BreathAmt', 'BubbleMesh', 'Inside', 'W']:
    if not any('"%s"' % v in u for u in used): raise SystemExit('variable %s is never used' % v)
open(os.path.join(HERE, 'VARIABLES_v2_BPVar.txt'), 'w', newline='\r\n').write(
    '# BP_RealmVision v2 (#381) - the 8 v1 variables stay; paste these 8 NEW lines one at a time on the VARIABLES header, then Compile\n'
    + '\n'.join(bpvar(*v) for v in NEW) + '\n')
print('new BPVar lines: %d' % len(NEW))
