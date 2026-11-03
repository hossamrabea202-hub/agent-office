# #451 lit A/B for one change (i5): spawns a TEMPORARY 5000 K point light (no shadows from far fill, one key with shadows),
# renders final colour at locked exposure, runs a toggle script (revert = A, apply = B), renders again, deletes the lights.
#   py lit_ab_ue.py <tag> <cx,cy,cz> <tx,ty,tz> <lightx,lighty,lightz> <toggle script> <A args;...> <B args;...>
import os, runpy, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
tag, cam, tgt, lp, scr, a_args, b_args = sys.argv[1:8]
for kv in sys.argv[8:]: k, v = kv.split('='); os.environ[k] = v           # KEY=<cd> LIT_EV=<bias>
V = lambda s: unreal.Vector(*[float(x) for x in s.split(',')])
cam, tgt, lp = V(cam), V(tgt), V(lp)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
made = []


def light(at, inten, shadows):
    L = EAS.spawn_actor_from_class(unreal.PointLight, at, unreal.Rotator()); made.append(L)
    c = L.point_light_component; c.set_editor_property('intensity', inten); c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', 5000.0); c.set_editor_property('attenuation_radius', 1500.0); c.set_editor_property('cast_shadows', shadows)


def shot(name):
    rt = unreal.RenderingLibrary.create_render_target2d(w, 960, 540, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
    try:
        c = cap.capture_component2d
        c.set_editor_property('texture_target', rt); c.set_editor_property('fov_angle', 40.0)
        c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR); c.set_editor_property('capture_every_frame', False)
        c.set_editor_property('show_flag_settings', [unreal.EngineShowFlagsSetting(show_flag_name=n, enabled=False) for n in ('TemporalAA', 'MotionBlur', 'DepthOfField', 'VolumetricFog', 'Fog', 'Cloud', 'Atmosphere')])
        pp = c.get_editor_property('post_process_settings')
        for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL), ('auto_exposure_bias', float(os.environ.get('LIT_EV', '0'))), ('auto_exposure_apply_physical_camera_exposure', False)):
            pp.set_editor_property('override_' + k, True); pp.set_editor_property(k, v)
        c.set_editor_property('post_process_settings', pp); c.set_editor_property('post_process_blend_weight', 1.0)
        c.capture_scene(); c.capture_scene()
        unreal.RenderingLibrary.export_render_target(w, rt, H + 'shots/', '%s_%s.png' % (tag, name)); print('shot', name)
    finally:
        EAS.destroy_actor(cap)


def toggle(args):
    old = sys.argv; sys.argv = [scr] + [x for x in args.split(';') if x]
    try: runpy.run_path(H + scr, run_name='__main__')
    except SystemExit: pass
    finally: sys.argv = old


try:
    light(lp, float(os.environ.get('KEY', '40')), True); light(cam + unreal.Vector(0, 0, 200), float(os.environ.get('KEY', '40')) * 0.15, False)
    toggle(a_args); shot('A')
    toggle(b_args); shot('B')
finally:
    for L in made: EAS.destroy_actor(L)
