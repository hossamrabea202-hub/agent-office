import unreal, json
EAL = unreal.EditorAssetLibrary; KN = '/Game/CastleDefender/Characters/Knight'; out = {}
def chains(rigpath):
    rig = unreal.load_asset(rigpath); c = unreal.IKRigController.get_controller(rig); res = []
    for ch in c.get_retarget_chains():
        g = lambda k: str(ch.get_editor_property(k)) if True else ''
        try: res.append((g('chain_name'), g('start_bone'), g('end_bone')))
        except Exception as e: res.append(('ERR', repr(e)[:60], [x for x in dir(ch) if not x.startswith('_')][:12]))
    return res, str(c.get_retarget_root()), c.get_skeletal_mesh().get_path_name() if c.get_skeletal_mesh() else None
for p in [KN + '/Retarget/IK_ShadowKnight', '/Game/CastleDefender/Characters/Enemies/FleshBrute/IKR_Zombie_Src']:
    try: out[p.split('/')[-1]] = chains(p)
    except Exception as e: out[p.split('/')[-1]] = repr(e)[:100]
# bone names of both skeletons
for nm, anim in (('knight', '/Game/ShadowKight/Animations/Anim_ShadowKight'), ('knight2', '/Game/ShadowKight/Animations/ThirdPersonIdle'), ('zombie', '/Game/CastleDefender/Characters/Enemies/Zombie/AnimsPack/ZA_Idle_A')):
    a = unreal.load_asset(anim)
    if not a: out[nm + '_bones'] = 'no anim'; continue
    try:
        sk = a.get_editor_property('skeleton').get_name(); pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, unreal.AnimPoseEvaluationOptions())
        names = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(pose)]
        hts = {b: round(unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation.z, 1) for b in names if b in ('pelvis', 'spine_01', 'spine_03', 'neck_01', 'head', 'hand_l', 'foot_l', 'Hips', 'Spine2', 'Neck', 'Head', 'LeftHand', 'LeftFoot')}
        out[nm + '_bones'] = {'skeleton': sk, 'n': len(names), 'names': names[:80], 'heights': hts}
    except Exception as e: out[nm + '_bones'] = repr(e)[:120]
json.dump(out, open('C:/Users/hossam.rabea/ckw/ztools/probe_knight2.json', 'w'), indent=1); print('KPROBE2 OK')
