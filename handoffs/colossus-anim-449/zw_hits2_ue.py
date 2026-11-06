# Directional hits (#519, for the i9's C++ directional flinch) - Unreal editor script (Python), adjustedfilm 2026-11-06.
#   py ".../colossus-anim-449/zw_hits2_ue.py" --dry-run | (install) | --restore
# Writes ZW_Hit_Back into ZA_Taking_Damage_B and ZW_Hit_SideRight into ZA_Taking_Damage_C (both held a copy of the front
# flinch since #521, so nothing is lost). Sets after this: FRONT = ZA_Taking_Damage_A, BACK = _B, LEFT = _F (struck on its
# left, twists right), RIGHT = _C (struck on its right, twists left), STAGGER = _D/_E, HEAVY = A_Hit. 20 frames each.
# Backups: the #521 backups in Zombie/Anims_BAKZW/ are the ORIGINALS and are kept; --restore puts the originals back.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('ZH_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Characters/Enemies/Zombie'; ZW = R + '/Anims_Walkers'; BAK = R + '/Anims_BAKZW'
EAL = unreal.EditorAssetLibrary
CLIPS = ['ZW_Hit_Back', 'ZW_Hit_SideRight']
MAP = {'AnimsPack/ZA_Taking_Damage_B': 'ZW_Hit_Back', 'AnimsPack/ZA_Taking_Damage_C': 'ZW_Hit_SideRight'}
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('ZH519', s); log.append(s)
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW); LOC = unreal.AnimPoseSpaces.LOCAL
def copy_anim(src, dst):
    n = unreal.AnimationLibrary.get_num_frames(src)
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    ctl = dst.controller; ctl.open_bracket(unreal.Text('ZH519 directional hits')); ctl.set_frame_rate(unreal.FrameRate(30, 1)); ctl.set_number_of_frames(unreal.FrameNumber(n))
    for b in bones:
        ts = [unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC) for p in poses]
        ctl.set_bone_track_keys(b, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
    ctl.close_bracket(); return n
def check(src, dst):
    import math
    n = min(unreal.AnimationLibrary.get_num_frames(src), unreal.AnimationLibrary.get_num_frames(dst)); worst = 0.0
    for f in range(0, n + 1, max(1, n // 6)):
        pa = unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts); pb = unreal.AnimPoseExtensions.get_anim_pose_at_frame(dst, f, opts)
        for b in ('Hips', 'Spine2', 'Head', 'LeftHand', 'RightFoot', 'LeftLeg'):
            qa = unreal.AnimPoseExtensions.get_bone_pose(pa, b, LOC).rotation; qb = unreal.AnimPoseExtensions.get_bone_pose(pb, b, LOC).rotation
            d = abs(qa.x*qb.x + qa.y*qb.y + qa.z*qb.z + qa.w*qb.w); worst = max(worst, math.degrees(2*math.acos(min(1.0, d))))
    return round(worst, 4)
say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'INSTALL'))
if RESTORE:
    for d in MAP:
        nm = d.split('/')[-1]; b = BAK + '/' + nm
        if not EAL.does_asset_exist(b): say('no backup for', nm); continue
        if not DRY:
            src = unreal.load_asset(b); dst = unreal.load_asset(R + '/' + d); copy_anim(src, dst); EAL.remove_metadata_tag(dst, 'ZH519'); EAL.save_loaded_asset(dst)
        say('restored', nm, '(the original)')
    say('DONE restore'); raise SystemExit(0)
missing = [c for c in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', c + '.fbx'))]
if missing: raise SystemExit('ZH519 missing FBX: %s (git pull?)' % missing)
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton'); tasks = []
for c in CLIPS:
    say('import', c, '(replace)' if EAL.does_asset_exist(ZW + '/' + c) else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 30)]:
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask(); t.set_editor_property('filename', os.path.join(HERE, 'fbx', c + '.fbx')); t.set_editor_property('destination_path', ZW)
    t.set_editor_property('destination_name', c); t.set_editor_property('automated', True); t.set_editor_property('replace_existing', True); t.set_editor_property('save', True); t.set_editor_property('options', ui); tasks.append(t)
if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    bad = [c for c in CLIPS if not EAL.does_asset_exist(ZW + '/' + c)]
    if bad: raise SystemExit('ZH519 import failed for %s - nothing else was changed' % bad)
report = {}
for d, c in MAP.items():
    dp = R + '/' + d; nm = d.split('/')[-1]
    if not EAL.does_asset_exist(dp): say('SKIP', d, 'not found'); continue
    if DRY: say('would write %s into %s (backup of the original stays in Anims_BAKZW)' % (c, nm)); continue
    if not EAL.does_asset_exist(BAK + '/' + nm):
        EAL.duplicate_asset(dp, BAK + '/' + nm); EAL.save_asset(BAK + '/' + nm, only_if_is_dirty=False)
    src = unreal.load_asset(ZW + '/' + c); dst = unreal.load_asset(dp); n = copy_anim(src, dst)
    EAL.set_metadata_tag(dst, 'ZH519', 'directional hit: ' + c); EAL.save_loaded_asset(dst)
    report[nm] = {'from': c, 'frames': n, 'max_diff_deg': check(src, dst)}; say(nm, '<-', c, json.dumps(report[nm]))
json.dump({'report': report, 'log': log}, open(os.path.join(HERE, 'hits2_install_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'installed')
