import unreal, traceback
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
L = []
D = '/Game/Codex/AssignmentMarkers102_v1'
try:
    EAL = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    BPL = unreal.BlueprintEditorLibrary
    path = D + '/BP_AssignmentMarker102'
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path); L.append('exists, reusing')
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = tools.create_asset('BP_AssignmentMarker102', D, unreal.Blueprint, f); L.append('created %s' % bp.get_path_name())
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    root_h = None
    for h in handles:
        d = sds.k2_find_subobject_data_from_handle(h)
        name = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(d))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
        L.append('sub %s %s' % (name, obj.get_class().get_name() if obj else None))
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_default_scene_root(d) or name == 'DefaultSceneRoot':
            root_h = h; root_obj = obj
    if root_h is None:
        raise RuntimeError('no default scene root')
    # rename root -> MarkerRoot, absolute rotation/scale
    sds.rename_subobject(root_h, unreal.Text('MarkerRoot'))
    root_obj.set_editor_property('absolute_rotation', True); root_obj.set_editor_property('absolute_scale', True)
    root_obj.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    def add(cls, name):
        p = unreal.AddNewSubobjectParams(parent_handle=root_h, new_class=cls, blueprint_context=bp)
        h, fail = sds.add_new_subobject(p)
        if not fail.is_empty(): raise RuntimeError('add %s: %s' % (name, fail))
        sds.rename_subobject(h, unreal.Text(name))
        d = sds.k2_find_subobject_data_from_handle(h)
        return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
    gm = unreal.load_asset(D + '/M_Assignment102_Ground'); am = unreal.load_asset(D + '/M_Assignment102_Air'); sm = unreal.load_asset(D + '/SM_Assignment102_AirRim')
    dec = add(unreal.DecalComponent, 'GroundDecal')
    dec.set_editor_property('decal_material', gm)
    dec.set_editor_property('decal_size', unreal.Vector(60, 85, 85))
    dec.set_editor_property('relative_rotation', unreal.Rotator(0, -90, 0))
    dec.set_editor_property('fade_screen_size', 0.01)
    dec.set_editor_property('sort_order', 0)
    rim = add(unreal.StaticMeshComponent, 'AirRim')
    rim.set_editor_property('static_mesh', sm)
    rim.set_editor_property('relative_location', unreal.Vector(0, 0, 6))
    rim.set_editor_property('override_materials', [am])
    rim.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    rim.set_collision_profile_name('NoCollision')
    rim.set_editor_property('generate_overlap_events', False)
    rim.set_editor_property('cast_shadow', False)
    rim.set_editor_property('receives_decals', False)
    rim.set_editor_property('can_ever_affect_navigation', False)
    # variables
    def pt(cat, sub=None):
        t = unreal.EdGraphPinType(); t.set_editor_property('pin_category', cat)
        if sub: t.set_editor_property('pin_sub_category_object', sub)
        return t
    for nm, t, dv in (('GroundMID', pt('object', unreal.MaterialInstanceDynamic.static_class()), ''), ('AirMID', pt('object', unreal.MaterialInstanceDynamic.static_class()), ''), ('MarkerAlive', pt('bool'), 'true')):
        ok = BPL.add_member_variable(bp, nm, t, dv)
        L.append('var %s %s' % (nm, ok))
    BPL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('hidden', True)
    cdo.set_editor_property('replicates', False)
    BPL.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    L.append('saved; comps: %s' % [c.get_name() for c in bp.generated_class().get_default_object().get_components_by_class(unreal.ActorComponent)] if False else 'saved')
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
except Exception:
    L.append(traceback.format_exc())
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
