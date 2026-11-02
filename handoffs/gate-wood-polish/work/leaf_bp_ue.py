# Read-only: where does BP_GateBreachLeaf get M_Metal_Steel? (component template override, instance override, or runtime)
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
bp = None
for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')):
    if str(a.asset_name) == 'BP_GateBreachLeaf':
        bp = unreal.load_asset(str(a.package_name)); print('BP', a.package_name)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    d = sds.k2_find_subobject_data_from_handle(h)
    o = SDL.get_object(d)
    if isinstance(o, unreal.SkeletalMeshComponent):
        print('template', o.get_name(), 'mesh', o.get_editor_property('skeletal_mesh_asset').get_name() if o.get_editor_property('skeletal_mesh_asset') else None,
              'override', [m.get_path_name() if m else None for m in o.get_editor_property('override_materials')])
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == 'BP_GateBreachLeaf_C':
        c = a.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        print('instance', a.get_actor_label(), a.get_actor_location(), 'override', [m.get_path_name() if m else None for m in c.get_editor_property('override_materials')],
              'mesh', c.get_editor_property('skeletal_mesh_asset').get_path_name(), 'scale', a.get_actor_scale3d())
sk = unreal.load_asset('/Game/CastleDefender/Props/GateBreach/SK_GateLeaf_L') if unreal.EditorAssetLibrary.does_asset_exist('/Game/CastleDefender/Props/GateBreach/SK_GateLeaf_L') else None
if sk:
    print('SK slots', [(str(m.get_editor_property('material_slot_name')), m.get_editor_property('material_interface').get_path_name() if m.get_editor_property('material_interface') else None) for m in sk.get_editor_property('materials')])
