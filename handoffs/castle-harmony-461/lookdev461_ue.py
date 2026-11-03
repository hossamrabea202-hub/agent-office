# #461 lookdev (i5, temporary, nothing saved): the stone MIs as a row of 3 m walls next to the AAA reference, same light, locked
# exposure, on the empty Entry level. Stages run as separate scripts, so the editor ticks between them and the MI proxies refresh.
#   py lookdev461_ue.py setup | shot <name> | clean      (state: harmony461_ue.py --apply/--revert --nosave in between)
import os, sys, unreal
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/'
stage = sys.argv[1]
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); w = ues.get_editor_world()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); MEL = unreal.MaterialEditingLibrary
if w.get_name() != 'Entry': print('NOT ON ENTRY:', w.get_name(), 'abort'); raise SystemExit
CUBE = unreal.load_asset('/Engine/BasicShapes/Cube')
ROW = ['MI_Castle_StoneWall_World', 'MI_Castle_Trim_World', 'MI_Castle_WalkFlag_World', 'MI_Castle_StepCap']
C = '/Game/CastleDefender/Shared/Materials/Castle/'
if stage == 'clean':
    n = 0
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith('h461_'): EAS.destroy_actor(a); n += 1
    print('cleaned', n, 'left in level', len(EAS.get_all_level_actors())); raise SystemExit
if stage == 'setup':
    x = -1000
    for n in ROW:
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, 0, 150), unreal.Rotator()); a.set_actor_label('h461_' + n)
        c = a.static_mesh_component; c.set_static_mesh(CUBE); a.set_actor_scale3d(unreal.Vector(2.9, 0.5, 3.0)); c.set_material(0, unreal.load_asset(C + n)); x += 320
    ref = unreal.load_asset('/Game/CastleDefender/Environment/Castle/KeepEntrance/M_KeepEntrance_Baked')
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(1020, 710, 0), unreal.Rotator()); a.set_actor_label('h461_ref')
    a.static_mesh_component.set_static_mesh(unreal.load_asset('/Game/CastleDefender/Environment/Castle/KeepEntrance/SM_KeepEntrance_Baked'))
    d = a.static_mesh_component.create_dynamic_material_instance(0, ref)
    d.set_vector_parameter_value('Tint', unreal.LinearColor(0.5332, 0.5146, 0.4836, 1.0)); d.set_scalar_parameter_value('LimewashAmount', 0.0); d.set_scalar_parameter_value('CrackAmount', 0.0)
    S = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 2000), unreal.Rotator(0, -40, 60)); S.set_actor_label('h461_sun')
    L = S.get_component_by_class(unreal.DirectionalLightComponent); L.set_editor_property('intensity', 6.0); L.set_editor_property('use_temperature', True); L.set_editor_property('temperature', 5600.0)
    F = EAS.spawn_actor_from_class(unreal.PointLight, unreal.Vector(350, -2400, 500), unreal.Rotator()); F.set_actor_label('h461_fill')
    L = F.get_component_by_class(unreal.PointLightComponent); L.set_editor_property('intensity', 40.0); L.set_editor_property('attenuation_radius', 6000.0); L.set_editor_property('cast_shadows', False)
    print('setup ok'); raise SystemExit
name = sys.argv[2]
rt = unreal.RenderingLibrary.create_render_target2d(w, 1280, 400, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
cam = unreal.Vector(350, -2800, 170); tgt = unreal.Vector(350, 0, 150)
cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
try:
    c = cap.capture_component2d
    c.set_editor_property('texture_target', rt); c.set_editor_property('fov_angle', 56.0)
    c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR); c.set_editor_property('capture_every_frame', False)
    c.set_editor_property('show_flag_settings', [unreal.EngineShowFlagsSetting(show_flag_name=n, enabled=False) for n in ('TemporalAA', 'MotionBlur', 'DepthOfField', 'VolumetricFog', 'Fog', 'Cloud', 'Atmosphere', 'Bloom')])
    pp = c.get_editor_property('post_process_settings')
    for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL), ('auto_exposure_bias', float(os.environ.get('LIT_EV', '0'))), ('auto_exposure_apply_physical_camera_exposure', False)):
        pp.set_editor_property('override_' + k, True); pp.set_editor_property(k, v)
    c.set_editor_property('post_process_settings', pp); c.set_editor_property('post_process_blend_weight', 1.0)
    c.capture_scene(); c.capture_scene()
    unreal.RenderingLibrary.export_render_target(w, rt, HERE + 'shots/', 'h461_%s.png' % name); print('shot', name)
finally:
    EAS.destroy_actor(cap)
