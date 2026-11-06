# Lab: rebuild RTG_Zombie_to_Knight properly (5.8), then batch-retarget clips onto the knight and export them as FBX.
import unreal, os, json
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
KN = '/Game/CastleDefender/Characters/Knight'; ZR = '/Game/CastleDefender/Characters/Enemies/FleshBrute/IKR_Zombie_Src'
ZW = '/Game/CastleDefender/Characters/Enemies/Zombie/Anims_Walkers'
OUT = 'C:/Users/hossam.rabea/ckw/ztools/fbx_knight'; os.makedirs(OUT, exist_ok=True)
log = []
def say(*a): s = ' '.join(str(x) for x in a); print('RT334', s); log.append(s)
# 1. the zombie source rig: add the chains the knight rig has (clavicles, neck/head split, fingers skipped)
zr = unreal.load_asset(ZR); zc = unreal.IKRigController.get_controller(zr)
have = [str(ch.get_editor_property('chain_name')) for ch in zc.get_retarget_chains()]
want = [('Spine', 'Spine', 'Spine2'), ('Neck', 'Neck', 'Neck'), ('Head', 'Head', 'Head'),
        ('LeftClavicle', 'LeftShoulder', 'LeftShoulder'), ('RightClavicle', 'RightShoulder', 'RightShoulder'),
        ('LeftArm', 'LeftArm', 'LeftHand'), ('RightArm', 'RightArm', 'RightHand'),
        ('LeftLeg', 'LeftUpLeg', 'LeftFoot'), ('RightLeg', 'RightUpLeg', 'RightFoot'),
        ('LeftThumb', 'LeftHandThumb1', 'LeftHandThumb3'), ('LeftIndex', 'LeftHandIndex1', 'LeftHandIndex3'), ('LeftMiddle', 'LeftHandMiddle1', 'LeftHandMiddle3'),
        ('LeftRing', 'LeftHandRing1', 'LeftHandRing3'), ('LeftPinky', 'LeftHandPinky1', 'LeftHandPinky3'),
        ('RightThumb', 'RightHandThumb1', 'RightHandThumb3'), ('RightIndex', 'RightHandIndex1', 'RightHandIndex3'), ('RightMiddle', 'RightHandMiddle1', 'RightHandMiddle3'),
        ('RightRing', 'RightHandRing1', 'RightHandRing3'), ('RightPinky', 'RightHandPinky1', 'RightHandPinky3')]
for nm, a, b in want:
    if nm in have: continue
    if nm == 'Head' and 'Head' in have: continue
    try: zc.add_retarget_chain(nm, a, b, ''); say('zombie rig: added chain', nm, a, '->', b)
    except Exception as e: say('zombie rig: chain', nm, 'ERR', str(e)[:80])
# the old 'Head' chain was Neck->Head on the zombie; keep it if Neck chain exists separately? list final
say('zombie chains:', [str(ch.get_editor_property('chain_name')) for ch in zc.get_retarget_chains()])
EAL.save_loaded_asset(zr)
# knight chains
kr = unreal.load_asset(KN + '/Retarget/IK_ShadowKnight'); kc = unreal.IKRigController.get_controller(kr)
say('knight chains:', [str(ch.get_editor_property('chain_name')) for ch in kc.get_retarget_chains()], 'root', str(kc.get_retarget_root()))
# 2. the retargeter
rtg = unreal.load_asset(KN + '/Retarget/RTG_Zombie_to_Knight'); rc = unreal.IKRetargeterController.get_controller(rtg)
S, T = unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET
rc.set_ik_rig(S, zr); rc.set_ik_rig(T, kr)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
for side in (S, T):
    try: rc.auto_align_all_bones(side); say('auto-aligned', 'source' if side == S else 'target')
    except Exception as e: say('auto_align', str(e)[:80])
mapping = {}
for ch in kc.get_retarget_chains():
    t = str(ch.get_editor_property('chain_name'))
    try: mapping[t] = str(rc.get_source_chain(t))
    except Exception as e: mapping[t] = 'ERR ' + str(e)[:40]
say('MAP', json.dumps(mapping))
# scale: retarget root = pelvis/Hips: let the retargeter scale translation (global settings)
try:
    gs = rc.get_global_settings(); say('global settings', [x for x in dir(gs) if not x.startswith('_')][:12])
except Exception as e: say('global settings', str(e)[:60])
EAL.save_loaded_asset(rtg)
# 3. batch retarget 3 clips onto the knight
src_mesh = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/SK_Zombie'); tgt_mesh = unreal.load_asset('/Game/ShadowKight/Mesh/ShadowknightUE_SK')
clips = [unreal.load_asset(ZW + '/' + c) for c in ('ZW_Walk_Shamble', 'ZW_Idle_Shamble', 'ZW_Attack_Claw')]
try:
    res = unreal.IKRetargetBatchOperation.duplicate_and_retarget([c for c in clips if c], src_mesh, tgt_mesh, rtg, '', 'KN_', True, True)
    say('retargeted', [str(r.get_name()) if hasattr(r, 'get_name') else str(r) for r in (res or [])])
except Exception as e: say('batch ERR', repr(e)[:160])
# 4. export the retargeted clips (next to the source) as FBX
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for a in reg.get_assets_by_path(ZW, recursive=False):
    n = str(a.asset_name)
    if n.startswith('KN_'):
        s = unreal.load_asset(str(a.package_name)); t = unreal.AssetExportTask(); t.object = s; t.filename = OUT + '/' + n + '.fbx'; t.automated = True; t.prompt = False; t.replace_identical = True
        o = unreal.FbxExportOption(); o.set_editor_property('export_preview_mesh', False); t.options = o
        say('export', n, unreal.Exporter.run_asset_export_task(t), 'skeleton', s.get_editor_property('skeleton').get_name(), 'frames', unreal.AnimationLibrary.get_num_frames(s))
json.dump(log, open('C:/Users/hossam.rabea/ckw/ztools/retarget_log.json', 'w'), indent=1); print('RT334 DONE')
