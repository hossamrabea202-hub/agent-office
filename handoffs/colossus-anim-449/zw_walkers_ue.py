# Walker animation set (#519 stage 3) - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06.
#   py ".../colossus-anim-449/zw_walkers_ue.py" --dry-run    report; changes nothing
#   py ".../colossus-anim-449/zw_walkers_ue.py"              install (about 40 s)
#   py ".../colossus-anim-449/zw_walkers_ue.py" --restore    put every touched clip back exactly
# What "install" does:
#   1. imports the 11 authored clips (fbx/ZW_*.fbx, SK_Zombie skeleton animation only) into Zombie/Anims_Walkers/
#   2. backs up the clips the game plays into Zombie/Anims_BAKZW/, then writes the new animation INTO them (MAP),
#      so the ABP blend space, the hit/death montages and every BP call play the new motion with no Blueprint change.
#      Lengths are kept (the attack strike frames too), so the BP damage timers still match.
#   3. the walk keeps AN_ColossusStomp notifies on its footfalls (ZA_Walk_A carried 4 of them).
# Run AFTER cz_colossus_ue.py (#520): that one writes A_Walk, this one leaves A_Walk alone.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('ZW_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Characters/Enemies/Zombie'
ZW = R + '/Anims_Walkers'; BAK = R + '/Anims_BAKZW'
EAL = unreal.EditorAssetLibrary
CLIPS = ['ZW_Idle_Shamble', 'ZW_Walk_Shamble', 'ZW_Run_Lurch', 'ZW_Sprint', 'ZW_Hit_Flinch', 'ZW_Hit_Stagger', 'ZW_Hit_Side',
         'ZW_Hit_Heavy', 'ZW_Death_Collapse', 'ZW_Attack_Claw', 'ZW_Attack_Bite']
MAP = {  # game clip (relative to Zombie/)  <-  new clip
    'AnimsPack/ZA_Idle_A': 'ZW_Idle_Shamble',          # blend space 0
    'AnimsPack/ZA_Walk_A': 'ZW_Walk_Shamble',          # blend space 113 (feet matched to 113 cm/s)
    'AnimsPack/ZA_Run_A': 'ZW_Run_Lurch',              # blend space 249
    'Anims/A_Run': 'ZW_Sprint',                        # blend space 350
    'AnimsPack/ZA_Taking_Damage_A': 'ZW_Hit_Flinch', 'AnimsPack/ZA_Taking_Damage_B': 'ZW_Hit_Flinch', 'AnimsPack/ZA_Taking_Damage_C': 'ZW_Hit_Flinch',
    'AnimsPack/ZA_Taking_Damage_D': 'ZW_Hit_Stagger', 'AnimsPack/ZA_Taking_Damage_E': 'ZW_Hit_Stagger',
    'AnimsPack/ZA_Taking_Damage_F': 'ZW_Hit_Side',
    'Anims/A_Hit': 'ZW_Hit_Heavy',
    'Anims/A_Death': 'ZW_Death_Collapse',              # montage AM_ZDeath_A_Death
    'Anims/A_Attack': 'ZW_Attack_Claw',                # same 79 frames, strike on frame 26
    'AnimsPack/ZA_Attack_D': 'ZW_Attack_Bite',         # same 60 frames, strike on frame 16
}
STOMP = R + '/AN_ColossusStomp'
STOMPS = {'AnimsPack/ZA_Walk_A': [0.0, 15/30.0]}       # the walk's footfalls (frames 1 and 16 of 31)
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('ZW519', s); log.append(s)
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL

def copy_anim(src, dst):
    n = unreal.AnimationLibrary.get_num_frames(src)
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    ctl = dst.controller
    ctl.open_bracket(unreal.Text('ZW519 walker set'))
    ctl.set_frame_rate(unreal.FrameRate(30, 1)); ctl.set_number_of_frames(unreal.FrameNumber(n))
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

def notifies(seq): return [str(n.get_editor_property('notify_name')) for n in unreal.AnimationLibrary.get_animation_notify_events(seq)]

say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'INSTALL'))

if RESTORE:
    for d in MAP:
        nm = d.split('/')[-1]; b = BAK + '/' + nm
        if not EAL.does_asset_exist(b): say('no backup for', nm); continue
        if not DRY:
            src = unreal.load_asset(b); dst = unreal.load_asset(R + '/' + d); copy_anim(src, dst)
            for x in set(notifies(dst)): unreal.AnimationLibrary.remove_animation_notify_events_by_name(dst, x)
            unreal.AnimationLibrary.copy_anim_notifies_from_sequence(src, dst, True)
            EAL.remove_metadata_tag(dst, 'ZW519'); EAL.save_loaded_asset(dst)
        say('restored', nm)
    say('DONE restore'); raise SystemExit(0)

missing = [c for c in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('ZW519 missing FBX: %s (git pull?)' % missing)
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton'); tasks = []
for c in CLIPS:
    say('import', c, '(replace)' if EAL.does_asset_exist(ZW + '/' + c) else '(new)')
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
    t.set_editor_property('filename', os.path.join(HERE, 'fbx', c + '.fbx')); t.set_editor_property('destination_path', ZW)
    t.set_editor_property('destination_name', c); t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True); t.set_editor_property('save', True); t.set_editor_property('options', ui)
    tasks.append(t)
if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    bad = [c for c in CLIPS if not EAL.does_asset_exist(ZW + '/' + c)]
    if bad: raise SystemExit('ZW519 import failed for %s - nothing else was changed' % bad)

report = {}
stomp_cls = unreal.load_asset(STOMP); stomp_cls = stomp_cls.generated_class() if stomp_cls else None
for d, c in MAP.items():
    dp = R + '/' + d; nm = d.split('/')[-1]
    if not EAL.does_asset_exist(dp): say('SKIP', d, 'not found'); continue
    if DRY:
        w = unreal.load_asset(dp)
        say('would back up %s (%d frames, notifies %s) -> Anims_BAKZW and write %s into it%s' % (nm, unreal.AnimationLibrary.get_num_frames(w), notifies(w), c,
            (', stomps at %s s' % STOMPS[d]) if d in STOMPS else '')); continue
    if not EAL.does_asset_exist(BAK + '/' + nm):
        EAL.duplicate_asset(dp, BAK + '/' + nm); EAL.save_asset(BAK + '/' + nm, only_if_is_dirty=False)
    src = unreal.load_asset(ZW + '/' + c); dst = unreal.load_asset(dp)
    n = copy_anim(src, dst)
    if d in STOMPS:
        for x in set(notifies(dst)): unreal.AnimationLibrary.remove_animation_notify_events_by_name(dst, x)
        if stomp_cls:
            if 'Stomp' not in [str(t) for t in unreal.AnimationLibrary.get_animation_notify_track_names(dst)]:
                unreal.AnimationLibrary.add_animation_notify_track(dst, 'Stomp')
            for t in STOMPS[d]: unreal.AnimationLibrary.add_animation_notify_event(dst, 'Stomp', t, stomp_cls)
    EAL.set_metadata_tag(dst, 'ZW519', 'walker set: ' + c); EAL.save_loaded_asset(dst)
    report[nm] = {'from': c, 'frames': n, 'max_diff_deg': check(src, dst), 'notifies': notifies(dst)}
    say(nm, '<-', c, json.dumps(report[nm]))
json.dump({'report': report, 'log': log}, open(os.path.join(HERE, 'walkers_install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed; backups in ' + BAK)
