# Temporary side-by-side: SM_Emberoath_Kit vs SM_CK_Longsword at the same scale (100, like the hand chain), at the ore shed.
#   py ".../kitcompare_ue.py"          spawn (tag TmpKit418) + frame the camera   |   --remove   delete them
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if 'TmpKit418' in [str(t) for t in a.tags]: EAS.destroy_actor(a)
if '--remove' not in sys.argv:
    base = unreal.Vector(247, -1950, -100); out = []
    for i, p in enumerate(('/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath_Kit2', '/Game/CastleDefender/Weapons/CK/Longsword/SM_CK_Longsword',
                           '/Game/CastleDefender/Weapons/CK/ArmingSword/SM_CK_ArmingSword')):
        a = EAS.spawn_actor_from_object(unreal.load_asset(p), base + unreal.Vector(0, i * 60, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_scale3d(unreal.Vector(100, 100, 100)); a.tags = [unreal.Name('TmpKit418')]; a.set_actor_label('TmpKit418_%d' % i)
        o, e = a.get_actor_bounds(False); out.append('%s height %.0f cm' % (p.split('/')[-1], e.z * 2))
    cam = base + unreal.Vector(-260, 60, 60)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam, unreal.MathLibrary.make_rot_from_x(base + unreal.Vector(0, 60, 60) - cam))
    unreal.log('i5 kitcompare: ' + ' / '.join(out))
