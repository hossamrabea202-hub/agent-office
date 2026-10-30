# #182 Huge soldier in the castle: BP_ZombieRisen (the risen soldier, child of BP_Zombie) inherits BP_Zombie's BeginPlay,
# which rolls the giant / wall-breaker size (SetActorScale3D 3x and 1.35x, Mesh scale 3x) - so a risen soldier can come up
# three times tall inside the castle. Fix: right after the parent BeginPlay call in BP_ZombieRisen, force the actor and
# both meshes back to scale 1 (the #41 director then applies its own 1.2 for a risen commander, as before).
#   python gen182.py -> ZombieRisen_ScaleFix_graph.txt + manifest.json   (rewire: rZombieBeginPla1.then -> fix -> rSetHiddenInGam3)
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
G = Graph(); b = B(G, 'sf')
ONE = '1.000000,1.000000,1.000000'
self_ = b.self_node(0, 300)
a1 = b.call(ACT, 'SetActorScale3D', [V('NewScale3D', default=ONE)], 0, 0, target=self_, tag='ScaleOne')
mesh = b.get('Mesh', ob('v', SKEL), 300, 300)
a2 = b.call(SCENE, 'SetRelativeScale3D', [V('NewScale3D', default=ONE)], 350, 0, target=mesh, tag='MeshOne')
km = b.get('KnightMesh', ob('v', SKEL), 650, 300)
a3 = b.call(SCENE, 'SetRelativeScale3D', [V('NewScale3D', default=ONE)], 700, 0, target=km, tag='KnightOne')
b.chain(a1, a2, a3)
open(os.path.join(HERE, 'ZombieRisen_ScaleFix_graph.txt'), 'w', encoding='utf-8').write(G.render())
import json
json.dump({'blueprint': 'BP_ZombieRisen', 'pastes': ['ZombieRisen_ScaleFix_graph.txt'], 'rewires': [
  {'from': 'rZombieBeginPla1.then', 'to': a1 + '.execute', 'replace': True, 'note': 'was -> rSetHiddenInGam3'},
  {'from': a3 + '.then', 'to': 'rSetHiddenInGam3.execute'}]}, open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote', len(G.nodes), 'nodes', a1, a3)
