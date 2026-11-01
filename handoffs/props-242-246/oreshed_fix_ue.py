# #242: the SM_OreShed import came in at 1/100 scale (metres read as cm). Scale the placed actor x100, sit it on the
# ground (bounds bottom = trace Z) and frame it in the viewport. Also reports the sign meshes' sizes. UE 5.8 Python.
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
log = []
sh = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Props242_246_OreShed'][0]
sh.set_actor_scale3d(unreal.Vector(100, 100, 100))
o, e = sh.get_actor_bounds(False)
l = sh.get_actor_location()
ground = -125.4
sh.set_actor_location(unreal.Vector(l.x, l.y, l.z + (ground - 5) - (o.z - e.z)), False, False)
o, e = sh.get_actor_bounds(False)
log.append('OreShed loc %s origin %s extent %s' % (sh.get_actor_location(), o, e))
for n in ('SM_Sign_Smith', 'SM_Sign_Tavern', 'SM_Sign_Shop'):
    m = unreal.load_asset('/Game/CastleDefender/Props/Town/Signs/' + n)
    b = m.get_bounding_box(); log.append('%s box %s .. %s' % (n, b.min, b.max))
cam = o + unreal.Vector(-900, 900, 450)
d = o - cam
UES.set_level_viewport_camera_info(cam, unreal.MathLibrary.make_rot_from_x(d))
out = '\n'.join(log); unreal.log(out); print(out)
