# #437 P1 (Alien): "at wave 3 the camera keeps shaking with drum sound" (i5 / adjustedfilm, 2026-11-02).
# Brutes arrive with wave 3. While a brute hits the gate it loops every 2.4 s: GateDamage (CX_85) -> camera shake CX_88
# (full within 25 m, felt up to 120 m) -> Explosion_Cue at pitch 0.38 (CX_89) + heavy metal hit (CX_90), both with NO
# attenuation (heard castle-wide) = the endless "drums". This makes the shake + booms a one-shot per brute:
#   CX_85.then -> GtIfShook (GateShook?) -- true  -> CX_91 (dust emitter; damage already applied, loop continues)
#                                      -- false -> Set GateShook = true -> CX_88 (shake) -> CX_89 -> CX_90 -> CX_91
# Output: build/FleshBrute_GateShookOnce_graph.txt (3 nodes) -> paste into BP_FleshBrute's EventGraph, then
# fix_brute437_ue.py wires it (and trims the shake radii / boom volumes).
#   "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" -I gen_brute437.py
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)

G = Graph(); b = B(G, 'g437')
get = b.get('GateShook', bo('GateShook'), 0, 120)
branch(G, 'GtIfShook', 220, 0); b.wire(get, 'GtIfShook', 'Condition')
varset(G, 'GtSetShook', None, 'GateShook', None, bo('GateShook', default='true'), 480, 120, self_ctx=True)
G.link('GtIfShook', 'else', 'GtSetShook', 'execute')
open(os.path.join(OUT, 'FleshBrute_GateShookOnce_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('nodes %d, links %d' % (len(G.nodes), len(G.links)))
