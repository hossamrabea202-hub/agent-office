# Read-only: dump every FB_* clip's per-frame local bone transforms + component-space positions of key bones.
import unreal, json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dump')
os.makedirs(OUT, exist_ok=True)
ROOT = '/Game/CastleDefender/Characters/Enemies/FleshBrute/Anims'
KEYS = ['root', 'spine_01', 'spine_03', 'neck', 'head', 'jaw', 'tongue_01', 'tongue_03', 'belly_C', 'hand_L', 'hand_R', 'foot_L', 'foot_R', 'toe_L', 'toe_R']
reg = unreal.AssetRegistryHelpers.get_asset_registry()
L = unreal.AnimPoseSpaces.LOCAL
W = unreal.AnimPoseSpaces.WORLD
def tr(t):
    q = t.rotation; p = t.translation; s = t.scale3d
    return [round(p.x, 3), round(p.y, 3), round(p.z, 3), round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6), round(s.x, 4), round(s.y, 4), round(s.z, 4)]
for a in reg.get_assets_by_path(ROOT, recursive=False):
    if str(a.asset_class_path.asset_name) != 'AnimSequence':
        continue
    s = unreal.load_asset(str(a.package_name))
    n = unreal.AnimationLibrary.get_num_frames(s)
    opts = unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
    frames = []
    names = None
    for f in range(n):
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_frame(s, f, opts)
        if names is None:
            names = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(pose)]
        loc = [tr(unreal.AnimPoseExtensions.get_bone_pose(pose, b, L)) for b in names]
        wk = {k: tr(unreal.AnimPoseExtensions.get_bone_pose(pose, k, W))[:7] for k in KEYS}
        frames.append({'l': loc, 'w': wk})
    ref = unreal.AnimPoseExtensions.get_anim_pose_at_frame(s, 0, opts)
    refpose = None
    try:
        rp = unreal.AnimPoseExtensions.get_reference_pose(unreal.load_asset('/Game/CastleDefender/Characters/Enemies/FleshBrute/SK_FleshBrute_Skeleton'))
        refpose = [tr(unreal.AnimPoseExtensions.get_ref_bone_pose(rp, b, L)) for b in names]
    except Exception as e:
        refpose = repr(e)
    nm = str(a.asset_name)
    json.dump({'name': nm, 'frames_n': n, 'len': s.get_play_length(), 'bones': names, 'frames': frames, 'ref': refpose,
               'root_motion': s.get_editor_property('enable_root_motion')}, open(os.path.join(OUT, nm + '.json'), 'w'))
    print('DUMP', nm, n)
print('DUMP OK')
