# #487 E2 part 2 (i5, read-only): links of the zombie scans in the LIVE BP_ZombieHUD (H2128) and BP_MinimapHUD (CX_116).
import unreal
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
for p, nm in (('/Game/CastleDefender/UI/BP_ZombieHUD', 'K2Node_CallFunction_H2128'), ('/Game/CastleDefender/UI/BP_MinimapHUD', 'CX_116')):
    a = unreal.EditorAssetLibrary.find_asset_data(p)
    if not a.is_valid():
        r = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint'))
        hits = [str(x.package_name) for x in r if str(x.asset_name) == p.split('/')[-1]]; print(p, 'not here, found', hits)
        if not hits: continue
        p = hits[0]
    bp = unreal.load_asset(p); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
    n = live.get(nm); print('==', p, len(live), 'nodes', nm, 'found' if n else 'MISSING')
    if not n: continue
    for pin_name in ('execute', 'then', 'OutActors', 'ActorClass'):
        for out in (True, False):
            q = BEL.find_output_pin(n, pin_name) if out else BEL.find_input_pin(n, pin_name)
            if q and PL.is_valid(q):
                print(' ', pin_name, 'out' if out else 'in', '->', [(PL.get_owning_node(x).get_name(), str(x)[-40:]) for x in PL.list_connected_pins(q)])
