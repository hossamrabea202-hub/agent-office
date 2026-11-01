# i5 helper (2026-11-01): render a still WITHOUT the viewport (works while the laptop's screen is locked).
#   py ".../capture_shot_ue.py" <out.png> camX camY camZ tgtX tgtY tgtZ [fov=60] [w=1280] [h=720]
# A temporary SceneCapture2D (final colour, LDR) renders into a transient render target, which is exported to <out.png>;
# the capture actor is destroyed again (nothing saved). Editor time keeps running, so animated materials show a frame.
import os, sys, unreal
a = sys.argv[1:]
out = a[0]; cam = unreal.Vector(*[float(v) for v in a[1:4]]); tgt = unreal.Vector(*[float(v) for v in a[4:7]])
fov = float(a[7]) if len(a) > 7 else 60.0; w = int(a[8]) if len(a) > 8 else 1280; h = int(a[9]) if len(a) > 9 else 720
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
rt = unreal.RenderingLibrary.create_render_target2d(world, w, h, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
cap = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(tgt - cam))
c = cap.capture_component2d
c.set_editor_property('texture_target', rt)
c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
c.set_editor_property('fov_angle', fov)
c.set_editor_property('capture_every_frame', False)
c.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, os.path.dirname(out), os.path.basename(out))   
EAS.destroy_actor(cap)
print('captured', out, os.path.exists(out) or os.path.exists(out[:-4] + '.hdr'))
