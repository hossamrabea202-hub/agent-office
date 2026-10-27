"""gen_revenge.py: BPC_TentacleStrike -> REVENGE strike (owner 2026-10-27).

A tentacle strikes (one cannon) only after its HP drops to <= 10% (re-arms above 50%) or its jelly shield
reaches 0% (once). Target = the cannon whose ball hit it last (OnRevengeHit, bound to every TentacleHit
hitbox's OnTakeAnyDamage) if it still has the Cannon tag and is in StrikeRange, else the nearest cannon.
Bigger rear-back + faster tremble + low growl at the cannon when the strike is claimed.
Writes paste_strike_revenge.t3d + bpvars_revenge.json (4 new vars).
"""
import os, sys, json, re
W = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
sys.path.insert(0, W)
import kit2 as K
import t3dlib as T
from kit2 import G, link, chain, KML, KMLD, ACTOR, BPC, FO, VEC
OUT = os.path.join(W, 'revenge')
STRIKE = '/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleStrike'
SELF = BPC(STRIKE)
VITP = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'
VIT = BPC(VITP)
LV, LS = 'live_BP_TentacleVitals', 'live_BPC_TentacleStrike'

g = G(SELF)
N = g.load_graph(LS, 'EventGraph')


def realfix(n):  # real pins on hand-made var nodes need the double subcategory
    for p in n.pins:
        if 'PinCategory="real"' in p.line:
            p.line = p.line.replace('PinType.PinSubCategory=""', 'PinType.PinSubCategory="double"')
    return n


def isvalid(x, y):
    return g.clone(LS, 'K2Node_CallFunction_2', x, y)


# ------------------------------------------------------------ BeginPlay: bind every hitbox's damage
X0, Y0 = N['K2Node_CallFunction_5'].x + 400, N['K2Node_CallFunction_5'].y
att = g.clone(LV, 'CX_11', X0, Y0 + 260)                       # GetAttachedActors (pure)
link(N['K2Node_CallFunction_1'], 'ReturnValue', att, 'self')   # owner's attach parent = tentacle
loop = g.clone(LV, 'CX_12', X0 + 400, Y0)                      # ForEachLoop
link(att, 'OutActors', loop, 'Array')
link(N['K2Node_CallFunction_5'], 'then', loop, 'Exec')
tag = g.clone(LV, 'CX_13', X0 + 750, Y0 + 220)                 # ActorHasTag TentacleHit
link(loop, 'Array Element', tag, 'self')
b = g.branch(X0 + 1000, Y0)
link(loop, 'LoopBody', b, 'execute'); link(tag, 'ReturnValue', b, 'Condition')
add = g.clone(LV, 'CX_16', X0 + 1250, Y0)                       # AddDelegate OnTakeAnyDamage
link(b, 'then', add, 'execute'); link(loop, 'Array Element', add, 'self')
ev = g.clone(LV, 'CX_15', X0 + 800, Y0 + 500)                   # custom event, damage signature
ev.props = [s.replace('CustomFunctionName="OnShocked"', 'CustomFunctionName="OnRevengeHit"') for s in ev.props]
od = ev.p('OutputDelegate')
od.line = re.sub(r'PinType\.PinSubCategoryMemberReference=\([^)]*\)',
                 'PinType.PinSubCategoryMemberReference=(MemberParent="%s",MemberName="OnRevengeHit")' % SELF, od.line)
link(ev, 'OutputDelegate', add, 'Delegate')

# OnRevengeHit: ball -> its cannon (Owner) -> LastAttacker
cast = g.clone(LV, 'CX_219', X0 + 1250, Y0 + 500)
link(ev, 'then', cast, 'execute'); link(ev, 'DamageCauser', cast, 'Object')
own = g.mcall(ACTOR, 'GetOwner', [('ReturnValue', 'object', True, '', ACTOR)], X0 + 1550, Y0 + 700, pure=True)
link(cast, 'AsBP Cannonball', own, 'self')
v = isvalid(X0 + 1800, Y0 + 700); link(own, 'ReturnValue', v, 'Object')
b = g.branch(X0 + 1800, Y0 + 500); link(cast, 'then', b, 'execute'); link(v, 'ReturnValue', b, 'Condition')
s = g.vset('LastAttacker', 'object', ACTOR, x=X0 + 2050, y=Y0 + 500)
link(b, 'then', s, 'execute'); link(own, 'ReturnValue', s, 'LastAttacker')

# ------------------------------------------------------------ TryStrike gate (State == 0 -> revenge armed?)
if1, c7 = N['K2Node_IfThenElse_1'], N['K2Node_CallFunction_7']
if1.unlink('then')
X, Y = if1.x, if1.y + 1400
gown = g.clone(LS, 'K2Node_CallFunction_0', X + 100, Y + 250)            # component GetOwner
castV = g.clone(LV, 'CX_219', X + 300, Y)
castV.props = [s.replace('/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball.BP_Cannonball_C', VITP + '.BP_TentacleVitals_C') for s in castV.props]
ap = castV.p('AsBP Cannonball')
ap.line = ap.line.replace('PinName="AsBP Cannonball"', 'PinName="AsBP Tentacle Vitals"')
ap.line = re.sub(r'PinType\.PinSubCategoryObject="[^"]*"', 'PinType.PinSubCategoryObject="%s"' % VIT, ap.line)
ap.name = 'AsBP Tentacle Vitals'
link(if1, 'then', castV, 'execute'); link(gown, 'ReturnValue', castV, 'Object')
hp = realfix(g.vget('Health', 'real', None, parent=VIT, x=X + 600, y=Y + 300, external=True))
link(castV, 'AsBP Tentacle Vitals', hp, 'self')
c_hi = g.cmp('Greater_DoubleDouble', b=50000.0, x=X + 850, y=Y + 250); link(hp, 'Health', c_hi, 'A')
b_re = g.branch(X + 700, Y); link(castV, 'then', b_re, 'execute'); link(c_hi, 'ReturnValue', b_re, 'Condition')
s_arm = g.vset('HPArmed', 'bool', x=X + 950, y=Y - 150, default='true'); link(b_re, 'then', s_arm, 'execute')
# HP <= 10% (and alive) while armed
b_hp = g.branch(X + 1250, Y); link(b_re, 'else', b_hp, 'execute'); link(s_arm, 'then', b_hp, 'execute')
g_arm = g.vget('HPArmed', 'bool', None, x=X + 900, y=Y + 450)
c_lo = g.cmp('LessEqual_DoubleDouble', b=10000.0, x=X + 850, y=Y + 550); link(hp, 'Health', c_lo, 'A')
c_alive = g.cmp('Greater_DoubleDouble', b=0.5, x=X + 850, y=Y + 700); link(hp, 'Health', c_alive, 'A')
a1 = g.b2('BooleanAND', X + 1050, Y + 600); link(c_lo, 'ReturnValue', a1, 'A'); link(c_alive, 'ReturnValue', a1, 'B')
a2 = g.b2('BooleanAND', X + 1100, Y + 400); link(g_arm, 'HPArmed', a2, 'A'); link(a1, 'ReturnValue', a2, 'B')
link(a2, 'ReturnValue', b_hp, 'Condition')
s_hpoff = g.vset('HPArmed', 'bool', x=X + 1500, y=Y - 150, default='false')
s_pend1 = g.vset('RevengePending', 'bool', x=X + 1750, y=Y - 150, default='true')
link(b_hp, 'then', s_hpoff, 'execute'); chain(s_hpoff, s_pend1)
# jelly shield at 0% while armed
b_sh = g.branch(X + 2050, Y); link(b_hp, 'else', b_sh, 'execute'); link(s_pend1, 'then', b_sh, 'execute')
g_sarm = g.vget('ShieldArmed', 'bool', None, x=X + 1750, y=Y + 400)
a3 = g.b2('BooleanAND', X + 1950, Y + 400); link(g_sarm, 'ShieldArmed', a3, 'A'); link(c_alive, 'ReturnValue', a3, 'B')
link(a3, 'ReturnValue', b_sh, 'Condition')
fct = g.clone(LV, 'CX_257', X + 2100, Y + 300)                            # FindComponentByTag JellyShell
link(N['K2Node_CallFunction_1'], 'ReturnValue', fct, 'self')
v2 = isvalid(X + 2350, Y + 300); link(fct, 'ReturnValue', v2, 'Object')
b_v = g.branch(X + 2350, Y); link(b_sh, 'then', b_v, 'execute'); link(v2, 'ReturnValue', b_v, 'Condition')
dmi = g.clone(LV, 'CX_258', X + 2600, Y)
link(b_v, 'then', dmi, 'execute'); link(fct, 'ReturnValue', dmi, 'self')
gmax = g.clone(LV, 'CX_259', X + 2900, Y); gl = g.clone(LV, 'CX_260', X + 3200, Y)
chain(dmi, gmax, gl); link(dmi, 'ReturnValue', gmax, 'self'); link(dmi, 'ReturnValue', gl, 'self')
sub = g.f2('Subtract_DoubleDouble', x=X + 3200, y=Y + 300); link(gmax, 'ReturnValue', sub, 'A'); link(gl, 'ReturnValue', sub, 'B')
c_empty = g.cmp('LessEqual_DoubleDouble', b=0.5, x=X + 3400, y=Y + 300); link(sub, 'ReturnValue', c_empty, 'A')
c_has = g.cmp('Greater_DoubleDouble', b=0.5, x=X + 3400, y=Y + 450); link(gmax, 'ReturnValue', c_has, 'A')
a4 = g.b2('BooleanAND', X + 3600, Y + 350); link(c_empty, 'ReturnValue', a4, 'A'); link(c_has, 'ReturnValue', a4, 'B')
b_z = g.branch(X + 3550, Y); link(gl, 'then', b_z, 'execute'); link(a4, 'ReturnValue', b_z, 'Condition')
s_shoff = g.vset('ShieldArmed', 'bool', x=X + 3850, y=Y - 150, default='false')
s_pend2 = g.vset('RevengePending', 'bool', x=X + 4100, y=Y - 150, default='true')
link(b_z, 'then', s_shoff, 'execute'); chain(s_shoff, s_pend2)
# go only while a revenge is pending and the tentacle lives
b_go = g.branch(X + 4450, Y)
for src, pin in ((b_sh, 'else'), (b_v, 'else'), (b_z, 'else'), (s_pend2, 'then')):
    link(src, pin, b_go, 'execute')
g_pend = g.vget('RevengePending', 'bool', None, x=X + 4150, y=Y + 300)
a5 = g.b2('BooleanAND', X + 4300, Y + 300); link(g_pend, 'RevengePending', a5, 'A'); link(c_alive, 'ReturnValue', a5, 'B')
link(a5, 'ReturnValue', b_go, 'Condition')
link(b_go, 'then', c7, 'execute')

# ------------------------------------------------------------ target: last attacker cannon, else nearest
if2, vs2, if3 = N['K2Node_IfThenElse_2'], N['K2Node_VariableSet_2'], N['K2Node_IfThenElse_3']
if2.unlink('then')
X, Y = if2.x, if2.y + 1300
g_la = g.vget('LastAttacker', 'object', ACTOR, x=X, y=Y + 300)
v3 = isvalid(X + 250, Y + 300); link(g_la, 'LastAttacker', v3, 'Object')
b_la = g.branch(X + 250, Y); link(if2, 'then', b_la, 'execute'); link(v3, 'ReturnValue', b_la, 'Condition')
tagc = g.clone(LV, 'CX_13', X + 500, Y + 300).default('Tag', 'Cannon'); link(g_la, 'LastAttacker', tagc, 'self')
laloc = g.loc_of(X + 500, Y + 450); link(g_la, 'LastAttacker', laloc, 'self')
dist = g.pure(KML, KMLD, 'Vector_Distance', [('V1', 'struct', False, '', VEC), ('V2', 'struct', False, '', VEC), ('ReturnValue',) + FO], X + 750, Y + 450)
link(laloc, 'ReturnValue', dist, 'V1'); link(N['K2Node_CallFunction_10'], 'ReturnValue', dist, 'V2')   # root bone location
c_in = g.cmp('LessEqual_DoubleDouble', b=19000.0, x=X + 950, y=Y + 450); link(dist, 'ReturnValue', c_in, 'A')
link(N['K2Node_VariableGet_5'], 'StrikeRange', c_in, 'B')
a6 = g.b2('BooleanAND', X + 1150, Y + 350); link(tagc, 'ReturnValue', a6, 'A'); link(c_in, 'ReturnValue', a6, 'B')
b_la2 = g.branch(X + 600, Y); link(b_la, 'then', b_la2, 'execute'); link(a6, 'ReturnValue', b_la2, 'Condition')
s_tc = g.vset('TargetCannon', 'object', ACTOR, x=X + 950, y=Y); link(b_la2, 'then', s_tc, 'execute'); link(g_la, 'LastAttacker', s_tc, 'TargetCannon')
link(s_tc, 'then', if3, 'execute')
link(b_la, 'else', vs2, 'execute'); link(b_la2, 'else', vs2, 'execute')

# ------------------------------------------------------------ claim: clear pending + low growl at the target cannon
vs11 = N['K2Node_VariableSet_11']
s_pclr = g.vset('RevengePending', 'bool', x=vs11.x + 300, y=vs11.y, default='false')
link(vs11, 'then', s_pclr, 'execute')
growl = g.clone(LS, 'K2Node_CallFunction_77', vs11.x + 600, vs11.y)
growl.default('VolumeMultiplier', '2.0').default('PitchMultiplier', '0.45')
link(s_pclr, 'then', growl, 'execute')
link(N['K2Node_VariableGet_51'], 'HitSound', growl, 'Sound')
link(N['K2Node_CallFunction_75'], 'ReturnValue', growl, 'Location')        # TargetCannon location

# ------------------------------------------------------------ bigger rear-back, faster tremble
N['K2Node_CallFunction_32'].default('B', '0.95')    # windup height  (was 0.85 x reach)
N['K2Node_CallFunction_34'].default('B', '-0.4')    # rear back      (was -0.2 x reach)
N['K2Node_CallFunction_46'].default('B', '9.0')     # tremble freq   (was 6)

n, size = g.emit(os.path.join(OUT, 'paste_strike_revenge.t3d'))


def bpvar(name, cat, default, sub='', subobj=''):
    vt = 'PinCategory="%s"' % cat + (',PinSubCategory="%s"' % sub if sub else '') + (',PinSubCategoryObject="%s"' % subobj if subobj else '')
    return ('BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5%s)'
            % (name, T.gid(), vt, name, (',DefaultValue="%s"' % default) if default is not None else ''))


vars_ = [bpvar('LastAttacker', 'object', None, subobj=ACTOR), bpvar('RevengePending', 'bool', 'False'),
         bpvar('HPArmed', 'bool', 'True'), bpvar('ShieldArmed', 'bool', 'True')]
json.dump({'BPC_TentacleStrike': vars_}, open(os.path.join(OUT, 'bpvars_revenge.json'), 'w'), indent=1)
print('nodes', n, 'chars', size)
