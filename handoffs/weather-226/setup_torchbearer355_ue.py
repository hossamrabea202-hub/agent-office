# #355 torch-bearer soldier, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/weather-226/setup_torchbearer355_ue.py" --dry-run / (no flag)
# Makes /Game/CastleDefender/Environment/Weather/BP_TorchBearer (a Character, possessed by the default AI controller so it
# can walk the navmesh). It looks like the garrison (soldier_components.txt): the inherited Mesh = SKM_Quinn_Simple +
# ABP_Quinn (walk animation from its speed), hidden but always ticking; Knight = ShadowknightUE_SK + ABP_KnightFollow on
# top; Taper = the castle's own SM_IronTorch held in hand_r; Flame = a warm 2700 K point light on it (KB rule 6).
import sys, unreal

DRY = '--dry-run' in sys.argv
DST, NAME = '/Game/CastleDefender/Environment/Weather', 'BP_TorchBearer'
Q = '/Game/CastleDefender/Characters/Mannequins/Mannequins/Meshes/SKM_Quinn_Simple'
QABP = '/Game/CastleDefender/Characters/Mannequins/Mannequins/Animations/ABP_Quinn'
KN, KABP = '/Game/ShadowKight/Mesh/ShadowknightUE_SK', '/Game/CastleDefender/Characters/Knight/ABP_KnightFollow'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#355 torch-bearer setup' + (' (DRY RUN, nothing written)' if DRY else '')]

torch = [str(ad.package_name) for ad in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh')],
                                                                    package_paths=['/Game'], recursive_paths=True)) if str(ad.asset_name) == 'SM_IronTorch']
log.append('hand torch mesh: %s' % (torch[0] if torch else 'SM_IronTorch NOT FOUND (Taper left empty: pick a torch mesh by hand)'))
missing = [p for p in (Q, QABP, KN, KABP) if not EAL.does_asset_exist(p)]
if missing: raise SystemExit('missing ' + ', '.join(missing))


def comps(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add(bp, cls, name, parent):
    have = comps(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, why = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s' % (name, why))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + ' + name); return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


path = DST + '/' + NAME
log.append(('reuse ' if EAL.does_asset_exist(path) else 'create ') + path)
if not DRY:
    bp = unreal.load_asset(path)
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Character)
        bp = AT.create_asset(NAME, DST, unreal.Blueprint, f)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    cdo.character_movement.set_editor_property('max_walk_speed', 230.0)          # a calm walk, not a run
    cdo.character_movement.set_editor_property('orient_rotation_to_movement', True)
    cdo.set_editor_property('use_controller_rotation_yaw', False)
    m = cdo.mesh
    m.set_editor_property('skeletal_mesh', unreal.load_asset(Q))
    m.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
    m.set_editor_property('anim_class', unreal.load_class(None, QABP + '.ABP_Quinn_C'))
    m.set_editor_property('relative_location', unreal.Vector(0, 0, -89)); m.set_editor_property('relative_rotation', unreal.Rotator(0, 0, -90))
    m.set_editor_property('visible', False)
    m.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    h = comps(bp)
    mesh_h = h.get('CharacterMesh0') or h.get('Mesh') or SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    k = add(bp, unreal.SkeletalMeshComponent, 'Knight', mesh_h)
    k.set_editor_property('skeletal_mesh', unreal.load_asset(KN)); k.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
    k.set_editor_property('anim_class', unreal.load_class(None, KABP + '.ABP_KnightFollow_C')); k.set_collision_profile_name('NoCollision')
    t = add(bp, unreal.StaticMeshComponent, 'Taper', mesh_h)
    if torch: t.set_editor_property('static_mesh', unreal.load_asset(torch[0]))
    t.set_editor_property('attach_socket_name', 'hand_r'); t.set_editor_property('relative_scale3d', unreal.Vector(0.6, 0.6, 0.6))
    t.set_collision_profile_name('NoCollision')
    fl = add(bp, unreal.PointLightComponent, 'Flame', comps(bp)['Taper'])
    fl.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); fl.set_editor_property('intensity', 300.0)
    fl.set_editor_property('use_temperature', True); fl.set_editor_property('temperature', 2700.0)
    fl.set_editor_property('attenuation_radius', 700.0); fl.set_editor_property('source_radius', 3.0)
    fl.set_editor_property('relative_location', unreal.Vector(0, 0, 45))
    BEL.compile_blueprint(bp); EAL.save_asset(path)
    log.append('done. Next: 6 BPVar lines + paste BP_TorchBearer_graph.txt (README).')
    log.append('MANUAL check (1 min): Taper sits in the right hand; Flame at the torch head (nudge if not).')
out = '\n'.join(log); unreal.log(out); print(out)
