# #530 tentacle style pass: install the clips (adjustedfilm, 2026-11-06). Editor idle, not in Play.
#   py ".../tentacle-style-530/style_install_ue.py" --dry-run    report only, changes nothing
#   py ".../tentacle-style-530/style_install_ue.py"              install
#   py ".../tentacle-style-530/style_install_ue.py" --restore    put every idle clip back exactly as before
# Install:
#   1. imports fbx/Tentacle_*.fbx as AS_Tentacle_Strike, _Hunt_A/B/C, _Wounded into Environment/Tentacles/Rig/Style530/
#   2. makes the montage AM_Tentacle_Strike (blend in 0.4, out 0.6); the strike only plays after wire_strike_ue.py --apply
#   3. backs up each idle clip into Rig/Style530_BAK/, then writes the hunting idles INTO them, so all placed tentacles and
#      their JellyShells change with no level edit and keep their own play rate and start position:
#      Ripple -> A, Ripple_Sway000/020 -> B, Ripple_Sway030/040 -> C, and Polish457_A/B/C -> A/B/C where those exist.
# AS_Tentacle_Wounded is imported only: nothing plays it yet.
import unreal, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args
R = '/Game/CastleDefender/Environment/Tentacles/Rig'; DST = R + '/Style530'; BAK = R + '/Style530_BAK'
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
CLIPS = {'STRIKE': 'AS_Tentacle_Strike', 'HUNT_A': 'AS_Tentacle_Hunt_A', 'HUNT_B': 'AS_Tentacle_Hunt_B', 'HUNT_C': 'AS_Tentacle_Hunt_C', 'WOUNDED': 'AS_Tentacle_Wounded'}
A0 = R + '/SK_CorruptedTentacle_01_Anim_'; P = R + '/Polish457/AS_Tentacle_Polish457_'
TARGETS = [(A0 + 'Ripple', 'A'), (A0 + 'Ripple_Sway000', 'B'), (A0 + 'Ripple_Sway020', 'B'), (A0 + 'Ripple_Sway030', 'C'), (A0 + 'Ripple_Sway040', 'C'),
           (P + 'A', 'A'), (P + 'B', 'B'), (P + 'C', 'C')]
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL
def say(*a): print('STYLE530', ' '.join(str(x) for x in a))
def copy_anim(src, dst):
    n = unreal.AnimationLibrary.get_num_frames(src)
    poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]
    bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
    c = dst.controller; c.open_bracket(unreal.Text('STYLE530 clips'))
    c.set_frame_rate(unreal.FrameRate(24, 1)); c.set_number_of_frames(unreal.FrameNumber(n))
    for b in bones:
        c.add_bone_curve(b)      # most old clips have no track on the frozen base bones: without one the write below is silently dropped
        ts = [unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC) for p in poses]
        c.set_bone_track_keys(b, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
    c.close_bracket(); return n
def check(a, b):
    n = min(unreal.AnimationLibrary.get_num_frames(a), unreal.AnimationLibrary.get_num_frames(b)); worst = 0.0
    for f in range(0, n + 1, max(1, n // 8)):
        pa = unreal.AnimPoseExtensions.get_anim_pose_at_frame(a, f, opts); pb = unreal.AnimPoseExtensions.get_anim_pose_at_frame(b, f, opts)
        for i in range(14):
            q1 = unreal.AnimPoseExtensions.get_bone_pose(pa, 'seg_%02d' % i, LOC).rotation; q2 = unreal.AnimPoseExtensions.get_bone_pose(pb, 'seg_%02d' % i, LOC).rotation
            worst = max(worst, math.degrees(2 * math.acos(min(1.0, abs(q1.x*q2.x + q1.y*q2.y + q1.z*q2.z + q1.w*q2.w)))))
    return round(worst, 4)
def bak_path(p): return BAK + '/' + p.rsplit('/', 1)[1]
say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'INSTALL'))
targets = [(p, v) for p, v in TARGETS if EAL.does_asset_exist(p)]
say('idle clips found', len(targets), [p.rsplit('/', 1)[1] for p, v in targets])

if RESTORE:
    for p, v in targets:
        b = bak_path(p)
        if not EAL.does_asset_exist(b): say('no backup for', p.rsplit('/', 1)[1], '(left as it is)'); continue
        if DRY: say('would restore', p.rsplit('/', 1)[1]); continue
        s, d = unreal.load_asset(b), unreal.load_asset(p); copy_anim(s, d); EAL.save_loaded_asset(d)
        say('restored', p.rsplit('/', 1)[1], 'worst vs backup deg', check(s, d))
    say('DONE restore'); raise SystemExit(0)

skel = unreal.load_asset(R + '/SK_CorruptedTentacle_01_Skeleton')
if not skel: raise SystemExit('STYLE530 skeleton missing')
missing = [k for k in CLIPS if not os.path.exists(os.path.join(HERE, 'fbx', 'Tentacle_%s.fbx' % k))]
if missing: raise SystemExit('STYLE530 missing FBX (git pull?): %s' % missing)
tasks = []
for k, nm in CLIPS.items():
    say('import', k, '->', DST + '/' + nm, '(replace)' if EAL.does_asset_exist(DST + '/' + nm) else '(new)')
    if DRY: continue
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for pk, pv in [('use_default_sample_rate', False), ('custom_sample_rate', 24)]:
        try: ad.set_editor_property(pk, pv)
        except Exception: pass
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', 'Tentacle_%s.fbx' % k); t.destination_path = DST; t.destination_name = nm
    t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; tasks.append(t)
if tasks:
    AT.import_asset_tasks(tasks)
    bad = [nm for nm in CLIPS.values() if not EAL.does_asset_exist(DST + '/' + nm)]
    if bad: raise SystemExit('STYLE530 import failed for %s; nothing else was changed' % bad)
    for nm in CLIPS.values():
        s = unreal.load_asset(DST + '/' + nm); s.set_editor_property('enable_root_motion', False); EAL.save_loaded_asset(s)
        say('imported', nm, 'frames', unreal.AnimationLibrary.get_num_frames(s), 'len', round(s.get_play_length(), 3))
mon = DST + '/AM_Tentacle_Strike'
if DRY: say('would make montage', mon, 'exists now:', EAL.does_asset_exist(mon))
elif not EAL.does_asset_exist(mon):
    f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', unreal.load_asset(DST + '/AS_Tentacle_Strike')); f.set_editor_property('target_skeleton', skel)
    m = AT.create_asset('AM_Tentacle_Strike', DST, unreal.AnimMontage, f)
    for k, v in (('blend_in', 0.4), ('blend_out', 0.6)):
        b = m.get_editor_property(k); b.set_editor_property('blend_time', v); m.set_editor_property(k, b)
    EAL.save_loaded_asset(m); say('montage', mon, round(m.get_play_length(), 3))
for p, v in targets:
    b = bak_path(p); nm = p.rsplit('/', 1)[1]
    if DRY: say('would back up and write', nm, '<- Hunt_' + v, '(backup exists)' if EAL.does_asset_exist(b) else ''); continue
    if not EAL.does_asset_exist(b):
        if not EAL.duplicate_asset(p, b): raise SystemExit('STYLE530 backup failed for ' + nm)
        EAL.save_asset(b, only_if_is_dirty=False)
    s, d = unreal.load_asset(DST + '/AS_Tentacle_Hunt_' + v), unreal.load_asset(p); copy_anim(s, d); EAL.save_loaded_asset(d)
    say('wrote', nm, '<- Hunt_' + v, 'worst deg', check(s, d), 'len', round(d.get_play_length(), 3))
say('DONE', 'dry-run' if DRY else 'install')
