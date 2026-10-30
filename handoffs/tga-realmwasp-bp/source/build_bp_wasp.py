# BP_RealmWasp (#167 behaviour) + the swarm spawn hook in BP_ZombieWaveManager. TGA, 2026-10-30.
# Writes the paste files, BPVar lines and manifests into OUT. Node blocks are cloned from the Master's 2026-10-30
# exports (bpkit), so their pins are exactly what UE 5.3 serialises.
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bpkit import Export, Graph, bpvar, var_get, var_set, fl, it, bo, ob, vec, CLS
E = r'R:\handoffs\exports\master\2026-10-30'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'T:\bp\out'
os.makedirs(OUT, exist_ok=True)
Z = Export(E + r'\BP_Zombie.t3d'); W = Export(E + r'\BP_ZombieWaveManager.t3d'); A = Export(E + r'\BP_ArmoryHUD.t3d')
WASP = '/Game/CastleDefender/Characters/Enemies/RealmWasp'
def asset(n): return '%s/%s.%s' % (WASP, n, n)
BPC = lambda p: '"/Script/Engine.BlueprintGeneratedClass\'%s\'"' % p
CANNON = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannon.BP_Cannon_C'
GATE = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl.BP_CastleGateControl_C'
WASPC = WASP + '/BP_RealmWasp.BP_RealmWasp_C'
OBJT = lambda path: 'PinType.PinCategory="object",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass\'%s\'"' % path

def T(ex, cls, member=None, extra=None): return ex.find(cls, member, extra)
G = Graph('WSP')
def C(ex, cls, member=None, x=0, y=0, extra=None): return G.clone(ex, T(ex, cls, member, extra), x, y)
def call(member, x, y, ex=Z, extra=None): return C(ex, 'K2Node_CallFunction', member, x, y, extra)
def br(x, y): return C(Z, 'K2Node_IfThenElse', None, x, y)
def seq(n, x, y):
    s = C(Z, 'K2Node_ExecutionSequence', None, x, y)
    proto = [p for p in s.pins if p['name'] == 'then_1'][0]
    for i in range(2, n):
        q = dict(proto); q['name'] = 'then_%d' % i; q['id'] = __import__('bpkit').g(); q['line'] = proto['line'].replace('PinName="then_1"', 'PinName="then_%d"' % i); s.pins.append(q)
    return s
def mesh(x, y): return C(Z, 'K2Node_VariableGet', 'Mesh', x, y)
def getv(name, pin, x, y): return var_get(G, name, pin, x, y)
def setv(name, pin, x, y, value=None):
    n = var_set(G, name, pin, x, y)
    if value is not None: n.set_default(name, value)
    return n
def play(anim, loop, x, y):
    n = call('PlayAnimation', x, y); n.set_default('NewAnimToPlay', obj=asset(anim)); n.set_default('bLooping', 'true' if loop else 'false')
    G.link(mesh(x - 220, y + 120), 'Mesh', n, 'self'); return n
def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]): G.link(a, 'then', b, 'execute')
    return nodes[-1]
def eqint(var, k, x, y):
    e = call('EqualEqual_IntInt', x, y); G.link(getv(var, it(var), x - 200, y), var, e, 'A'); e.set_default('B', str(k)); return e
def stg(x, y, lit=None):     # StateTime > lit
    c = call('Greater_DoubleDouble', x, y); G.link(getv('StateTime', fl('StateTime'), x - 200, y), 'StateTime', c, 'A'); c.set_default('B', str(lit)); return c
def actor_loc_of(objnode, pin, x, y):
    n = call('K2_GetActorLocation', x, y)   # UE writes calls on other actors as self-context with an Actor self pin
    G.link(objnode, pin, n, 'self'); return n
def self_loc(x, y): return call('K2_GetActorLocation', x, y, extra='bSelfContext=True')
def vadd(a, apin, b, bpin, x, y):
    n = call('Add_VectorVector', x, y); G.link(a, apin, n, 'A'); G.link(b, bpin, n, 'B'); return n
def mkvec(x, y, X=None, Y=None, Zv=None):
    n = call('MakeVector', x, y)
    for k, v in (('X', X), ('Y', Y), ('Z', Zv)):
        if v is not None: n.set_default(k, str(v))
    return n
OBJ_ACTOR = ob('Target', CLS('Actor'))

# ---------------- BeginPlay ----------------------------------------------------------------------------------------
x0, y0 = 0, 0
ev = C(Z, 'K2Node_Event', 'ReceiveBeginPlay', x0, y0)
# SetSkeletalMeshAsset is not in the exports: clone SetMaterial's shell (a SkeletalMeshComponent call) and retarget it
sm = call('SetMaterial', x0 + 300, y0)
sm.sub_prop('/Script/Engine.PrimitiveComponent', '/Script/Engine.SkeletalMeshComponent').sub_prop('MemberName="SetMaterial"', 'MemberName="SetSkeletalMeshAsset"')
sm.pins = [p for p in sm.pins if p['name'] not in ('ElementIndex',)]
mp = sm.pin('Material'); mp['name'] = 'NewMesh'
mp['line'] = re.sub(r'PinName="Material"', 'PinName="NewMesh"', mp['line']).replace("/Script/Engine.MaterialInterface", "/Script/Engine.SkeletalMesh")
sm.set_default('NewMesh', obj=asset('SK_RealmWasp'))
sp = sm.pin('self'); sp['line'] = sp['line'].replace('/Script/Engine.PrimitiveComponent', '/Script/Engine.SkeletalMeshComponent')
G.link(mesh(x0 + 100, y0 + 150), 'Mesh', sm, 'self')
rel = call('K2_SetRelativeLocation', x0 + 600, y0); rel.set_default('NewLocation', '0.000000,0.000000,-130.000000'); G.link(mesh(x0 + 400, y0 + 150), 'Mesh', rel, 'self')
cap = G.clone(W, T(W, 'K2Node_CallFunction', 'SetCapsuleSize'), x0 + 900, y0); cap.set_default('InRadius', '45.0').set_default('InHalfHeight', '60.0')
G.link(C(Z, 'K2Node_VariableGet', 'CapsuleComponent', x0 + 700, y0 + 150), 'CapsuleComponent', cap, 'self')
grav = G.clone(W, T(W, 'K2Node_VariableSet', 'GravityScale'), x0 + 1200, y0); grav.set_default('GravityScale', '0.0')
G.link(C(Z, 'K2Node_VariableGet', 'CharacterMovement', x0 + 1000, y0 + 150), 'CharacterMovement', grav, 'self')
chain(ev, sm, rel, cap, grav)
skin = br(x0 + 1500, y0); rb = call('RandomBoolWithWeight', x0 + 1300, y0 + 180); rb.set_default('Weight', '0.3'); G.link(rb, 'ReturnValue', skin, 'Condition')
G.link(grav, 'then', skin, 'execute')
def setmat(idx, mi, x, y):
    n = call('SetMaterial', x, y); n.set_default('ElementIndex', str(idx)); n.set_default('Material', obj=asset(mi)); G.link(mesh(x - 200, y + 150), 'Mesh', n, 'self'); return n
b0, b1 = setmat(0, 'MI_RealmWasp_Body_Blight', x0 + 1800, y0 - 250), setmat(1, 'MI_RealmWasp_Wings_Blight', x0 + 2100, y0 - 250)
e0, e1 = setmat(0, 'MI_RealmWasp_Body_Ember', x0 + 1800, y0 + 250), setmat(1, 'MI_RealmWasp_Wings_Ember', x0 + 2100, y0 + 250)
G.link(skin, 'then', b0, 'execute'); G.link(b0, 'then', b1, 'execute'); G.link(skin, 'else', e0, 'execute'); G.link(e0, 'then', e1, 'execute')
hp = setv('MaxHP', fl('MaxHP'), x0 + 2400, y0, '80.0'); G.link(b1, 'then', hp, 'execute'); G.link(e1, 'then', hp, 'execute')
xpv = setv('XPValue', it('XPValue'), x0 + 2650, y0, '6'); ad = setv('AttackDamage', fl('AttackDamage'), x0 + 2900, y0, '14.0')
spl = setv('SpawnLoc', vec('SpawnLoc'), x0 + 3150, y0); G.link(self_loc(x0 + 2950, y0 + 200), 'ReturnValue', spl, 'SpawnLoc')
gl0 = setv('GoalLoc', vec('GoalLoc'), x0 + 3400, y0); G.link(self_loc(x0 + 3200, y0 + 200), 'ReturnValue', gl0, 'GoalLoc')
s0 = setv('State', it('State'), x0 + 3650, y0, '0'); st0 = setv('StateTime', fl('StateTime'), x0 + 3900, y0, '0.0')
cs0 = setv('CurSpeed', fl('CurSpeed'), x0 + 4150, y0); G.link(getv('FlySpeed', fl('FlySpeed'), x0 + 3950, y0 + 200), 'FlySpeed', cs0, 'CurSpeed')
chain(hp, xpv, ad, spl, gl0, s0, st0, cs0, play('A_RealmWasp_Hover', True, x0 + 4450, y0))

# ---------------- Tick: fly toward GoalLoc, face it, think every 0.2 s --------------------------------------------
x0, y0 = 0, 1200
tk = C(Z, 'K2Node_Event', 'ReceiveTick', x0, y0)
bd = br(x0 + 300, y0); G.link(C(Z, 'K2Node_VariableGet', 'Dead', x0 + 100, y0 + 150), 'Dead', bd, 'Condition'); G.link(tk, 'then', bd, 'execute')
ta = setv('ThinkAcc', fl('ThinkAcc'), x0 + 600, y0); add = call('Add_DoubleDouble', x0 + 400, y0 + 200)
G.link(getv('ThinkAcc', fl('ThinkAcc'), x0 + 200, y0 + 200), 'ThinkAcc', add, 'A'); G.link(tk, 'DeltaSeconds', add, 'B'); G.link(add, 'ReturnValue', ta, 'ThinkAcc')
G.link(bd, 'else', ta, 'execute')
# VInterpTo_Constant: clone Add_VectorVector (a KismetMathLibrary pure call) and give it the 4-input signature
vi = call('Add_VectorVector', x0 + 700, y0 + 300); vi.sub_prop('MemberName="Add_VectorVector"', 'MemberName="VInterpTo_Constant"')
for old, new in (('A', 'Current'), ('B', 'Target')):
    p = vi.pin(old, False); p['name'] = new; p['line'] = p['line'].replace('PinName="%s"' % old, 'PinName="%s"' % new)
rp = G.clone(Z, T(Z, 'K2Node_CallFunction', 'Multiply_DoubleDouble'), 0, 0).pin('A', False); del G.nodes[list(G.nodes)[-1]]
for nm in ('DeltaTime', 'InterpSpeed'):
    q = dict(rp); q['name'] = nm; q['id'] = __import__('bpkit').g(); q['line'] = rp['line'].replace('PinName="A"', 'PinName="%s"' % nm); vi.pins.insert(-1, q)
G.link(self_loc(x0 + 450, y0 + 300), 'ReturnValue', vi, 'Current'); G.link(getv('GoalLoc', vec('GoalLoc'), x0 + 450, y0 + 400), 'GoalLoc', vi, 'Target')
G.link(tk, 'DeltaSeconds', vi, 'DeltaTime'); G.link(getv('CurSpeed', fl('CurSpeed'), x0 + 450, y0 + 500), 'CurSpeed', vi, 'InterpSpeed')
# K2_SetActorLocation: clone K2_SetRelativeLocation (same parameter names) and retarget it to the actor, self context
sl = call('K2_SetRelativeLocation', x0 + 1000, y0)
sl.props = [l for l in sl.props if not l.startswith('FunctionReference')] + ['FunctionReference=(MemberName="K2_SetActorLocation",bSelfContext=True)']
rot_t = G.clone(Z, T(Z, 'K2Node_CallFunction', 'K2_SetActorRotation'), 0, 0); del G.nodes[rot_t.name]
sl.pins = [p if p['name'] != 'self' else dict(rot_t.pin('self'), id=__import__('bpkit').g()) for p in sl.pins]
rv = dict(rot_t.pin('ReturnValue'), id=__import__('bpkit').g()); sl.pins.append(rv)
sl.set_default('bTeleport', 'true')
G.link(vi, 'ReturnValue', sl, 'NewLocation'); G.link(ta, 'then', sl, 'execute')
fr = call('FindLookAtRotation', x0 + 1100, y0 + 300); G.link(self_loc(x0 + 900, y0 + 300), 'ReturnValue', fr, 'Start'); G.link(getv('GoalLoc', vec('GoalLoc'), x0 + 900, y0 + 420), 'GoalLoc', fr, 'Target')
brk = call('BreakRotator', x0 + 1300, y0 + 300); G.link(fr, 'ReturnValue', brk, 'InRot')
mr = call('MakeRotator', x0 + 1500, y0 + 300); G.link(brk, 'Yaw', mr, 'Yaw')
sr = call('K2_SetActorRotation', x0 + 1700, y0); G.link(mr, 'ReturnValue', sr, 'NewRotation'); G.link(sl, 'then', sr, 'execute')
bt = br(x0 + 2000, y0); ge = call('GreaterEqual_DoubleDouble', x0 + 1800, y0 + 200); G.link(getv('ThinkAcc', fl('ThinkAcc'), x0 + 1600, y0 + 200), 'ThinkAcc', ge, 'A'); ge.set_default('B', '0.2')
G.link(ge, 'ReturnValue', bt, 'Condition'); G.link(sr, 'then', bt, 'execute')
tr = setv('ThinkAcc', fl('ThinkAcc'), x0 + 2300, y0, '0.0'); G.link(bt, 'then', tr, 'execute')
sta = setv('StateTime', fl('StateTime'), x0 + 2550, y0); a2 = call('Add_DoubleDouble', x0 + 2350, y0 + 200)
G.link(getv('StateTime', fl('StateTime'), x0 + 2150, y0 + 200), 'StateTime', a2, 'A'); a2.set_default('B', '0.2'); G.link(a2, 'ReturnValue', sta, 'StateTime')
G.link(tr, 'then', sta, 'execute')
S = seq(6, x0 + 2850, y0); G.link(sta, 'then', S, 'execute')

# ---- then_0: pick a target when NeedTarget (cannons while Phase 0, then the castle gate, else the hero) -----------
x1, y1 = x0 + 3200, y0 - 1400
bn = br(x1, y1); G.link(getv('NeedTarget', bo('NeedTarget'), x1 - 200, y1 + 150), 'NeedTarget', bn, 'Condition'); G.link(S, 'then_0', bn, 'execute')
bp0 = br(x1 + 300, y1); G.link(eqint('Phase', 0, x1 + 100, y1 + 200), 'ReturnValue', bp0, 'Condition'); G.link(bn, 'then', bp0, 'execute')
ga = call('GetAllActorsOfClass', x1 + 600, y1 - 200); ga.set_default('ActorClass', obj=CANNON)
ga.retype('OutActors', "BP_SoldierSword.BP_SoldierSword_C", "BP_Cannon.BP_Cannon_C").retype('OutActors', '/Game/CastleDefender/Characters/Knight/', '/Game/CastleDefender/Gameplay/Cannon/')
G.link(bp0, 'then', ga, 'execute')
ln = G.clone(W, 'CX_2', x1 + 800, y1); ln.retype('TargetArray', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C', CANNON); G.link(ga, 'OutActors', ln, 'TargetArray')
gz = call('Greater_IntInt', x1 + 1000, y1, ex=W); G.link(ln, 'ReturnValue', gz, 'A'); gz.set_default('B', '0')
bc = br(x1 + 1200, y1 - 200); G.link(gz, 'ReturnValue', bc, 'Condition'); G.link(ga, 'then', bc, 'execute')
sub = call('Subtract_IntInt', x1 + 1000, y1 + 150, ex=W); G.link(ln, 'ReturnValue', sub, 'A'); sub.set_default('B', '1')
ri = call('RandomIntegerInRange', x1 + 1200, y1 + 150); ri.set_default('Min', '0'); G.link(sub, 'ReturnValue', ri, 'Max')
gi = G.clone(A, T(A, 'K2Node_GetArrayItem'), x1 + 1400, y1 + 50)
for pn in ('Array', 'Output'):
    p = gi.pin(pn); p['line'] = re.sub(r'PinType\.PinCategory="real",PinType\.PinSubCategory="\w*",PinType\.PinSubCategoryObject=None', OBJT(CANNON), p['line'])
G.link(ga, 'OutActors', gi, 'Array'); G.link(ri, 'ReturnValue', gi, 'Dimension 1')
stc = setv('Target', OBJ_ACTOR, x1 + 1700, y1 - 200); G.link(gi, 'Output', stc, 'Target'); G.link(bc, 'then', stc, 'execute')
nt0 = setv('NeedTarget', bo('NeedTarget'), x1 + 1950, y1 - 200, 'false'); G.link(stc, 'then', nt0, 'execute')
ph1 = setv('Phase', it('Phase'), x1 + 1500, y1 + 300, '1'); G.link(bc, 'else', ph1, 'execute')
gg = call('GetActorOfClass', x1 + 600, y1 + 500); gg.set_default('ActorClass', obj=GATE); G.link(bp0, 'else', gg, 'execute')
bv = br(x1 + 900, y1 + 500); iv = call('IsValid', x1 + 750, y1 + 650); G.link(gg, 'ReturnValue', iv, 'Object'); G.link(iv, 'ReturnValue', bv, 'Condition'); G.link(gg, 'then', bv, 'execute')
stg_ = setv('Target', OBJ_ACTOR, x1 + 1200, y1 + 450); G.link(gg, 'ReturnValue', stg_, 'Target'); G.link(bv, 'then', stg_, 'execute')
sth = setv('Target', OBJ_ACTOR, x1 + 1200, y1 + 650); G.link(call('GetPlayerCharacter', x1 + 1000, y1 + 800), 'ReturnValue', sth, 'Target'); G.link(bv, 'else', sth, 'execute')
nt1 = setv('NeedTarget', bo('NeedTarget'), x1 + 1500, y1 + 550, 'false'); G.link(stg_, 'then', nt1, 'execute'); G.link(sth, 'then', nt1, 'execute')

# ---- then_1: State 0 = circle once out of the crack, then go for a target --------------------------------------
x1, y1 = x0 + 3200, y0 - 300
b = br(x1, y1); G.link(eqint('State', 0, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_1', b, 'execute')
m1 = call('Multiply_DoubleDouble', x1, y1 + 350); G.link(getv('StateTime', fl('StateTime'), x1 - 200, y1 + 350), 'StateTime', m1, 'A'); m1.set_default('B', '1.6')
cs = call('Sin', x1 + 200, y1 + 300, ex=A); cs.sub_prop('MemberName="Sin"', 'MemberName="Cos"'); sn = call('Sin', x1 + 200, y1 + 420, ex=A)
G.link(m1, 'ReturnValue', cs, 'A'); G.link(m1, 'ReturnValue', sn, 'A')
mx = call('Multiply_DoubleDouble', x1 + 400, y1 + 300); G.link(cs, 'ReturnValue', mx, 'A'); mx.set_default('B', '700.0')
my = call('Multiply_DoubleDouble', x1 + 400, y1 + 420); G.link(sn, 'ReturnValue', my, 'A'); my.set_default('B', '700.0')
mv = mkvec(x1 + 600, y1 + 350, Zv='300.0'); G.link(mx, 'ReturnValue', mv, 'X'); G.link(my, 'ReturnValue', mv, 'Y')
va = vadd(getv('SpawnLoc', vec('SpawnLoc'), x1 + 600, y1 + 250), 'SpawnLoc', mv, 'ReturnValue', x1 + 800, y1 + 300)
g0 = setv('GoalLoc', vec('GoalLoc'), x1 + 300, y1); G.link(va, 'ReturnValue', g0, 'GoalLoc'); G.link(b, 'then', g0, 'execute')
b4 = br(x1 + 600, y1); G.link(stg(x1 + 450, y1 + 150, 4.0), 'ReturnValue', b4, 'Condition'); G.link(g0, 'then', b4, 'execute')
chain(*[n for n in (b4,)], ) ; s1 = setv('State', it('State'), x1 + 900, y1, '1'); G.link(b4, 'then', s1, 'execute')
chain(s1, setv('StateTime', fl('StateTime'), x1 + 1150, y1, '0.0'), setv('NeedTarget', bo('NeedTarget'), x1 + 1400, y1, 'true'), play('A_RealmWasp_Fly', True, x1 + 1700, y1))

# ---- then_2: State 1 = approach: hover above the target, dive when within 3.5 m ---------------------------------
x1, y1 = x0 + 3200, y0 + 500
b = br(x1, y1); G.link(eqint('State', 1, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_2', b, 'execute')
bv = br(x1 + 300, y1); tg = getv('Target', OBJ_ACTOR, x1 + 50, y1 + 250); iv = call('IsValid', x1 + 150, y1 + 200); G.link(tg, 'Target', iv, 'Object'); G.link(iv, 'ReturnValue', bv, 'Condition'); G.link(b, 'then', bv, 'execute')
G.link(bv, 'else', setv('NeedTarget', bo('NeedTarget'), x1 + 600, y1 + 250, 'true'), 'execute')
tl = actor_loc_of(getv('Target', OBJ_ACTOR, x1 + 300, y1 + 450), 'Target', x1 + 500, y1 + 450)
hv = mkvec(x1 + 500, y1 + 550, X='0.0', Y='0.0'); G.link(getv('HoverHeight', fl('HoverHeight'), x1 + 300, y1 + 600), 'HoverHeight', hv, 'Z')
g1 = setv('GoalLoc', vec('GoalLoc'), x1 + 600, y1); G.link(vadd(tl, 'ReturnValue', hv, 'ReturnValue', x1 + 750, y1 + 450), 'ReturnValue', g1, 'GoalLoc'); G.link(bv, 'then', g1, 'execute')
d2 = call('Vector_Distance2D', x1 + 750, y1 + 250); G.link(self_loc(x1 + 550, y1 + 250), 'ReturnValue', d2, 'V1'); G.link(tl, 'ReturnValue', d2, 'V2')
lt = call('Less_DoubleDouble', x1 + 950, y1 + 250); G.link(d2, 'ReturnValue', lt, 'A'); lt.set_default('B', '350.0')
bd2 = br(x1 + 900, y1); G.link(lt, 'ReturnValue', bd2, 'Condition'); G.link(g1, 'then', bd2, 'execute')
csd = setv('CurSpeed', fl('CurSpeed'), x1 + 1700, y1); G.link(getv('DiveSpeed', fl('DiveSpeed'), x1 + 1500, y1 + 200), 'DiveSpeed', csd, 'CurSpeed')
chain(setv('State', it('State'), x1 + 1200, y1, '2'), setv('StateTime', fl('StateTime'), x1 + 1450, y1, '0.0'), csd, play('A_RealmWasp_Dive', True, x1 + 2000, y1))
G.link(bd2, 'then', G.nodes[[n for n in G.nodes][-6]], 'execute') if False else None
G.link(bd2, 'then', [n for n in G.nodes.values() if n.x == x1 + 1200 and n.y == y1][0], 'execute')

# ---- then_3: State 2 = dive onto the target; sting: damage on frame 13 (0.43 s), cannons lose their load ----------
x1, y1 = x0 + 3200, y0 + 1300
b = br(x1, y1); G.link(eqint('State', 2, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_3', b, 'execute')
bv = br(x1 + 300, y1); iv = call('IsValid', x1 + 150, y1 + 200); G.link(getv('Target', OBJ_ACTOR, x1 + 50, y1 + 250), 'Target', iv, 'Object'); G.link(iv, 'ReturnValue', bv, 'Condition'); G.link(b, 'then', bv, 'execute')
chain(setv('NeedTarget', bo('NeedTarget'), x1 + 600, y1 + 300, 'true'), setv('State', it('State'), x1 + 850, y1 + 300, '1'))
G.link(bv, 'else', [n for n in G.nodes.values() if n.x == x1 + 600 and n.y == y1 + 300][0], 'execute')
tl = actor_loc_of(getv('Target', OBJ_ACTOR, x1 + 300, y1 + 500), 'Target', x1 + 500, y1 + 500)
g2 = setv('GoalLoc', vec('GoalLoc'), x1 + 600, y1); G.link(vadd(tl, 'ReturnValue', mkvec(x1 + 500, y1 + 600, '0.0', '0.0', '140.0'), 'ReturnValue', x1 + 750, y1 + 500), 'ReturnValue', g2, 'GoalLoc'); G.link(bv, 'then', g2, 'execute')
dd = call('Vector_Distance', x1 + 900, y1 + 250); G.link(self_loc(x1 + 700, y1 + 250), 'ReturnValue', dd, 'V1'); G.link(g2, 'Output_Get', dd, 'V2')
ll = call('Less_DoubleDouble', x1 + 1100, y1 + 250); G.link(dd, 'ReturnValue', ll, 'A'); ll.set_default('B', '160.0')
orr = call('BooleanOR', x1 + 1300, y1 + 250); G.link(ll, 'ReturnValue', orr, 'A'); G.link(stg(x1 + 1100, y1 + 380, 2.5), 'ReturnValue', orr, 'B')
bh = br(x1 + 1000, y1); G.link(orr, 'ReturnValue', bh, 'Condition'); G.link(g2, 'then', bh, 'execute')
dl = call('Delay', x1 + 2000, y1); dl.set_default('Duration', '0.43')
s3 = chain(setv('State', it('State'), x1 + 1300, y1, '3'), setv('StateTime', fl('StateTime'), x1 + 1550, y1, '0.0'), play('A_RealmWasp_Sting', False, x1 + 1800, y1), dl)
G.link(bh, 'then', [n for n in G.nodes.values() if n.x == x1 + 1300 and n.y == y1][0], 'execute')
dmg = call('ApplyDamage', x1 + 2300, y1); G.link(getv('Target', OBJ_ACTOR, x1 + 2100, y1 + 200), 'Target', dmg, 'DamagedActor')
G.link(getv('AttackDamage', fl('AttackDamage'), x1 + 2100, y1 + 300), 'AttackDamage', dmg, 'BaseDamage'); G.link(C(Z, 'K2Node_Self', None, x1 + 2100, y1 + 400), 'self', dmg, 'DamageCauser')
G.link(dl, 'then', dmg, 'execute')
cc = C(Z, 'K2Node_DynamicCast', None, x1 + 2600, y1, extra='BP_ThirdPersonCharacter')
cc.set_prop('TargetType', "/Script/Engine.BlueprintGeneratedClass'%s'" % CANNON)
co = cc.pin('AsBP Third Person Character'); co['name'] = 'AsBP Cannon'
co['line'] = co['line'].replace('PinName="AsBP Third Person Character"', 'PinName="AsBP Cannon"').replace('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C', CANNON)
G.link(getv('Target', OBJ_ACTOR, x1 + 2400, y1 + 200), 'Target', cc, 'Object'); G.link(dmg, 'then', cc, 'execute')
ul = G.clone(Z, T(Z, 'K2Node_VariableSet', 'XP'), x1 + 2900, y1)       # a set on another BP's variable, retargeted to BP_Cannon.bLoaded
ul.props = [l.replace('MemberName="XP"', 'MemberName="bLoaded"').replace('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C', CANNON) for l in ul.props]
for pn in ('XP', 'Output_Get'):
    p = ul.pin(pn); p['line'] = re.sub(r'PinType\.PinCategory="int",PinType\.PinSubCategory="",PinType\.PinSubCategoryObject=None', 'PinType.PinCategory="bool",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None', p['line'])
    if pn == 'XP': p['name'] = 'bLoaded'; p['line'] = p['line'].replace('PinName="XP"', 'PinName="bLoaded"')
ul.set_default('bLoaded', 'false')
sp = ul.pin('self'); sp['line'] = sp['line'].replace('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C', CANNON)
G.link(cc, 'AsBP Cannon', ul, 'self'); G.link(cc, 'then', ul, 'execute')
hb = br(x1 + 3200, y1); hd = call('GetDistanceTo', x1 + 2900, y1 + 250); G.link(call('GetPlayerCharacter', x1 + 2700, y1 + 300), 'ReturnValue', hd, 'OtherActor')
hl = call('Less_DoubleDouble', x1 + 3050, y1 + 250); G.link(hd, 'ReturnValue', hl, 'A'); hl.set_default('B', '450.0'); G.link(hl, 'ReturnValue', hb, 'Condition')
G.link(ul, 'then', hb, 'execute'); G.link(cc, 'CastFailed', hb, 'execute')
dh = call('ApplyDamage', x1 + 3500, y1 - 150); G.link(call('GetPlayerCharacter', x1 + 3300, y1 - 50), 'ReturnValue', dh, 'DamagedActor')
G.link(getv('AttackDamage', fl('AttackDamage'), x1 + 3300, y1 + 50), 'AttackDamage', dh, 'BaseDamage'); G.link(C(Z, 'K2Node_Self', None, x1 + 3300, y1 + 120), 'self', dh, 'DamageCauser')
G.link(hb, 'then', dh, 'execute')
hi = setv('Hits', it('Hits'), x1 + 3800, y1); ai = call('Add_IntInt', x1 + 3600, y1 + 200); G.link(getv('Hits', it('Hits'), x1 + 3400, y1 + 250), 'Hits', ai, 'A'); ai.set_default('B', '1'); G.link(ai, 'ReturnValue', hi, 'Hits')
G.link(dh, 'then', hi, 'execute'); G.link(hb, 'else', hi, 'execute')

# ---- then_4: State 3 = after the sting, rise straight up ------------------------------------------------------------
x1, y1 = x0 + 3200, y0 + 2300
b = br(x1, y1); G.link(eqint('State', 3, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_4', b, 'execute')
b8 = br(x1 + 300, y1); G.link(stg(x1 + 150, y1 + 150, 0.8), 'ReturnValue', b8, 'Condition'); G.link(b, 'then', b8, 'execute')
csf = setv('CurSpeed', fl('CurSpeed'), x1 + 1100, y1); G.link(getv('FlySpeed', fl('FlySpeed'), x1 + 900, y1 + 200), 'FlySpeed', csf, 'CurSpeed')
gu = setv('GoalLoc', vec('GoalLoc'), x1 + 1350, y1); G.link(vadd(self_loc(x1 + 1100, y1 + 300), 'ReturnValue', mkvec(x1 + 1100, y1 + 400, '0.0', '0.0', '350.0'), 'ReturnValue', x1 + 1300, y1 + 300), 'ReturnValue', gu, 'GoalLoc')
first = setv('State', it('State'), x1 + 600, y1, '4'); G.link(b8, 'then', first, 'execute')
chain(first, setv('StateTime', fl('StateTime'), x1 + 850, y1, '0.0'), csf, gu, play('A_RealmWasp_Hover', True, x1 + 1650, y1))

# ---- then_5: State 4 = recover, then the next pass (after HitsPerTarget hits, the castle phase) ---------------------
x1, y1 = x0 + 3200, y0 + 3000
b = br(x1, y1); G.link(eqint('State', 4, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_5', b, 'execute')
b14 = br(x1 + 300, y1); G.link(stg(x1 + 150, y1 + 150, 1.4), 'ReturnValue', b14, 'Condition'); G.link(b, 'then', b14, 'execute')
bh2 = br(x1 + 600, y1); gh = call('GreaterEqual_IntInt', x1 + 450, y1 + 150, ex=W)
G.link(getv('Hits', it('Hits'), x1 + 250, y1 + 150), 'Hits', gh, 'A'); G.link(getv('HitsPerTarget', it('HitsPerTarget'), x1 + 250, y1 + 250), 'HitsPerTarget', gh, 'B')
G.link(gh, 'ReturnValue', bh2, 'Condition'); G.link(b14, 'then', bh2, 'execute')
p1 = setv('Phase', it('Phase'), x1 + 900, y1 - 150, '1'); chain(p1, setv('Hits', it('Hits'), x1 + 1150, y1 - 150, '0'), setv('NeedTarget', bo('NeedTarget'), x1 + 1400, y1 - 150, 'true'))
G.link(bh2, 'then', p1, 'execute')
s1b = setv('State', it('State'), x1 + 1700, y1, '1'); G.link([n for n in G.nodes.values() if n.x == x1 + 1400 and n.y == y1 - 150][0], 'then', s1b, 'execute'); G.link(bh2, 'else', s1b, 'execute')
chain(s1b, setv('StateTime', fl('StateTime'), x1 + 1950, y1, '0.0'), play('A_RealmWasp_Fly', True, x1 + 2250, y1))

# ---------------- AnyDamage: HP, death, XP to the hero (as BP_Zombie does), fall out of the air -------------------
x0, y0 = 0, 6000
ed = C(Z, 'K2Node_Event', 'ReceiveAnyDamage', x0, y0)
bdd = br(x0 + 300, y0); G.link(C(Z, 'K2Node_VariableGet', 'Dead', x0 + 100, y0 + 150), 'Dead', bdd, 'Condition'); G.link(ed, 'then', bdd, 'execute')
sdt = C(Z, 'K2Node_VariableSet', 'DamageTaken', x0 + 600, y0); adt = call('Add_DoubleDouble', x0 + 450, y0 + 200)
G.link(C(Z, 'K2Node_VariableGet', 'DamageTaken', x0 + 250, y0 + 200), 'DamageTaken', adt, 'A'); G.link(ed, 'Damage', adt, 'B'); G.link(adt, 'ReturnValue', sdt, 'DamageTaken')
G.link(bdd, 'else', sdt, 'execute')
bk = br(x0 + 900, y0); gek = call('GreaterEqual_DoubleDouble', x0 + 750, y0 + 200); G.link(sdt, 'Output_Get', gek, 'A'); G.link(C(Z, 'K2Node_VariableGet', 'MaxHP', x0 + 550, y0 + 300), 'MaxHP', gek, 'B')
G.link(gek, 'ReturnValue', bk, 'Condition'); G.link(sdt, 'then', bk, 'execute')
sd = C(Z, 'K2Node_VariableSet', 'Dead', x0 + 1200, y0); sd.set_default('Dead', 'true'); G.link(bk, 'then', sd, 'execute')
hc = C(Z, 'K2Node_DynamicCast', None, x0 + 1500, y0, extra='BP_ThirdPersonCharacter'); G.link(call('GetPlayerCharacter', x0 + 1300, y0 + 200), 'ReturnValue', hc, 'Object'); G.link(sd, 'then', hc, 'execute')
hxp = C(Z, 'K2Node_VariableSet', 'XP', x0 + 1900, y0); hadd = call('Add_IntInt', x0 + 1700, y0 + 250)
hxg = C(Z, 'K2Node_VariableGet', 'XP', x0 + 1500, y0 + 250); G.link(hc, 'AsBP Third Person Character', hxg, 'self'); G.link(hxg, 'XP', hadd, 'A')
G.link(C(Z, 'K2Node_VariableGet', 'XPValue', x0 + 1500, y0 + 350), 'XPValue', hadd, 'B'); G.link(hadd, 'ReturnValue', hxp, 'XP'); G.link(hc, 'AsBP Third Person Character', hxp, 'self')
G.link(hc, 'then', hxp, 'execute')
lvl = C(Z, 'K2Node_CallFunction', 'CheckLevelUp', x0 + 2200, y0); G.link(hc, 'AsBP Third Person Character', lvl, 'self'); G.link(hxp, 'then', lvl, 'execute')
g1d = G.clone(W, T(W, 'K2Node_VariableSet', 'GravityScale'), x0 + 2500, y0); g1d.set_default('GravityScale', '1.0')
G.link(C(Z, 'K2Node_VariableGet', 'CharacterMovement', x0 + 2300, y0 + 200), 'CharacterMovement', g1d, 'self')
G.link(lvl, 'then', g1d, 'execute'); G.link(hc, 'CastFailed', g1d, 'execute')
ls = C(Z, 'K2Node_CallFunction', 'SetLifeSpan', x0 + 3100, y0); ls.set_default('InLifespan', '6.0')
chain(g1d, play('A_RealmWasp_Death', False, x0 + 2800, y0), ls)

open(os.path.join(OUT, 'BP_RealmWasp_EventGraph.txt'), 'w', encoding='utf-8').write(G.render())
V = [bpvar('State', 'int', '0'), bpvar('Phase', 'int', '0'), bpvar('Hits', 'int', '0'), bpvar('HitsPerTarget', 'int', '3'),
     bpvar('NeedTarget', 'bool', 'False'), bpvar('StateTime', 'real', '0.0', sub='double'), bpvar('ThinkAcc', 'real', '0.0', sub='double'),
     bpvar('CurSpeed', 'real', '900.0', sub='double'), bpvar('FlySpeed', 'real', '900.0', sub='double'), bpvar('DiveSpeed', 'real', '1700.0', sub='double'),
     bpvar('HoverHeight', 'real', '380.0', sub='double'),
     bpvar('SpawnLoc', 'struct', '0.000000,0.000000,0.000000', obj="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),
     bpvar('GoalLoc', 'struct', '0.000000,0.000000,0.000000', obj="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'"),
     bpvar('Target', 'object', '', obj="/Script/CoreUObject.Class'/Script/Engine.Actor'")]
open(os.path.join(OUT, 'BP_RealmWasp_vars.txt'), 'w', encoding='utf-8').write('\n'.join(V) + '\n')
print('WASP nodes', len(G.nodes), 'links', len(G.links))

# ================= BP_ZombieWaveManager: swarm waves =================================================================
H = Graph('SWM')
def hc_(ex, cls, member=None, x=0, y=0, extra=None): return H.clone(ex, T(ex, cls, member, extra), x, y)
sq = hc_(Z, 'K2Node_ExecutionSequence', None, 0, 0)
bw = hc_(Z, 'K2Node_IfThenElse', None, 300, 100)
andn = hc_(Z, 'K2Node_CallFunction', 'BooleanAND', 100, 250)
H.link(var_get(H, 'SwarmUnlocked', bo('SwarmUnlocked'), -150, 250), 'SwarmUnlocked', andn, 'A')
pc = hc_(W, 'K2Node_CallFunction', 'Percent_IntInt', -250, 400); H.link(hc_(W, 'K2Node_VariableGet', 'Wave', -450, 400), 'Wave', pc, 'A')
H.link(var_get(H, 'SwarmEveryNthWave', it('SwarmEveryNthWave'), -450, 500), 'SwarmEveryNthWave', pc, 'B')
eq = hc_(Z, 'K2Node_CallFunction', 'EqualEqual_IntInt', -50, 400); H.link(pc, 'ReturnValue', eq, 'A'); eq.set_default('B', '0'); H.link(eq, 'ReturnValue', andn, 'B')
H.link(andn, 'ReturnValue', bw, 'Condition'); H.link(sq, 'then_1', bw, 'execute')
fo = H.clone(W, 'CX_26', 600, 100); fo.set_default('FirstIndex', '1'); H.link(var_get(H, 'SwarmSize', it('SwarmSize'), 400, 250), 'SwarmSize', fo, 'LastIndex'); H.link(bw, 'then', fo, 'execute')
spw = H.clone(W, 'CX_30', 1000, 100); spw.set_default('Class', obj=WASPC)
rv = spw.pin('ReturnValue'); rv['line'] = rv['line'].replace('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C', WASPC)
mt = H.clone(W, 'CX_29', 800, 350)
rr = [hc_(Z, 'K2Node_CallFunction', 'RandomFloatInRange', 200 + 0 * i, 500 + 100 * i) for i in range(3)]
for r_, lo, hi in zip(rr, (-400, -400, 0), (400, 400, 300)): r_.set_default('Min', '%.1f' % lo).set_default('Max', '%.1f' % hi)
mv = hc_(Z, 'K2Node_CallFunction', 'MakeVector', 400, 550)
for r_, k in zip(rr, 'XYZ'): H.link(r_, 'ReturnValue', mv, k)
av = hc_(Z, 'K2Node_CallFunction', 'Add_VectorVector', 600, 450); H.link(var_get(H, 'SwarmSpawnLocation', vec('SwarmSpawnLocation'), 400, 420), 'SwarmSpawnLocation', av, 'A'); H.link(mv, 'ReturnValue', av, 'B')
H.link(av, 'ReturnValue', mt, 'Location'); H.link(mt, 'ReturnValue', spw, 'SpawnTransform'); H.link(fo, 'LoopBody', spw, 'execute')
open(os.path.join(OUT, 'BP_ZombieWaveManager_Swarm_graph.txt'), 'w', encoding='utf-8').write(H.render())
VW = [bpvar('SwarmUnlocked', 'bool', 'False'), bpvar('SwarmEveryNthWave', 'int', '2'), bpvar('SwarmSize', 'int', '6'),
      bpvar('SwarmSpawnLocation', 'struct', '-14171.000000,11000.000000,1500.000000', obj="/Script/CoreUObject.ScriptStruct'/Script/CoreUObject.Vector'")]
open(os.path.join(OUT, 'BP_ZombieWaveManager_vars.txt'), 'w', encoding='utf-8').write('\n'.join(VW) + '\n')
man = {'blueprint': 'BP_ZombieWaveManager', '_note': 'Swarm waves (#169 stage 3 / #167): after the wave counter goes up, every SwarmEveryNthWave-th wave spawns SwarmSize BP_RealmWasp at SwarmSpawnLocation once SwarmUnlocked is true (the breach sets it).',
       'pastes': [{'file': 'BP_ZombieWaveManager_Swarm_graph.txt', 'offset': [0, 0]}],
       'rewires': [{'from': 'WV_90.then', 'to': '%s.execute' % sq.name, 'replace': True, 'note': 'was -> CX_9 (K2_SetTimer ForceNextWave)'},
                   {'from': '%s.then_0' % sq.name, 'to': 'CX_9.execute', 'note': 'original flow continues first'}]}
json.dump(man, open(os.path.join(OUT, 'manifest_wavemanager.json'), 'w'), indent=2)
print('WAVE nodes', len(H.nodes), 'links', len(H.links), 'seq', sq.name)
