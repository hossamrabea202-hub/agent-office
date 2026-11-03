# #451 light inspection renders for i5 (2 GB GPU). Rule (i5-lookdev-render-limits): below the cloud layer, VolumetricCloud /
# Fog / Atmosphere-heavy show flags OFF, 960x540, at most 3 shots per run, locked exposure (manual, EV bias).
#   py shots_ue.py <tag>[:EV][@bc = base colour, no lighting] "<name>;cx,cy,cz;tx,ty,tz[;fov]" ["..."] ["..."]   -> gpt-review-polish/shots/<tag>_<name>.png
import os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/shots/'
os.makedirs(H, exist_ok=True)
tag = sys.argv[1]; specs = sys.argv[2:5]
BC = tag.endswith('@bc'); tag = tag.replace('@bc', '')
if ':' in tag: tag, _ev = tag.split(':'); os.environ['SHOT_EV'] = _ev
EV = float(os.environ.get('SHOT_EV', '1.5'))
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rt = unreal.RenderingLibrary.create_render_target2d(w, 960, 540, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
OFF = ('TemporalAA', 'MotionBlur', 'DepthOfField', 'LensFlares', 'VolumetricFog', 'Fog', 'Cloud', 'Atmosphere')
for s in specs:
    parts = s.split(';'); name = parts[0]
    cam = unreal.Vector(*[float(v) for v in parts[1].split(',')]); tgt = unreal.Vector(*[float(v) for v in parts[2].split(',')])
    fov = float(parts[3]) if len(parts) > 3 else 50.0
    if cam.z > 15000: print('SKIP', name, 'camera above 150 m (cloud layer)'); continue
    cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
    try:
        c = cap.capture_component2d
        c.set_editor_property('texture_target', rt); c.set_editor_property('fov_angle', fov)
        c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_BASE_COLOR if BC else unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        c.set_editor_property('capture_every_frame', False)
        c.set_editor_property('show_flag_settings', [unreal.EngineShowFlagsSetting(show_flag_name=n, enabled=False) for n in OFF])
        pp = c.get_editor_property('post_process_settings')
        for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL), ('auto_exposure_bias', EV), ('auto_exposure_apply_physical_camera_exposure', False)):
            pp.set_editor_property('override_' + k, True); pp.set_editor_property(k, v)
        c.set_editor_property('post_process_settings', pp); c.set_editor_property('post_process_blend_weight', 1.0)
        c.capture_scene(); c.capture_scene()
        unreal.RenderingLibrary.export_render_target(w, rt, H, '%s_%s.png' % (tag, name))
        print('shot', name)
    finally:
        EAS.destroy_actor(cap)
