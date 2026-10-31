# Master only (UE 5.3, Output Log > Python), read-only: dumps the hero knight's reference pose so TGA can model the Yellow
# Eagle set (#367) in the right place for BPC_ObsidianSet-style rigid attach (each piece's offset from its bone is taken
# from where it sits in the knight mesh's ref pose). Bone names + transforms only: no mesh data, nothing licensed.
# Output: <repo>/handoffs/exports/master/knight_refpose.txt   (name, parent, local + component loc cm, quat xyzw)
import unreal, os
REPO = os.environ.get('AGENT_OFFICE_REPO', r'C:\agent-office')        # set to your agent-office checkout if different
reg = unreal.AssetRegistryHelpers.get_asset_registry()
skels = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Skeleton')) if 'shadowknight' in str(a.asset_name).lower()]
if not skels: raise SystemExit(unreal.log_error('knight_refpose: no Skeleton asset with "Shadowknight" in its name; tell TGA the hero skeleton path'))
skel = unreal.load_asset(str(skels[0].package_name))
pose = unreal.AnimPoseExtensions.get_reference_pose(skel)
out = ['# %s reference pose (UE cm, Z up, mesh component space): name\tparent\tlocal_loc\tlocal_quat\tworld_loc\tworld_quat' % skels[0].package_name]
for b in unreal.AnimPoseExtensions.get_bone_names(pose):
    loc = unreal.AnimPoseExtensions.get_ref_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)
    wld = unreal.AnimPoseExtensions.get_ref_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD)
    par = unreal.AnimPoseExtensions.get_parent_bone_name(pose, b) if hasattr(unreal.AnimPoseExtensions, 'get_parent_bone_name') else ''
    f = lambda t: '%.4f,%.4f,%.4f\t%.6f,%.6f,%.6f,%.6f' % (t.translation.x, t.translation.y, t.translation.z, t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)
    out.append('%s\t%s\t%s\t%s' % (b, par, f(loc), f(wld)))
# the hero's KnightMesh component transform inside BP_ThirdPersonCharacter, so pieces can be placed in actor space too
try:
    bp = unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
    cdo = unreal.get_default_object(bp.generated_class())
    for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
        t = c.get_relative_transform(); out.append('# component %s rel loc %s rot %s scale %s mesh %s' % (c.get_name(), t.translation, t.rotation.rotator(), t.scale3d, c.get_editor_property('skeletal_mesh')))
except Exception as e:
    out.append('# component transforms not read: %s' % e)
p = os.path.join(REPO, 'handoffs', 'exports', 'master', 'knight_refpose.txt')
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, 'w').write('\n'.join(out) + '\n')
unreal.log('knight_refpose: %d bones -> %s (commit + push it)' % (len(out) - 1, p))
