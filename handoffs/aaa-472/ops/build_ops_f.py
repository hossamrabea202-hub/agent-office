# #472 Track L, fix F (i5): wires that were never made, found by t3d_orphans.js. Proven on i5: an impure node with no exec input returns None at runtime and the Blueprint still
# compiles, with only a warning. Links only, except the hero's array guard. Writes ops_F_<name>.json next to this file.
#   python build_ops_f.py
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
G = '/Game/CastleDefender/Gameplay/'
def R(a, b): return [a, b, True]       # the one-link end lets go of its old wire first
FIXES = {
 'halfhorse': ('/Game/CastleDefender/Characters/Enemies/HalfHorseZombie/BP_HalfHorseZombie', [R('HHZ_N24.then', 'HHZ_N26.execute')]),
 'director': (G + 'Siege/BP_BattleDirector', [R('bdSpawnZombieWal94.then', 'bdAsSpot96.execute'), R('bdAsSpot96.then', 'bdSetTarget95.execute'), R('bdAsSpot96.CastFailed', 'bdForLoop99.execute')]),
 'upgrades': (G + 'Castle/BPC_CastleUpgrades', [R('BP.then', 'cuHasSave1.execute'), R('cuHasSave1.then', 'cuIfSave2.execute'), R('cuIfOffer36.then', 'cuAsBPNoticeHUD52.execute')]),
 'shieldkit': (G + 'Castle/BPC_ShieldKit', [R('vSetOffHand5.then', 'vHasSave6.execute'), R('vHasSave6.then', 'vIfSave7.execute')]),
 'flares': (G + 'Castle/BPC_Flares', [R('fxIfShopPrompt70.then', 'fxAsBPNoticeHUD73.execute')]),
 'medics': (G + 'Castle/BPC_Medics', [R('mdIfOffer19.then', 'mdAsBPNoticeHUD30.execute')]),
 'gore': ('', [R('gSpawnSeveredLi116.then', 'gHideBoneByName131.execute'), R('gSpawnWoundCap3134.then', 'gAddSevered141.execute')]),
 'barracks': (G + 'Castle/BP_BarracksHUD', [R('rqIfDraw38.then', 'rqFindNPC_Barrac39.execute'), R('rqFindNPC_Barrac39.then', 'rqTrack50.execute')]),
 'risen': (G + 'Castle/BP_RisenDirector', [R('NoticeJoin.then_0', 'dSetText186.execute')]),
}
PATHS = json.load(open(os.path.join(HERE, 'paths_f.json')))
for k, (p, links) in FIXES.items():
    json.dump({'fix': 'F', 'bp': PATHS[k], 'vars': [], 'nodes': [], 'links': links, 'remove': [], 'set_live': [], 'dx': 0, 'dy': 0}, open(os.path.join(HERE, 'ops_F_%s.json' % k), 'w'), indent=0)
    print('ops_F_%s.json' % k, PATHS[k].split('/')[-1], len(links), 'links')
# hero: BurnThink reads BurnEnd[0] next to a length check, but Blueprint's AND does not short-circuit: "index 0 of array length 0" on every empty tick
n = lambda i, k, x, y, **kw: dict(id=i, kind=k, x=x, y=y, defaults=kw.pop('defaults', []), **kw)
hero = {'fix': 'F', 'bp': PATHS['hero'], 'vars': [], 'set_live': [], 'dx': 0, 'dy': 60000, 'remove': [],
        'nodes': [n('hbLen', 'call', 0, 0, path='/Script/Engine.KismetArrayLibrary:Array_Length'), n('hbMore', 'call', 300, 0, path='/Script/Engine.KismetMathLibrary:Greater_IntInt', defaults=[['B', '0']]), n('hbIf', 'branch', 600, 0)],
        'links': [['sfGetBurnEnd79.BurnEnd', 'hbLen.TargetArray', False], ['hbLen.ReturnValue', 'hbMore.A', False], ['hbMore.ReturnValue', 'hbIf.Condition', False], R('sfForEach68.Completed', 'hbIf.execute'), ['hbIf.then', 'sfIfBurnOver84.execute', False]]}
json.dump(hero, open(os.path.join(HERE, 'ops_F_hero.json'), 'w'), indent=0); print('ops_F_hero.json')
