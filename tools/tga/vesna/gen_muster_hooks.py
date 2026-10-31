# The Muster (#359): the small pastes around BPC_Muster.
#   python gen_muster_hooks.py -> handoffs/barracks-hud-359/build/
#     addon_<BP>_graph.txt + manifest_<BP>.json   one custom event per buy ("HudBuy..."), wired into the system's own
#                                                 branch right after its key check, so the system pays, saves and notifies
#                                                 exactly as with its key; the once-per-visit "[J] / [F] / [M]" notices are
#                                                 skipped (owner: remove them once the HUD works), the keys still work.
#     ArmoryHUD_MusterHook_graph.txt + manifest_armoryhud_muster.json   DrawMuster before the #66 reveal (ObsHookSeq.then_2)
#     BarracksHUD_MusterGate_graph.txt + manifest_barrackshud.json      the old recruit screen is skipped while Muster.Near
# The node names on the right of the rewires come from the generated graphs in the repo; applyall matches those graphs
# against the fresh export by PinIds, so they resolve to the live names.
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(REPO, 'handoffs', 'barracks-hud-359', 'build')
COMP = CLS('ActorComponent'); HUDC = CLS('HUD')
MUC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Muster', 'BPC_Muster')
INT, BOOL = it('v', default='0'), bo('v', default='false')

def write(G, name):
    open(os.path.join(OUT, name), 'w', newline='\r\n', encoding='utf-8').write(G.render()); return name

ADDONS = [  # blueprint, original generated graph (repo path, from build/), [(event, entry node)], [(offer branch, set-near node)]
    ('BPC_CastleUpgrades', '../../castle-upgrades-224/BPC_CastleUpgrades_graph.txt', [('HudBuyWalls', 'cuIfMaxWalls66'), ('HudBuyTowers', 'cuIfMaxTowers135')], [('cuIfOffer36', 'cuSetNearShop54')]),
    ('BPC_Flares', '../../flares-277/BPC_Flares_graph.txt', [('HudBuy', 'fxAsBPZombieHUD36')], [('fxIfShopPrompt70', 'fxSetNearShop75')]),
    ('BPC_Medics', '../../medics-185/BPC_Medics_graph.txt', [('HudBuy', 'mdIfFull45')], [('mdIfOffer19', 'mdSetNearShop32')]),
    ('BP_CannonOrder', '../../deploy-cannon-230/BP_CannonOrder_graph.txt', [('HudOrder', 'coAsZHud15')], []),
]
for bp, orig, evs, offers in ADDONS:
    G = Graph(); b = bpkit.B(G, 'mu')
    for k, (ev, _) in enumerate(evs): b.event(ev, [], 0, k * 300)
    f = write(G, 'addon_%s_graph.txt' % bp)
    man = {'blueprint': bp, '_note': 'Muster #359 add-on: %s' % ', '.join(e for e, _ in evs),
           'pastes': [{'file': orig}, {'file': f, 'offset': [0, -1500]}],
           'rewires': [{'from': '%s.then' % ev, 'to': '%s.execute' % node, 'note': 'enters right after the key check'} for ev, node in evs] +
                      [{'from': '%s.then' % br, 'to': '%s.execute' % sn, 'replace': True, 'note': 'skip the once-per-visit key notice (owner)'} for br, sn in offers]}
    json.dump(man, open(os.path.join(OUT, 'manifest_%s.json' % bp), 'w'), indent=1)

def muster_comp(b, x, y):
    pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], x, y, pure=True, tag='MuPawn')
    mc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_Muster.BPC_Muster_C'), ob('ReturnValue', MUC, out=True)],
                x + 250, y, target=(pp, 'ReturnValue'), pure=True, const=True, tag='MuComp')
    return (mc, 'ReturnValue')

# ---- BP_ArmoryHUD: MusterSeq at ObsHookSeq.then_2: then_0 DrawMuster, then_1 the #66 reveal (ohHookIfFX9) as before
G = Graph(); b = bpkit.B(G, 'mh')
sequence(G, 'MusterSeq', 2, 0, 0)
mc = muster_comp(b, 0, 300)
branch(G, 'MusterIfV', 300, 0); b.wire(b.valid(mc, 300, 200), 'MusterIfV', 'Condition'); G.link('MusterSeq', 'then_0', 'MusterIfV', 'execute')
me = b.self_node(500, 400)
callfn(G, 'MusterDraw', MUC, 'DrawMuster', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], x=600, y=0)
G.link(mc[0], mc[1], 'MusterDraw', 'self'); G.link(me[0], me[1], 'MusterDraw', 'Hud'); G.link('MusterIfV', 'then', 'MusterDraw', 'execute')
f = write(G, 'ArmoryHUD_MusterHook_graph.txt')
json.dump({'blueprint': 'BP_ArmoryHUD', '_note': 'after #380 (manifest_trade.json), which puts the #222/#66 hook in',
           'pastes': [{'file': '../../obsidian-set-v2/ArmoryHUD_ObsHook_graph.txt'}, {'file': f, 'offset': [-200, -3400]}],
           'rewires': [{'from': 'ObsHookSeq.then_2', 'to': 'MusterSeq.execute', 'replace': True, 'note': 'was -> ohHookIfFX9 (reveal)'},
                       {'from': 'MusterSeq.then_1', 'to': 'ohHookIfFX9.execute', 'note': 'the reveal still draws last, on top'},
                       {'from': 'HookSizeX.ReturnValue', 'to': 'MusterDraw.SizeX'}, {'from': 'HookSizeY.ReturnValue', 'to': 'MusterDraw.SizeY'}]},
          open(os.path.join(OUT, 'manifest_armoryhud_muster.json'), 'w'), indent=1)

# ---- BP_BarracksHUD: after the parent DrawHUD (CX_2) the old barracks draw (CX_3182 ...) runs only when not Muster.Near
G = Graph(); b = bpkit.B(G, 'mg')
mc = muster_comp(b, 0, 300)
branch(G, 'MusterGateIfV', 300, 0); b.wire(b.valid(mc, 300, 200), 'MusterGateIfV', 'Condition')
branch(G, 'MusterGateIfN', 600, 0); G.link('MusterGateIfV', 'then', 'MusterGateIfN', 'execute')
b.wire(b.getm('Near', MUC, BOOL, mc, 600, 200), 'MusterGateIfN', 'Condition')
f = write(G, 'BarracksHUD_MusterGate_graph.txt')
json.dump({'blueprint': 'BP_BarracksHUD', '_built_on': 'handoffs/exports/master/2026-10-30b/BP_BarracksHUD_EventGraph.txt (CX_2 = parent DrawHUD, CX_3182 = first node of the old barracks draw)',
           'pastes': [{'file': f, 'offset': [0, -1500]}],
           'rewires': [{'from': 'CX_2.then', 'to': 'MusterGateIfV.execute', 'replace': True, 'note': 'was -> CX_3182'},
                       {'from': 'MusterGateIfV.else', 'to': 'CX_3182.execute'}, {'from': 'MusterGateIfN.else', 'to': 'CX_3182.execute'}]},
          open(os.path.join(OUT, 'manifest_barrackshud.json'), 'w'), indent=1)
print('Muster hooks written:', sorted(n for n in os.listdir(OUT) if n.startswith(('addon_', 'manifest_', 'ArmoryHUD_', 'BarracksHUD_'))))
