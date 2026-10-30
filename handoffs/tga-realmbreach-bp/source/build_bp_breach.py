# BP_RealmBreach (#169 stage 2). TGA, 2026-10-30. A separate actor (no merge into the wave manager): once a second it
# reads WaveManager.Wave; at BreachWave (5) it breaks the realm wall once: hides Realm_Wall_Breach_A/B, shows the
# pre-placed broken wall (SM_SiegeBarricade_Breach), smoke burst + crash + camera shake, sets WaveManager.SwarmUnlocked
# (wasps + half-horses, #174/#175), and spawns the realm horde at laptop2's points: a BP_Zombie at every
# Realm_Spawn_Zombie_NN and a BP_HalfHorseZombie at every Realm_Spawn_Giant_NN, all told to ResumeMove (they head out).
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpkit
from bpkit import Export, Graph, var_get, var_set, fl, it, bo, ob, vec, CLS
OUT = sys.argv[1] if len(sys.argv) > 1 else r'T:\bp\out'
Z = Export(r'R:\handoffs\exports\master\2026-10-30\BP_Zombie.t3d'); W = Export(r'R:\handoffs\exports\master\2026-10-30\BP_ZombieWaveManager.t3d')
WM = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager.BP_ZombieWaveManager_C'
ZC = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C'
HC = '/Game/CastleDefender/Characters/Enemies/HalfHorseZombie/BP_HalfHorseZombie.BP_HalfHorseZombie_C'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C'
G = Graph('RBR')
def T(ex, cls, member=None, extra=None): return ex.find(cls, member, extra)
def C(ex, cls, member=None, x=0, y=0, extra=None): return G.clone(ex, T(ex, cls, member, extra), x, y)
def call(member, x, y, ex=Z): return C(ex, 'K2Node_CallFunction', member, x, y)
def br(x, y): return C(Z, 'K2Node_IfThenElse', None, x, y)
def getv(name, pin, x, y): return var_get(G, name, pin, x, y)
def setv(name, pin, x, y, value=None):
    n = var_set(G, name, pin, x, y)
    if value is not None: n.set_default(name, value)
    return n
def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]): G.link(a, 'then', b, 'execute')
    return nodes[-1]
ACT = lambda n: ob(n, CLS('Actor'))
WMREF = lambda n: ob(n, '"/Script/Engine.BlueprintGeneratedClass\'%s\'"' % WM)
def actor_toggle(member, pin, val, x, y):       # SetActorHiddenInGame / SetActorEnableCollision on SetLifeSpan's shell
    n = call('SetLifeSpan', x, y); n.sub_prop('MemberName="SetLifeSpan"', 'MemberName="%s"' % member)
    p = n.pin('InLifespan'); p['name'] = pin
    p['line'] = re.sub(r'PinType\.PinCategory="real",PinType\.PinSubCategory="\w*"', 'PinType.PinCategory="bool",PinType.PinSubCategory=""', p['line'].replace('PinName="InLifespan"', 'PinName="%s"' % pin))
    n.set_default(pin, val); return n
def other_var(member, cat_from, cat_to, x, y, setter=False):   # Get/Set a variable on the wave manager (hero XP node retargeted)
    n = C(Z, 'K2Node_VariableSet' if setter else 'K2Node_VariableGet', 'XP', x, y)
    n.props = [l.replace('MemberName="XP"', 'MemberName="%s"' % member).replace(HERO, WM) for l in n.props]
    for p in n.pins:
        if p['name'] in ('XP', 'Output_Get'):
            if p['name'] == 'XP': p['name'] = member; p['line'] = p['line'].replace('PinName="XP"', 'PinName="%s"' % member)
            p['line'] = p['line'].replace('PinType.PinCategory="int"', 'PinType.PinCategory="%s"' % cat_to)
        if p['name'] == 'self': p['line'] = p['line'].replace(HERO, WM)
    return n

x0, y0 = 0, 0
tk = C(Z, 'K2Node_Event', 'ReceiveTick', x0, y0)
b0 = br(x0 + 300, y0); G.link(getv('Broken', bo('Broken'), x0 + 100, y0 + 150), 'Broken', b0, 'Condition'); G.link(tk, 'then', b0, 'execute')
ca = setv('CheckAcc', fl('CheckAcc'), x0 + 600, y0); ad = call('Add_DoubleDouble', x0 + 450, y0 + 200)
G.link(getv('CheckAcc', fl('CheckAcc'), x0 + 250, y0 + 200), 'CheckAcc', ad, 'A'); G.link(tk, 'DeltaSeconds', ad, 'B'); G.link(ad, 'ReturnValue', ca, 'CheckAcc'); G.link(b0, 'else', ca, 'execute')
b1 = br(x0 + 900, y0); g1 = call('GreaterEqual_DoubleDouble', x0 + 750, y0 + 200); G.link(ca, 'Output_Get', g1, 'A'); g1.set_default('B', '1.0'); G.link(g1, 'ReturnValue', b1, 'Condition'); G.link(ca, 'then', b1, 'execute')
c0 = setv('CheckAcc', fl('CheckAcc'), x0 + 1200, y0, '0.0'); G.link(b1, 'then', c0, 'execute')
iv = call('IsValid', x0 + 1300, y0 + 250); wmg = getv('WaveManager', WMREF('WaveManager'), x0 + 1100, y0 + 300); G.link(wmg, 'WaveManager', iv, 'Object')
wv = other_var('Wave', 'int', 'int', x0 + 1300, y0 + 400); G.link(getv('WaveManager', WMREF('WaveManager'), x0 + 1100, y0 + 450), 'WaveManager', wv, 'self')
ge = call('GreaterEqual_IntInt', x0 + 1500, y0 + 400, W); G.link(wv, 'Wave', ge, 'A'); G.link(getv('BreachWave', it('BreachWave'), x0 + 1300, y0 + 550), 'BreachWave', ge, 'B')
an = call('BooleanAND', x0 + 1700, y0 + 300); G.link(iv, 'ReturnValue', an, 'A'); G.link(ge, 'ReturnValue', an, 'B')
b2 = br(x0 + 1500, y0); G.link(an, 'ReturnValue', b2, 'Condition'); G.link(c0, 'then', b2, 'execute')
# ---- the break --------------------------------------------------------------------------------------------------
x1 = x0 + 1800
brk = setv('Broken', bo('Broken'), x1, y0, 'true'); G.link(b2, 'then', brk, 'execute')
steps = [brk]
for i, (var, member, pin, val) in enumerate((('BreachA', 'SetActorHiddenInGame', 'bNewHidden', 'true'), ('BreachA', 'SetActorEnableCollision', 'bNewActorEnableCollision', 'false'),
                                             ('BreachB', 'SetActorHiddenInGame', 'bNewHidden', 'true'), ('BreachB', 'SetActorEnableCollision', 'bNewActorEnableCollision', 'false'),
                                             ('BreachedWall', 'SetActorHiddenInGame', 'bNewHidden', 'false'), ('BreachedWall', 'SetActorEnableCollision', 'bNewActorEnableCollision', 'true'))):
    n = actor_toggle(member, pin, val, x1 + 250 * (i + 1), y0); G.link(getv(var, ACT(var), x1 + 250 * (i + 1) - 150, y0 + 180), var, n, 'self'); steps.append(n)
chain(*steps)
wl = call('K2_GetActorLocation', x1 + 1700, y0 + 300); G.link(getv('BreachedWall', ACT('BreachedWall'), x1 + 1500, y0 + 350), 'BreachedWall', wl, 'self')
fx = call('SpawnEmitterAtLocation', x1 + 1900, y0); fx.set_default('Scale', '3.500000,3.500000,3.500000'); G.link(wl, 'ReturnValue', fx, 'Location')
snd = call('PlaySoundAtLocation', x1 + 2200, y0); snd.set_default('Sound', obj='/Game/CastleDefender/AssetPacks/StarterContent/Audio/Explosion_Cue.Explosion_Cue')
snd.set_default('VolumeMultiplier', '2.0').set_default('PitchMultiplier', '0.6'); G.link(wl, 'ReturnValue', snd, 'Location')
sk = call('PlayWorldCameraShake', x1 + 2500, y0); sk.set_default('OuterRadius', '9000.0'); G.link(wl, 'ReturnValue', sk, 'Epicenter')
su = other_var('SwarmUnlocked', 'int', 'bool', x1 + 2800, y0, setter=True); su.set_default('SwarmUnlocked', 'true')
G.link(getv('WaveManager', WMREF('WaveManager'), x1 + 2600, y0 + 200), 'WaveManager', su, 'self')
chain(steps[-1], fx, snd, sk, su)
# ---- the horde walks out ----------------------------------------------------------------------------------------
def horde(arr, cls_path, x, y):
    fe = C(Z, 'K2Node_MacroInstance', None, x, y, extra='ForEachLoop')
    fe.props = [re.sub(r"PinSubCategoryObject=\"/Script/Engine\.BlueprintGeneratedClass'[^']+'\"", "PinSubCategoryObject=\"/Script/CoreUObject.Class'/Script/Engine.Actor'\"", l) for l in fe.props]
    for pn in ('Array', 'Array Element'):
        p = fe.pin(pn); p['line'] = re.sub(r"PinSubCategoryObject=\"/Script/Engine\.BlueprintGeneratedClass'[^']+'\"", "PinSubCategoryObject=\"/Script/CoreUObject.Class'/Script/Engine.Actor'\"", p['line'])
    G.link(getv(arr, dict(ACT(arr), container='Array'), x - 200, y + 150), arr, fe, 'Array')
    sp = G.clone(W, 'CX_30', x + 300, y); sp.set_default('Class', obj=cls_path)
    rv = sp.pin('ReturnValue'); rv['line'] = rv['line'].replace(ZC, cls_path)
    pl = call('K2_GetActorLocation', x + 100, y + 300); G.link(fe, 'Array Element', pl, 'self')
    mt = G.clone(W, 'CX_29', x + 200, y + 400); G.link(pl, 'ReturnValue', mt, 'Location'); G.link(mt, 'ReturnValue', sp, 'SpawnTransform')
    rm = G.clone(W, 'WV_65', x + 600, y); G.link(sp, 'ReturnValue', rm, 'self')
    G.link(fe, 'LoopBody', sp, 'execute'); G.link(sp, 'then', rm, 'execute')
    return fe
hz = horde('RealmSpawns', ZC, x1 + 3200, y0); G.link(su, 'then', hz, 'Exec')
hg = horde('GiantSpawns', HC, x1 + 4200, y0); G.link(hz, 'Completed', hg, 'Exec')

open(os.path.join(OUT, 'BP_RealmBreach_EventGraph.txt'), 'w', encoding='utf-8').write(G.render())
def bv(name, cat, default, sub=None, obj=None, arr=False):
    vt = 'PinCategory="%s"' % cat + (',PinSubCategory="%s"' % sub if sub else '') + (',PinSubCategoryObject="%s"' % obj if obj else '') + (',ContainerType=Array' if arr else '')
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (name, bpkit.g(), vt, name, default)
A_ = "/Script/CoreUObject.Class'/Script/Engine.Actor'"
V = [bv('BreachWave', 'int', '5'), bv('Broken', 'bool', 'False'), bv('CheckAcc', 'real', '0.0', sub='double'),
     bv('WaveManager', 'object', '', obj="/Script/Engine.BlueprintGeneratedClass'%s'" % WM),
     bv('BreachA', 'object', '', obj=A_), bv('BreachB', 'object', '', obj=A_), bv('BreachedWall', 'object', '', obj=A_),
     bv('RealmSpawns', 'object', '', obj=A_, arr=True), bv('GiantSpawns', 'object', '', obj=A_, arr=True)]
open(os.path.join(OUT, 'BP_RealmBreach_vars.txt'), 'w', encoding='utf-8').write('\n'.join(V) + '\n')
print('BREACH nodes', len(G.nodes), 'links', len(G.links))
