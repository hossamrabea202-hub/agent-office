# #449 stage 2: install the Flesh Brute's NEW creature clip set - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06.
#   py ".../stage2/fb449_stage2_ue.py" --dry-run     report what it would import / write / change; changes nothing
#   py ".../stage2/fb449_stage2_ue.py"               install (about 30 s)
#   py ".../stage2/fb449_stage2_ue.py" --restore     put every touched clip + the blend space back exactly as before stage 2
# What "install" does:
#   1. imports the 11 authored clips (fbx/CR_*.fbx, skeleton animation only) into FleshBrute/Anims_Creature/
#   2. runs the #449 creature layer on them (../fb449_creature_ue.py --src Anims_Creature: jaw, tongue, flesh, heft)
#   3. backs up the FB_* clips it replaces into FleshBrute/Anims_BAK449S2/, then writes the new animation INTO them,
#      so all 40 BP calls, the montages and the blend space play the new motion with no Blueprint change (MAP below)
#   4. blend space BS_FleshBrute_Locomotion (backup BS_..._BAK449S2): idle 0, heavy walk at the walk speed 71.5,
#      charge at 170 (axis max raised to 180)
# CR_Roar_Threat and CR_Death_Side are imported but not wired: they need BP changes (see README, request filed).
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('FB449S2_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Characters/Enemies/FleshBrute'
CR = R + '/Anims_Creature'; DST = R + '/Anims'; BAK = R + '/Anims_BAK449S2'
BS = R + '/Anim/BS_FleshBrute_Locomotion'; BS_BAK = R + '/Anim/BS_FleshBrute_Locomotion_BAK449S2'
EAL = unreal.EditorAssetLibrary
CLIPS = ['CR_Idle_Hunt', 'CR_Walk_Heavy', 'CR_Charge', 'CR_Roar_Threat', 'CR_Attack_Slam', 'CR_Attack_Swipe',
         'CR_Hit_Front', 'CR_Hit_Left', 'CR_Hit_Right', 'CR_Death_Forward', 'CR_Death_Side']
MAP = {  # existing clip the BP / blend space plays  <-  new creature clip
    'FB_ZA_Idle_A': 'CR_Idle_Hunt', 'FB_A_Walk': 'CR_Walk_Heavy', 'FB_A_Run': 'CR_Charge',
    'FB_A_Attack': 'CR_Attack_Slam',            # same length, hit at frame 26 (BP damage timing kept)
    'FB_ZA_Attack_D': 'CR_Attack_Swipe',        # same length, hit at frame 14-15
    'FB_A_Hit': 'CR_Hit_Front',
    'FB_ZA_Taking_Damage_A': 'CR_Hit_Front', 'FB_ZA_Taking_Damage_B': 'CR_Hit_Left', 'FB_ZA_Taking_Damage_C': 'CR_Hit_Right',
    'FB_ZA_Taking_Damage_D': 'CR_Hit_Front', 'FB_ZA_Taking_Damage_E': 'CR_Hit_Left', 'FB_ZA_Taking_Damage_F': 'CR_Hit_Right',
    'FB_A_Death': 'CR_Death_Forward',
}
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('FB449S2', s); log.append(s)
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL

def copy_anim(src, dst):
    """make dst hold exactly src's bone animation (length, frame count, every bone track)."""
    n = unreal.AnimationLibrary.get_num_frames(src)          # frame INTERVALS; the clip has n + 1 keys
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    ctl = dst.controller
    ctl.open_bracket(unreal.Text('FB449 stage 2'))
    ctl.set_frame_rate(unreal.FrameRate(30, 1))
    ctl.set_number_of_frames(unreal.FrameNumber(n))
    for b in bones:
        ts = [unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC) for p in poses]
        ctl.set_bone_track_keys(b, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
    ctl.close_bracket()
    return n

def check(src, dst):
    """worst local rotation difference (deg) between the two clips on a few frames."""
    import math
    n = min(unreal.AnimationLibrary.get_num_frames(src), unreal.AnimationLibrary.get_num_frames(dst)); worst = 0.0
    for f in range(0, n, max(1, n // 6)):
        pa = unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts); pb = unreal.AnimPoseExtensions.get_anim_pose_at_frame(dst, f, opts)
        for b in ('spine_01', 'head', 'jaw', 'hand_L', 'foot_R', 'belly_C'):
            qa = unreal.AnimPoseExtensions.get_bone_pose(pa, b, LOC).rotation; qb = unreal.AnimPoseExtensions.get_bone_pose(pb, b, LOC).rotation
            d = abs(qa.x*qb.x + qa.y*qb.y + qa.z*qb.z + qa.w*qb.w); worst = max(worst, math.degrees(2*math.acos(min(1.0, d))))
    return round(worst, 4)

say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'INSTALL'))

if RESTORE:
    for d in MAP:
        b = BAK + '/' + d
        if not EAL.does_asset_exist(b): say('no backup for', d); continue
        if not DRY:
            dst = unreal.load_asset(DST + '/' + d); copy_anim(unreal.load_asset(b), dst)
            EAL.remove_metadata_tag(dst, 'FB449S2'); EAL.save_loaded_asset(dst)
        say('restored', d)
    if EAL.does_asset_exist(BS_BAK):
        if not DRY:
            src = unreal.load_asset(BS_BAK); dst = unreal.load_asset(BS)
            dst.set_editor_property('sample_data', src.get_editor_property('sample_data'))
            dst.set_editor_property('blend_parameters', src.get_editor_property('blend_parameters'))
            EAL.save_loaded_asset(dst)
        say('restored blend space')
    say('DONE restore'); raise SystemExit(0)

# 1. import
missing = [c for c in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('FB449S2 missing FBX: %s (git pull?)' % missing)
tasks = []
skel = unreal.load_asset(R + '/SK_FleshBrute_Skeleton')
for c in CLIPS:
    exists = EAL.does_asset_exist(CR + '/' + c)
    say('import', c, '(replace)' if exists else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data')
    ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(HERE, 'fbx', c + '.fbx')); t.set_editor_property('destination_path', CR)
    t.set_editor_property('destination_name', c); t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True); t.set_editor_property('save', True); t.set_editor_property('options', ui)
    tasks.append(t)
if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    bad = [c for c in CLIPS if not EAL.does_asset_exist(CR + '/' + c)]
    if bad: raise SystemExit('FB449S2 import failed for %s - nothing else was changed' % bad)

# 2. the creature layer on the new clips (fresh: bake from the just-imported clips)
if not DRY:
    for c in CLIPS:
        if EAL.does_asset_exist(CR + '_BAK449/' + c): EAL.delete_asset(CR + '_BAK449/' + c)
    sys.argv = [sys.argv[0], '--src', 'Anims_Creature', '--clips', ','.join(CLIPS)]
    os.environ['FB449_ARGS'] = ''
    layer = os.path.join(os.path.dirname(HERE), 'fb449_creature_ue.py')
    exec(compile(open(layer).read(), layer, 'exec'), {'__file__': layer, '__name__': '__main__'})
    say('layer applied to', len(CLIPS), 'clips')
else:
    say('layer: would run ../fb449_creature_ue.py --src Anims_Creature on', len(CLIPS), 'clips')

# 3. write into the clips the game plays (backup first)
report = {}
for d, c in MAP.items():
    dp = DST + '/' + d
    if not EAL.does_asset_exist(dp): say('SKIP', d, 'not found'); continue
    if DRY: say('would back up', d, '-> Anims_BAK449S2 and write', c, 'into it'); continue
    if not EAL.does_asset_exist(BAK + '/' + d):
        EAL.duplicate_asset(dp, BAK + '/' + d); EAL.save_asset(BAK + '/' + d, only_if_is_dirty=False)
    src = unreal.load_asset(CR + '/' + c); dst = unreal.load_asset(dp)
    n = copy_anim(src, dst)
    EAL.set_metadata_tag(dst, 'FB449S2', 'creature clip set: ' + c); EAL.save_loaded_asset(dst)
    report[d] = {'from': c, 'frames': n, 'max_diff_deg': check(src, dst)}
    say(d, '<-', c, json.dumps(report[d]))

# 4. blend space
bs = unreal.load_asset(BS)
smp = list(bs.get_editor_property('sample_data'))
want = {'FB_ZA_Idle_A': 0.0, 'FB_A_Walk': 71.5, 'FB_A_Run': 170.0}
for s in smp:
    a = s.get_editor_property('animation'); nm = a.get_name() if a else None
    if nm in want:
        v = s.get_editor_property('sample_value')
        say('BS', nm, v.x, 'rate', round(s.get_editor_property('rate_scale'), 2), '->', want[nm], 'rate 1.0')
        if not DRY:
            s.set_editor_property('sample_value', unreal.Vector(want[nm], v.y, v.z)); s.set_editor_property('rate_scale', 1.0)
if not DRY:
    if not EAL.does_asset_exist(BS_BAK):
        EAL.duplicate_asset(BS, BS_BAK); EAL.save_asset(BS_BAK, only_if_is_dirty=False)
    params = list(bs.get_editor_property('blend_parameters')); params[0].set_editor_property('max', 180.0)
    bs.set_editor_property('blend_parameters', params)
    bs.set_editor_property('sample_data', smp)
    EAL.save_loaded_asset(bs); say('BS saved (axis max 180)')
json.dump({'report': report, 'log': log}, open(os.path.join(os.environ.get('FB449_OUT', HERE), 'stage2_install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed; backups in ' + BAK + ' and ' + BS_BAK)
