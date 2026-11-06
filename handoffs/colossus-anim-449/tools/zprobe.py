# Read-only probe of the zombie clips + blend space (scratch lab zlab). Writes probe_z.json next to this script.
import unreal, json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probe_z.json')
ROOT = '/Game/CastleDefender/Characters/Enemies/Zombie'
res = {'seqs': {}, 'bones': [], 'errors': [], 'all': []}
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_path(ROOT, recursive=True)
for a in assets:
    res['all'].append('%s %s' % (a.asset_class_path.asset_name, a.package_name))
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
first = None
for a in assets:
    if str(a.asset_class_path.asset_name) != 'AnimSequence': continue
    p = str(a.package_name); s = unreal.load_asset(p); d = {}
    try:
        d['len'] = s.get_play_length(); d['frames'] = unreal.AnimationLibrary.get_num_frames(s)
        d['ntracks'] = len(unreal.AnimationLibrary.get_animation_track_names(s))
        d['notifies'] = []
        for n in unreal.AnimationLibrary.get_animation_notify_events(s):
            try:
                nm = str(n.get_editor_property('notify_name'))
                nn = n.get_editor_property('notify'); cls = type(nn).__name__ if nn else None
                d['notifies'].append([nm, cls, round(unreal.AnimationLibrary.get_animation_notify_event_trigger_time(n), 3)])
            except Exception as e: d['notifies'].append(repr(e))
        d['root_motion'] = s.get_editor_property('enable_root_motion')
        d['skeleton'] = str(s.get_editor_property('skeleton').get_name())
        # pelvis + foot travel: root/hips position at first and last frame (in-place check), and hip height
        pose0 = unreal.AnimPoseExtensions.get_anim_pose_at_frame(s, 0, opts)
        names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pose0)]
        if first is None: first = names; res['bones'] = names
        for b in ('Hips', 'LeftFoot', 'RightFoot', 'Head'):
            if b in names:
                t0 = unreal.AnimPoseExtensions.get_bone_pose(pose0, b, unreal.AnimPoseSpaces.WORLD).translation
                d['p0_' + b] = [round(t0.x, 1), round(t0.y, 1), round(t0.z, 1)]
    except Exception as e: d['err'] = repr(e)
    res['seqs'][p.replace(ROOT + '/', '')] = d
try:
    bs = unreal.load_asset(ROOT + '/Anim/BS_Zombie_Locomotion')
    smp = bs.get_editor_property('sample_data')
    res['bs_samples'] = [[str(x.get_editor_property('animation').get_name()) if x.get_editor_property('animation') else None,
                          x.get_editor_property('sample_value').x, x.get_editor_property('rate_scale')] for x in smp]
    prm = bs.get_editor_property('blend_parameters')
    res['bs_axis'] = [[str(x.get_editor_property('display_name')), x.get_editor_property('min'), x.get_editor_property('max')] for x in prm]
except Exception as e: res['errors'].append('bs: %r' % e)
try:
    sk = unreal.load_asset(ROOT + '/SK_Zombie'); res['mesh_bounds'] = str(sk.get_bounds().box_extent)
    res['ref_skel_bones'] = len(res['bones'])
except Exception as e: res['errors'].append('sk: %r' % e)
json.dump(res, open(OUT, 'w'), indent=1); print('PROBE OK', OUT)
