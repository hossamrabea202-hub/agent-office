import unreal
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()
path = [str(a.package_name) for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_Crossbow'][0]
bp = unreal.load_asset(path)
cdo = unreal.get_default_object(bp.generated_class())
t = BEL.get_basic_type_by_name('real'); t.set_editor_property('pin_sub_category', 'double')
added = []
for n in ('NextFireAt', 'FireCooldown'):
    try: cdo.get_editor_property(n)
    except Exception: BEL.add_member_variable(bp, n, t); added.append(n)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property('FireCooldown', 1.0); cdo.set_editor_property('NextFireAt', 0.0)
EAL.save_asset(path)
print('VARS214', path, added)
