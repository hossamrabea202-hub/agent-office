import unreal
EAL=unreal.EditorAssetLibrary
L=[]
for p in ['/Game/CastleDefender/Gameplay/Gore/BPC_Gore337','/Game/CastleDefender/Gameplay/Gore/BP_SeveredLimb337','/Game/CastleDefender/Gameplay/Gore/BP_WoundCap337']:
    L.append('%s %s'%(p,EAL.does_asset_exist(p)))
r=unreal.AssetRegistryHelpers.get_asset_registry()
for n in ['BPC_Gore337','BP_SeveredLimb337','BP_WoundCap337','BP_Zombie']:
    a=[x.package_name for x in r.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine','Blueprint')) if str(x.asset_name)==n]
    L.append('%s -> %s'%(n,a))
    if a:
        bp=unreal.load_asset(str(a[0]))
        try:
            g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
            L.append('   graph nodes %s'%len(g.get_editor_property('nodes')))
        except Exception as e: L.append('   graph ? %s'%e)
        if n=='BP_Zombie':
            cdo=unreal.get_default_object(bp.generated_class())
            L.append('   comps %s'%[c.get_name() for c in cdo.get_components_by_class(unreal.ActorComponent)])
open(r'C:/Users/hossa/Documents/agent-office/_gorechk_out.txt','w').write('\n'.join(L))
