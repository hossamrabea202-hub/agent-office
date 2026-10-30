# BP_BlobMine (#154). TGA, 2026-10-30. A bio-active land mine on laptop2's SM_Flora_BlobMine: it lies still until the
# player steps within TriggerRange (1.5 m) or it takes any damage (shot, cannon, sword); then it bursts: smoke + squelch,
# MineDamage (25) to the player if within 2.5 m, and BlobsMin..BlobsMax (3-6) BP_JellyBlob spill out, AttackedBonus (+3)
# more when it was attacked rather than stepped on. Nodes cloned from the Master's exports (bpkit).
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpkit
from bpkit import Export, Graph, var_get, var_set, fl, it, bo, ob, vec, CLS
OUT = sys.argv[1] if len(sys.argv) > 1 else r'T:\bp\out'
Z = Export(r'R:\handoffs\exports\master\2026-10-30\BP_Zombie.t3d'); W = Export(r'R:\handoffs\exports\master\2026-10-30\BP_ZombieWaveManager.t3d')
GC = Export(r'R:\handoffs\exports\laptop2\prompt68\BP_CastleGateControl.t3d')
ZC = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C'
BLOB = '/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob.BP_JellyBlob_C'
G = Graph('BLM')
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
def actor_toggle(member, pin, val, x, y):
    n = call('SetLifeSpan', x, y); n.sub_prop('MemberName="SetLifeSpan"', 'MemberName="%s"' % member)
    p = n.pin('InLifespan'); p['name'] = pin
    p['line'] = re.sub(r'PinType\.PinCategory="real",PinType\.PinSubCategory="\w*"', 'PinType.PinCategory="bool",PinType.PinSubCategory=""', p['line'].replace('PinName="InLifespan"', 'PinName="%s"' % pin))
    n.set_default(pin, val); return n

# ---- Tick: arm check every 0.2 s (player within TriggerRange -> Trigger) and the burst itself ---------------------
x0, y0 = 0, 0
tk = C(Z, 'K2Node_Event', 'ReceiveTick', x0, y0)
b0 = br(x0 + 300, y0); G.link(getv('Burst', bo('Burst'), x0 + 100, y0 + 150), 'Burst', b0, 'Condition'); G.link(tk, 'then', b0, 'execute')
ca = setv('CheckAcc', fl('CheckAcc'), x0 + 600, y0); ad = call('Add_DoubleDouble', x0 + 450, y0 + 200)
G.link(getv('CheckAcc', fl('CheckAcc'), x0 + 250, y0 + 200), 'CheckAcc', ad, 'A'); G.link(tk, 'DeltaSeconds', ad, 'B'); G.link(ad, 'ReturnValue', ca, 'CheckAcc'); G.link(b0, 'else', ca, 'execute')
b1 = br(x0 + 900, y0); g1 = call('GreaterEqual_DoubleDouble', x0 + 750, y0 + 200); G.link(ca, 'Output_Get', g1, 'A'); g1.set_default('B', '0.2'); G.link(g1, 'ReturnValue', b1, 'Condition'); G.link(ca, 'then', b1, 'execute')
c0 = setv('CheckAcc', fl('CheckAcc'), x0 + 1200, y0, '0.0'); G.link(b1, 'then', c0, 'execute')
pawn = call('GetPlayerPawn', x0 + 1100, y0 + 300, GC); dist = call('GetDistanceTo', x0 + 1300, y0 + 300); G.link(pawn, 'ReturnValue', dist, 'OtherActor')
lt = call('Less_DoubleDouble', x0 + 1500, y0 + 300); G.link(dist, 'ReturnValue', lt, 'A'); G.link(getv('TriggerRange', fl('TriggerRange'), x0 + 1300, y0 + 450), 'TriggerRange', lt, 'B')
orr = call('BooleanOR', x0 + 1700, y0 + 300); G.link(lt, 'ReturnValue', orr, 'A'); G.link(getv('Trigger', bo('Trigger'), x0 + 1500, y0 + 450), 'Trigger', orr, 'B')
b2 = br(x0 + 1500, y0); G.link(orr, 'ReturnValue', b2, 'Condition'); G.link(c0, 'then', b2, 'execute')
x1 = x0 + 1800
bu = setv('Burst', bo('Burst'), x1, y0, 'true'); G.link(b2, 'then', bu, 'execute')
hide = actor_toggle('SetActorHiddenInGame', 'bNewHidden', 'true', x1 + 250, y0); col = actor_toggle('SetActorEnableCollision', 'bNewActorEnableCollision', 'false', x1 + 500, y0)
me = call('K2_GetActorLocation', x1 + 600, y0 + 300)
fx = call('SpawnEmitterAtLocation', x1 + 750, y0); fx.set_default('Scale', '1.400000,1.400000,1.400000'); G.link(me, 'ReturnValue', fx, 'Location')
snd = call('PlaySoundAtLocation', x1 + 1000, y0); snd.set_default('Sound', obj='/Game/Audio/Kenney/SFX_impactPunch_heavy_002.SFX_impactPunch_heavy_002')
snd.set_default('PitchMultiplier', '0.5').set_default('VolumeMultiplier', '1.5'); G.link(me, 'ReturnValue', snd, 'Location')
chain(bu, hide, col, fx, snd)
bh = br(x1 + 1300, y0); d2 = call('GetDistanceTo', x1 + 1100, y0 + 300); G.link(call('GetPlayerPawn', x1 + 900, y0 + 350, GC), 'ReturnValue', d2, 'OtherActor')
l2 = call('Less_DoubleDouble', x1 + 1250, y0 + 300); G.link(d2, 'ReturnValue', l2, 'A'); l2.set_default('B', '250.0'); G.link(l2, 'ReturnValue', bh, 'Condition'); G.link(snd, 'then', bh, 'execute')
dm = call('ApplyDamage', x1 + 1600, y0 - 150); G.link(call('GetPlayerPawn', x1 + 1400, y0 - 50, GC), 'ReturnValue', dm, 'DamagedActor')
G.link(getv('MineDamage', fl('MineDamage'), x1 + 1400, y0 + 50), 'MineDamage', dm, 'BaseDamage'); G.link(C(Z, 'K2Node_Self', None, x1 + 1400, y0 + 130), 'self', dm, 'DamageCauser')
G.link(bh, 'then', dm, 'execute')
# blobs: RandomInt(BlobsMin, BlobsMax) + Extra, each spawned around the mine
ri = call('RandomIntegerInRange', x1 + 1700, y0 + 300); G.link(getv('BlobsMin', it('BlobsMin'), x1 + 1500, y0 + 300), 'BlobsMin', ri, 'Min'); G.link(getv('BlobsMax', it('BlobsMax'), x1 + 1500, y0 + 400), 'BlobsMax', ri, 'Max')
cnt = call('Add_IntInt', x1 + 1900, y0 + 300); G.link(ri, 'ReturnValue', cnt, 'A'); G.link(getv('Extra', it('Extra'), x1 + 1700, y0 + 450), 'Extra', cnt, 'B')
fo = G.clone(W, 'CX_26', x1 + 2000, y0); fo.set_default('FirstIndex', '1'); G.link(cnt, 'ReturnValue', fo, 'LastIndex')
G.link(dm, 'then', fo, 'execute'); G.link(bh, 'else', fo, 'execute')
sp = G.clone(W, 'CX_30', x1 + 2400, y0); sp.set_default('Class', obj=BLOB); rv = sp.pin('ReturnValue'); rv['line'] = rv['line'].replace(ZC, BLOB)
rr = [call('RandomFloatInRange', x1 + 2000, y0 + 400 + 100 * i) for i in range(2)]
for r_ in rr: r_.set_default('Min', '-160.0').set_default('Max', '160.0')
mv = call('MakeVector', x1 + 2200, y0 + 450); mv.set_default('Z', '60.0'); G.link(rr[0], 'ReturnValue', mv, 'X'); G.link(rr[1], 'ReturnValue', mv, 'Y')
av = call('Add_VectorVector', x1 + 2400, y0 + 350); G.link(call('K2_GetActorLocation', x1 + 2200, y0 + 300), 'ReturnValue', av, 'A'); G.link(mv, 'ReturnValue', av, 'B')
mt = G.clone(W, 'CX_29', x1 + 2600, y0 + 350); G.link(av, 'ReturnValue', mt, 'Location'); G.link(mt, 'ReturnValue', sp, 'SpawnTransform'); G.link(fo, 'LoopBody', sp, 'execute')
ls = call('SetLifeSpan', x1 + 2800, y0); ls.set_default('InLifespan', '0.3'); G.link(fo, 'Completed', ls, 'execute')
# ---- AnyDamage: shot / hit -> burst with the attacked bonus ------------------------------------------------------
x0, y0 = 0, 1200
ed = C(Z, 'K2Node_Event', 'ReceiveAnyDamage', x0, y0)
bd = br(x0 + 300, y0); G.link(getv('Trigger', bo('Trigger'), x0 + 100, y0 + 150), 'Trigger', bd, 'Condition'); G.link(ed, 'then', bd, 'execute')
ex_ = setv('Extra', it('Extra'), x0 + 600, y0); G.link(getv('AttackedBonus', it('AttackedBonus'), x0 + 400, y0 + 200), 'AttackedBonus', ex_, 'Extra'); G.link(bd, 'else', ex_, 'execute')
chain(ex_, setv('Trigger', bo('Trigger'), x0 + 850, y0, 'true'))

open(os.path.join(OUT, 'BP_BlobMine_EventGraph.txt'), 'w', encoding='utf-8').write(G.render())
def bv(name, cat, default, sub=None):
    vt = 'PinCategory="%s"' % cat + (',PinSubCategory="%s"' % sub if sub else '')
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (name, bpkit.g(), vt, name, default)
V = [bv('Burst', 'bool', 'False'), bv('Trigger', 'bool', 'False'), bv('CheckAcc', 'real', '0.0', 'double'), bv('TriggerRange', 'real', '150.0', 'double'),
     bv('MineDamage', 'real', '25.0', 'double'), bv('BlobsMin', 'int', '3'), bv('BlobsMax', 'int', '6'), bv('Extra', 'int', '0'), bv('AttackedBonus', 'int', '3')]
open(os.path.join(OUT, 'BP_BlobMine_vars.txt'), 'w', encoding='utf-8').write('\n'.join(V) + '\n')
print('BLOBMINE nodes', len(G.nodes), 'links', len(G.links))
