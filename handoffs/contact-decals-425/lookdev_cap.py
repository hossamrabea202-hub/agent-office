# #425 locked-exposure capture (shared by the preview). shot(path, cam, tgt, ev) renders 1280x720 with MANUAL exposure
# (no physical camera, bias = ev), no TAA / motion blur / DOF / eye adaptation history, warmed up over 3 captures.
import unreal
def shot(path, cam, tgt, ev=0.0, fov=42.0):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rt = unreal.RenderingLibrary.create_render_target2d(w, 1280, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
    try:
        c = cap.capture_component2d
        c.set_editor_property('texture_target', rt); c.set_editor_property('fov_angle', fov)
        c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        c.set_editor_property('capture_every_frame', False)
        c.set_editor_property('show_flag_settings', [unreal.EngineShowFlagsSetting(show_flag_name=n, enabled=False) for n in ('TemporalAA', 'MotionBlur', 'DepthOfField', 'LensFlares')])
        pp = c.get_editor_property('post_process_settings')
        for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL), ('auto_exposure_bias', float(ev)), ('auto_exposure_apply_physical_camera_exposure', False)):
            pp.set_editor_property('override_' + k, True); pp.set_editor_property(k, v)
        c.set_editor_property('post_process_settings', pp); c.set_editor_property('post_process_blend_weight', 1.0)
        for _ in range(3): c.capture_scene()
        import os; unreal.RenderingLibrary.export_render_target(w, rt, os.path.dirname(path), os.path.basename(path))
    finally:
        EAS.destroy_actor(cap)
    print('shot', path, 'ev', ev)
