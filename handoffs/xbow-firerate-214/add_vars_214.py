# #214 step 1: adds NextFireAt (0.0) and FireCooldown (1.0 s) to BP_Crossbow. Safe to re-run.
#   py "<repo>/handoffs/xbow-firerate-214/add_vars_214.py"
import unreal
P = '/Game/CastleDefender/Gameplay/Crossbow/BP_Crossbow'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
def _var_names(bp, wanted):
    """UE 5.8: Blueprint.new_variables is not readable from Python (#380). Compile, then probe the class default object."""
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have
reg = unreal.AssetRegistryHelpers.get_asset_registry()
hits = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == 'BP_Crossbow']
path = str(hits[0].package_name) if hits else P
bp = unreal.load_asset(path)
have = _var_names(bp, ('NextFireAt', 'FireCooldown'))
t = BEL.get_basic_type_by_name('real')  # UE 5.8: 'real' is already double; EdGraphPinType fields can't be set from Python
for n in ('NextFireAt', 'FireCooldown'):
    if n not in have: BEL.add_member_variable(bp, n, t)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property('FireCooldown', 1.0); cdo.set_editor_property('NextFireAt', 0.0)
EAL.save_asset(path)
unreal.log('#214 vars on ' + path + ': NextFireAt, FireCooldown = 1.0')
