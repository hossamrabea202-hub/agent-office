# #504 preview, part 2: the AFTER shot from the same camera as the before shot (separate run, so the new card shaders have
# compiled). Then removes the preview cards unless --keep.     py shot_after504_ue.py <dir> [--keep]
import sys, unreal
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504'
sys.path.insert(0, 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425'); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
c = [float(x) for x in open(HERE + '/_preview_cam.txt').read().split()]
out = [a for a in sys.argv[1:] if not a.startswith('--')][0]
lookdev_cap.shot(out + '/cw504_after.png', unreal.Vector(*c[:3]), unreal.Vector(*c[3:]), 1.5, 50.0)
if '--keep' not in sys.argv:
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = [x for x in EAS.get_all_level_actors() if 'CW504' in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('preview cards removed:', len(gone))
