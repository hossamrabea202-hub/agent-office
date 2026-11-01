# Frame the viewport on an actor from an offset (i5 helper):  py ".../look_ue.py" <label> <dx> <dy> <dz>
import sys, unreal
LABEL = sys.argv[1]; OFF = unreal.Vector(*[float(v) for v in sys.argv[2:5]])
a = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == LABEL][0]
o, e = a.get_actor_bounds(False); cam = o + OFF
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam, unreal.MathLibrary.make_rot_from_x(o - cam))
