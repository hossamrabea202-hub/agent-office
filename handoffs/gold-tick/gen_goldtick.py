# Gold ticks up (TGA1's spec, chat 487 + 541; i5 / adjustedfilm, 2026-11-02). Generates:
#   build/BPC_GoldTick_graph.txt        EventGraph of the NEW component BPC_GoldTick (added to BP_SkillTreeHUD)
#   build/SkillTreeHUD_GoldTickHook_graph.txt   2 nodes for BP_SkillTreeHUD: Self -> GetComponentByClass(BPC_GoldTick) -> ShownInt
# BPC_GoldTick: BeginPlay  Shown = ShownInt = owner.Gold (no count-up from 0 at start)
#               Tick       Shown = FInterpTo(Shown, owner.Gold, DeltaSeconds, 8); ShownInt = Round(Shown)
# The digits read ShownInt instead of Gold (rewire_goldtick_ue.py: CX_1883.InInt only). Shop money checks keep reading
# the real Gold (CX_778 and the other reads are untouched). Tick even when paused: set by setup_goldtick_ue.py.
#   "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" -I gen_goldtick.py
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)

COMP = CLS('ActorComponent')
P_ST = '/Game/CastleDefender/Gameplay/Castle/BP_SkillTreeHUD'
P_GT = '/Game/CastleDefender/Gameplay/Castle/BPC_GoldTick'
STHUD, GOLDT = BPC(P_ST, 'BP_SkillTreeHUD'), BPC(P_GT, 'BPC_GoldTick')
SPEED = '8.0'


def comp_event(G, nm, member, extra, x, y):
    ref = '(MemberParent=%s,MemberName="%s")' % (COMP, member)
    G.node(nm, 'K2Node_Event', ['EventReference=' + ref, 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': ref}, ex('then', True)] + extra, x, y)
    return nm


G = Graph(); b = B(G, 'gt')
# ---- BeginPlay: Shown = ShownInt = Gold
bp = comp_event(G, 'GtBeginPlay', 'ReceiveBeginPlay', [], 0, 0)
own1 = b.call_self('GetOwner', [ob('ReturnValue', ACT, out=True)], 0, 160, COMP, pure=True, const=True, tag='Owner')
c1 = 'GtCastHud1'; cast(G, c1, STHUD, 'AsBP Skill Tree HUD', 260, 0)
G.link(bp, 'then', c1, 'execute'); G.link(own1, 'ReturnValue', c1, 'Object')
gold1 = b.getm('Gold', STHUD, it('Gold'), (c1, 'AsBP Skill Tree HUD'), 560, 160)
s1 = b.set('Shown', D('Shown'), b.i2d(gold1, 760, 200), 960, 0)
s2 = b.set('ShownInt', it('ShownInt'), gold1, 1200, 0)
G.link(c1, 'then', s1, 'execute'); G.link(s1, 'then', s2, 'execute')

# ---- Tick: Shown = FInterpTo(Shown, Gold, Delta, 8); ShownInt = Round(Shown)
tk = comp_event(G, 'GtTick', 'ReceiveTick', [fl('DeltaSeconds', out=True)], 0, 500)
own2 = b.call_self('GetOwner', [ob('ReturnValue', ACT, out=True)], 0, 660, COMP, pure=True, const=True, tag='Owner')
c2 = 'GtCastHud2'; cast(G, c2, STHUD, 'AsBP Skill Tree HUD', 260, 500)
G.link(tk, 'then', c2, 'execute'); G.link(own2, 'ReturnValue', c2, 'Object')
gold2 = b.getm('Gold', STHUD, it('Gold'), (c2, 'AsBP Skill Tree HUD'), 560, 660)
cur = b.get('Shown', D('Shown'), 560, 760)
interp = b.math('FInterpTo', [(D('Current', default='0.0'), cur), (D('Target', default='0.0'), b.i2d(gold2, 760, 700)),
                              (D('DeltaTime', default='0.0'), (tk, 'DeltaSeconds')), (D('InterpSpeed', default=SPEED), None)],
                D('ReturnValue', out=True), 980, 700)
s3 = b.set('Shown', D('Shown'), interp, 1220, 500)
rnd = b.math('Round', [(D('A', default='0.0'), (s3, 'Output_Get'))], it('ReturnValue', out=True), 1420, 660)
s4 = b.set('ShownInt', it('ShownInt'), rnd, 1640, 500)
G.link(c2, 'then', s3, 'execute'); G.link(s3, 'then', s4, 'execute')
open(os.path.join(OUT, 'BPC_GoldTick_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_GoldTick: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---- BP_SkillTreeHUD hook: Self -> GetComponentByClass(BPC_GoldTick) -> ShownInt (rewire_goldtick_ue.py wires it to CX_1883.InInt)
H = Graph(); hb = B(H, 'gthk')
me = hb.self_node(0, 0)
fc = hb.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, P_GT + '.BPC_GoldTick_C'), ob('ReturnValue', GOLDT, out=True)],
             200, 0, target=me, pure=True, const=True, tag='FindGoldTick')
varget(H, 'GtHookShownInt', GOLDT, 'ShownInt', GOLDT, it('ShownInt'), x=480, y=0)
H.link(fc, 'ReturnValue', 'GtHookShownInt', 'self')
open(os.path.join(OUT, 'SkillTreeHUD_GoldTickHook_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(H.render())
print('hook: nodes %d (finder %s, value node GtHookShownInt)' % (len(H.nodes), fc))
