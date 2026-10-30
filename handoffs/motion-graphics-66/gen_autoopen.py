# Motion graphics #139 / #140 (checkking, 2026-10-30): "the HUD opens out of it". Two 4-node pastes that OR the hero's
# BPC_MotionFX one-frame signal into the key that opens the panel:
#   SkillTree_AutoOpen_graph.txt  BP_SkillTreeHUD: T key (CX_23) OR MotionFX.BookOpenNow -> CX_112.A  (manifest_skilltreehud.json)
#   Queue_AutoOpen_graph.txt      BP_QueueHUD:     I key (CX_67) OR MotionFX.BagOpenNow  -> CX_73.A   (manifest_queuehud.json)
# Built on handoffs/exports/master/2026-10-30b (BP_SkillTreeHUD.T3D, BP_QueueHUD.T3D).
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
FXC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX', 'BPC_MotionFX')

def build(var, out, prefix):
    G = Graph(); b = bpkit.B(G, prefix)
    pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 0, pure=True, tag='Pawn')
    gc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX.BPC_MotionFX_C'),
                ob('ReturnValue', FXC, out=True)], 250, 0, target=(pp, 'ReturnValue'), pure=True, const=True, tag='FX')
    v = b.getm(var, FXC, bo('v', default='false'), (gc, 'ReturnValue'), 500, 0)
    mathfn(G, 'AutoOpenOR', 'BooleanOR', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True, default='false')], 750, 0)
    G.link(v[0], v[1], 'AutoOpenOR', 'B')
    open(os.path.join(HERE, out), 'w', newline='\r\n').write(G.render())
    print(out, 'nodes', len(G.nodes))

build('BookOpenNow', 'SkillTree_AutoOpen_graph.txt', 'ao')
build('BagOpenNow', 'Queue_AutoOpen_graph.txt', 'aq')
