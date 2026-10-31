# #349 fix (adjustedfilm, 2026-10-31): UE 5.3 python can't set a component template's parent socket, so the miner's gear sat
# at the Body root. This BeginPlay paste for BP_MineWorker snaps Pick -> hand_r, Helmet -> head (+9 cm), Satchel -> spine_03,
# and the Candle light onto the helmet.   "<blender python>" -I gen_workergear.py -> BP_MineWorker_Gear_graph.txt
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
G = Graph(); b = bpkit.B(G, 'mw'); g = b.get
b.override('mwBegin', 'ReceiveBeginPlay', 0, 0)
EN = lambda n, d: {'name': n, 'cat': 'byte', 'obj': ENUM('EAttachmentRule'), 'default': d}
prev, x = ('mwBegin', 'then'), 300
for comp, parent, sock, loc in (('MinerPick', 'Body', 'hand_r', None), ('MinerHelmet', 'Body', 'head', '0, 0, 9'),
                                ('MinerSatchel', 'Body', 'spine_03', None), ('Candle', 'MinerHelmet', 'None', '0, -12, 8')):
    at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName', sock), EN('LocationRule', 'SnapToTarget'), EN('RotationRule', 'SnapToTarget'),
                                                EN('ScaleRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')],
                x, 0, target=g(comp, ob('v', SCENE), x - 150, 250), tag='Attach' + comp)
    b.wire(g(parent, ob('v', SCENE), x - 150, 350), at, 'Parent'); G.link(prev[0], prev[1], at, 'execute'); prev = (at, 'then'); x += 350
    if loc:
        rl = b.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation', default=loc), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')],
                    x, 0, target=g(comp, ob('v', SCENE), x - 150, 250), tag='Offset' + comp)
        G.link(prev[0], prev[1], rl, 'execute'); prev = (rl, 'then'); x += 350
open(os.path.join(HERE, 'BP_MineWorker_Gear_graph.txt'), 'w', newline='\r\n').write(G.render())
print('nodes %d links %d' % (len(G.nodes), len(G.links)))
