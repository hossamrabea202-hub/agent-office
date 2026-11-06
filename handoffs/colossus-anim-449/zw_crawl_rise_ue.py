# Crawlers + spawn rise + stunned laying (#519 stage 5) - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06.
#   py ".../colossus-anim-449/zw_crawl_rise_ue.py" --dry-run    report; changes nothing
#   py ".../colossus-anim-449/zw_crawl_rise_ue.py"              install (about 25 s)
#   py ".../colossus-anim-449/zw_crawl_rise_ue.py" --restore    put the 4 clips back exactly
# Why (measured): the crawl loops slide (natural 50 cm/s vs MaxWalkSpeed 45) and pop; the spawn "rise" ZA_Burst_H is a
# 5-frame pop from the rest pose onto the ground followed by 85 motionless frames (played at rate 0.5 while the BP
# waits 5.4 s): the dead pause the owner rejected on #164. ZA_Laying_Idle_A (after a knock-down) pops 124 deg.
# What "install" does: imports 4 clips into Zombie/Anims_Walkers/, backs up the 4 game clips into Zombie/Anims_BAKZW/,
# writes the new motion INTO them (MAP). No Blueprint change: the same nodes play the same assets.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('ZC_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Characters/Enemies/Zombie'
ZW = R + '/Anims_Walkers'; BAK = R + '/Anims_BAKZW'
EAL = unreal.EditorAssetLibrary
CLIPS = ['ZW_Crawl_A', 'ZW_Crawl_B', 'ZW_Rise', 'ZW_Laying_Stunned']
MAP = {
    'AnimsPack/ZA_Belly_Crawling_A': 'ZW_Crawl_A',       # crawl loop (LoopCount 9999), hands matched to 45 cm/s
    'AnimsPack/ZA_Belly_Crawling_B': 'ZW_Crawl_B',       # the one-arm drag variant
    'AnimsPack/ZA_Burst_H': 'ZW_Rise',                   # the spawn rise: 90 frames, continuous heap -> standing (rate 0.5 in the BP = 6 s)
    'AnimsPack/ZA_Laying_Idle_A': 'ZW_Laying_Stunned',   # knocked down: stunned, a twitch, rolls onto the hands ready to rise
}
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('ZC519', s); log.append(s)
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL

def copy_anim(src, dst):
    n = unreal.AnimationLibrary.get_num_frames(src)
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    ctl = dst.controller
    ctl.open_bracket(unreal.Text('ZC519 crawl / rise'))
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
            EAL.remove_metadata_tag(dst, 'ZC519'); EAL.save_loaded_asset(dst)
        say('restored', nm)
    say('DONE restore'); raise SystemExit(0)

missing = [c for c in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('ZC519 missing FBX: %s (git pull?)' % missing)
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
    if bad: raise SystemExit('ZC519 import failed for %s - nothing else was changed' % bad)

report = {}
for d, c in MAP.items():
    dp = R + '/' + d; nm = d.split('/')[-1]
    if not EAL.does_asset_exist(dp): say('SKIP', d, 'not found'); continue
    if DRY:
        w = unreal.load_asset(dp); say('would back up %s (%d frames) -> Anims_BAKZW and write %s into it' % (nm, unreal.AnimationLibrary.get_num_frames(w), c)); continue
    if not EAL.does_asset_exist(BAK + '/' + nm):
        EAL.duplicate_asset(dp, BAK + '/' + nm); EAL.save_asset(BAK + '/' + nm, only_if_is_dirty=False)
    src = unreal.load_asset(ZW + '/' + c); dst = unreal.load_asset(dp)
    n = copy_anim(src, dst)
    EAL.set_metadata_tag(dst, 'ZC519', 'crawl / rise set: ' + c); EAL.save_loaded_asset(dst)
    report[nm] = {'from': c, 'frames': n, 'max_diff_deg': check(src, dst)}
    say(nm, '<-', c, json.dumps(report[nm]))
json.dump({'report': report, 'log': log}, open(os.path.join(HERE, 'crawl_rise_install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed; backups in ' + BAK)
