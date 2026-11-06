# #449 Flesh Brute ("big mouth") creature animation layer - Unreal editor script (Python), adjustedfilm (Claude) 2026-11-06.
#   py ".../fb449_creature_ue.py" --dry-run     report only (strike frames, footfalls, jaw range, FK check), changes nothing
#   py ".../fb449_creature_ue.py"               backup every clip to Anims_BAK449/, then bake the layer INTO the FB_* clips
#                                                (so the blend space, montages and the 40 BP calls pick it up with no rewiring)
#   py ".../fb449_creature_ue.py" --restore     put the backups back (exact copies of the clips before #449)
#   options: --clips FB_A_Walk,FB_A_Attack  (subset)   --strength 0.8  (overall amount, 1 = as designed)   --no-loco
# Always bakes from the BACKUP when it exists, so running it twice never doubles the effect.
import unreal, sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib, fb2_layer as L; importlib.reload(L)

args = sys.argv[1:] + os.environ.get('FB449_ARGS', '').split()
DRY = '--dry-run' in args; RESTORE = '--restore' in args; NOLOCO = '--no-loco' in args
def opt(k, d):
    return args[args.index(k)+1] if k in args and args.index(k)+1 < len(args) else d
STRENGTH = float(opt('--strength', '1.0')); ONLY = [c for c in opt('--clips', '').split(',') if c]
R = '/Game/CastleDefender/Characters/Enemies/FleshBrute'
SRC = R + '/' + opt('--src', 'Anims'); BAK = SRC + '_BAK449'   # --src Anims_Creature runs the layer on the new clip set
BS = R + '/Anim/BS_FleshBrute_Locomotion'
ORIG = SRC.endswith('/Anims')   # the blend-space gait fix only belongs to the original clip set
EAL = unreal.EditorAssetLibrary
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('FB449', s); log.append(s)

reg = unreal.AssetRegistryHelpers.get_asset_registry()
names = sorted(str(a.asset_name) for a in reg.get_assets_by_path(SRC, recursive=False) if str(a.asset_class_path.asset_name) == 'AnimSequence')
if ONLY: names = [n for n in names if n in ONLY]
say('mode', 'DRY-RUN' if DRY else ('RESTORE' if RESTORE else 'APPLY'), 'clips', len(names), 'strength', STRENGTH)

if RESTORE:
    for n in names:
        b = BAK + '/' + n
        if not EAL.does_asset_exist(b): say('no backup for', n); continue
        if not DRY:
            src = unreal.load_asset(b); dst = unreal.load_asset(SRC + '/' + n)
            copy_from = src
            # copy every bone track back (same length/rate as the backup)
            nf = unreal.AnimationLibrary.get_num_frames(copy_from) + 1
            opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
            poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(copy_from, f, opts) for f in range(nf)]
            bones = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(poses[0])]
            ctl = dst.controller; ctl.open_bracket(unreal.Text('FB449 restore'))
            ctl.set_number_of_frames(unreal.FrameNumber(nf - 1))
            for bn in bones:
                ts = [unreal.AnimPoseExtensions.get_bone_pose(p, bn, unreal.AnimPoseSpaces.LOCAL) for p in poses]
                ctl.set_bone_track_keys(bn, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
            ctl.close_bracket()
            EAL.remove_metadata_tag(dst, 'FB449'); EAL.save_loaded_asset(dst)
        say('restored', n)
    raise SystemExit(0)

skel = unreal.load_asset(R + '/SK_FleshBrute_Skeleton')
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
LOC = unreal.AnimPoseSpaces.LOCAL; WLD = unreal.AnimPoseSpaces.WORLD
def tr(t): return [t.translation.x, t.translation.y, t.translation.z, t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w, t.scale3d.x, t.scale3d.y, t.scale3d.z]
rig = None; report = {}
for idx, n in enumerate(names):
    t0 = time.time()
    dst_path = SRC + '/' + n; bak_path = BAK + '/' + n
    have_bak = EAL.does_asset_exist(bak_path)
    if not DRY and not have_bak:
        EAL.duplicate_asset(dst_path, bak_path); EAL.save_asset(bak_path, only_if_is_dirty=False); have_bak = True
    src = unreal.load_asset(bak_path if have_bak else dst_path)
    nf = unreal.AnimationLibrary.get_num_frames(src) + 1   # KEYS (get_num_frames counts intervals)
    length = src.get_play_length(); dt = length/max(1, nf-1)
    p0 = unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, 0, opts)
    bones = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(p0)]
    if rig is None:
        par = []
        for b in bones:
            path = [str(x) for x in unreal.AnimationLibrary.find_bone_path_to_root(src, b)]
            par.append(bones.index(path[1]) if len(path) > 1 else -1)
        rig = L.Rig(bones, par)
        cal_src = unreal.load_asset(R + ('/Anims_BAK449' if EAL.does_asset_exist(R + '/Anims_BAK449/FB_ZA_Idle_A') else '/Anims') + '/FB_ZA_Idle_A')
        cp = unreal.AnimPoseExtensions.get_anim_pose_at_frame(cal_src, 0, opts)
        rig.calib = [tr(unreal.AnimPoseExtensions.get_bone_pose(cp, b, LOC)) for b in bones]
        L.head_lateral(L.fk(rig.calib, par), rig)   # fix the skull hinge axis on the upright idle pose
    cat = L.classify(n)
    if NOLOCO and cat == 'loco': say('skip (no-loco)', n); continue
    if EAL.get_metadata_tag(unreal.load_asset(dst_path), 'FB449S2') and '--force' not in args:
        say('skip', n, '(holds a stage-2 creature clip; its layer is already in it - use --force to override)'); continue
    def sample(times=None):
        out = []
        for f in range(nf):
            p = unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) if times is None else \
                unreal.AnimPoseExtensions.get_anim_pose_at_time(src, max(0.0, min(length, times[f])), opts)
            out.append([tr(unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC)) for b in bones])
        return out
    poses = sample()
    # FK check against Unreal's own component-space pose (frame 0)
    w = L.fk(poses[0], rig.parents); err = 0.0
    for b in ('head', 'hand_L', 'foot_R', 'jaw', 'belly_C'):
        u = unreal.AnimPoseExtensions.get_bone_pose(p0, b, WLD).translation
        err = max(err, L.vlen(L.vsub(w[rig.i(b)][0], (u.x, u.y, u.z))))
    if cat == 'attack' and not n.startswith('CR_'):   # retime around the strike (authored CR_ clips are already timed)
        world = [L.fk(p, rig.parents) for p in poses]
        sf = L.strike_frame(world, rig, nf, dt)
        poses = sample(L.retime_times(nf, dt, sf, 0.45*STRENGTH))
    new, rep = L.bake(n, poses, rig, dt, seed=idx+1.0, strength=STRENGTH)
    rep['fk_err_cm'] = round(err, 3); rep['secs'] = round(time.time()-t0, 1)
    report[n] = rep
    if not DRY:
        dst = unreal.load_asset(dst_path); ctl = dst.controller
        ctl.open_bracket(unreal.Text('FB449 creature layer'))
        ctl.set_number_of_frames(unreal.FrameNumber(nf - 1))   # same length as the source (nf = keys)
        for bi, bn in enumerate(bones):
            ctl.set_bone_track_keys(bn, [unreal.Vector(*new[f][bi][0:3]) for f in range(nf)],
                                    [unreal.Quat(*new[f][bi][3:7]) for f in range(nf)],
                                    [unreal.Vector(*new[f][bi][7:10]) for f in range(nf)])
        ctl.close_bracket()
        EAL.set_metadata_tag(dst, 'FB449', 'creature layer v1, strength %.2f' % STRENGTH)
        EAL.save_loaded_asset(dst)
        # read back: the clip must now hold the baked pose
        chk = unreal.AnimPoseExtensions.get_anim_pose_at_frame(dst, nf//2, opts)
        jq = unreal.AnimPoseExtensions.get_bone_pose(chk, 'jaw', LOC).rotation
        rep['readback_jaw_err'] = round(max(abs(a-b) for a, b in zip((jq.x, jq.y, jq.z, jq.w), new[nf//2][rig.i('jaw')][3:7])) if
                                        min(abs(a-b) for a, b in [(jq.w, new[nf//2][rig.i('jaw')][6])]) < 1 else -1, 5)
    say(n, json.dumps(rep))

# locomotion: the brute jogged (FB_A_Run, a 0.8 s human jog) at its walk speed 71.5. Place the run sample at the speed it
# covers when played at 0.8 (the -20 % limit), so the brute lumbers with longer, heavier strides instead of jogging.
bs = unreal.load_asset(BS)
smp = list(bs.get_editor_property('sample_data')) if ORIG else []; changed = False
for s in smp:
    a = s.get_editor_property('animation')
    if a and a.get_name() == 'FB_A_Run':
        v = s.get_editor_property('sample_value'); say('BS run sample', v.x, 'rate', s.get_editor_property('rate_scale'), '-> 79, 0.8')
        if not DRY and (abs(v.x-79.0) > 0.01 or abs(s.get_editor_property('rate_scale')-0.8) > 0.001):
            if not EAL.does_asset_exist(R + '/Anim/BS_FleshBrute_Locomotion_BAK449'):
                EAL.duplicate_asset(BS, R + '/Anim/BS_FleshBrute_Locomotion_BAK449'); EAL.save_asset(R + '/Anim/BS_FleshBrute_Locomotion_BAK449', only_if_is_dirty=False)
            s.set_editor_property('sample_value', unreal.Vector(79.0, v.y, v.z)); s.set_editor_property('rate_scale', 0.8); changed = True
if changed and not NOLOCO:
    bs.set_editor_property('sample_data', smp)
    try: bs.validate_sample_data()
    except Exception: pass
    EAL.save_loaded_asset(bs); say('BS saved')
json.dump({'report': report, 'log': log, 'bones': rig.bones if rig else [], 'parents': rig.parents if rig else []}, open(os.path.join(os.environ.get('FB449_OUT', HERE), 'fb449_report.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'applied; backups in ' + BAK)
