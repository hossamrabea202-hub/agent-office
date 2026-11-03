# #457 (i5): round-trip check, no rendering. Old vs new clip, every bone, 5 times: bone translation must match (same rig)
# and the rotation difference must stay in the animation's range (a few degrees), not an axis flip (90/180 deg).
import unreal, math
R = '/Game/CastleDefender/Environment/Tentacles/Rig/'
old = unreal.load_asset(R + 'SK_CorruptedTentacle_01_Anim_Ripple_Sway030')
AL = unreal.AnimationLibrary
bones = [str(n) for n in AL.get_animation_track_names(old)]
for v in 'ABC':
    new = unreal.load_asset(R + 'Polish457/AS_Tentacle_Polish457_' + v)
    worst_t = worst_r = 0.0
    for t in (0.0, 5.0, 12.5, 25.0, 39.9):
        for b in bones:
            po = AL.get_bone_pose_for_time(old, b, t, False); pn = AL.get_bone_pose_for_time(new, b, t, False)
            worst_t = max(worst_t, (po.translation - pn.translation).length())
            qo, qn = po.rotation, pn.rotation
            d = abs(qo.x * qn.x + qo.y * qn.y + qo.z * qn.z + qo.w * qn.w)
            worst_r = max(worst_r, math.degrees(2 * math.acos(min(1.0, d))))
    print('CHECK %s bones %d  max translation diff %.3f cm  max rotation diff %.1f deg' % (v, len(bones), worst_t, worst_r))
