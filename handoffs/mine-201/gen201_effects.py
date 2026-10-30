# #201 part 3: the forge levels change the fight. Pure data inserts (no exec changes) read from BP_ZombieHUD:
#   BP_SoldierSword: sword damage x (1 + 0.2*ForgeSword)   [CX_556 -> CX_297.BaseDamage]
#                    damage taken / (1 + 0.3*ForgePlate)   [CX_601.Damage -> CX_612.B]   (= soldier HP +30 %)
#   BP_Zombie:       bolt damage x (1 + ForgeBolt*(0.25, or 1.0 when this zombie is a risen soldier)) when the causer is a BP_SoldierBolt
#                    [ZB60.Damage -> ZB64.B]
#                    gate damage per hit / (1 + 0.5*ForgeGate)   [CX_83 -> CX_84.A: GateDamage + (new - GateDamage)/k]
#   python gen201_effects.py -> SoldierSword_Forge_graph.txt + manifest_soldier.json, Zombie_Forge_graph.txt + manifest_zombie.json
import os, sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
P_HUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
P_BOLT = '/Game/CastleDefender/Characters/Knight/BP_SoldierBolt'
HUDC, BOLTC, RISENC = BPC(P_HUD, 'BP_ZombieHUD'), BPC(P_BOLT, 'BP_SoldierBolt'), BPC(P_RISEN, 'BP_ZombieRisen')
HUDCLS = CLS('HUD')


def hud(b, x, y):
    """pure chain: player 0 -> HUD -> cast BP_ZombieHUD. Returns the cast output handle."""
    pc = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC')
    h = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x + 250, y, target=(pc, 'ReturnValue'), pure=True, const=True, tag='HUD')
    cs = b.name('AsZombieHUD'); cast(b.G, cs, HUDC, 'AsBP Zombie HUD', x + 500, y, pure=True); b.wire((h, 'ReturnValue'), cs, 'Object')
    return (cs, 'AsBP Zombie HUD')


def factor(b, var, per, zh, x, y):
    """1 + per * HUD.var  (double)"""
    lv = b.i2d(b.getm(var, HUDC, INT, zh, x, y), x + 250, y)
    return b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', lv, None, x + 500, y, db=per), None, x + 750, y, db='1.0')


# ------------------------------------------------ BP_SoldierSword ------------------------------------------------
G = Graph(); b = B(G, 'fs')
zh = hud(b, 0, 300)
ks = factor(b, 'ForgeSword', '0.2', zh, 900, 0)
sword = b.d2('Multiply_DoubleDouble', None, ks, 1800, 0, da='1.0')           # A <- CX_556.ReturnValue (rewire); out -> CX_297.BaseDamage
kp = factor(b, 'ForgePlate', '0.3', zh, 900, 400)
plate = b.d2('Divide_DoubleDouble', None, kp, 1800, 400, da='0.0', db='1.0')   # A <- CX_601.Damage (rewire); out -> CX_612.B
open(os.path.join(HERE, 'SoldierSword_Forge_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_SoldierSword', 'pastes': ['SoldierSword_Forge_graph.txt'], 'rewires': [
  {'from': 'CX_556.ReturnValue', 'to': sword[0] + '.A', 'note': 'the sword damage value'},
  {'from': sword[0] + '.ReturnValue', 'to': 'CX_297.BaseDamage', 'replace': True, 'note': 'x (1 + 0.2 ForgeSword) into ApplyDamage'},
  {'from': 'CX_601.Damage', 'to': plate[0] + '.A', 'note': 'incoming damage'},
  {'from': plate[0] + '.ReturnValue', 'to': 'CX_612.B', 'replace': True, 'note': '/ (1 + 0.3 ForgePlate) before the HP subtract'}]},
  open(os.path.join(HERE, 'manifest_soldier.json'), 'w'), indent=1)
print('SoldierSword', len(G.nodes), 'nodes', sword[0], plate[0])

# ------------------------------------------------ BP_Zombie ------------------------------------------------
G = Graph(); b = B(G, 'fz')
zh = hud(b, 0, 300)
# bolt: k = 1 + ForgeBolt * (risen ? 1.0 : 0.25), used only when the causer is a soldier bolt
lv = b.i2d(b.getm('ForgeBolt', HUDC, INT, zh, 900, 0), 1150, 0)
me = b.self_node(900, 250)
rc = b.name('AsRisen'); cast(G, rc, RISENC, 'AsBP Zombie Risen', 1150, 250, pure=True); b.wire(me, rc, 'Object')
risen = b.valid((rc, 'AsBP Zombie Risen'), 1450, 250)
per = b.self_(None, None, risen, 1450, 100, da='1.0', db='0.25')
k = b.d2('Add_DoubleDouble', b.d2('Multiply_DoubleDouble', lv, per, 1700, 0), None, 1950, 0, db='1.0')
bc = b.name('AsBolt'); cast(G, bc, BOLTC, 'AsBP Soldier Bolt', 1450, 500, pure=True)          # Object <- ZB60.DamageCauser (rewire)
isbolt = b.valid((bc, 'AsBP Soldier Bolt'), 1750, 500)
k2 = b.self_(k, None, isbolt, 2200, 100, db='1.0')
bolt = b.d2('Multiply_DoubleDouble', None, k2, 2500, 0, da='0.0')                              # A <- ZB60.Damage; out -> ZB64.B
# gate: GateDamage + (CX_83 - GateDamage) / (1 + 0.5 ForgeGate)  -> CX_84.A
kg = factor(b, 'ForgeGate', '0.5', zh, 900, 900)
diff = b.d2('Subtract_DoubleDouble', None, None, 1800, 1100)                                   # A <- CX_83.ReturnValue, B <- CX_82.GateDamage
gate = b.d2('Add_DoubleDouble', None, b.d2('Divide_DoubleDouble', diff, kg, 2100, 1000, db='1.0'), 2400, 900)   # A <- CX_82.GateDamage
open(os.path.join(HERE, 'Zombie_Forge_graph.txt'), 'w', encoding='utf-8').write(G.render())
json.dump({'blueprint': 'BP_Zombie', 'pastes': ['Zombie_Forge_graph.txt'], 'rewires': [
  {'from': 'K2Node_Event_ZB60.DamageCauser', 'to': bc + '.Object', 'note': 'is it a soldier bolt?'},
  {'from': 'K2Node_Event_ZB60.Damage', 'to': bolt[0] + '.A', 'note': 'incoming damage'},
  {'from': bolt[0] + '.ReturnValue', 'to': 'K2Node_CallFunction_ZB64.B', 'replace': True, 'note': 'x bolt factor into the DamageTaken add'},
  {'from': 'CX_83.ReturnValue', 'to': diff[0] + '.A', 'note': 'GateDamage + hit'},
  {'from': 'CX_82.GateDamage', 'to': diff[0] + '.B'},
  {'from': 'CX_82.GateDamage', 'to': gate[0] + '.A'},
  {'from': gate[0] + '.ReturnValue', 'to': 'CX_84.A', 'replace': True, 'note': 'softened gate hit into the FMin'}]},
  open(os.path.join(HERE, 'manifest_zombie.json'), 'w'), indent=1)
print('Zombie', len(G.nodes), 'nodes', bolt[0], gate[0])
