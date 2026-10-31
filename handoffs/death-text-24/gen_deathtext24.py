# #24 "Upon Death" (owner 2026-10-27): "text if died by tanticle attack you fallen, if died by zombie : you been bitten or
# something like that". adjustedfilm, 2026-10-31. Built on the Master's 2026-10-30b exports.
#   "<blender python>" -I gen_deathtext24.py -> Hero_DeathCause_graph.txt + manifest_hero_deathcause.json,
#                                               HUD_DeathText_graph.txt + manifest_hud_deathtext.json, DeathText_BPVar.txt
# Hero (BP_ThirdPersonCharacter): at the start of ReceiveAnyDamage, if the causer is valid: DeathText =
#   "YOU WERE BITTEN" when the causer's name has Zombie / Brute / Horse / Wasp / Risen (a zombie got you),
#   else "YOU HAVE FALLEN" (tentacle strikes, the realm, falls, anything else). Then the old chain goes on unchanged.
# HUD (BP_ZombieHUD): the two death titles ("YOU HAVE FALLEN" at IW2772 + its centring GetTextSize IW2767, and the older
# "YOU DIED" at H2153) draw the hero's DeathText. One cast to the hero in front of each draw (one cast per consumer).
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
HERO = BPC(P_HERO, 'BP_ThirdPersonCharacter')


def check_write(G, fname):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('%s: bad %s dup %s' % (fname, bad[:5], [n for n in names if names.count(n) > 1][:5]))
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (fname, len(G.nodes), len(G.links)))


# ---------------------------------------------------------------- hero
G = Graph(); b = B(G, 'dt')
din = b.seq('DeathIn', 1, 13072, 26400)
cz = b.lib(KSL, 'GetObjectName', [ob('Object', OBJ), S('ReturnValue', out=True)], 13300, 26700, pure=True, tag='CauserName')
has = lambda w, x, y: b.lib(KSTR, 'Contains', [S('SearchIn'), S('Substring', default=w), bo('bUseCase', default='false'), bo('bSearchFromEnd', default='false'),
                                               bo('ReturnValue', out=True, default='false')], x, y, pure=True, tag='Has' + w)
hs = [has(w, 13550, 26700 + 120 * i) for i, w in enumerate(('Zombie', 'Brute', 'Horse', 'Wasp', 'Risen'))]
for h in hs: b.wire((cz, 'ReturnValue'), h, 'SearchIn')
o = (hs[0], 'ReturnValue')
for i, h in enumerate(hs[1:]): o = b.b2('BooleanOR', o, (h, 'ReturnValue'), 13800 + 150 * i, 26700 + 120 * i)
txt = b.selstr(None, None, o, 14500, 26700, da='YOU WERE BITTEN', db='YOU HAVE FALLEN')
bv = b.branch(None, 13300, 26400, tag='IfCauser')          # Condition <- IsValid(DamageCauser), wired by the manifest
vl = b.lib(KSL, 'IsValid', [ob('Object', OBJ), bo('ReturnValue', out=True, default='false')], 13100, 26550, pure=True, tag='CauserValid')
G.link(vl, 'ReturnValue', bv, 'Condition')
sdt = b.set('DeathText', S('v'), txt, 14700, 26400)
dout = b.seq('DeathOut', 1, 15000, 26400)
G.link(din, 'then_0', bv, 'execute'); G.link(bv, 'then', sdt, 'execute'); G.link(sdt, 'then', dout, 'execute'); G.link(bv, 'else', dout, 'execute')
check_write(G, 'Hero_DeathCause_graph.txt')
json.dump({'blueprint': 'BP_ThirdPersonCharacter', 'note': '#24: remember what hit the hero, for the death screen',
           'pastes': [{'file': 'Hero_DeathCause_graph.txt'}],
           'rewires': [{'from': 'K2Node_Event_PH0.then', 'to': 'DeathIn.execute', 'replace': True, 'note': 'was -> K2Node_CallFunction_15'},
                       {'from': 'DeathOut.then_0', 'to': 'K2Node_CallFunction_15.execute'},
                       {'from': 'K2Node_Event_PH0.DamageCauser', 'to': vl + '.Object'},
                       {'from': 'K2Node_Event_PH0.DamageCauser', 'to': cz + '.Object'}]},
          open(os.path.join(HERE, 'manifest_hero_deathcause.json'), 'w'), indent=1)

# ---------------------------------------------------------------- HUD
G = Graph(); b = B(G, 'hd')
casts = []
for tag, x, y in (('Fallen', 29300, 137100), ('Died', 4100, 81900)):
    pc = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], x - 250, y + 200, pure=True, tag='PC' + tag)
    cn = 'Cast' + tag; cast(G, cn, HERO, 'AsHero', x, y); b.wire((pc, 'ReturnValue'), cn, 'Object')
    gt = b.getm('DeathText', HERO, S('v'), (cn, 'AsHero'), x + 300, y + 250)
    casts.append((cn, gt))
check_write(G, 'HUD_DeathText_graph.txt')
(cf, gf), (cd, gd) = casts
json.dump({'blueprint': 'BP_ZombieHUD', 'note': '#24: the death titles show the hero DeathText',
           'pastes': [{'file': 'HUD_DeathText_graph.txt'}],
           'rewires': [{'from': 'K2Node_IfThenElse_IW2762.then', 'to': cf + '.execute', 'replace': True, 'note': 'was -> IW2772 (YOU HAVE FALLEN)'},
                       {'from': cf + '.then', 'to': 'K2Node_CallFunction_IW2772.execute'},
                       {'from': cf + '.CastFailed', 'to': 'K2Node_CallFunction_IW2772.execute'},
                       {'from': gf[0] + '.DeathText', 'to': 'K2Node_CallFunction_IW2772.Text'},
                       {'from': gf[0] + '.DeathText', 'to': 'K2Node_CallFunction_IW2767.Text'},
                       {'from': 'K2Node_IfThenElse_H2152.then', 'to': cd + '.execute', 'replace': True, 'note': 'was -> H2153 (YOU DIED)'},
                       {'from': cd + '.then', 'to': 'K2Node_CallFunction_H2153.execute'},
                       {'from': cd + '.CastFailed', 'to': 'K2Node_CallFunction_H2153.execute'},
                       {'from': gd[0] + '.DeathText', 'to': 'K2Node_CallFunction_H2153.Text'}]},
          open(os.path.join(HERE, 'manifest_hud_deathtext.json'), 'w'), indent=1)
bpv = 'BPVar(VarName="DeathText",VarGuid=%s,VarType=(PinCategory="string"),FriendlyName="DeathText",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="YOU HAVE FALLEN")' % uuid.uuid5(uuid.NAMESPACE_URL, 'death24/DeathText').hex.upper()
open(os.path.join(HERE, 'DeathText_BPVar.txt'), 'w', newline='\r\n').write('# #24 BP_ThirdPersonCharacter - paste on the VARIABLES header, then Compile\n' + bpv + '\n')
