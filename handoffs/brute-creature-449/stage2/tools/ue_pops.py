# Unreal (read-only): list bones that turn more than LIMIT deg in one frame. env FB_A = clip path, FB_LIMIT (default 12)
import unreal, os, math
A = unreal.load_asset(os.environ['FB_A']); lim = float(os.environ.get('FB_LIMIT', '12'))
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
n = unreal.AnimationLibrary.get_num_frames(A); prev = None; hits = {}
for f in range(n):
    p = unreal.AnimPoseExtensions.get_anim_pose_at_frame(A, f, opts)
    names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(p)]
    cur = {b: unreal.AnimPoseExtensions.get_bone_pose(p, b, unreal.AnimPoseSpaces.LOCAL).rotation for b in names}
    if prev:
        for b in names:
            qa, qb = cur[b], prev[b]; d = abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w); ang = math.degrees(2*math.acos(min(1.0, d)))
            if ang > lim: hits.setdefault(b, []).append((f, round(ang, 1)))
    prev = cur
for b, v in sorted(hits.items(), key=lambda kv: -max(x[1] for x in kv[1])):
    print('POP', b, v[:8])
print('POPS DONE', len(hits))
