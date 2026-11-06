# #519 colossus paste 2 (adjustedfilm, 2026-11-06): roar at spawn + loom idle while stuck. Built ON TOP of paste 1
# (manifest_cz519.json): merge this manifest on the graph that already has #522 in it (or paste merged_cz519b.t3d).
#   1. BeginPlay: BP_XP.then -> PlayAnimation(CZ_Roar) -> Delay 3.0 -> BP_Walk (the old walk) -> BP_Tmr: the giant roars
#      once before it starts walking (the BreakerThink timer starts after the roar).
#   2. BreakerThink, the stuck watchdog (#317): when StuckTicks becomes 1 (first slow tick) -> PlayAnimation(CZ_Idle_Loom,
#      loop); when it moves again (the reset branch) and StuckTicks was > 0 -> PlayAnimation(A_Walk, loop).
#   python gen_cz519b.py
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
ANIMA = CLS('AnimationAsset')
ZA = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims_Colossus/'; ZB = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims/'
asset = lambda root, n: '%s%s.%s' % (root, n, n)
G = Graph(); b = B(G, 'cr')
def mesh(x, y): return b.getm('Mesh', CHARC, ob('v', SKEL), b.self_node(x - 150, y), x, y)
def play(root, anim, loop, x, y, tag):
    return b.call(SKEL, 'PlayAnimation', [dict(ob('NewAnimToPlay', ANIMA), dobj=asset(root, anim)), bo('bLooping', default='true' if loop else 'false')], x, y,
                  target=mesh(x - 220, y + 180), tag=tag)
# 1. roar at spawn
roar = play(ZA, 'CZ_Roar', False, 0, 0, 'Roar')
wait = b.lib(KSL, 'Delay', [WC(), fl('Duration', default='3.0'), {'name': 'LatentInfo', 'cat': 'struct', 'obj': '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.LatentActionInfo\'"', 'hidden': True}], 350, 0, tag='RoarWait')
G.link(roar, 'then', wait, 'execute')
# 2. loom idle while stuck
one = b.icmp('EqualEqual_IntInt', b.get('StuckTicks', it('v'), 0, 700), None, 250, 700, db='1')
ifone = b.branch(one, 450, 500, 'IfJustStuck')
loom = play(ZA, 'CZ_Idle_Loom', True, 750, 500, 'Loom')
G.link(ifone, 'then', loom, 'execute')
was = b.icmp('Greater_IntInt', b.get('StuckTicks', it('v'), 0, 1300), None, 250, 1300, db='0')
ifwas = b.branch(was, 450, 1100, 'IfWasStuck')
walk = play(ZB, 'A_Walk', True, 750, 1100, 'WalkAgain')
G.link(ifwas, 'then', walk, 'execute')
name = 'BP_ZombieWallBreaker_CZ519b_graph.txt'
open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print(name, len(G.nodes), 'nodes')
man = {'blueprint': 'BP_ZombieWallBreaker', 'pastes': [name], 'rewires': [
    {'from': 'BP_XP.then', 'to': '%s.execute' % roar, 'replace': True, 'note': 'spawn: roar first (was -> BP_Walk)'},
    {'from': '%s.then' % wait, 'to': 'BP_Walk.execute', 'note': 'after the roar: the old walk + timer'},
    {'from': 'czSetStuckTicks9.then', 'to': '%s.execute' % ifone, 'replace': True, 'note': 'stuck watchdog: after StuckTicks += 1 (was -> czIfStuck12)'},
    {'from': '%s.then' % loom, 'to': 'czIfStuck12.execute', 'note': 'just stuck: loom, then the old check'},
    {'from': '%s.else' % ifone, 'to': 'czIfStuck12.execute', 'note': 'already looming: the old check'},
    {'from': 'czIfSlow6.else', 'to': '%s.execute' % ifwas, 'replace': True, 'note': 'moving: was it looming? (was -> czSetStuckTicks24)'},
    {'from': '%s.then' % walk, 'to': 'czSetStuckTicks24.execute', 'note': 'back to the walk, then the old reset'},
    {'from': '%s.else' % ifwas, 'to': 'czSetStuckTicks24.execute', 'note': 'was walking: the old reset'},
]}
json.dump(man, open(os.path.join(HERE, 'manifest_cz519b.json'), 'w'), indent=1)
print('manifest_cz519b.json', len(man['rewires']), 'rewires', roar, wait, ifone, loom, ifwas, walk)
