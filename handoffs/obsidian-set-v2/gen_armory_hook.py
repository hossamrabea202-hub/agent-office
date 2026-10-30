# Obsidian set v2 part 2 (checkking, 2026-10-30): the hook in BP_ArmoryHUD's EventGraph (Vesna's shop screen).
#   python gen_armory_hook.py  ->  ArmoryHUD_ObsHook_graph.txt  (6 nodes, merged by manifest_armoryhud.json)
# A two-pin Sequence goes between the parent DrawHUD call (CX_2) and the shop drawing (CX_26):
#   then_0 = the whole existing shop draw, unchanged;  then_1 = the hero's BPC_ObsidianSet.DrawArmoury(self, SizeX, SizeY),
# so the Obsidian panel draws after (on top of) the shop. Built on handoffs/exports/master/2026-10-30b/BP_ArmoryHUD_EventGraph.txt.
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

SETC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', 'BPC_ObsidianSet')
HUDC = CLS('HUD')
G = Graph(); b = bpkit.B(G, 'oh')

sequence(G, 'ObsHookSeq', 3, 0, 0)
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 250, pure=True, tag='HookPawn')
gc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet.BPC_ObsidianSet_C'),
            ob('ReturnValue', SETC, out=True)], 250, 250, target=(pp, 'ReturnValue'), pure=True, const=True, tag='HookSet')
ok = b.branch(b.valid((gc, 'ReturnValue'), 500, 250), 300, 0, tag='HookIf')
G.link('ObsHookSeq', 'then_1', ok, 'execute')
me = b.self_node(500, 400)
dr = b.call(SETC, 'DrawArmoury', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 700, 0, target=(gc, 'ReturnValue'), tag='HookDraw')
G.link(ok, 'then', dr, 'execute'); b.wire(me, dr, 'Hud')
# named pass-through for the two size ints, so the manifest can wire CX_1.SizeX / SizeY in
for p in ('SizeX', 'SizeY'):
    n = 'HookSize' + p[-1]
    mathfn(G, n, 'Add_IntInt', [it('A', default='0'), it('B', default='0'), it('ReturnValue', out=True)], 500, 550 if p == 'SizeX' else 650)
    G.link(n, 'ReturnValue', dr, p)
# then_2 (motion graphics #66/#139/#140, 2026-10-30): the hero's BPC_MotionFX.DrawReveal(self, SizeX, SizeY), last = on top
FXC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX', 'BPC_MotionFX')
gf = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX.BPC_MotionFX_C'),
            ob('ReturnValue', FXC, out=True)], 250, 800, target=(pp, 'ReturnValue'), pure=True, const=True, tag='HookFX')
okf = b.branch(b.valid((gf, 'ReturnValue'), 500, 800), 300, 700, tag='HookIfFX')
G.link('ObsHookSeq', 'then_2', okf, 'execute')
drf = b.call(FXC, 'DrawReveal', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 700, 700, target=(gf, 'ReturnValue'), tag='HookReveal')
G.link(okf, 'then', drf, 'execute'); b.wire(me, drf, 'Hud')
G.link('HookSizeX', 'ReturnValue', drf, 'SizeX'); G.link('HookSizeY', 'ReturnValue', drf, 'SizeY')
open(os.path.join(HERE, 'ArmoryHUD_ObsHook_graph.txt'), 'w', newline='\r\n').write(G.render())
print('ArmoryHUD hook: nodes %d, links %d' % (len(G.nodes), len(G.links)))
