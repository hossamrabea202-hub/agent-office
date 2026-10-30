# #214 step 1: adds NextFireAt (0.0) and FireCooldown (1.0 s) to BP_Crossbow. Safe to re-run.
#   py "<repo>/handoffs/xbow-firerate-214/add_vars_214.py"
import unreal
P = '/Game/CastleDefender/Gameplay/Crossbow/BP_Crossbow'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()
hits = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_Crossbow']
path = str(hits[0].package_name) if hits else P
bp = unreal.load_asset(path)
have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
t = BEL.get_basic_type_by_name('real'); t.set_editor_property('pin_sub_category', 'double')
for n in ('NextFireAt', 'FireCooldown'):
    if n not in have: BEL.add_member_variable(bp, n, t)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property('FireCooldown', 1.0); cdo.set_editor_property('NextFireAt', 0.0)
EAL.save_asset(path)
unreal.log('#214 vars on ' + path + ': NextFireAt, FireCooldown = 1.0')
