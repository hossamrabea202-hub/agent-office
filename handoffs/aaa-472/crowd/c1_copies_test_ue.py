# i5 #493: two temp copies of BP_Zombie (Zc0 plain, Zc1 + BPC_CrowdTier) for an A/B test in Play. Temp folder only.
import unreal
EA, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
F, ZP = '/Game/_i5tmpC1z', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
for n in ('Zc0', 'Zc1'):
    if not EA.does_asset_exist(F + '/' + n): EA.duplicate_asset(ZP, F + '/' + n)
z1 = unreal.load_asset(F + '/Zc1'); ct = unreal.load_asset(F + '/BPC_CrowdTier')
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SL = unreal.SubobjectDataBlueprintFunctionLibrary
hs = sds.k2_gather_subobject_data_for_blueprint(z1)
names = [str(SL.get_variable_name(SL.get_data(h))) for h in hs]
if not any(x.startswith('CrowdTier') for x in names):
    h, why = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=ct.generated_class(), blueprint_context=z1))
    print('attach valid', SL.is_handle_valid(h), why); sds.rename_subobject(h, unreal.Text('CrowdTier'))
for n in ('Zc0', 'Zc1'):
    b = unreal.load_asset(F + '/' + n); BEL.compile_blueprint(b); EA.save_asset(F + '/' + n, only_if_is_dirty=False)
    print(n, 'components', [str(SL.get_variable_name(SL.get_data(h))) for h in sds.k2_gather_subobject_data_for_blueprint(b)])
