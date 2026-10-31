# #337 part 2: blood splats on every hit + "not too gory" limb severing on heavy / killing melee hits (adjustedfilm,
# 2026-10-31). Spec: handoffs/gore-337/RESEARCH.md §5.2 / §5.3. Built on the Master's 2026-10-30b BP_Zombie export (the
# Master: "use 10-30b for now"); bones from handoffs/exports/adjustedfilm/gore-337/bones.txt (SK_Zombie, Mixamo names).
#   "<blender python>" -I gen_gore337.py -> BPC_Gore337_graph.txt, BP_SeveredLimb337_graph.txt, BP_WoundCap337_graph.txt,
#                                           Zombie_GoreHook_graph.txt + manifest_zombie_gore.json, *_BPVar.txt, VARIABLES.md
# BPC_Gore337 (component on BP_Zombie, so every child zombie gets it):
#   OnHit(Damage, Causer, Killing, MaxHP)  <- BP_Zombie's ReceiveAnyDamage, right after its BP_BloodBurst spawn
#     every hit: one blood splat decal under the zombie (trace down, random of the 8 atlas splats, 15-40 cm, heavy 50 cm),
#       it dries by itself in the material (SpawnT -> 30 s wet->dry, then 3 s fade; decal life 33 s)
#     sever: only melee (Causer is a Pawn within 3.5 m), only heavy (Damage >= 25 % MaxHP) or killing hits, a normal heavy
#       hit only once the zombie is already wounded (2nd hit+), max 2 per zombie, max 8 loose limbs in the world.
#       Chances heavy / killing: forearm 25 / 35 %, upper arm 10 / 20 %, lower leg 0 / 15 %, head 0 / 10 % (GoreLevel 2 only).
#       -> BP_SeveredLimb337 at the limb (falls with physics, own cap on its cut end, gone after 20 s)
#       -> zombie Mesh HideBoneByName(bone)  -> BP_WoundCap337 stuck on the stump (dried cap, no hanging gore)
#       -> a BP_BloodBurst at the cut (the game's own burst)
# BP_SeveredLimb337.Setup: a PoseableMesh copy of the zombie (same mesh + its live materials, pose copied once); every bone
#   is scaled to 1e-4 at the Hips and the cut bone back to 1 in component space, so only the limb stays; the copy is moved
#   so the limb sits exactly where it was, then the capsule root falls with an outward push + spin. Collides with the world
#   only (pawns ignored).
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

D3 = '/Game/CastleDefender/VFX/Blood337'
P_GORE, P_LIMB, P_CAP = D3 + '/BPC_Gore337', D3 + '/BP_SeveredLimb337', D3 + '/BP_WoundCap337'
P_BURST = '/Game/CastleDefender/VFX/BP_BloodBurst'
GORE, LIMB, CAPA = BPC(P_GORE, 'BPC_Gore337'), BPC(P_LIMB, 'BP_SeveredLimb337'), BPC(P_CAP, 'BP_WoundCap337')
BURST = BPC(P_BURST, 'BP_BloodBurst')
ACOMP, POSE, SMC, CAPS = CLS('ActorComponent'), CLS('PoseableMeshComponent'), CLS('StaticMeshComponent'), CLS('CapsuleComponent')
SMESH, SKASSET, DECALC = CLS('StaticMesh'), CLS('SkinnedAsset'), CLS('DecalComponent')
EN = lambda n, e, d: {'name': n, 'cat': 'byte', 'obj': ENUM(e), 'default': d}
ROTP = lambda n, d='0, 0, 0', out=False: st(n, ROT, out=out, default=d)
F = lambda n, d=None, out=False: fl(n, out=out, default=d)
NAMEV, STRA, NAMEA = N('v'), arr(S('v')), arr(N('v'))


class B(bpkit.B):
    def pure(s, parent, member, pins, target, x, y, tag=None): return s.call(parent, member, pins, x, y, target=target, pure=True, const=True, tag=tag)
    def sockloc(s, mesh, name, x, y):
        n = s.pure(SCENE, 'GetSocketLocation', [N('InSocketName'), V('ReturnValue', out=True)], mesh, x, y); s.wire(name, n, 'InSocketName'); return (n, 'ReturnValue')
    def tostrname(s, src, x, y):
        n = s.lib(KSTR, 'Conv_StringToName', [S('InString'), dict(N('ReturnValue'), out=True)], x, y, pure=True)
        s.wire(src, n, 'InString'); return (n, 'ReturnValue')
    def vmulf(s, v, f_, x, y, db='1.0'):
        return s.math('Multiply_VectorFloat', [(V('A'), v), (D('B', default=db), f_)], V('ReturnValue', out=True), x, y)


def check_write(G, fname):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('%s: bad links %s / dup %s' % (fname, bad[:10], [n for n in names if names.count(n) > 1][:5]))
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write(G.render())
    print('%s: nodes %d, links %d' % (fname, len(G.nodes), len(G.links)))


# ====================================================================================================== BPC_Gore337
G = Graph(); b = B(G, 'g'); g = b.get
b.event('OnHit', [D('Damage'), ob('Causer', ACT), bo('Killing'), D('MaxHP')], 0, 0)
ev = lambda p: ('OnHit', p)
hits = b.set('Hits', INT, b.i2('Add_IntInt', g('Hits', INT, 200, 200), None, 400, 200, db='1'), 300, 0)
G.link('OnHit', 'then', hits, 'execute')
ok = b.branch(b.b2('BooleanAND', b.icmp('Greater_IntInt', g('GoreLevel', INT, 500, 200), None, 700, 200), b.valid(ev('Causer'), 700, 300), 900, 200), 600, 0, tag='IfGore')
G.link(hits, 'then', ok, 'execute')
sq = b.seq('gSeq', 2, 900, 0); G.link(ok, 'then', sq, 'execute')
owner = b.call(ACOMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], 900, 400, pure=True, const=True)
G.nodes[-1][3][0]['hidden'] = True
oloc = b.pure(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], (owner, 'ReturnValue'), 1100, 400)

# ---- then_0: one drying splat under the zombie
Y = -900
off = b.vec(b.rnd('-40.0', '40.0', 1100, Y + 300), b.rnd('-40.0', '40.0', 1100, Y + 400), None, 1300, Y + 300, dz='60.0')
start = b.v2('Add_VectorVector', (oloc, 'ReturnValue'), off, 1500, Y + 300)
end = b.v2('Subtract_VectorVector', start, None, 1700, Y + 400, db='0, 0, 400')
tr = b.lib(KSL, 'LineTraceSingle', [WC(), V('Start'), V('End'), EN('TraceChannel', 'ETraceTypeQuery', 'TraceTypeQuery1'), bo('bTraceComplex', default='false'),
                                     arr(ob('ActorsToIgnore', ACT)), EN('DrawDebugType', 'EDrawDebugTrace', 'None'), st('OutHit', HITRES, out=True),
                                     bo('bIgnoreSelf', default='true'), bo('ReturnValue', out=True, default='false')], 1900, Y, tag='TraceDown')
b.wire(start, tr, 'Start'); b.wire(end, tr, 'End'); G.link(sq, 'then_0', tr, 'execute')
bh = b.lib(GS, 'BreakHitResult', [st('Hit', HITRES), bo('bBlockingHit', out=True, default='false'), V('Location', out=True), V('ImpactNormal', out=True)], 2150, Y + 300, pure=True)
b.wire((tr, 'OutHit'), bh, 'Hit')
bt = b.branch((tr, 'ReturnValue'), 2200, Y, tag='IfFloor')
G.link(tr, 'then', bt, 'execute')
heavy = b.dcmp('GreaterEqual_DoubleDouble', ev('Damage'), b.d2('Multiply_DoubleDouble', ev('MaxHP'), g('HeavyFrac', DBL, 2200, Y + 650), 2400, Y + 600), 2600, Y + 600)
big = b.b2('BooleanOR', heavy, ev('Killing'), 2800, Y + 600)
sz = b.self_(b.rnd('40.0', '55.0', 2800, Y + 750), b.rnd('15.0', '40.0', 2800, Y + 850), big, 3000, Y + 700)
dsize = b.vec(None, sz, sz, 3200, Y + 650, dx='12.0')
drot = b.math('MakeRotator', [(D('Roll', default='0.0'), None), (D('Pitch', default='-90.0'), None), (D('Yaw'), b.rnd('0.0', '360.0', 3200, Y + 850))],
              ROTP('ReturnValue', out=True), 3400, Y + 800)
dec = b.lib(GS, 'SpawnDecalAtLocation', [WC(), ob('DecalMaterial', MATI), V('DecalSize', default='12, 30, 30'), V('Location'), ROTP('Rotation', '-90, 0, 0'),
                                         F('LifeSpan', '33.0'), ob('ReturnValue', DECALC, out=True)], 3600, Y, tag='Splat')
b.wire(g('DecalMat', MATV, 3400, Y + 250), dec, 'DecalMaterial'); b.wire(dsize, dec, 'DecalSize'); b.wire((bh, 'Location'), dec, 'Location'); b.wire(drot, dec, 'Rotation')
G.link(bt, 'then', dec, 'execute')
mid = b.call(DECALC, 'CreateDynamicMaterialInstance', [ob('ReturnValue', MID, out=True)], 3900, Y, target=(dec, 'ReturnValue'))
G.link(dec, 'then', mid, 'execute')
ri = b.lib(KML, 'RandomIntegerInRange', [it('Min', default='0'), it('Max', default='7'), it('ReturnValue', out=True)], 3900, Y + 300, pure=True)
idx = b.i2d((ri, 'ReturnValue'), 4100, Y + 300)
sp1 = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', 'Index'), F('Value')], 4200, Y, target=(mid, 'ReturnValue'), tag='SetIndex')
b.wire(idx, sp1, 'Value'); G.link(mid, 'then', sp1, 'execute')
sp2 = b.call(MID, 'SetScalarParameterValue', [N('ParameterName', 'SpawnT'), F('Value')], 4500, Y, target=(mid, 'ReturnValue'), tag='SetSpawnT')
b.wire(b.now(4300, Y + 300), sp2, 'Value'); G.link(sp1, 'then', sp2, 'execute')

# ---- then_1: sever?
Y = 600
twice = b.b2('BooleanOR', ev('Killing'), b.icmp('GreaterEqual_IntInt', g('Hits', INT, 1000, Y + 500), None, 1200, Y + 500, db='2'), 1400, Y + 500)
room = b.icmp('Less_IntInt', b.alen('Severed', N('v'), 1200, Y + 650), g('MaxSevers', INT, 1200, Y + 750), 1500, Y + 650)
c1 = b.b2('BooleanAND', b.b2('BooleanAND', big, twice, 1600, Y + 400), b.b2('BooleanAND', room, g('LimbsOn', BOOL, 1500, Y + 800), 1700, Y + 700), 1800, Y + 500)
b1 = b.branch(c1, 1100, Y, tag='IfSever'); G.link(sq, 'then_1', b1, 'execute')
cp = 'gCastPawn'; cast(G, cp, PAWN, 'AsPawn', 1350, Y); b.wire(ev('Causer'), cp, 'Object'); G.link(b1, 'then', cp, 'execute')
dist = b.pure(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), D('ReturnValue', out=True)], (owner, 'ReturnValue'), 1500, Y + 250, tag='DistCauser')
b.wire(ev('Causer'), dist, 'OtherActor')
near = b.dcmp('Less_DoubleDouble', (dist, 'ReturnValue'), g('MeleeRange', DBL, 1650, Y + 350), 1800, Y + 250)
b2_ = b.branch(near, 1650, Y, tag='IfMelee'); G.link(cp, 'then', b2_, 'execute')
ga = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_LIMB)), arr(ob('OutActors', ACT, out=True))], 1900, Y, tag='AllLimbs')
G.link(b2_, 'then', ga, 'execute')
alen = b.name('LenLimbs')
G.node(alen, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Length")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('ReturnValue', out=True, default='0')], 2100, Y + 300)
G.link(ga, 'OutActors', alen, 'TargetArray')
b3 = b.branch(b.icmp('Less_IntInt', (alen, 'ReturnValue'), g('MaxLimbs', INT, 2100, Y + 450), 2300, Y + 300), 2200, Y, tag='IfRoomLimbs')
G.link(ga, 'then', b3, 'execute')
# roll the limb: 0 forearm, 1 upper arm, 2 lower leg, 3 head, -1 none
r = b.math('RandomFloat', [], D('ReturnValue', out=True), 2300, Y + 600)
K = ev('Killing')
pF = b.self_(None, None, K, 2300, Y + 750, da='0.35', db='0.25')
pU = b.d2('Add_DoubleDouble', pF, b.self_(None, None, K, 2300, Y + 900, da='0.20', db='0.10'), 2500, Y + 850)
pL = b.d2('Add_DoubleDouble', pU, b.self_(None, None, K, 2300, Y + 1050, da='0.15', db='0.0'), 2500, Y + 1000)
headok = b.b2('BooleanAND', K, b.icmp('GreaterEqual_IntInt', g('GoreLevel', INT, 2300, Y + 1250), None, 2450, Y + 1250, db='2'), 2600, Y + 1200)
pH = b.d2('Add_DoubleDouble', pL, b.self_(None, None, headok, 2700, Y + 1200, da='0.10', db='0.0'), 2900, Y + 1150)
sel = lambda a, c, cond, x, y, da='0', db='0': b.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), c), (bo('bPickA', default='false'), cond)], it('ReturnValue', out=True), x, y)
lt = lambda p, x, y: b.dcmp('Less_DoubleDouble', r, p, x, y)
k3 = sel(None, None, lt(pH, 3000, Y + 1150), 3200, Y + 1150, da='3', db='-1')
k2 = sel(None, k3, lt(pL, 3000, Y + 1000), 3400, Y + 1000, da='2')
k1 = sel(None, k2, lt(pU, 3000, Y + 850), 3600, Y + 850, da='1')
kind = sel(None, k1, lt(pF, 3000, Y + 700), 3800, Y + 700, da='0')
sk = b.set('Kind', INT, kind, 2500, Y)
G.link(b3, 'then', sk, 'execute')
# names: head = Neck / Head, else Left|Right + base
side = b.selstr(None, None, b.math('RandomBool', [], bo('ReturnValue', out=True), 2700, Y + 200), 2900, Y + 200, da='Left', db='Right')
isHead = b.icmp('EqualEqual_IntInt', g('Kind', INT, 2700, Y + 400), None, 2900, Y + 400, db='3')
kg = g('Kind', INT, 2700, Y + 500)
bone_s = b.selstr(None, b.concat(side, b.aget('BoneBase', S('v'), kg, 3000, Y + 300), 3300, Y + 300), isHead, 3500, Y + 300, da='Neck')
child_s = b.selstr(None, b.concat(side, b.aget('ChildBase', S('v'), kg, 3000, Y + 450), 3300, Y + 450), isHead, 3500, Y + 450, da='Head')
sb = b.set('CutBone', NAMEV, b.tostrname(bone_s, 3700, Y + 300), 2800, Y)
sc_ = b.set('CutChild', NAMEV, b.tostrname(child_s, 3700, Y + 450), 3100, Y)
b.chain(sk, sb, sc_)
cont = b.name('Contains')
G.node(cont, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True, 'const': True},
        {'name': 'ItemToFind', 'cat': 'wildcard', 'ref': True}, bo('ReturnValue', out=True, default='false')], 3300, Y + 600)
b.wire(g('Severed', NAMEA, 3100, Y + 600), cont, 'TargetArray'); b.wire(g('CutBone', NAMEV, 3100, Y + 700), cont, 'ItemToFind')
go = b.b2('BooleanAND', b.icmp('GreaterEqual_IntInt', g('Kind', INT, 3300, Y + 800), None, 3500, Y + 800, db='0'), b.bnot((cont, 'ReturnValue'), 3500, Y + 650), 3700, Y + 700)
b4 = b.branch(go, 3400, Y, tag='IfLimb'); G.link(sc_, 'then', b4, 'execute')
cc = 'gCastChar'; cast(G, cc, CHARC, 'AsCharacter', 3650, Y); b.wire((owner, 'ReturnValue'), cc, 'Object'); G.link(b4, 'then', cc, 'execute')
mesh = b.getm('Mesh', CHARC, ob('v', SKEL), (cc, 'AsCharacter'), 3900, Y + 250)
sm = b.set('ZMesh', ob('v', SKEL), mesh, 4100, Y); G.link(cc, 'then', sm, 'execute')
zm = lambda x, y: g('ZMesh', ob('v', SKEL), x, y)
bl = b.sockloc(zm(4200, Y + 400), g('CutBone', NAMEV, 4200, Y + 500), 4400, Y + 400)
cl = b.sockloc(zm(4200, Y + 600), g('CutChild', NAMEV, 4200, Y + 700), 4400, Y + 600)
dirv = b.math('GetDirectionUnitVector', [(V('From'), bl), (V('To'), cl)], V('ReturnValue', out=True), 4600, Y + 500)
midp = b.math('Divide_VectorFloat', [(V('A'), b.v2('Add_VectorVector', bl, cl, 4600, Y + 300)), (D('B', default='2.0'), None)], V('ReturnValue', out=True), 4800, Y + 300)
rz = b.math('MakeRotFromZ', [(V('Z'), dirv)], ROTP('ReturnValue', out=True), 4800, Y + 500)
xf = b.math('MakeTransform', [(V('Location'), midp), (ROTP('Rotation'), rz), (V('Scale', default='1.000000,1.000000,1.000000'), None)], st('ReturnValue', XFORM, out=True), 5000, Y + 400)
sl = spawn(b, P_LIMB, LIMB, xf, 5200, Y); G.link(sm, 'then', sl, 'execute')
away = b.math('Normal', [(V('A'), b.v2('Subtract_VectorVector', (oloc, 'ReturnValue'), (b.pure(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], (cp, 'AsPawn'), 5000, Y + 900, tag='CauserLoc'), 'ReturnValue'),
                                                   5200, Y + 850)), (fl('Tolerance', default='0.0001'), None)], V('ReturnValue', out=True), 5400, Y + 850)
imp = b.vmulf(b.v2('Add_VectorVector', away, None, 5600, Y + 850, db='0, 0, 0.7'), b.rnd('300.0', '600.0', 5600, Y + 1000), 5800, Y + 850)
capm = b.aget('Caps', ob('v', SMESH), g('Kind', INT, 5300, Y + 1150), 5400, Y + 1100)
setup = b.call(LIMB, 'Setup', [ob('Src', SKEL), N('Bone'), N('Child'), ob('CapMesh', SMESH), V('Impulse')], 5600, Y, target=(sl, 'ReturnValue'), tag='LimbSetup')
for p, src in (('Src', zm(5400, Y + 300)), ('Bone', g('CutBone', NAMEV, 5400, Y + 400)), ('Child', g('CutChild', NAMEV, 5400, Y + 500)), ('CapMesh', capm), ('Impulse', imp)):
    b.wire(src, setup, p)
G.link(sl, 'then', setup, 'execute')
hide = b.call(SKIN, 'HideBoneByName', [N('BoneName'), EN('PhysBodyOption', 'EPhysBodyOp', 'PBO_None')], 5900, Y, target=zm(5800, Y + 250))
b.wire(g('CutBone', NAMEV, 5800, Y + 350), hide, 'BoneName'); G.link(setup, 'then', hide, 'execute')
cxf = b.math('MakeTransform', [(V('Location'), bl), (ROTP('Rotation'), None), (V('Scale', default='1.000000,1.000000,1.000000'), None)], st('ReturnValue', XFORM, out=True), 6000, Y + 400)
scp = spawn(b, P_CAP, CAPA, cxf, 6200, Y); G.link(hide, 'then', scp, 'execute')
csu = b.call(CAPA, 'Setup', [ob('Src', SKEL), N('Bone'), N('Child'), ob('CapMesh', SMESH)], 6500, Y, target=(scp, 'ReturnValue'), tag='CapSetup')
for p, src in (('Src', zm(6300, Y + 300)), ('Bone', g('CutBone', NAMEV, 6300, Y + 400)), ('Child', g('CutChild', NAMEV, 6300, Y + 500)), ('CapMesh', capm)):
    b.wire(src, csu, p)
G.link(scp, 'then', csu, 'execute')
add = b.aadd('Severed', N('v'), g('CutBone', NAMEV, 6700, Y + 300), 6800, Y); G.link(csu, 'then', add, 'execute')
bb = spawn(b, P_BURST, BURST, cxf, 7100, Y); G.link(add, 'then', bb, 'execute')
check_write(G, 'BPC_Gore337_graph.txt')

# ====================================================================================================== BP_SeveredLimb337
G = Graph(); b = B(G, 'l'); g = b.get
b.event('Setup', [ob('Src', SKEL), N('Bone'), N('Child'), ob('CapMesh', SMESH), V('Impulse')], 0, 0)
E_ = lambda p: ('Setup', p)
limb = lambda x, y: g('Limb', ob('v', POSE), x, y)
body = lambda x, y: g('Body', ob('v', CAPS), x, y)
asset = b.pure(SKIN, 'GetSkinnedAsset', [ob('ReturnValue', SKASSET, out=True)], E_('Src'), 200, 300)
s1 = b.call(SKIN, 'SetSkinnedAssetAndUpdate', [ob('NewMesh', SKASSET), bo('bReinitPose', default='true')], 300, 0, target=limb(150, 200))
b.wire((asset, 'ReturnValue'), s1, 'NewMesh'); G.link('Setup', 'then', s1, 'execute')
nm = b.pure(PRIM, 'GetNumMaterials', [it('ReturnValue', out=True)], E_('Src'), 400, 300)
fl_ = b.forloop(None, b.i2('Subtract_IntInt', (nm, 'ReturnValue'), None, 600, 300, db='1'), 700, 0); G.link(s1, 'then', fl_, 'execute')
gm = b.pure(PRIM, 'GetMaterial', [it('ElementIndex'), ob('ReturnValue', MATI, out=True)], E_('Src'), 900, 300); b.wire((fl_, 'Index'), gm, 'ElementIndex')
sm_ = b.call(PRIM, 'SetMaterial', [it('ElementIndex'), ob('Material', MATI)], 1000, -200, target=limb(900, -50))
b.wire((fl_, 'Index'), sm_, 'ElementIndex'); b.wire((gm, 'ReturnValue'), sm_, 'Material'); G.link(fl_, 'LoopBody', sm_, 'execute')
cpy = b.call(POSE, 'CopyPoseFromSkeletalComponent', [ob('InComponentToCopy', SKEL)], 1000, 0, target=limb(900, 200))
b.wire(E_('Src'), cpy, 'InComponentToCopy'); G.link(fl_, 'Completed', cpy, 'execute')
sh = b.call(POSE, 'SetBoneScaleByName', [N('BoneName', 'Hips'), V('InScale3D', default='0.0001, 0.0001, 0.0001'), EN('BoneSpace', 'EBoneSpaces', 'ComponentSpace')], 1300, 0,
            target=limb(1200, 200), tag='CollapseAll')
sk_ = b.call(POSE, 'SetBoneScaleByName', [N('BoneName'), V('InScale3D', default='1, 1, 1'), EN('BoneSpace', 'EBoneSpaces', 'ComponentSpace')], 1600, 0,
             target=limb(1500, 200), tag='KeepLimb')
b.wire(E_('Bone'), sk_, 'BoneName'); b.chain(cpy, sh, sk_)
tm = b.call(POSE, 'GetBoneTransformByName', [N('BoneName'), EN('BoneSpace', 'EBoneSpaces', 'WorldSpace'), st('ReturnValue', XFORM, out=True)], 1900, 0, target=limb(1800, 200))
b.wire(E_('Bone'), tm, 'BoneName'); G.link(sk_, 'then', tm, 'execute')
tt = b.pure(SCENE, 'GetSocketTransform', [N('InSocketName'), EN('TransformSpace', 'ERelativeTransformSpace', 'RTS_World'), st('ReturnValue', XFORM, out=True)], E_('Src'), 1900, 400)
b.wire(E_('Bone'), tt, 'InSocketName')
cw = b.pure(SCENE, 'K2_GetComponentToWorld', [st('ReturnValue', XFORM, out=True)], limb(1900, 650), 2100, 600)
inv = b.math('InvertTransform', [(st('T', XFORM), (tm, 'ReturnValue'))], st('ReturnValue', XFORM, out=True), 2200, 300)
c1_ = b.math('ComposeTransforms', [(st('A', XFORM), (cw, 'ReturnValue')), (st('B', XFORM), inv)], st('ReturnValue', XFORM, out=True), 2400, 400)
c2_ = b.math('ComposeTransforms', [(st('A', XFORM), c1_), (st('B', XFORM), (tt, 'ReturnValue'))], st('ReturnValue', XFORM, out=True), 2600, 400)
swt = b.call(SCENE, 'K2_SetWorldTransform', [st('NewTransform', XFORM), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             2800, 0, target=limb(2700, 250))
b.wire(c2_, swt, 'NewTransform'); G.link(tm, 'then', swt, 'execute')
blo = b.sockloc(E_('Src'), E_('Bone'), 2900, 500); clo = b.sockloc(E_('Src'), E_('Child'), 2900, 650)
ln = b.math('Vector_Distance', [(V('V1'), blo), (V('V2'), clo)], D('ReturnValue', out=True), 3100, 550)
hh = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', ln, None, 3300, 550, db='0.5'), None, 3500, 550, db='7.0')
cs = b.call(CAPS, 'SetCapsuleSize', [F('InRadius', '7.0'), F('InHalfHeight'), bo('bUpdateOverlaps', default='true')], 3100, 0, target=body(3000, 250))
b.wire(hh, cs, 'InHalfHeight'); G.link(swt, 'then', cs, 'execute')
lc = lambda x, y: g('LimbCap', ob('v', SMC), x, y)
at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName'), EN('LocationRule', 'EAttachmentRule', 'SnapToTarget'), EN('RotationRule', 'EAttachmentRule', 'KeepWorld'),
                                            EN('ScaleRule', 'EAttachmentRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')],
            3400, 0, target=lc(3300, 250), tag='AttachLimbCap')
b.wire(limb(3300, 350), at, 'Parent'); b.wire(E_('Bone'), at, 'SocketName'); G.link(cs, 'then', at, 'execute')
ssm = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SMESH), bo('ReturnValue', out=True, default='false')], 3700, 0, target=lc(3600, 250))
b.wire(E_('CapMesh'), ssm, 'NewMesh'); G.link(at, 'then', ssm, 'execute')
rx = b.math('MakeRotFromX', [(V('X'), b.v2('Subtract_VectorVector', blo, clo, 3800, 500))], ROTP('ReturnValue', out=True), 4000, 450)   # faces back toward the body
swr = b.call(SCENE, 'K2_SetWorldRotation', [ROTP('NewRotation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             4000, 0, target=lc(3900, 250))
b.wire(rx, swr, 'NewRotation'); G.link(ssm, 'then', swr, 'execute')
cpn = b.call(PRIM, 'SetCollisionProfileName', [N('InCollisionProfileName', 'PhysicsActor'), bo('bUpdateOverlaps', default='true')], 4300, 0, target=body(4200, 250))
crp = b.call(PRIM, 'SetCollisionResponseToChannel', [EN('Channel', 'ECollisionChannel', 'ECC_Pawn'), EN('NewResponse', 'ECollisionResponse', 'ECR_Ignore')], 4600, 0, target=body(4500, 250))
phy = b.call(PRIM, 'SetSimulatePhysics', [bo('bSimulate', default='true')], 4900, 0, target=body(4800, 250))
ai = b.call(PRIM, 'AddImpulse', [V('Impulse'), N('BoneName', 'None'), bo('bVelChange', default='true')], 5200, 0, target=body(5100, 250))
b.wire(E_('Impulse'), ai, 'Impulse')
spin = b.vmulf(b.math('RandomUnitVector', [], V('ReturnValue', out=True), 5300, 400), b.rnd('90.0', '360.0', 5300, 550), 5500, 450)
aa = b.call(PRIM, 'AddAngularImpulseInDegrees', [V('Impulse'), N('BoneName', 'None'), bo('bVelChange', default='true')], 5500, 0, target=body(5400, 250))
b.wire(spin, aa, 'Impulse')
ls = b.call_self('SetLifeSpan', [F('InLifespan', '20.0')], 5800, 0, ACT)
b.chain(swr, cpn, crp, phy, ai, aa, ls)
check_write(G, 'BP_SeveredLimb337_graph.txt')

# ====================================================================================================== BP_WoundCap337
G = Graph(); b = B(G, 'c'); g = b.get
cap = lambda x, y: g('Cap', ob('v', SMC), x, y)
b.event('Setup', [ob('Src', SKEL), N('Bone'), N('Child'), ob('CapMesh', SMESH)], 0, 0)
E_ = lambda p: ('Setup', p)
ssm = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SMESH), bo('ReturnValue', out=True, default='false')], 300, 0, target=cap(200, 250))
b.wire(E_('CapMesh'), ssm, 'NewMesh'); G.link('Setup', 'then', ssm, 'execute')
at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName'), EN('LocationRule', 'EAttachmentRule', 'SnapToTarget'), EN('RotationRule', 'EAttachmentRule', 'KeepWorld'),
                                            EN('ScaleRule', 'EAttachmentRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')],
            600, 0, target=cap(500, 250), tag='AttachStump')
b.wire(E_('Src'), at, 'Parent'); b.wire(E_('Bone'), at, 'SocketName'); G.link(ssm, 'then', at, 'execute')
blo = b.sockloc(E_('Src'), E_('Bone'), 600, 400); clo = b.sockloc(E_('Src'), E_('Child'), 600, 550)
rx = b.math('MakeRotFromX', [(V('X'), b.v2('Subtract_VectorVector', clo, blo, 800, 450))], ROTP('ReturnValue', out=True), 1000, 450)   # faces out of the stump
swr = b.call(SCENE, 'K2_SetWorldRotation', [ROTP('NewRotation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
             900, 0, target=cap(800, 250))
b.wire(rx, swr, 'NewRotation'); G.link(at, 'then', swr, 'execute')
tmr = b.timer('CheckParent', 1200, 0, dtime='1.0', loop=True); G.link(swr, 'then', tmr, 'execute')
b.wire(b.self_node(1000, 200), tmr, 'Object')
# CheckParent: the zombie is gone -> the cap goes too
b.event('CheckParent', [], 0, 800)
par = b.call_self('GetAttachParentActor', [ob('ReturnValue', ACT, out=True)], 200, 1000, ACT, pure=True, const=True)
bv = b.branch(b.valid((par, 'ReturnValue'), 300, 1000), 300, 800, tag='IfParent')
G.link('CheckParent', 'then', bv, 'execute')
G.link(bv, 'else', b.call_self('K2_DestroyActor', [], 600, 800, ACT), 'execute')
check_write(G, 'BP_WoundCap337_graph.txt')

# ====================================================================================================== BP_Zombie hook
G = Graph(); b = B(G, 'zg'); g = b.get
ZB = BPC('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', 'BP_Zombie')
seqi = b.seq('GoreIn', 1, 3700, 11500)
kill = b.dcmp('GreaterEqual_DoubleDouble', g('DamageTaken', DBL, 3700, 11800), g('MaxHP', DBL, 3700, 11900), 3900, 11850)
oh = b.call(GORE, 'OnHit', [D('Damage'), ob('Causer', ACT), bo('Killing', default='false'), D('MaxHP')], 4100, 11500, target=g('Gore', ob('v', GORE), 3900, 11700), tag='GoreHit')
b.wire(kill, oh, 'Killing'); b.wire(g('MaxHP', DBL, 3900, 12000), oh, 'MaxHP')
G.link(seqi, 'then_0', oh, 'execute')
seqo = b.seq('GoreOut', 1, 4400, 11500); G.link(oh, 'then', seqo, 'execute')
check_write(G, 'Zombie_GoreHook_graph.txt')
man = {'blueprint': 'BP_Zombie', 'note': '#337: gore hook right after the BP_BloodBurst spawn (built on the 10-30b export)',
       'pastes': [{'file': 'Zombie_GoreHook_graph.txt'}],
       'rewires': [{'from': 'K2Node_SpawnActorFromClass_ZB93.then', 'to': 'GoreIn.execute', 'replace': True, 'note': 'was -> K2Node_IfThenElse_ZB68'},
                   {'from': 'GoreOut.then_0', 'to': 'K2Node_IfThenElse_ZB68.execute'},
                   {'from': 'K2Node_Event_ZB60.Damage', 'to': oh + '.Damage'},
                   {'from': 'K2Node_Event_ZB60.DamageCauser', 'to': oh + '.Causer'}]}
json.dump(man, open(os.path.join(HERE, 'manifest_zombie_gore.json'), 'w'), indent=1)

# ====================================================================================================== BPVar lines
DT = 'PinCategory="real",PinSubCategory="double"'
OBJT = lambda c: 'PinCategory="object",PinSubCategoryObject="%s"' % c.strip('"')
GVARS = [('Hits', 'PinCategory="int"', '0', 'hits taken'), ('Severed', 'PinCategory="name",ContainerType=Array', '', 'bones already cut'),
         ('MaxSevers', 'PinCategory="int"', '2', 'max limbs per zombie'), ('HeavyFrac', DT, '0.25', 'heavy hit = this share of MaxHP or more'),
         ('GoreLevel', 'PinCategory="int"', '1', '0 off (no splats, no severing), 1 reduced (default, no head), 2 full'),
         ('LimbsOn', 'PinCategory="bool"', 'true', 'false = splats only'), ('MeleeRange', DT, '350.0', 'cm: only hits from this close can sever'),
         ('MaxLimbs', 'PinCategory="int"', '8', 'loose limbs in the world at once'),
         ('BoneBase', 'PinCategory="string",ContainerType=Array', '("ForeArm","Arm","Leg","Neck")', 'SK_Zombie bone per kind (with Left/Right)'),
         ('ChildBase', 'PinCategory="string",ContainerType=Array', '("Hand","ForeArm","Foot","Head")', 'the next bone down (sets the limb length)'),
         ('Caps', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.StaticMesh\'",ContainerType=Array', '', 'set by the setup script: Forearm / UpperArm / Calf / Neck caps'),
         ('DecalMat', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.MaterialInterface\'"', '', 'set by the setup script: MI_BloodDecal_337'),
         ('Kind', 'PinCategory="int"', '-1', 'state'), ('CutBone', 'PinCategory="name"', '', 'state'), ('CutChild', 'PinCategory="name"', '', 'state'),
         ('ZMesh', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.SkeletalMeshComponent\'"', '', 'state')]


def bpvars(rows, tag, fname, title):
    bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
        n, uuid.uuid5(uuid.NAMESPACE_URL, tag + n).hex.upper(), t, n, d.replace('"', '\\"'))
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write('# ' + title + '\n' + '\n'.join(bpv(*v[:3]) for v in rows) + '\n')
    print('%s: %d' % (fname, len(rows)))


bpvars(GVARS, 'gore337/bpc/', 'BPC_Gore337_BPVar.txt', '#337 BPC_Gore337 - paste one line at a time on the VARIABLES header, then Compile')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #337 BPC_Gore337 variables\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _t, d, m in GVARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
