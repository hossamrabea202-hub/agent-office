# i5 lookdev helper (#447): like capture_shot_ue.py, plus a temporary neutral point light at the camera so night scenes
# can be compared. Nothing is saved; the light and capture actor are destroyed again.
#   py shot_lit_ue.py <out.png> camX camY camZ tgtX tgtY tgtZ [fov=60] [w=960] [h=540] [intensity=60000]
import os, sys, unreal
a = sys.argv[1:]
out = a[0]; cam = unreal.Vector(*[float(v) for v in a[1:4]]); tgt = unreal.Vector(*[float(v) for v in a[4:7]])
fov = float(a[7]) if len(a) > 7 else 60.0; w = int(a[8]) if len(a) > 8 else 960; h = int(a[9]) if len(a) > 9 else 540
inten = float(a[10]) if len(a) > 10 else 2500.0
ev = float(a[11]) if len(a) > 11 else 6.5
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
lt = EAS.spawn_actor_from_class(unreal.PointLight, cam + (tgt - cam) * 0.15 + unreal.Vector(0, 0, 120), unreal.Rotator(0, 0, 0))
pc = lt.point_light_component
pc.set_editor_property('intensity', inten); pc.set_editor_property('attenuation_radius', 4000.0)
pc.set_editor_property('use_temperature', True); pc.set_editor_property('temperature', 5600.0)
pc.set_editor_property('source_radius', 40.0)
rt = unreal.RenderingLibrary.create_render_target2d(world, w, h, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
c = cap.capture_component2d
c.set_editor_property('texture_target', rt)
c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
c.set_editor_property('fov_angle', fov)
c.set_editor_property('capture_every_frame', False)
pp = c.get_editor_property('post_process_settings')          # locked exposure (lookdev rule: Min EV = Max EV)
pp.set_editor_property('override_auto_exposure_method', True)
pp.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
pp.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True)
pp.set_editor_property('auto_exposure_apply_physical_camera_exposure', False)
pp.set_editor_property('override_auto_exposure_bias', True)
pp.set_editor_property('auto_exposure_bias', -ev + 3.0)
c.set_editor_property('post_process_settings', pp)
c.set_editor_property('post_process_blend_weight', 1.0)
c.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, os.path.dirname(out), os.path.basename(out))
EAS.destroy_actor(cap); EAS.destroy_actor(lt)
print('captured', out, os.path.exists(out))
