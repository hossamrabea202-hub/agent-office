# #201 Mine + ore carts + metal stockpile (Blueprint-only, UE 5.3). Owner design 2026-10-30, graphs by laptop2.
#   BP_Mine    (new Actor)      every Period s rolls a metal (wave-shifted, with 'vein strikes') and sends a BP_OreCart.
#   BP_OreCart (new Character)  tints its Load mesh, walks to the castle gate (NavMesh), delivers 1 ore to the HUD
#                               stockpile; if zombies kill it (HP 300) it drops a BP_OrePile instead.
#   BP_OrePile (new Actor)      tinted ore on the road; the hero walks over it -> stockpile; gone after 60 s.
#   BP_ZombieHUD                new int array Ore[5] (Iron, Copper, Silver, Gold ore, Starmetal) + a counter line
#                               under the XP bar (paste + 2 rewires, see manifest_hud.json).
#   python gen201.py -> BP_Mine_graph.txt, BP_OreCart_graph.txt, BP_OrePile_graph.txt, ZombieHUD_Ore_graph.txt, manifest_hud.json
import os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

P_CASTLE = '/Game/CastleDefender/Gameplay/Castle/'
P_MINE, P_CART, P_PILE = P_CASTLE + 'BP_Mine', P_CASTLE + 'BP_OreCart', P_CASTLE + 'BP_OrePile'
P_HUD, P_GATE = P_CASTLE + 'BP_ZombieHUD', P_CASTLE + 'BP_CastleGateControl'
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
CARTC, PILEC, HUDC = BPC(P_CART, 'BP_OreCart'), BPC(P_PILE, 'BP_OrePile'), BPC(P_HUD, 'BP_ZombieHUD')
GATEC, HEROC = BPC(P_GATE, 'BP_CastleGateControl'), BPC(P_HERO, 'BP_ThirdPersonCharacter')
SMC, HUDCLS, FONT = CLS('StaticMeshComponent'), CLS('HUD'), CLS('Font')
METALS = ['Iron', 'Copper', 'Silver', 'Gold ore', 'Starmetal']
COLORS = ['0.25, 0.25, 0.28', '0.75, 0.35, 0.15', '0.85, 0.85, 0.90', '1.00, 0.75, 0.20', '0.30, 0.60, 1.00']
CUM = ['55.0', '75.0', '90.0', '97.0']            # roll < 55 iron, < 75 copper, < 90 silver, < 97 gold ore, else starmetal


def event_override(b, nm, member, params, x, y):
    """Actor event with output pins (ReceiveAnyDamage, ReceiveActorBeginOverlap)."""
    b.G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (ACT, member), 'bOverrideFunction=True'],
             [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (ACT, member)}, ex('then', True)]
             + [dict(p, out=True) for p in params], x, y)
    return nm


def selint(b, a, b_, pick, x, y, da='0', db='0'):
    return b.math('SelectInt', [(it('A', default=da), a), (it('B', default=db), b_), (bo('bPickA', default='false'), pick)], it('ReturnValue', out=True), x, y)


def destroy(b, x, y): return b.call_self('K2_DestroyActor', [], x, y, ACT, tag='Destroy')


def tint_load(b, metal, x, y):
    """Load (StaticMeshComponent) -> SetVectorParameterValueOnMaterials('Tint', colour of the metal). Returns the exec node."""
    c = b.selvec(None, None, b.icmp('EqualEqual_IntInt', metal, None, x, y + 650, db='0'), x + 250, y + 500, da=COLORS[0], db=COLORS[1])
    for i in (2, 3, 4):
        c = b.selvec(c, None, b.icmp('Less_IntInt', metal, None, x + 250 * (i - 1), y + 650, db=str(i)), x + 250 * i, y + 500, db=COLORS[i])
    load = b.get('Load', ob('v', SMC), x + 900, y + 300)
    n = b.call(PRIM, 'SetVectorParameterValueOnMaterials', [N('ParameterName', default='Tint'), V('ParameterValue')], x + 1200, y, target=load, tag='TintLoad')
    b.wire(c, n, 'ParameterValue'); return n


def deliver(b, metal, x, y):
    """HUD.Ore[metal] += 1. Returns (first exec node, last exec node)."""
    pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y + 300, pure=True, tag='PC')
    hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x + 250, y + 300, target=(pc, 'ReturnValue'), pure=True, const=True, tag='HUD')
    cs = b.name('AsZombieHUD'); cast(b.G, cs, HUDC, 'AsBP Zombie HUD', x + 500, y); b.wire((hud, 'ReturnValue'), cs, 'Object')
    ore = b.getm('Ore', HUDC, arr(INT), (cs, 'AsBP Zombie HUD'), x + 850, y + 300)
    gi = b.name('OreItem'); b.G.node(gi, 'K2Node_GetArrayItem', [], [arr(dict(INT, name='Array')), it('Dimension 1', default='0'), dict(INT, name='Output', out=True)], x + 1100, y + 300)
    b.wire(ore, gi, 'Array'); b.wire(metal, gi, 'Dimension 1')
    plus = b.i2('Add_IntInt', (gi, 'Output'), None, x + 1350, y + 300, db='1')
    ore2 = b.getm('Ore', HUDC, arr(INT), (cs, 'AsBP Zombie HUD'), x + 1350, y + 500)
    aset = b.name('SetOre')
    b.G.node(aset, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Set")' % KARR],
             [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
              it('Index', default='0'), {'name': 'Item', 'cat': 'wildcard', 'ref': True, 'default': '0'}, bo('bSizeToFit', default='true')], x + 1650, y)
    b.wire(ore2, aset, 'TargetArray'); b.wire(metal, aset, 'Index'); b.wire(plus, aset, 'Item')
    b.G.link(cs, 'then', aset, 'execute')
    return cs, aset


# ---------------------------------------------------------------- BP_Mine ----------------------------------------------------------------
G = Graph(); b = B(G, 'mn')
bp = b.override('MineBeginPlay', 'ReceiveBeginPlay', 0, 0)
tm = b.timer('Produce', 300, 0, time=b.get('Period', D('v', default='45.0'), 100, 200), loop=True); G.link(bp, 'then', tm, 'execute')
ev = b.event('Produce', [], 0, 800)
Y = 800
wmf = b.actor_of(P_WM, WM, 0, Y + 500); wave = b.getm('Wave', WM, INT, (wmf, 'ReturnValue'), 300, Y + 500)
roll = b.d2('Add_DoubleDouble', b.rnd('0.0', '100.0', 300, Y + 300), b.d2('Multiply_DoubleDouble', b.i2d(wave, 550, Y + 500), None, 800, Y + 500, db='1.5'), 1050, Y + 300)
m = selint(b, None, None, b.dcmp('Less_DoubleDouble', roll, None, 1300, Y + 700, db=CUM[3]), 1550, Y + 600, da='3', db='4')
m = selint(b, None, m, b.dcmp('Less_DoubleDouble', roll, None, 1300, Y + 550, db=CUM[2]), 1800, Y + 500, da='2')
m = selint(b, None, m, b.dcmp('Less_DoubleDouble', roll, None, 1300, Y + 400, db=CUM[1]), 2050, Y + 400, da='1')
m = selint(b, None, m, b.dcmp('Less_DoubleDouble', roll, None, 1300, Y + 250, db=CUM[0]), 2300, Y + 300, da='0')
# vein: while VeinLeft > 0 the mine keeps giving VeinMetal
vl = b.get('VeinLeft', INT, 2300, Y + 800)
m = selint(b, m, b.get('VeinMetal', INT, 2300, Y + 950), b.icmp('LessEqual_IntInt', vl, None, 2550, Y + 850, db='0'), 2800, Y + 300)
s_last = b.set('LastMetal', INT, m, 300, Y); G.link(ev, 'then', s_last, 'execute')
br = b.branch(b.icmp('Greater_IntInt', b.get('VeinLeft', INT, 3000, Y + 150), None, 3250, Y + 150, db='0'), 3500, Y, 'IfVein')
G.link(s_last, 'then', br, 'execute')
s_dec = b.set('VeinLeft', INT, b.i2('Subtract_IntInt', b.get('VeinLeft', INT, 3750, Y + 150), None, 4000, Y + 150, db='1'), 4250, Y)
G.link(br, 'then', s_dec, 'execute')
br2 = b.branch(b.dcmp('Less_DoubleDouble', b.rnd('0.0', '100.0', 3750, Y + 400), None, 4000, Y + 400, db='10.0'), 4250, Y + 250, 'IfStrike')   # 10 %: a vein of 3
G.link(br, 'else', br2, 'execute')
s_vm = b.set('VeinMetal', INT, b.get('LastMetal', INT, 4500, Y + 400), 4750, Y + 250)
s_vl = b.set('VeinLeft', it('v', default='2'), None, 5000, Y + 250)   # a vein = 2 more carts of the same metal
G.link(br2, 'then', s_vm, 'execute'); G.link(s_vm, 'then', s_vl, 'execute')
# spawn the cart 3 m in front of the mine, then hand it the metal (SetLoad also starts its trip)
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 5000, Y + 600, ACT, pure=True, const=True, tag='MineLoc')
fwd = b.call_self('GetActorForwardVector', [V('ReturnValue', out=True)], 5000, Y + 750, ACT, pure=True, const=True, tag='MineFwd')
off = b.math('Multiply_VectorFloat', [(V('A'), (fwd, 'ReturnValue')), (fl('B', default='300.0'), None)], V('ReturnValue', out=True), 5250, Y + 750)
loc = b.v2('Add_VectorVector', (me, 'ReturnValue'), off, 5500, Y + 600)
sp = spawn(b, P_CART, CARTC, transform(b, loc, 5750, Y + 600), 5500, Y)
G.link(s_dec, 'then', sp, 'execute'); G.link(s_vl, 'then', sp, 'execute'); G.link(br2, 'else', sp, 'execute')
ld = b.call(CARTC, 'SetLoad', [it('Metal', default='0')], 6100, Y, target=(sp, 'ReturnValue'), tag='CartSetLoad')
b.wire(b.get('LastMetal', INT, 5850, Y + 300), ld, 'Metal'); G.link(sp, 'then', ld, 'execute')
open(os.path.join(HERE, 'BP_Mine_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('BP_Mine', len(G.nodes), 'nodes')

# ---------------------------------------------------------------- BP_OreCart ----------------------------------------------------------------
G = Graph(); b = B(G, 'oc')
ev = b.event('SetLoad', [it('Metal', default='0')], 0, 0)
s_m = b.set('Metal', INT, (ev, 'Metal'), 300, 0); G.link(ev, 'then', s_m, 'execute')
tn = tint_load(b, b.get('Metal', INT, 600, 300), 600, 0); G.link(s_m, 'then', tn, 'execute')
gate = b.actor_of(P_GATE, GATEC, 2100, 400)
ctl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 2100, 250, PAWN, pure=True, const=True, tag='Ctl')
mv = b.lib(NAVSYS, 'SimpleMoveToActor', [ob('Controller', CTRL), ob('Goal', ACT)], 2400, 0, tag='GoToGate')
b.wire((ctl, 'ReturnValue'), mv, 'Controller'); b.wire((gate, 'ReturnValue'), mv, 'Goal'); G.link(tn, 'then', mv, 'execute')
tm = b.timer('Arrive', 2800, 0, dtime='0.5', loop=True); G.link(mv, 'then', tm, 'execute')
Y = 900
ev2 = b.event('Arrive', [], 0, Y)
gate2 = b.actor_of(P_GATE, GATEC, 0, Y + 300)
dist = b.call_self('GetDistanceTo', [ob('OtherActor', ACT), fl('ReturnValue', out=True)], 300, Y + 300, ACT, pure=True, const=True, tag='DistGate')
b.wire((gate2, 'ReturnValue'), dist, 'OtherActor')
br = b.branch(b.dcmp('Less_DoubleDouble', (dist, 'ReturnValue'), None, 600, Y + 300, db='500.0'), 900, Y, 'IfAtGate'); G.link(ev2, 'then', br, 'execute')
d0, d1 = deliver(b, b.get('Metal', INT, 1200, Y + 600), 1200, Y); G.link(br, 'then', d0, 'execute')
ds = destroy(b, 3200, Y); G.link(d1, 'then', ds, 'execute')
Y = 2200
dmg = event_override(b, 'CartAnyDamage', 'ReceiveAnyDamage', [fl('Damage'), ob('DamageType', CLS('DamageType')), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 0, Y)
hp = b.set('HP', DBL, b.d2('Subtract_DoubleDouble', b.get('HP', DBL, 300, Y + 300), (dmg, 'Damage'), 550, Y + 300), 800, Y); G.link(dmg, 'then', hp, 'execute')
br2 = b.branch(b.dcmp('LessEqual_DoubleDouble', b.get('HP', DBL, 1100, Y + 300), None, 1350, Y + 300, db='0.0'), 1600, Y, 'IfDead'); G.link(hp, 'then', br2, 'execute')
me = b.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], 1900, Y + 400, ACT, pure=True, const=True, tag='CartLoc')
sp = spawn(b, P_PILE, PILEC, transform(b, (me, 'ReturnValue'), 2150, Y + 400), 2000, Y); G.link(br2, 'then', sp, 'execute')
ld = b.call(PILEC, 'SetLoad', [it('Metal', default='0')], 2600, Y, target=(sp, 'ReturnValue'), tag='PileSetLoad')
b.wire(b.get('Metal', INT, 2350, Y + 300), ld, 'Metal'); G.link(sp, 'then', ld, 'execute')
ds2 = destroy(b, 3000, Y); G.link(ld, 'then', ds2, 'execute')
open(os.path.join(HERE, 'BP_OreCart_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('BP_OreCart', len(G.nodes), 'nodes')

# ---------------------------------------------------------------- BP_OrePile ----------------------------------------------------------------
G = Graph(); b = B(G, 'op')
ev = b.event('SetLoad', [it('Metal', default='0')], 0, 0)
s_m = b.set('Metal', INT, (ev, 'Metal'), 300, 0); G.link(ev, 'then', s_m, 'execute')
tn = tint_load(b, b.get('Metal', INT, 600, 300), 600, 0); G.link(s_m, 'then', tn, 'execute')
tm = b.timer('Vanish', 2100, 0, dtime='60.0'); G.link(tn, 'then', tm, 'execute')
Y = 900
ev2 = b.event('Vanish', [], 0, Y); ds = destroy(b, 300, Y); G.link(ev2, 'then', ds, 'execute')
Y = 1300
ov = event_override(b, 'PileOverlap', 'ReceiveActorBeginOverlap', [ob('OtherActor', ACT)], 0, Y)
cs = b.name('AsHero'); cast(G, cs, HEROC, 'AsBP Third Person Character', 300, Y); b.wire((ov, 'OtherActor'), cs, 'Object'); G.link(ov, 'then', cs, 'execute')
d0, d1 = deliver(b, b.get('Metal', INT, 700, Y + 600), 700, Y); G.link(cs, 'then', d0, 'execute')
ds2 = destroy(b, 2700, Y); G.link(d1, 'then', ds2, 'execute')
open(os.path.join(HERE, 'BP_OrePile_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('BP_OrePile', len(G.nodes), 'nodes')

# ---------------------------------------------------------------- BP_ZombieHUD: ore counter line ----------------------------------------------------------------
G = Graph(); b = B(G, 'or')
pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], 0, 400, pure=True, tag='PC')
vs = b.call(PCON, 'GetViewportSize', [it('SizeX', out=True), it('SizeY', out=True)], 250, 400, target=(pc, 'ReturnValue'), pure=True, const=True, tag='ViewSize')
sx = b.d2('Multiply_DoubleDouble', b.i2d((vs, 'SizeX'), 500, 400), None, 750, 400, db='0.015')
sy = b.d2('Multiply_DoubleDouble', b.i2d((vs, 'SizeY'), 500, 550), None, 750, 550, db='0.14')
s = None
for i, (lab, _) in enumerate(zip(['Fe', 'Cu', 'Ag', 'Au', 'Star'], METALS)):
    gi = b.name('Ore%d' % i); G.node(gi, 'K2Node_GetArrayItem', [], [arr(dict(INT, name='Array')), it('Dimension 1', default=str(i)), dict(INT, name='Output', out=True)], 250 + i * 500, 900)
    b.wire(b.get('Ore', arr(INT), i * 500, 900), gi, 'Array')
    n = b.name('IntStr%d' % i); callfn(G, n, KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], pure=True, x=250 + i * 500, y=1050, self_hidden=True)
    b.wire((gi, 'Output'), n, 'InInt')
    s = b.concat(s, (n, 'ReturnValue'), 250 + i * 500, 750, da=('ORE   ' if i == 0 else '') + lab + ' ')
    s = b.concat(s, None, 250 + i * 500 + 250, 750, db='   ')
dt = b.call_self('DrawText', [S('Text'), st('TextColor', LC, default='(R=0.950000,G=0.880000,B=0.760000,A=1.000000)'), fl('ScreenX'), fl('ScreenY'),
                               ob('Font', FONT), fl('Scale', default='1.400000'), bo('bScalePosition', default='false')], 3000, 0, HUDCLS, tag='DrawOre')
b.wire(s, dt, 'Text'); b.wire(sx, dt, 'ScreenX'); b.wire(sy, dt, 'ScreenY')
open(os.path.join(HERE, 'ZombieHUD_Ore_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_ZombieHUD', 'pastes': ['ZombieHUD_Ore_graph.txt'], 'rewires': [
  {'from': 'UX_CallFunction_23.then', 'to': dt + '.execute', 'replace': True, 'note': 'after the XP bar texture draw (was -> K2Node_IfThenElse_H296)'},
  {'from': dt + '.then', 'to': 'K2Node_IfThenElse_H296.execute', 'note': 'then the rest of the draw chain'}]},
  open(os.path.join(HERE, 'manifest_hud.json'), 'w'), indent=1)
print('ZombieHUD ore line', len(G.nodes), 'nodes; draw node', dt)
