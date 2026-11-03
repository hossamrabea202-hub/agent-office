import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
o = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
for p in ('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet',):
    print('REFS', p, [str(x) for x in ar.get_referencers(p, o)])
