import unreal
AR=unreal.AssetRegistryHelpers.get_asset_registry(); opt=unreal.AssetRegistryDependencyOptions()
def f(n):
    for a in AR.get_assets_by_path('/Game',True):
        if str(a.asset_name)==n: return str(a.package_name)
obs=f('BPC_ObsidianSet'); arm=f('BP_ArmoryHUD')
print('obs',obs,'armory',arm)
print('referencers of BPC_ObsidianSet:',[str(x) for x in AR.get_referencers(obs,opt)])
c=unreal.load_asset(obs).generated_class(); d=unreal.get_default_object(c)
print('funcs', [x for x in dir(d) if 'rmour' in x.lower() or 'armou' in x.lower() or 'draw' in x.lower()][:20])
for k in ('AvailMask','WornMask','OwnedMask','PieceId','Price'):
    try: print(k, d.get_editor_property(k))
    except Exception as e: print(k,'-',e)
gm=unreal.EditorLevelLibrary.get_editor_world().get_world_settings().get_editor_property('default_game_mode')
print('world gamemode', gm)
if gm:
    g=unreal.get_default_object(gm); print('HUD class', g.get_editor_property('hud_class'))
