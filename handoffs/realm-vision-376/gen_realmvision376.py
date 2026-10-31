# #376 Realm vision (adjustedfilm, 2026-10-31 late): EventGraph of the NEW actor BP_RealmVision.
#   "<blender python>" -I gen_realmvision376.py  ->  BP_RealmVision_graph.txt, VARIABLES_BPVar.txt
# The owner reshaped the realm bubble (tall, organic, wraps the tentacle), so no sphere / capsule volume: the inside test runs
# against the REAL bubble mesh, any shape, no re-fit after a future reshape.
#   BeginPlay: Bubble (instance variable, set by setup --place) -> its first StaticMeshComponent -> BubbleMesh; looping 0.05 s timer
#   RvTick (every 0.05 s):
#     camera outside the bubble's bounds (+2 m)       -> outside, no traces
#     else 3 rays from the camera (+Z, +X, -Y). Each ray walks OUT (camera -> far) and IN (far -> camera), stepping past every
#       hit with ComponentLineTrace (complex), up to 8 hits each way. Crossings: two-sided collision -> hits out; single-sided
#       -> hits out + hits in (out only sees faces that look back at the camera, in only the others). Odd = inside.
#       Majority of the 3 rays (a fold of the membrane can fool one ray).
#     bubble gone or hidden (realm collapse #284) -> outside
#     W = FInterpTo(W, inside, 0.05, FadeSpeed)       (~0.6 s soft crossing at FadeSpeed 5)
#     Vision.BlendWeight = W * (1 - BreathAmt * (0.5 + 0.5 sin(2 pi BreathHz t)))   (the look pulses with the membrane)
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))          # bpkit's import overwrites HERE

PPC, SMC, PCM = CLS('PostProcessComponent'), CLS('StaticMeshComponent'), CLS('PlayerCameraManager')
STEPS, DT = 8, 0.05
RAYS = (('Up', ('0.0', '0.0', '1.0')), ('Fwd', ('1.0', '0.0', '0.0')), ('Left', ('0.0', '-1.0', '0.0')))

G = Graph(); b = B(G, 'rv')
g = lambda var, pin, x, y: b.get(var, pin, x, y)
DBLV, BOOLV, OBJV = D('v', default='0.0'), bo('v', default='false'), lambda c: ob('v', c)
mesh = lambda x, y: g('BubbleMesh', OBJV(PRIM), x, y)

# ================================================================================================= BeginPlay
b.override('BP', 'ReceiveBeginPlay', 0, 0)
bub = g('Bubble', OBJV(ACT), 0, 250)
gc = b.call(ACT, 'K2_GetComponentsByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Script/Engine.StaticMeshComponent'),
            arr(ob('ReturnValue', SMC, out=True))], 250, 250, target=bub, pure=True, const=True, tag='BubbleMeshes')
it0 = b.name('FirstMesh')
G.node(it0, 'K2Node_GetArrayItem', [], [arr(ob('Array', SMC)), it('Dimension 1', default='0'), ob('Output', SMC, out=True)], 500, 250)
b.wire((gc, 'ReturnValue'), it0, 'Array')
vb = b.branch(b.valid(g('Bubble', OBJV(ACT), 300, 100), 450, 100), 300, 0, tag='IfBubble'); G.link('BP', 'then', vb, 'execute')
sm = b.set('BubbleMesh', OBJV(PRIM), (it0, 'Output'), 600, 0); G.link(vb, 'then', sm, 'execute')
w0 = b.setm('BlendWeight', PPC, fl('v', default='0.0'), None, g('Vision', OBJV(PPC), 700, 300), 850, 0)
tm = b.timer('RvTick', 1100, 0, dtime=repr(DT), loop=True)
b.chain(sm, w0, tm)

# ================================================================================================= RvTick
Y0 = 1200
b.event('RvTick', [], 0, Y0)
pcm = b.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], 0, Y0 + 300, pure=True, tag='CamMgr')
camn = b.call(PCM, 'GetCameraLocation', [V('ReturnValue', out=True)], 250, Y0 + 300, target=(pcm, 'ReturnValue'), pure=True, const=True, tag='CamLoc')
cam = (camn, 'ReturnValue')
bnd = b.lib(KSL, 'GetComponentBounds', [ob('Component', SCENE), V('Origin', out=True), V('BoxExtent', out=True), fl('SphereRadius', out=True, default='0.0')],
            0, Y0 + 500, pure=True, tag='Bounds')
b.wire(mesh(-200, Y0 + 500), bnd, 'Component')
org, ext = (bnd, 'Origin'), (bnd, 'BoxExtent')
# alive = bubble mesh valid + visible (the realm collapse hides / removes it)
vis = b.call(SCENE, 'IsVisible', [bo('ReturnValue', out=True, default='false')], 250, Y0 + 700, target=mesh(0, Y0 + 700), pure=True, const=True, tag='BubbleVis')
alive = b.b2('BooleanAND', b.valid(mesh(0, Y0 + 850), 250, Y0 + 850), (vis, 'ReturnValue'), 450, Y0 + 750)
# near = |cam - origin| <= extent + 200 on every axis
d = b.brk(b.v2('Subtract_VectorVector', cam, org, 450, Y0 + 400), 650, Y0 + 400)
e = b.brk(ext, 650, Y0 + 550)
near = None
for i, c in enumerate('XYZ'):
    t = b.dcmp('LessEqual_DoubleDouble', b.math('Abs', [(D('A', default='0.0'), d[c])], D('ReturnValue', out=True), 850, Y0 + 350 + 100 * i),
               b.d2('Add_DoubleDouble', e[c], None, 850, Y0 + 650 + 100 * i, db='200.0'), 1050, Y0 + 400 + 100 * i)
    near = t if near is None else b.b2('BooleanAND', near, t, 1250, Y0 + 400 + 100 * i)
bn = b.branch(b.b2('BooleanAND', alive, near, 1450, Y0 + 500), 300, Y0, tag='IfNear'); G.link('RvTick', 'then', bn, 'execute')
off = b.set('Inside', BOOLV, None, 600, Y0 - 250); G.link(bn, 'else', off, 'execute')

# ---- the rays: reach = 2 |extent| + 10 m
reach = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', b.math('VSize', [(V('A'), ext)], D('ReturnValue', out=True), 850, Y0 + 1000), None, 1050, Y0 + 1000, db='2.0'),
             None, 1250, Y0 + 1000, db='1000.0')
last, X, votes = bn, 600, []
two = g('TwoSided', BOOLV, 600, Y0 + 1200)
for ri, (rname, dvec) in enumerate(RAYS):
    dirv = b.vec(None, None, None, X, Y0 + 1100, *dvec)
    far = b.v2('Add_VectorVector', cam, b.math('Multiply_VectorFloat', [(V('A'), dirv), (D('B', default='1.0'), reach)], V('ReturnValue', out=True), X, Y0 + 1250), X + 200, Y0 + 1200)
    counts = []
    for way, (start0, end, sign) in enumerate(((cam, far, '2.0'), (far, cam, '-2.0'))):
        step = b.math('Multiply_VectorFloat', [(V('A'), dirv), (D('B', default=sign), None)], V('ReturnValue', out=True), X, Y0 + 1400 + 150 * way)
        start, hits = start0, []
        for k in range(STEPS):
            tr = b.call(PRIM, 'K2_LineTraceComponent', [V('TraceStart'), V('TraceEnd'), bo('bTraceComplex', default='true'), bo('bShowTrace', default='false'),
                        bo('bPersistentShowTrace', default='false'), V('HitLocation', out=True), V('HitNormal', out=True), {'name': 'BoneName', 'cat': 'name', 'out': True},
                        st('OutHit', HITRES, out=True), bo('ReturnValue', out=True, default='false')], X, Y0 + 200 * way, target=mesh(X - 150, Y0 + 300 + 200 * way),
                        tag='Ray%s%s%d' % (rname, 'Out' if way == 0 else 'In', k))
            b.wire(start, tr, 'TraceStart'); b.wire(end, tr, 'TraceEnd')
            if last == bn: G.link(bn, 'then', tr, 'execute')
            else: b.chain(last, tr)
            last = tr
            hit = (tr, 'ReturnValue')
            hits.append(b.math('Conv_BoolToInt', [(bo('InBool', default='false'), hit)], it('ReturnValue', out=True), X + 150, Y0 + 2000 + 100 * k + 900 * way))
            nxt = b.v2('Add_VectorVector', (tr, 'HitLocation'), step, X + 150, Y0 + 1700 + 150 * way)
            start = b.selvec(nxt, end, hit, X + 300, Y0 + 1700 + 150 * way)     # past the hit, or done (start = end: no more hits)
            X += 450
        acc = hits[0]
        for h in hits[1:]: acc = b.i2('Add_IntInt', acc, h, X, Y0 + 2000 + 900 * way)
        counts.append(acc)
    both = b.i2('Add_IntInt', counts[0], counts[1], X, Y0 + 3000)
    n_ = b.math('SelectInt', [(it('A', default='0'), counts[0]), (it('B', default='0'), both), (bo('bPickA', default='false'), two)], it('ReturnValue', out=True), X + 200, Y0 + 3000)
    odd = b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', n_, None, X + 400, Y0 + 3000, db='2'), None, X + 600, Y0 + 3000, db='1')
    votes.append(odd)
r1, r2, r3 = votes
maj = b.b2('BooleanOR', b.b2('BooleanOR', b.b2('BooleanAND', r1, r2, X, Y0 + 3200), b.b2('BooleanAND', r1, r3, X, Y0 + 3300), X + 200, Y0 + 3250),
           b.b2('BooleanAND', r2, r3, X, Y0 + 3400), X + 400, Y0 + 3300)
si = b.set('Inside', BOOLV, maj, X + 200, Y0); b.chain(last, si)
mg = b.seq('AfterTest', 1, X + 500, Y0); G.link(si, 'then', mg, 'execute'); G.link(off, 'then', mg, 'execute')
X += 800

# ---- fade + breathing -> Vision.BlendWeight
tgt = b.self_(None, None, g('Inside', BOOLV, X, Y0 + 400), X + 200, Y0 + 400, da='1.0', db='0.0')
wi = b.math('FInterpTo', [(D('Current', default='0.0'), g('W', DBLV, X, Y0 + 300)), (D('Target', default='0.0'), tgt), (D('DeltaTime', default=repr(DT)), None),
            (D('InterpSpeed', default='5.0'), g('FadeSpeed', DBLV, X, Y0 + 600))], D('ReturnValue', out=True), X + 400, Y0 + 400)
sw = b.set('W', DBLV, wi, X, Y0); G.link(mg, 'then_0', sw, 'execute')
ph = b.d2('Multiply_DoubleDouble', b.d2('Multiply_DoubleDouble', b.now(X, Y0 + 800), g('BreathHz', DBLV, X, Y0 + 900), X + 200, Y0 + 850), None, X + 400, Y0 + 850, db='6.2831853')
pulse = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', b.math('Sin', [(D('A', default='0.0'), ph)], D('ReturnValue', out=True), X + 600, Y0 + 850), None, X + 800, Y0 + 850, db='0.5'),
             None, X + 1000, Y0 + 850, db='0.5')
damp = b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', g('BreathAmt', DBLV, X + 1000, Y0 + 1000), pulse, X + 1200, Y0 + 950), X + 1400, Y0 + 900, da='1.0')
wf = b.clamp(b.d2('Multiply_DoubleDouble', g('W', DBLV, X + 1400, Y0 + 700), damp, X + 1600, Y0 + 800), '0.0', '1.0', X + 1800, Y0 + 800)
sb = b.setm('BlendWeight', PPC, fl('v', default='0.0'), wf, g('Vision', OBJV(PPC), X + 1800, Y0 + 300), X + 400, Y0)
b.chain(sw, sb)

# ================================================================================================= checks + output
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
names = [n[0] for n in G.nodes]
dup = {n for n in names if names.count(n) > 1}
if dup: raise SystemExit('duplicate node names: %s' % sorted(dup)[:10])
open(os.path.join(HERE, 'BP_RealmVision_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_RealmVision: nodes %d, links %d' % (len(G.nodes), len(G.links)))


def bpvar(name, vt, default, flags):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Realm Vision"),PropertyFlags=%d,DefaultValue="%s")' % (
        name, uuid.uuid5(uuid.NAMESPACE_URL, 'realmvision376/' + name).hex.upper(), vt, name, flags, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
OBJ_ = lambda c: 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % c
EDIT, HIDDEN = 5, 4 | 0x10000      # 5 = instance editable; 4|DisableEditOnInstance = runtime only
VARS = [('Bubble', OBJ_('Actor'), '', EDIT), ('TwoSided', 'PinCategory="bool"', 'false', EDIT), ('FadeSpeed', REAL, '5.0', EDIT),
        ('BreathHz', REAL, '0.25', EDIT), ('BreathAmt', REAL, '0.08', EDIT),
        ('BubbleMesh', OBJ_('PrimitiveComponent'), '', HIDDEN), ('Inside', 'PinCategory="bool"', 'false', HIDDEN), ('W', REAL, '0.0', HIDDEN)]
used = {p for n in G.nodes for p in n[2] if 'VariableReference' in p}
for v, *_ in VARS:
    if not any('"%s"' % v in u for u in used): raise SystemExit('BPVar %s is never used' % v)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BP_RealmVision (#376) - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpvar(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
