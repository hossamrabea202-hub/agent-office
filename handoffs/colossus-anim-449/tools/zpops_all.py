# Unreal (read-only): one-frame pops per clip. env Z_POPS = comma list relative to Zombie/, Z_LIMIT (default 12)
import unreal, os, math
R = '/Game/CastleDefender/Characters/Enemies/Zombie/'; lim = float(os.environ.get('Z_LIMIT', '12'))
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
for c in os.environ['Z_POPS'].split(','):
    A = unreal.load_asset(R + c.strip()); n = unreal.AnimationLibrary.get_num_frames(A); prev = None; hits = {}; worst = (0, None, 0)
    for f in range(n + 1):
        p = unreal.AnimPoseExtensions.get_anim_pose_at_frame(A, f, opts)
        names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(p)]
        cur = {b: unreal.AnimPoseExtensions.get_bone_pose(p, b, unreal.AnimPoseSpaces.LOCAL).rotation for b in names}
        if prev:
            for b in names:
                qa, qb = cur[b], prev[b]; d = abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w); ang = math.degrees(2*math.acos(min(1.0, d)))
                if ang > worst[0]: worst = (ang, b, f)
                if ang > lim: hits.setdefault(b, []).append((f, round(ang)))
        prev = cur
    print('POPS %-22s frames %3d | bones over %g deg/frame: %2d | worst %.0f deg %s @%d | %s' % (c.strip(), n, lim, len(hits), worst[0], worst[1], worst[2],
          ' '.join('%s:%s' % (b, v[:3]) for b, v in sorted(hits.items(), key=lambda kv: -max(x[1] for x in kv[1]))[:4])))
print('POPS DONE')
