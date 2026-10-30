# #216 (checkking, 2026-10-30 night): zoomed aim can shoot backwards (at the gate behind the hero).
# Fix: when a shot fires, turn the hero to the camera's yaw first, so the crossbow points where the player aims and the
# bolt (spawned from the muzzle, CX_137/CX_138, evaluated after this) always leaves from the front.
#   SetNextFire.then (from #214) -> FaceAim: hero.K2_SetActorRotation((0, ControlRotation.Yaw, 0)) -> CX_123
# Apply AFTER #214 (it hooks onto #214's SetNextFire node). python gen216.py -> Xbow_FaceAim_graph.txt (manifest_crossbow_216.json)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
HERO = BPC('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter', 'BP_ThirdPersonCharacter')

G = Graph(); b = bpkit.B(G, 'fa')
cr = b.call(PAWN, 'GetControlRotation', [st('ReturnValue', ROT, out=True)], 0, 200, pure=True, const=True, tag='CtrlRot')
mathfn(G, 'FaceBreak', 'BreakRotator', [st('InRot', ROT), D('Roll', out=True, default='0.0'), D('Pitch', out=True, default='0.0'), D('Yaw', out=True, default='0.0')], 250, 200)
G.link(cr, 'ReturnValue', 'FaceBreak', 'InRot')
mathfn(G, 'FaceMake', 'MakeRotator', [D('Roll', default='0.0'), D('Pitch', default='0.0'), D('Yaw', default='0.0'), st('ReturnValue', ROT, out=True)], 500, 200)
G.link('FaceBreak', 'Yaw', 'FaceMake', 'Yaw')
G.node('FaceAim', 'K2Node_CallFunction', ['FunctionReference=(MemberParent=%s,MemberName="K2_SetActorRotation")' % ACT],
       [ex(), ex('then', True), selfpin(ACT), st('NewRotation', ROT, default='0, 0, 0'), bo('bTeleportPhysics', default='false'),
        bo('ReturnValue', out=True, default='false')], 750, 0)
G.link('FaceMake', 'ReturnValue', 'FaceAim', 'NewRotation')
# the hero: a pass-through cast-free reroute so the manifest can wire CX_106's hero output to both pins
G.node('FaceHeroIn', 'K2Node_Knot', [], [dict(ob('InputPin', HERO)), dict(ob('OutputPin', HERO, out=True))], 600, 350)
G.link('FaceHeroIn', 'OutputPin', 'FaceAim', 'self'); G.link('FaceHeroIn', 'OutputPin', cr, 'self')
open(os.path.join(HERE, 'Xbow_FaceAim_graph.txt'), 'w', newline='\r\n').write(G.render())
print('face aim: nodes', len(G.nodes), 'links', len(G.links))
