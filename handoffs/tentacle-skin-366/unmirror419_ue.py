# #419 tentacle bio-shield cut off / clipping (owner screenshot 2026-11-01 20:59, Env_CorruptedTentacle_5) (i5 core).
# Cause: JellyShellVS rotates the gel offset by the skinning rotation it estimates from the pre-skinned vs skinned normal.
# On a MIRRORED actor (scale X < 0) the engine flips the world normal, the estimate fails (cr < -0.95) and the gel offset
# is applied unrotated: on the bent trunk it shoots sideways into flat sheets that cut through the body and the ground
# (the shader's own comment: "or bent sections push the gel sideways into flat sheets"). Un-mirrored tentacles (_04,
# _05, Fog1) look right.
# Fix without touching the shared material: give every mirrored tentacle the same look with a positive scale.
#   S(-a, a, a) == Rz(180) * S(a, a, a) * MirrorY, and the spine bends almost only in local X/Z (|y| <= 308 local units),
#   so: scale (a, a, a), yaw + 180, and move the actor along its right axis by 2 * a * y_root (y_root = -307.7, the
#   spine root) so the root stays exactly where it was. Only the small sideways lean flips.
#   py ".../unmirror419_ue.py"            dry run: every tentacle actor, its transform, and the planned change
#   py ".../unmirror419_ue.py" --apply    apply + save the level (old transforms saved to unmirror419_backup.json)
#   py ".../unmirror419_ue.py" --revert   put the saved transforms back + save
import json, os, sys, unreal
A = sys.argv[1:]
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/tentacle-skin-366'
BK = HERE + '/unmirror419_backup.json'
Y_ROOT = -307.7
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = [a for a in EAS.get_all_level_actors() if 'tentacle' in a.get_actor_label().lower() and isinstance(a, unreal.SkeletalMeshActor)]
log = ['#419 unmirror' + (' --apply' if '--apply' in A else ' --revert' if '--revert' in A else ' (DRY RUN)')]
V = lambda v: '(%.0f, %.0f, %.0f)' % (v.x, v.y, v.z)
if '--revert' in A:
    bk = json.load(open(BK))
    for a in acts:
        t = bk.get(a.get_actor_label())
        if t:
            a.set_actor_location_and_rotation(unreal.Vector(*t['loc']), unreal.Rotator(*t['rot']), False, False)
            a.set_actor_scale3d(unreal.Vector(*t['scale'])); log.append('reverted ' + a.get_actor_label())
else:
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a in acts:
        s, l, r = a.get_actor_scale3d(), a.get_actor_location(), a.get_actor_rotation()
        if s.x >= 0:
            log.append('%-30s scale %s ok' % (a.get_actor_label(), V(s))); continue
        av = abs(s.x)
        nl = l + a.get_actor_right_vector() * (2.0 * av * Y_ROOT)
        nr = unreal.Rotator(r.roll, r.pitch, r.yaw + 180.0)
        log.append('%-30s scale %s yaw %.0f loc %s -> scale (%.2f, %.2f, %.2f) yaw %.0f loc %s' % (a.get_actor_label(), V(s), r.yaw, V(l), av, s.y, s.z, nr.yaw, V(nl)))
        if '--apply' in A:
            bk.setdefault(a.get_actor_label(), {'loc': [l.x, l.y, l.z], 'rot': [r.roll, r.pitch, r.yaw], 'scale': [s.x, s.y, s.z]})
            a.set_actor_location_and_rotation(nl, nr, False, False)
            a.set_actor_scale3d(unreal.Vector(av, s.y, s.z))
    if '--apply' in A:
        json.dump(bk, open(BK, 'w'), indent=1)
if '--dry-run' not in A and ('--apply' in A or '--revert' in A):
    log.append('level saved: %s' % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
print('\n'.join(log))
