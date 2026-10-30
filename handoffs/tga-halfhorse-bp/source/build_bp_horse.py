# BP_HalfHorseZombie (#168 behaviour) + its spawn in the wave manager swarm paste. TGA, 2026-10-30.
# Child of BP_Zombie: Mesh becomes SK_HorseBody; a 'Torso' SkeletalMeshComponent (create script) gets the zombie's own
# mesh + materials (copied from the inherited Mesh before the swap), snaps to the TorsoSocket and hides its legs.
# Brain: chase the hero (walk near, gallop far), rear + knock-down on frame 22 (0.73 s) when within 3.2 m.
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpkit
from bpkit import Export, Graph, bpvar, var_get, var_set, fl, it, bo, ob, vec, CLS
E = r'R:\handoffs\exports\master\2026-10-30'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'T:\bp\out'
Z = Export(E + r'\BP_Zombie.t3d'); W = Export(E + r'\BP_ZombieWaveManager.t3d')
HB = '/Game/CastleDefender/Characters/Enemies/HalfHorseZombie'
ZA = '/Game/CastleDefender/Characters/Enemies/Zombie'
def asset(n, root=HB): return '%s/%s.%s' % (root, n, n)
G = Graph('HHZ')
def T(ex, cls, member=None, extra=None): return ex.find(cls, member, extra)
def C(ex, cls, member=None, x=0, y=0, extra=None): return G.clone(ex, T(ex, cls, member, extra), x, y)
def call(member, x, y, ex=Z, extra=None): return C(ex, 'K2Node_CallFunction', member, x, y, extra)
def br(x, y): return C(Z, 'K2Node_IfThenElse', None, x, y)
def comp(name, x, y):
    n = C(Z, 'K2Node_VariableGet', 'Mesh', x, y)
    if name != 'Mesh':
        n.sub_prop('MemberName="Mesh"', 'MemberName="%s"' % name); p = n.pin('Mesh'); p['name'] = name; p['line'] = p['line'].replace('PinName="Mesh"', 'PinName="%s"' % name)
    return n
def getv(name, pin, x, y): return var_get(G, name, pin, x, y)
def setv(name, pin, x, y, value=None):
    n = var_set(G, name, pin, x, y)
    if value is not None: n.set_default(name, value)
    return n
def play(target, anim_path, loop, x, y):
    n = call('PlayAnimation', x, y); n.set_default('NewAnimToPlay', obj=anim_path); n.set_default('bLooping', 'true' if loop else 'false')
    G.link(comp(target, x - 220, y + 120), target, n, 'self'); return n
def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]): G.link(a, 'then', b, 'execute')
    return nodes[-1]
def eqint(var, k, x, y):
    e = call('EqualEqual_IntInt', x, y); G.link(getv(var, it(var), x - 200, y), var, e, 'A'); e.set_default('B', str(k)); return e
def stg(lit, x, y):
    c = call('Greater_DoubleDouble', x, y); G.link(getv('StateTime', fl('StateTime'), x - 200, y), 'StateTime', c, 'A'); c.set_default('B', str(lit)); return c
def retarget(n, member, selfcls_from, selfcls_to):
    n.sub_prop('MemberName="%s"' % re.search(r'MemberName="(\w+)"', ' '.join(n.props)).group(1), 'MemberName="%s"' % member)
    n.sub_prop(selfcls_from, selfcls_to); sp = n.pin('self'); sp['line'] = sp['line'].replace(selfcls_from, selfcls_to); return n
def rename(n, old, new):
    p = n.pin(old); p['name'] = new; p['line'] = p['line'].replace('PinName="%s"' % old, 'PinName="%s"' % new); return p
def add_pin_from(n, src_node, src_pin, new, before=-1):
    s = src_node.pin(src_pin); q = dict(s, id=bpkit.g(), name=new, line=s['line'].replace('PinName="%s"' % src_pin, 'PinName="%s"' % new))
    n.pins.insert(len(n.pins) if before == -1 else before, q); return q
def scratch(ex, cls, member):   # a template node used only as a pin donor, not rendered
    n = C(ex, cls, member); del G.nodes[n.name]; return n
SKM = '/Script/Engine.SkeletalMeshComponent'; PRIM = '/Script/Engine.PrimitiveComponent'; SCENE = '/Script/Engine.SceneComponent'

# ---------------- BeginPlay ------------------------------------------------------------------------------------------
x0, y0 = 0, 0
ev = C(Z, 'K2Node_Event', 'ReceiveBeginPlay', x0, y0)
# pure getters built on K2_GetComponentRotation's shell: Mesh.GetSkeletalMeshAsset, Mesh.GetMaterial(i)
def getter(member, ret_obj, x, y):
    n = call('K2_GetComponentRotation', x, y); retarget(n, member, SCENE, SKM if member == 'GetSkeletalMeshAsset' else PRIM)
    rp = n.pin('ReturnValue'); rp['line'] = re.sub(r'PinType\.PinCategory="struct",PinType\.PinSubCategory="",PinType\.PinSubCategoryObject="[^"]+"',
                                                   'PinType.PinCategory="object",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % ret_obj, rp['line'])
    return n
gsk = getter('GetSkeletalMeshAsset', 'SkeletalMesh', x0 + 100, y0 + 250); G.link(comp('Mesh', x0 - 100, y0 + 250), 'Mesh', gsk, 'self')
setsk = call('SetMaterial', x0 + 300, y0); retarget(setsk, 'SetSkeletalMeshAsset', PRIM, SKM)
setsk.pins = [p for p in setsk.pins if p['name'] != 'ElementIndex']; np_ = rename(setsk, 'Material', 'NewMesh'); np_['line'] = np_['line'].replace('/Script/Engine.MaterialInterface', '/Script/Engine.SkeletalMesh')
G.link(comp('Torso', x0 + 100, y0 + 150), 'Torso', setsk, 'self'); G.link(gsk, 'ReturnValue', setsk, 'NewMesh'); G.link(ev, 'then', setsk, 'execute')
prev = setsk
for i in (0, 1):                                            # zombie skin onto the torso
    gm = getter('GetMaterial', 'MaterialInterface', x0 + 500 + 300 * i, y0 + 250)
    add_pin_from(gm, scratch(Z, 'K2Node_CallFunction', 'SetMaterial'), 'ElementIndex', 'ElementIndex', before=len(gm.pins) - 1); gm.set_default('ElementIndex', str(i))
    G.link(comp('Mesh', x0 + 300 + 300 * i, y0 + 300), 'Mesh', gm, 'self')
    sm = call('SetMaterial', x0 + 600 + 300 * i, y0); sm.set_default('ElementIndex', str(i)); G.link(gm, 'ReturnValue', sm, 'Material'); G.link(comp('Torso', x0 + 450 + 300 * i, y0 + 150), 'Torso', sm, 'self')
    G.link(prev, 'then', sm, 'execute'); prev = sm
hsk = call('SetMaterial', x0 + 1300, y0); retarget(hsk, 'SetSkeletalMeshAsset', PRIM, SKM)
hsk.pins = [p for p in hsk.pins if p['name'] != 'ElementIndex']; np_ = rename(hsk, 'Material', 'NewMesh'); np_['line'] = np_['line'].replace('/Script/Engine.MaterialInterface', '/Script/Engine.SkeletalMesh')
hsk.set_default('NewMesh', obj=asset('SK_HorseBody')); G.link(comp('Mesh', x0 + 1100, y0 + 150), 'Mesh', hsk, 'self'); G.link(prev, 'then', hsk, 'execute')
skin = br(x0 + 1600, y0); rb = call('RandomBoolWithWeight', x0 + 1450, y0 + 180); rb.set_default('Weight', '0.4'); G.link(rb, 'ReturnValue', skin, 'Condition'); G.link(hsk, 'then', skin, 'execute')
def hmat(mi, x, y):
    n = call('SetMaterial', x, y); n.set_default('ElementIndex', '0'); n.set_default('Material', obj=asset(mi)); G.link(comp('Mesh', x - 200, y + 150), 'Mesh', n, 'self'); return n
hg, hb = hmat('MI_HorseBody_Grey', x0 + 1900, y0 - 200), hmat('MI_HorseBody_Bay', x0 + 1900, y0 + 200)
G.link(skin, 'then', hg, 'execute'); G.link(skin, 'else', hb, 'execute')
rel = call('K2_SetRelativeLocation', x0 + 2200, y0); rel.set_default('NewLocation', '0.000000,0.000000,-110.000000'); G.link(comp('Mesh', x0 + 2000, y0 + 150), 'Mesh', rel, 'self')
G.link(hg, 'then', rel, 'execute'); G.link(hb, 'then', rel, 'execute')
cap = G.clone(W, T(W, 'K2Node_CallFunction', 'SetCapsuleSize'), x0 + 2500, y0); cap.set_default('InRadius', '60.0').set_default('InHalfHeight', '110.0')
G.link(C(Z, 'K2Node_VariableGet', 'CapsuleComponent', x0 + 2300, y0 + 150), 'CapsuleComponent', cap, 'self')
# Torso -> Mesh at TorsoSocket: snap the location, keep the world rotation and scale (the pose at BeginPlay is the rest
# pose, so the torso stands upright and from then on rides the socket); then lower it so its pelvis sits in the stump
att = call('K2_SetRelativeLocation', x0 + 2800, y0); retarget(att, 'K2_AttachToComponent', SCENE, SCENE)
att.pins = [p for p in att.pins if p['name'] in ('execute', 'then', 'self')]
spawn_t = scratch(W, 'K2Node_SpawnActorFromClass', None)
par = add_pin_from(att, comp('Mesh', 0, 0), 'Mesh', 'Parent'); del G.nodes[list(G.nodes)[-1]]
par['out'] = False; par['line'] = par['line'].replace('Direction="EGPD_Output",', '').replace('/Script/Engine.SkeletalMeshComponent', SCENE)
sock = add_pin_from(att, scratch(Z, 'K2Node_CallFunction', 'SetLifeSpan'), 'InLifespan', 'SocketName')
sock['line'] = re.sub(r'PinType\.PinCategory="real",PinType\.PinSubCategory="\w*"', 'PinType.PinCategory="name",PinType.PinSubCategory=""', sock['line'])
for rule, val in (('LocationRule', 'SnapToTarget'), ('RotationRule', 'KeepWorld'), ('ScaleRule', 'KeepWorld')):
    q = add_pin_from(att, spawn_t, 'CollisionHandlingOverride', rule)
    q['line'] = re.sub(r'PinSubCategoryObject="[^"]+"', 'PinSubCategoryObject="/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', q['line'])
    q['line'] = re.sub(r'(?<![A-Za-z])DefaultValue="[^"]*",', '', q['line'])
for nm in ('bWeldSimulatedBodies',):
    q = add_pin_from(att, scratch(Z, 'K2Node_CallFunction', 'PlayAnimation'), 'bLooping', nm)
rv = add_pin_from(att, scratch(Z, 'K2Node_CallFunction', 'K2_SetActorRotation'), 'ReturnValue', 'ReturnValue')
att.set_default('SocketName', 'TorsoSocket').set_default('LocationRule', 'SnapToTarget').set_default('RotationRule', 'KeepWorld').set_default('ScaleRule', 'KeepWorld').set_default('bWeldSimulatedBodies', 'false')
G.link(comp('Torso', x0 + 2600, y0 + 150), 'Torso', att, 'self'); G.link(comp('Mesh', x0 + 2600, y0 + 250), 'Mesh', att, 'Parent')
off = call('K2_SetRelativeLocation', x0 + 3100, y0); retarget(off, 'K2_AddWorldOffset', SCENE, SCENE); rename(off, 'NewLocation', 'DeltaLocation')
mo = call('MakeVector', x0 + 2900, y0 + 250); mo.set_default('X', '0.0').set_default('Y', '0.0'); G.link(getv('TorsoDrop', fl('TorsoDrop'), x0 + 2700, y0 + 300), 'TorsoDrop', mo, 'Z')
G.link(mo, 'ReturnValue', off, 'DeltaLocation'); G.link(comp('Torso', x0 + 2900, y0 + 150), 'Torso', off, 'self')
chain(cap, att, off)
prev = off
for i, bone in enumerate(('thigh_l', 'thigh_r', 'LeftUpLeg', 'RightUpLeg')):   # mannequin + Mixamo names; a missing bone is a no-op
    hd = call('SetLifeSpan', x0 + 3400 + 250 * i, y0); hd.props = [l for l in hd.props if not l.startswith('FunctionReference')] + ['FunctionReference=(MemberParent="/Script/CoreUObject.Class\'/Script/Engine.SkinnedMeshComponent\'",MemberName="HideBoneByName")']
    sp = hd.pin('self'); sp['line'] = re.sub(r'PinSubCategoryObject="[^"]+"', 'PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.SkinnedMeshComponent\'"', sp['line']).replace('bHidden=True', 'bHidden=False')
    bn = rename(hd, 'InLifespan', 'BoneName'); bn['line'] = re.sub(r'PinType\.PinCategory="real",PinType\.PinSubCategory="\w*"', 'PinType.PinCategory="name",PinType.PinSubCategory=""', bn['line'])
    po = add_pin_from(hd, spawn_t, 'CollisionHandlingOverride', 'PhysBodyOption')
    po['line'] = re.sub(r'PinSubCategoryObject="[^"]+"', 'PinSubCategoryObject="/Script/CoreUObject.Enum\'/Script/Engine.EPhysBodyOp\'"', po['line'])
    hd.set_default('BoneName', bone).set_default('PhysBodyOption', 'PBO_None')
    G.link(comp('Torso', x0 + 3250 + 250 * i, y0 + 150), 'Torso', hd, 'self'); G.link(prev, 'then', hd, 'execute'); prev = hd
st = chain(prev, setv('MaxHP', fl('MaxHP'), x0 + 4500, y0, '400.0'), setv('XPValue', it('XPValue'), x0 + 4750, y0, '20'),
           setv('AttackDamage', fl('AttackDamage'), x0 + 5000, y0, '30.0'), setv('State', it('State'), x0 + 5250, y0, '0'), setv('CurAnim', it('CurAnim'), x0 + 5500, y0, '0'),
           play('Torso', asset('ZA_Walk_A', ZA + '/AnimsPack'), True, x0 + 5800, y0))

# ---------------- Tick: think every 0.25 s ---------------------------------------------------------------------------
x0, y0 = 0, 1300
tk = C(Z, 'K2Node_Event', 'ReceiveTick', x0, y0)
bd = br(x0 + 300, y0); G.link(C(Z, 'K2Node_VariableGet', 'Dead', x0 + 100, y0 + 150), 'Dead', bd, 'Condition'); G.link(tk, 'then', bd, 'execute')
ta = setv('ThinkAcc', fl('ThinkAcc'), x0 + 600, y0); ad = call('Add_DoubleDouble', x0 + 400, y0 + 200)
G.link(getv('ThinkAcc', fl('ThinkAcc'), x0 + 200, y0 + 200), 'ThinkAcc', ad, 'A'); G.link(tk, 'DeltaSeconds', ad, 'B'); G.link(ad, 'ReturnValue', ta, 'ThinkAcc'); G.link(bd, 'else', ta, 'execute')
bt = br(x0 + 900, y0); ge = call('GreaterEqual_DoubleDouble', x0 + 750, y0 + 200); G.link(getv('ThinkAcc', fl('ThinkAcc'), x0 + 550, y0 + 200), 'ThinkAcc', ge, 'A'); ge.set_default('B', '0.25')
G.link(ge, 'ReturnValue', bt, 'Condition'); G.link(ta, 'then', bt, 'execute')
sta = setv('StateTime', fl('StateTime'), x0 + 1450, y0); a2 = call('Add_DoubleDouble', x0 + 1250, y0 + 200)
G.link(getv('StateTime', fl('StateTime'), x0 + 1050, y0 + 200), 'StateTime', a2, 'A'); a2.set_default('B', '0.25'); G.link(a2, 'ReturnValue', sta, 'StateTime')
chain(setv('ThinkAcc', fl('ThinkAcc'), x0 + 1200, y0, '0.0'), sta); G.link(bt, 'then', [n for n in G.nodes.values() if n.x == x0 + 1200 and n.y == y0][0], 'execute')
S = C(Z, 'K2Node_ExecutionSequence', None, x0 + 1750, y0); G.link(sta, 'then', S, 'execute')
# ---- then_0: State 0 = chase: walk near, gallop far; rear when within 3.2 m ----
x1, y1 = x0 + 2100, y0 - 400
b = br(x1, y1); G.link(eqint('State', 0, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_0', b, 'execute')
gc = call('GetController', x1 + 200, y1 + 250)
mv = call('SimpleMoveToActor', x1 + 400, y1); G.link(gc, 'ReturnValue', mv, 'Controller'); G.link(call('GetPlayerCharacter', x1 + 200, y1 + 350), 'ReturnValue', mv, 'Goal'); G.link(b, 'then', mv, 'execute')
dist = call('GetDistanceTo', x1 + 600, y1 + 300); G.link(call('GetPlayerCharacter', x1 + 400, y1 + 400), 'ReturnValue', dist, 'OtherActor')
bf = br(x1 + 700, y1); gt = call('Greater_DoubleDouble', x1 + 800, y1 + 250); G.link(dist, 'ReturnValue', gt, 'A'); gt.set_default('B', '900.0'); G.link(gt, 'ReturnValue', bf, 'Condition'); G.link(mv, 'then', bf, 'execute')
def speed(v, x, y):
    n = C(Z, 'K2Node_VariableSet', 'MaxWalkSpeed', x, y); n.set_default('MaxWalkSpeed', v); G.link(C(Z, 'K2Node_VariableGet', 'CharacterMovement', x - 200, y + 150), 'CharacterMovement', n, 'self'); return n
gal, wlk = speed('650.0', x1 + 1000, y1 - 150), speed('240.0', x1 + 1000, y1 + 150)
G.link(bf, 'then', gal, 'execute'); G.link(bf, 'else', wlk, 'execute')
mg, mw = setv('WantAnim', it('WantAnim'), x1 + 1250, y1 - 150, '2'), setv('WantAnim', it('WantAnim'), x1 + 1250, y1 + 150, '1')
G.link(gal, 'then', mg, 'execute'); G.link(wlk, 'then', mw, 'execute')
# play only when the wanted anim changes
bch = br(x1 + 1550, y1); ne = call('EqualEqual_IntInt', x1 + 1400, y1 + 300); G.link(getv('WantAnim', it('WantAnim'), x1 + 1200, y1 + 300), 'WantAnim', ne, 'A'); G.link(getv('CurAnim', it('CurAnim'), x1 + 1200, y1 + 400), 'CurAnim', ne, 'B')
G.link(ne, 'ReturnValue', bch, 'Condition'); G.link(mg, 'then', bch, 'execute'); G.link(mw, 'then', bch, 'execute')
bw2 = br(x1 + 1850, y1 + 100); G.link(eqint('WantAnim', 2, x1 + 1650, y1 + 250), 'ReturnValue', bw2, 'Condition'); G.link(bch, 'else', bw2, 'execute')
pg, pw = play('Mesh', asset('A_HorseBody_Gallop'), True, x1 + 2150, y1 - 50), play('Mesh', asset('A_HorseBody_Walk'), True, x1 + 2150, y1 + 250)
G.link(bw2, 'then', pg, 'execute'); G.link(bw2, 'else', pw, 'execute')
cu = setv('CurAnim', it('CurAnim'), x1 + 2450, y1 + 100); G.link(getv('WantAnim', it('WantAnim'), x1 + 2250, y1 + 400), 'WantAnim', cu, 'CurAnim')
G.link(pg, 'then', cu, 'execute'); G.link(pw, 'then', cu, 'execute')
br_ = br(x1 + 2750, y1); lt = call('Less_DoubleDouble', x1 + 2600, y1 + 250); G.link(dist, 'ReturnValue', lt, 'A'); lt.set_default('B', '320.0'); G.link(lt, 'ReturnValue', br_, 'Condition')
G.link(cu, 'then', br_, 'execute'); G.link(bch, 'then', br_, 'execute')
smi = call('StopMovementImmediately', x1 + 3600, y1); G.link(C(Z, 'K2Node_VariableGet', 'CharacterMovement', x1 + 3400, y1 + 150), 'CharacterMovement', smi, 'self')
dl = call('Delay', x1 + 4500, y1); dl.set_default('Duration', '0.73')
first = setv('State', it('State'), x1 + 3050, y1, '1'); G.link(br_, 'then', first, 'execute')
chain(first, setv('StateTime', fl('StateTime'), x1 + 3300, y1, '0.0'), smi, setv('CurAnim', it('CurAnim'), x1 + 3850, y1, '3'),
      play('Mesh', asset('A_HorseBody_Rear'), False, x1 + 4100, y1), play('Torso', asset('A_Attack', ZA + '/Anims'), False, x1 + 4300, y1 + 400), dl)
# impact: damage + knock the hero back, if still close
bi = br(x1 + 4800, y1); d2 = call('GetDistanceTo', x1 + 4600, y1 + 250); G.link(call('GetPlayerCharacter', x1 + 4400, y1 + 300), 'ReturnValue', d2, 'OtherActor')
l2 = call('Less_DoubleDouble', x1 + 4750, y1 + 250); G.link(d2, 'ReturnValue', l2, 'A'); l2.set_default('B', '420.0'); G.link(l2, 'ReturnValue', bi, 'Condition'); G.link(dl, 'then', bi, 'execute')
dm = call('ApplyDamage', x1 + 5100, y1); G.link(call('GetPlayerCharacter', x1 + 4900, y1 + 200), 'ReturnValue', dm, 'DamagedActor')
G.link(C(Z, 'K2Node_VariableGet', 'AttackDamage', x1 + 4900, y1 + 300) if False else getv('AttackDamage', fl('AttackDamage'), x1 + 4900, y1 + 300), 'AttackDamage', dm, 'BaseDamage')
G.link(C(Z, 'K2Node_Self', None, x1 + 4900, y1 + 400), 'self', dm, 'DamageCauser'); G.link(bi, 'then', dm, 'execute')
lc = call('LaunchCharacter', x1 + 5400, y1); G.link(call('GetPlayerCharacter', x1 + 5200, y1 + 200), 'ReturnValue', lc, 'self')
fwd = call('GetActorForwardVector', x1 + 5000, y1 + 500); mvf = call('Multiply_VectorFloat', x1 + 5200, y1 + 500); G.link(fwd, 'ReturnValue', mvf, 'A'); mvf.set_default('B', '750.0')
upv = call('MakeVector', x1 + 5200, y1 + 650); upv.set_default('X', '0.0').set_default('Y', '0.0').set_default('Z', '380.0')
av = call('Add_VectorVector', x1 + 5400, y1 + 550); G.link(mvf, 'ReturnValue', av, 'A'); G.link(upv, 'ReturnValue', av, 'B'); G.link(av, 'ReturnValue', lc, 'LaunchVelocity')
G.link(dm, 'then', lc, 'execute')
# ---- then_1: State 1 = rearing; back to the chase after 1.25 s ----
x1, y1 = x0 + 2100, y0 + 900
b = br(x1, y1); G.link(eqint('State', 1, x1 - 200, y1 + 150), 'ReturnValue', b, 'Condition'); G.link(S, 'then_1', b, 'execute')
b2 = br(x1 + 300, y1); G.link(stg(1.25, x1 + 150, y1 + 150), 'ReturnValue', b2, 'Condition'); G.link(b, 'then', b2, 'execute')
first = setv('State', it('State'), x1 + 600, y1, '0'); G.link(b2, 'then', first, 'execute')
chain(first, setv('CurAnim', it('CurAnim'), x1 + 850, y1, '0'), play('Torso', asset('ZA_Walk_A', ZA + '/AnimsPack'), True, x1 + 1150, y1))

# ---------------- AnyDamage: as BP_Zombie (HP, XP), then the horse falls on its side ---------------------------------
x0, y0 = 0, 3200
ed = C(Z, 'K2Node_Event', 'ReceiveAnyDamage', x0, y0)
bdd = br(x0 + 300, y0); G.link(C(Z, 'K2Node_VariableGet', 'Dead', x0 + 100, y0 + 150), 'Dead', bdd, 'Condition'); G.link(ed, 'then', bdd, 'execute')
sdt = C(Z, 'K2Node_VariableSet', 'DamageTaken', x0 + 600, y0); adt = call('Add_DoubleDouble', x0 + 450, y0 + 200)
G.link(C(Z, 'K2Node_VariableGet', 'DamageTaken', x0 + 250, y0 + 200), 'DamageTaken', adt, 'A'); G.link(ed, 'Damage', adt, 'B'); G.link(adt, 'ReturnValue', sdt, 'DamageTaken'); G.link(bdd, 'else', sdt, 'execute')
bk = br(x0 + 900, y0); gek = call('GreaterEqual_DoubleDouble', x0 + 750, y0 + 200); G.link(sdt, 'Output_Get', gek, 'A'); G.link(C(Z, 'K2Node_VariableGet', 'MaxHP', x0 + 550, y0 + 300), 'MaxHP', gek, 'B')
G.link(gek, 'ReturnValue', bk, 'Condition'); G.link(sdt, 'then', bk, 'execute')
sd = C(Z, 'K2Node_VariableSet', 'Dead', x0 + 1200, y0); sd.set_default('Dead', 'true'); G.link(bk, 'then', sd, 'execute')
hc = C(Z, 'K2Node_DynamicCast', None, x0 + 1500, y0, extra='BP_ThirdPersonCharacter'); G.link(call('GetPlayerCharacter', x0 + 1300, y0 + 200), 'ReturnValue', hc, 'Object'); G.link(sd, 'then', hc, 'execute')
hxp = C(Z, 'K2Node_VariableSet', 'XP', x0 + 1900, y0); hadd = call('Add_IntInt', x0 + 1700, y0 + 250)
hxg = C(Z, 'K2Node_VariableGet', 'XP', x0 + 1500, y0 + 250); G.link(hc, 'AsBP Third Person Character', hxg, 'self'); G.link(hxg, 'XP', hadd, 'A')
G.link(C(Z, 'K2Node_VariableGet', 'XPValue', x0 + 1500, y0 + 350), 'XPValue', hadd, 'B'); G.link(hadd, 'ReturnValue', hxp, 'XP'); G.link(hc, 'AsBP Third Person Character', hxp, 'self'); G.link(hc, 'then', hxp, 'execute')
lvl = C(Z, 'K2Node_CallFunction', 'CheckLevelUp', x0 + 2200, y0); G.link(hc, 'AsBP Third Person Character', lvl, 'self'); G.link(hxp, 'then', lvl, 'execute')
sce = call('SetCollisionEnabled', x0 + 2500, y0); G.link(C(Z, 'K2Node_VariableGet', 'CapsuleComponent', x0 + 2300, y0 + 150), 'CapsuleComponent', sce, 'self')
G.link(lvl, 'then', sce, 'execute'); G.link(hc, 'CastFailed', sce, 'execute')
sm2 = call('StopMovementImmediately', x0 + 2800, y0); G.link(C(Z, 'K2Node_VariableGet', 'CharacterMovement', x0 + 2600, y0 + 150), 'CharacterMovement', sm2, 'self')
ls = call('SetLifeSpan', x0 + 3700, y0); ls.set_default('InLifespan', '8.0')
chain(sce, sm2, play('Mesh', asset('A_HorseBody_Death'), False, x0 + 3100, y0), play('Torso', asset('A_Death', ZA + '/Anims'), False, x0 + 3400, y0 + 300), ls)

open(os.path.join(OUT, 'BP_HalfHorseZombie_EventGraph.txt'), 'w', encoding='utf-8').write(G.render())
V = [bpvar('State', 'int', '0'), bpvar('CurAnim', 'int', '0'), bpvar('WantAnim', 'int', '1'), bpvar('StateTime', 'real', '0.0', sub='double'),
     bpvar('ThinkAcc', 'real', '0.0', sub='double'), bpvar('TorsoDrop', 'real', '-100.0', sub='double')]
open(os.path.join(OUT, 'BP_HalfHorseZombie_vars.txt'), 'w', encoding='utf-8').write('\n'.join(V) + '\n')
print('HORSE nodes', len(G.nodes), 'links', len(G.links))
