# i5 (PIE): put the player pawn near an actor facing it (dx dy in cm), then HighResShot of the game viewport to <out.png>.
#   py ".../pie_view_ue.py" <label-substring> <out.png> [dx dy]
import sys, math, unreal
a = sys.argv[1:]
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
x = [y for y in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a[0].lower() in y.get_actor_label().lower()][0]
dx, dy = (float(a[2]), float(a[3])) if len(a) > 3 else (-700.0, -400.0)
p = unreal.GameplayStatics.get_player_pawn(w, 0); pc = unreal.GameplayStatics.get_player_controller(w, 0)
o = x.get_actor_location(); pos = o + unreal.Vector(dx, dy, 120)
p.set_actor_location(pos, False, True)
yaw = math.degrees(math.atan2(o.y - pos.y, o.x - pos.x)); pc.set_control_rotation(unreal.Rotator(0, -12, yaw))
unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename=' + a[1])
print('pawn at', pos, 'looking at', x.get_actor_label())
