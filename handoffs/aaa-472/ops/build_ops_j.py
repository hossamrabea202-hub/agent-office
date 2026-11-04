# #472 fix J (i5): BP_SoldierSword FocusCheck, audit #482 A1. Every soldier, 6.7 x a second, all in the same frame: GetAllActorsWithTag(SallyPort), which walks every actor in the world, and a scan of all soldiers.
#  - the tag result is kept in SallyCache and looked up again only while it is empty (the sally port can be streamed out at first);
#  - soldiers come from the manager's SoldierCache (fix A), with an IsValid guard: an entry can be destroyed up to 1 s old;
#  - the FocusCheck timer gets a start variance, so soldiers no longer all do this in one frame.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P_S = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'; WMC = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager.BP_ZombieWaveManager_C'
n = lambda i, k, x, y, **kw: dict(id=i, kind=k, x=x, y=y, defaults=kw.pop('defaults', []), **kw)
GS, KM, KA, KS = '/Script/Engine.GameplayStatics:', '/Script/Engine.KismetMathLibrary:', '/Script/Engine.KismetArrayLibrary:', '/Script/Engine.KismetSystemLibrary:'
nodes = [n('jGetS', 'get', 0, 0, var='SallyCache'), n('jLen', 'call', 250, 0, path=KA + 'Array_Length'), n('jMore', 'call', 500, 0, path=KM + 'Greater_IntInt', defaults=[['B', '0']]), n('jIf', 'branch', 750, 0),
         n('jSet', 'set', 1100, 200, var='SallyCache'), n('jGetS2', 'get', 1100, 400, var='SallyCache'),
         n('jFind', 'call', 0, 600, path=GS + 'GetActorOfClass', defaults=[['ActorClass', WMC]]), n('jSol', 'get', 300, 700, var='SoldierCache', cls=WMC), n('jIsV', 'call', 300, 850, path=KS + 'IsValid'), n('jIfV', 'branch', 600, 800)]
def R(a, b): return [a, b, True]
links = [['jGetS.SallyCache', 'jLen.TargetArray', False], ['jLen.ReturnValue', 'jMore.A', False], ['jMore.ReturnValue', 'jIf.Condition', False],
         R('CX_1032.then', 'jIf.execute'), R('CX_515.else', 'jIf.execute'), R('jIf.then', 'CX_519.Exec'), R('jIf.else', 'CX_518.execute'), R('CX_518.then', 'jSet.execute'), ['CX_518.OutActors', 'jSet.SallyCache', False], ['jSet.then', 'CX_519.Exec', False],
         R('jGetS2.SallyCache', 'CX_519.Array'),
         R('CX_496.then', 'jFind.execute'), ['jFind.ReturnValue', 'jSol.self', False], R('jFind.then', 'CX_999.execute'), R('jSol.SoldierCache', 'CX_1001.Array'),
         R('CX_1001.LoopBody', 'jIfV.execute'), ['jIfV.then', 'CX_1008.execute', False], ['CX_1001.Array Element', 'jIsV.Object', False], ['jIsV.ReturnValue', 'jIfV.Condition', False]]
ops = {'fix': 'J', 'bp': P_S, 'vars': [['SallyCache', {'object': 'Actor', 'array': True}]], 'nodes': nodes, 'links': links, 'remove': ['CX_499'], 'set_live': [['CX_497', 'InitialStartDelayVariance', '0.15']], 'dx': 0, 'dy': 22000}
json.dump(ops, open(os.path.join(HERE, 'ops_J_soldier.json'), 'w'), indent=0); print('ops_J_soldier.json', len(nodes), 'nodes', len(links), 'links')
