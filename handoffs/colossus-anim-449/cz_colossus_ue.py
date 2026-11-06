# Colossus animation set - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06. Owner: "enhance the zombie
# animations, specially the colossals" (the Stranger Things quality bar from #449).
#   py ".../colossus-anim-449/cz_colossus_ue.py" --dry-run    report what it would do; changes nothing
#   py ".../colossus-anim-449/cz_colossus_ue.py"              install (about 20 s)
#   py ".../colossus-anim-449/cz_colossus_ue.py" --restore    put A_Walk back exactly as before
# What "install" does:
#   1. imports the 3 authored clips (fbx/CZ_*.fbx, SK_Zombie skeleton animation only) into Zombie/Anims_Colossus/
#   2. backs up Zombie/Anims/A_Walk (only BP_ZombieWallBreaker plays it) into Zombie/Anims_BAKCZ/, then writes
#      CZ_Walk_Colossus INTO it, and puts the two AN_ColossusStomp notifies on the new footfalls (0.0 s and 1.3 s).
#      So the breaker walks the new giant walk with no Blueprint change.
#   CZ_Attack_Smash and CZ_Death_Colossus are imported only: the smash is a one-pin swap in BP_ZombieWallBreaker
#   (SM_Anim: NewAnimToPlay A_Attack -> CZ_Attack_Smash; same 79 frames, blow on frame 26, so SM_D1/SM_D2 keep their
#   timing); the death needs the wiring paste (waits for export #518). See README.md.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('CZ_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Characters/Enemies/Zombie'
CZ = R + '/Anims_Colossus'; BAK = R + '/Anims_BAKCZ'
WALK = R + '/Anims/A_Walk'
EAL = unreal.EditorAssetLibrary
CLIPS = ['CZ_Walk_Colossus', 'CZ_Attack_Smash', 'CZ_Death_Colossus', 'CZ_Idle_Loom', 'CZ_Roar']   # the last two: paste 2 (#519 stage 6)
STOMP = R + '/AN_ColossusStomp'
STOMP_TIMES = [0.0, 39/30.0]       # the footfalls of CZ_Walk_Colossus (frames 1 and 40 of 79; 2.6 s loop)
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('CZ449', s); log.append(s)
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL

def copy_anim(src, dst):
    """make dst hold exactly src's bone animation (length, frame count, every bone track). get_num_frames = INTERVALS."""
    n = unreal.AnimationLibrary.get_num_frames(src)
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    ctl = dst.controller
    ctl.open_bracket(unreal.Text('CZ449 colossus set'))
    ctl.set_frame_rate(unreal.FrameRate(30, 1))
    ctl.set_number_of_frames(unreal.FrameNumber(n))
    for b in bones:
        ts = [unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC) for p in poses]
        ctl.set_bone_track_keys(b, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
    ctl.close_bracket()
    return n

def check(src, dst):
    import math
    n = min(unreal.AnimationLibrary.get_num_frames(src), unreal.AnimationLibrary.get_num_frames(dst)); worst = 0.0
    for f in range(0, n + 1, max(1, n // 6)):
        pa = unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts); pb = unreal.AnimPoseExtensions.get_anim_pose_at_frame(dst, f, opts)
        for b in ('Hips', 'Spine2', 'Head', 'LeftHand', 'RightFoot', 'LeftLeg'):
            qa = unreal.AnimPoseExtensions.get_bone_pose(pa, b, LOC).rotation; qb = unreal.AnimPoseExtensions.get_bone_pose(pb, b, LOC).rotation
            d = abs(qa.x*qb.x + qa.y*qb.y + qa.z*qb.z + qa.w*qb.w); worst = max(worst, math.degrees(2*math.acos(min(1.0, d))))
    return round(worst, 4)

def notifies(seq):
    return [str(n.get_editor_property('notify_name')) for n in unreal.AnimationLibrary.get_animation_notify_events(seq)]

say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'INSTALL'))

if RESTORE:
    b = BAK + '/A_Walk'
    if not EAL.does_asset_exist(b): say('no backup, nothing to restore'); raise SystemExit(0)
    if not DRY:
        src = unreal.load_asset(b); dst = unreal.load_asset(WALK); copy_anim(src, dst)
        # notifies back: clear ours, copy the backup's
        unreal.AnimationLibrary.remove_animation_notify_events_by_track(dst, 'Stomp')
        try: unreal.AnimationLibrary.remove_animation_notify_track(dst, 'Stomp')
        except Exception as e: say('track', e)
        unreal.AnimationLibrary.copy_anim_notifies_from_sequence(src, dst, True)
        EAL.remove_metadata_tag(dst, 'CZ449'); EAL.save_loaded_asset(dst)
    say('restored A_Walk', '(notifies: %s)' % notifies(unreal.load_asset(WALK)))
    say('DONE restore'); raise SystemExit(0)

# 1. import
missing = [c for c in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('CZ449 missing FBX: %s (git pull?)' % missing)
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton')
tasks = []
for c in CLIPS:
    say('import', c, '(replace)' if EAL.does_asset_exist(CZ + '/' + c) else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data')
    ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 30)]:
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(HERE, 'fbx', c + '.fbx')); t.set_editor_property('destination_path', CZ)
    t.set_editor_property('destination_name', c); t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True); t.set_editor_property('save', True); t.set_editor_property('options', ui)
    tasks.append(t)
if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    bad = [c for c in CLIPS if not EAL.does_asset_exist(CZ + '/' + c)]
    if bad: raise SystemExit('CZ449 import failed for %s - nothing else was changed' % bad)
    for c in CLIPS:
        s = unreal.load_asset(CZ + '/' + c); say('imported', c, 'frames', unreal.AnimationLibrary.get_num_frames(s), 'len', round(s.get_play_length(), 3))

# 2. A_Walk <- CZ_Walk_Colossus (+ stomp notifies)
report = {}
if not EAL.does_asset_exist(WALK): say('SKIP A_Walk not found')
elif DRY:
    w = unreal.load_asset(WALK)
    say('would back up A_Walk (%d frames, notifies %s) -> Anims_BAKCZ and write CZ_Walk_Colossus into it, stomps at %s s' % (
        unreal.AnimationLibrary.get_num_frames(w), notifies(w), STOMP_TIMES))
else:
    if not EAL.does_asset_exist(BAK + '/A_Walk'):
        EAL.duplicate_asset(WALK, BAK + '/A_Walk'); EAL.save_asset(BAK + '/A_Walk', only_if_is_dirty=False)
    src = unreal.load_asset(CZ + '/CZ_Walk_Colossus'); dst = unreal.load_asset(WALK)
    n = copy_anim(src, dst)
    # notifies: drop the old stomps (they sat on the human walk's footfalls), add ours on a 'Stomp' track
    for nm in set(notifies(dst)): unreal.AnimationLibrary.remove_animation_notify_events_by_name(dst, nm)
    stomp_cls = unreal.load_asset(STOMP)
    cls = stomp_cls.generated_class() if stomp_cls else None
    if cls:
        if 'Stomp' not in [str(t) for t in unreal.AnimationLibrary.get_animation_notify_track_names(dst)]:
            unreal.AnimationLibrary.add_animation_notify_track(dst, 'Stomp')
        for t in STOMP_TIMES: unreal.AnimationLibrary.add_animation_notify_event(dst, 'Stomp', t, cls)
    else: say('WARNING AN_ColossusStomp not found: no stomp notifies added')
    EAL.set_metadata_tag(dst, 'CZ449', 'colossus walk: CZ_Walk_Colossus'); EAL.save_loaded_asset(dst)
    report['A_Walk'] = {'from': 'CZ_Walk_Colossus', 'frames': n, 'max_diff_deg': check(src, dst), 'notifies': notifies(dst)}
    say('A_Walk <- CZ_Walk_Colossus', json.dumps(report['A_Walk']))

json.dump({'report': report, 'log': log}, open(os.path.join(os.environ.get('CZ_OUT', HERE), 'install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed; backup in ' + BAK)
say('NEXT (Master): the breaker paste (README step 4): add GiantDead (bool), merge manifest_cz519.json on a fresh EventGraph export (or paste merged_cz519.t3d), Refresh All Nodes, compile, save. It sets the anim rate to 1.0, swaps the smash to CZ_Attack_Smash and plays CZ_Death_Colossus on death.')
