import unreal
EAL = unreal.EditorAssetLibrary
import _mh
path = _mh.find('BP_WallBreachSpot'); bp = unreal.load_asset(path)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
n = 0
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
    if isinstance(o, unreal.StaticMeshComponent) and o.get_name().startswith('Rubble'):
        o.set_editor_property('visible', False)
        o.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)
        n += 1
unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(path)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); m = 0
for a in eas.get_all_level_actors():
    if a.get_class() == bp.generated_class():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name().startswith('Rubble'):
                c.set_visibility(False, False); c.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO); m += 1
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_fix237.txt', 'w').write('template rubble %d, placed rubble %d, saved' % (n, m))
print('FIX237', n, m)
