# i5 helper (2026-11-01): Play-In-Editor control without the GUI (works with the screen locked).
#   py ".../pie_ue.py" start            begin PIE
#   py ".../pie_ue.py" unpause          close the start menu pause (game starts paused behind it)
#   py ".../pie_ue.py" stop             end PIE
#   py ".../pie_ue.py" damage <label-substring> <amount>    ApplyDamage to the first PIE actor whose label/name has it
#   py ".../pie_ue.py" shot <out.png> <label-substring> [dx dy dz]   capture the PIE world at that actor (offset in cm)
import os, sys, unreal
a = sys.argv[1:]
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def game_world():
    try: return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    except Exception: return None
def find(sub):
    w = game_world()
    for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if sub.lower() in (x.get_actor_label() if hasattr(x, 'get_actor_label') else x.get_name()).lower() or sub.lower() in x.get_name().lower(): return x
cmd = a[0] if a else ''
if cmd == 'start': LES.editor_request_begin_play(); print('PIE requested')
elif cmd == 'stop': LES.editor_request_end_play(); print('PIE end requested')
elif cmd == 'unpause':
    w = game_world(); unreal.GameplayStatics.set_game_paused(w, False); print('unpaused', w)
elif cmd == 'damage':
    x = find(a[1]); print('target', x and x.get_name())
    if x: print('applied', unreal.GameplayStatics.apply_damage(x, float(a[2]), None, None, unreal.DamageType))
elif cmd == 'shot':
    w = game_world(); x = find(a[2]); off = [float(v) for v in a[3:6]] if len(a) >= 6 else [-450.0, -350.0, 250.0]
    o = x.get_actor_location(); cam = o + unreal.Vector(*off)
    rt = unreal.RenderingLibrary.create_render_target2d(w, 1280, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cap = w.spawn_actor(unreal.SceneCapture2D, cam, unreal.MathLibrary.make_rot_from_x(o + unreal.Vector(0, 0, 60) - cam)) if hasattr(w, 'spawn_actor') else \
        unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(w, unreal.SceneCapture2D, unreal.Transform(cam, unreal.MathLibrary.make_rot_from_x(o - cam)))
    if not hasattr(w, 'spawn_actor'): unreal.GameplayStatics.finish_spawning_actor(cap, unreal.Transform(cam, unreal.MathLibrary.make_rot_from_x(o + unreal.Vector(0, 0, 60) - cam)))
    c = cap.capture_component2d
    c.set_editor_property('texture_target', rt); c.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    c.set_editor_property('capture_every_frame', False); c.capture_scene()
    unreal.RenderingLibrary.export_render_target(w, rt, os.path.dirname(a[1]), os.path.basename(a[1])); cap.destroy_actor()
    print('shot', a[1], 'at', x.get_name())
