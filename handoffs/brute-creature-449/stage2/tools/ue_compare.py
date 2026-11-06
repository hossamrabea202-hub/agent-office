# Unreal (read-only): compare two clips bone by bone (local space). env FB_A, FB_B = asset paths.
import unreal, os, math
A = unreal.load_asset(os.environ['FB_A']); B = unreal.load_asset(os.environ['FB_B'])
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
na = unreal.AnimationLibrary.get_num_frames(A); nb = unreal.AnimationLibrary.get_num_frames(B)
print('CMP frames', na, nb, 'len', A.get_play_length(), B.get_play_length())
L = unreal.AnimPoseSpaces.LOCAL; W = unreal.AnimPoseSpaces.WORLD
worst = (0, None, None); wpos = (0, None, None); wcomp = (0, None, None)
for f in range(0, min(na, nb), max(1, min(na, nb)//12)):
    pa = unreal.AnimPoseExtensions.get_anim_pose_at_frame(A, f, opts); pb = unreal.AnimPoseExtensions.get_anim_pose_at_frame(B, f, opts)
    for b in [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pa)]:
        ta = unreal.AnimPoseExtensions.get_bone_pose(pa, b, L); tb = unreal.AnimPoseExtensions.get_bone_pose(pb, b, L)
        qa, qb = ta.rotation, tb.rotation
        d = abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w); ang = math.degrees(2*math.acos(min(1.0, d)))
        if ang > worst[0]: worst = (ang, b, f)
        dp = (ta.translation - tb.translation).length()
        if dp > wpos[0]: wpos = (dp, b, f)
        ca = unreal.AnimPoseExtensions.get_bone_pose(pa, b, W).translation; cb = unreal.AnimPoseExtensions.get_bone_pose(pb, b, W).translation
        dc = (ca - cb).length()
        if dc > wcomp[0]: wcomp = (dc, b, f)
print('CMP worst local rot deg', worst, 'worst local pos cm', wpos, 'worst component pos cm', wcomp)
