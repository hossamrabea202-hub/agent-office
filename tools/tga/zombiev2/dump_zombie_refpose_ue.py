# Master only (UE 5.3, Output Log > Python): dumps the SK_Zombie reference pose so TGA's v2 zombie bodies (#199) bind with
# the same bone positions/rotations and the existing zombie anims play on them unchanged. Writes bone names + transforms only.
# Output: <repo>/handoffs/exports/master/zombie_refpose.txt   (name, parent, local + world location cm, rotation quat xyzw)
import unreal, os
SK = '/Game/CastleDefender/Characters/Enemies/Zombie/SK_Zombie_Skeleton'
REPO = os.environ.get('AGENT_OFFICE_REPO', r'C:\agent-office')        # set to your agent-office checkout if different
skel = unreal.load_asset(SK)
pose = unreal.AnimPoseExtensions.get_reference_pose(skel)
out = ['# SK_Zombie reference pose (UE cm, Z up): name\tparent\tlocal_loc\tlocal_quat\tworld_loc\tworld_quat']
for b in unreal.AnimPoseExtensions.get_bone_names(pose):
    loc = unreal.AnimPoseExtensions.get_ref_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)
    wld = unreal.AnimPoseExtensions.get_ref_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD)
    par = unreal.AnimPoseExtensions.get_parent_bone_name(pose, b) if hasattr(unreal.AnimPoseExtensions, 'get_parent_bone_name') else ''
    f = lambda t: '%.4f,%.4f,%.4f\t%.6f,%.6f,%.6f,%.6f' % (t.translation.x, t.translation.y, t.translation.z, t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
    out.append('%s\t%s\t%s\t%s' % (b, par, f(loc), f(wld)))
p = os.path.join(REPO, 'handoffs', 'exports', 'master', 'zombie_refpose.txt')
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, 'w').write('\n'.join(out) + '\n')
unreal.log('zombie_refpose: %d bones -> %s' % (len(out) - 1, p))
