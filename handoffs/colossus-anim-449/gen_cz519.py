# #519 colossus wiring (adjustedfilm, 2026-11-06): paste + manifest for BP_ZombieWallBreaker (export #518, 11-06 09:24).
# What it changes (every node is pasted; the manifest rewires around the old ones, nothing in the live graph is edited):
#   1. GlobalAnimRateScale 0.2 -> 1.0 at BeginPlay (after BP_Rate) and after each smash (after SM_D2): the breaker used to
#      slow the human A_Walk to 0.2 to hide its 1.2 m steps; the new CZ_Walk_Colossus is authored at 30 cm/s per unit
#      of scale = exactly MaxWalkSpeed (30 x GiantScale), so it must play at rate 1.
#   2. Smash: SM_Rate.then -> PlayAnimation(CZ_Attack_Smash) -> SM_D1 (replaces SM_Anim's A_Attack; same 79 frames,
#      blow on frame 26, so the 0.45 rate, SM_D1 1.5 s and SM_D2 1.7 s keep their timing).
#   3. Giant death: the breaker overrides AnyDamage: Parent (BP_Zombie does the HP, gore, XP, the melt and plays a human
#      death montage) -> if Dead and not GiantDead: GiantDead = true, rate 1.0, PlayAnimation(CZ_Death_Colossus).
#      PlayAnimation puts the mesh back in single-node mode, so the giant death replaces the montage from frame 0.
#   New variable on BP_ZombieWallBreaker: GiantDead (Boolean, default false). See VARIABLES.md.
#   python gen_cz519.py   (Blender's python is fine)
import os, sys, re, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
ANIMA, DMGT = CLS('AnimationAsset'), CLS('DamageType')
ZA = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims_Colossus/'
asset = lambda n: '%s%s.%s' % (ZA, n, n)
EXPORT = os.path.join(HERE, '..', 'exports', 'adjustedfilm', 'colossus-anim', 'BP_ZombieWallBreaker.t3d.txt')
# the Dead variable lives on the C++ ZombieBase now: copy its reference from the live TK_Dead node
live = open(EXPORT, encoding='utf-8', errors='replace').read()
m = re.search(r'Begin Object Name="TK_Dead".*?VariableReference=\(MemberParent=("[^"]*"),MemberName="Dead"', live, re.S)
DEAD_PARENT = m.group(1) if m else None
print('Dead variable parent:', DEAD_PARENT)

G = Graph(); b = B(G, 'cz')
def mesh(x, y): return b.getm('Mesh', CHARC, ob('v', SKEL), b.self_node(x - 150, y), x, y)
def rate1(x, y): return b.setm('GlobalAnimRateScale', SKEL, fl('v', default='1.0'), None, mesh(x - 220, y + 180), x, y)
def play(anim, x, y, tag):
    return b.call(SKEL, 'PlayAnimation', [dict(ob('NewAnimToPlay', ANIMA), dobj=asset(anim)), bo('bLooping', default='false')], x, y,
                  target=mesh(x - 220, y + 180), tag=tag)

# 1. rate 1.0 at BeginPlay and after the smash
r_begin = rate1(0, 0)                      # BP_Rate.then -> r_begin -> BP_HP
r_after = rate1(0, 500)                    # SM_D2.then -> r_after -> SM_Walk
# 2. the smash clip
smash = play('CZ_Attack_Smash', 0, 1000, 'Smash')      # SM_Rate.then -> smash -> SM_D1
# 3. the giant death
ev = 'czAnyDamage'
G.node(ev, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveAnyDamage")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveAnyDamage")' % ACT}, ex('then', True),
        fl('Damage', out=True, default='0.0'), ob('DamageType', DMGT, out=True), ob('InstigatedBy', CTRL, out=True), ob('DamageCauser', ACT, out=True)], 0, 1600)
par = 'czParentDamage'
G.node(par, 'K2Node_CallParentFunction', ['FunctionReference=(MemberParent=%s,MemberName="ReceiveAnyDamage")' % ZOMBIE],
       [ex(), ex('then', True), selfpin(ZOMBIE, hidden=True), fl('Damage', default='0.0'), ob('DamageType', DMGT), ob('InstigatedBy', CTRL), ob('DamageCauser', ACT)], 350, 1600)
for p in ('Damage', 'DamageType', 'InstigatedBy', 'DamageCauser'): G.link(ev, p, par, p)
G.link(ev, 'then', par, 'execute')
if DEAD_PARENT: dead = b.getm('Dead', DEAD_PARENT, BOOL, b.self_node(600, 1950), 800, 1900)
else: dead = b.get('Dead', BOOL, 800, 1900)
giant = b.get('GiantDead', BOOL, 800, 2050)
cond = b.b2('BooleanAND', dead, b.bnot(giant, 1000, 2050), 1200, 1950)
ifdead = b.branch(cond, 1400, 1600, 'IfGiantDies')
G.link(par, 'then', ifdead, 'execute')
mark = b.set('GiantDead', bo('v', default='true'), None, 1700, 1600)
r_dead = rate1(2000, 1600)
death = play('CZ_Death_Colossus', 2350, 1600, 'GiantDeath')
b.chain(ifdead, mark, r_dead, death)

name = 'BP_ZombieWallBreaker_CZ519_graph.txt'
open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print(name, len(G.nodes), 'nodes', len(G.links), 'links')
man = {'blueprint': 'BP_ZombieWallBreaker', 'pastes': [name], 'rewires': [
    {'from': 'BP_Rate.then', 'to': '%s.execute' % r_begin, 'replace': True, 'note': 'BeginPlay: after the old rate 0.2 set, set it to 1.0 (was -> BP_HP)'},
    {'from': '%s.then' % r_begin, 'to': 'BP_HP.execute', 'note': 'then carry on with MaxHP'},
    {'from': 'SM_D2.then', 'to': '%s.execute' % r_after, 'replace': True, 'note': 'after the smash: rate 1.0 (was -> SM_Rate2 = 0.2)'},
    {'from': '%s.then' % r_after, 'to': 'SM_Walk.execute', 'note': 'then back to the walk'},
    {'from': 'SM_Rate.then', 'to': '%s.execute' % smash, 'replace': True, 'note': 'smash plays CZ_Attack_Smash (was SM_Anim = A_Attack)'},
    {'from': '%s.then' % smash, 'to': 'SM_D1.execute', 'note': 'then the old damage delay'},
]}
json.dump(man, open(os.path.join(HERE, 'manifest_cz519.json'), 'w'), indent=1)
print('manifest_cz519.json', len(man['rewires']), 'rewires; nodes', r_begin, r_after, smash, ifdead)
