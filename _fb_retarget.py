# Flesh Brute retarget (Master, 2026-10-31, from TGA README #229/#273). UE 5.3 editor Python.
# Makes IKR_Zombie_Src (zombie, Mixamo names), IKR_FleshBrute, RTG_Zombie_to_FleshBrute, then duplicates + retargets every
# zombie AnimSequence and the zombie AnimBlueprint onto SK_FleshBrute (prefix FB_). Report: _fb_retarget.txt
import unreal, traceback
OUT = r'C:\Users\hossa\Documents\agent-office\_fb_retarget.txt'; L = []
def log(s):
    L.append(str(s)); open(OUT, 'w').write('\n'.join(L))
EAL = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
ar = unreal.AssetRegistryHelpers.get_asset_registry()
D = '/Game/CastleDefender/Characters/Enemies/FleshBrute'
FB = unreal.load_asset(D + '/SK_FleshBrute')
# ---- find the zombie mesh (has Mixamo 'Hips'), its skeleton, its anims + anim BP
def by_class(cls, path='/Game'):
    return [a for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', cls), True)]
zmesh = None
for a in by_class('SkeletalMesh'):
    n = str(a.asset_name)
    if n in ('SK_Zombie', 'SK_Zombie_Mesh') or (n.startswith('SK_Zombie') and 'V2' not in n):
        zmesh = unreal.load_asset(str(a.package_name)); break
if zmesh is None:
    for a in by_class('SkeletalMesh'):
        if 'zombie' in str(a.asset_name).lower() and 'v2' not in str(a.asset_name).lower(): zmesh = unreal.load_asset(str(a.package_name)); break
log('zombie mesh: %s' % (zmesh.get_path_name() if zmesh else None))
zskel = zmesh.get_editor_property('skeleton'); log('zombie skeleton: %s' % zskel.get_path_name())
bones = [str(zskel.get_editor_property('bone_tree')[i]) for i in range(0)] if False else []
anims = []
for a in by_class('AnimSequence'):
    try:
        s = str(a.get_tag_value('Skeleton'))
    except Exception: s = ''
    if zskel.get_path_name().split('.')[0] in s: anims.append(unreal.load_asset(str(a.package_name)))
abps = []
for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'AnimBlueprint'), True):
    try: s = str(a.get_tag_value('TargetSkeleton'))
    except Exception: s = ''
    if zskel.get_path_name().split('.')[0] in s: abps.append(unreal.load_asset(str(a.package_name)))
log('zombie anims: %d, anim BPs: %s' % (len(anims), [x.get_name() for x in abps]))

def make_rig(name, mesh, root, chains):
    p = D + '/' + name
    rig = unreal.load_asset(p) if EAL.does_asset_exist(p) else tools.create_asset(name, D, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    c = unreal.IKRigController.get_controller(rig)
    c.set_skeletal_mesh(mesh); c.set_retarget_root(root)
    for ch, s, e in chains:
        try: c.add_retarget_chain(ch, s, e, '')
        except Exception as ex: log('  chain %s: %s' % (ch, ex))
    EAL.save_asset(p); return rig
def pick(names, *opts):
    for o in opts:
        if o in names: return o
    return opts[0]
try:
    zn = set()
    try:
        ref = zmesh.get_editor_property('skeleton')
        for i in range(400):
            try: zn.add(str(unreal.SkeletalMeshEditorSubsystem.get_bone_name(zmesh, i)) if False else '')
            except Exception: break
    except Exception: pass
    MIX = [('Spine', 'Spine', 'Spine2'), ('Head', 'Neck', 'Head'),
           ('LeftArm', 'LeftArm', 'LeftHand'), ('RightArm', 'RightArm', 'RightHand'),
           ('LeftLeg', 'LeftUpLeg', 'LeftFoot'), ('RightLeg', 'RightUpLeg', 'RightFoot')]
    src = make_rig('IKR_Zombie_Src', zmesh, 'Hips', MIX)
    FBC = [('Spine', 'spine_01', 'spine_04'), ('Head', 'neck', 'head'),
           ('LeftArm', 'upper_arm_01.L', 'hand.L'), ('RightArm', 'upper_arm_01.R', 'hand.R'),
           ('LeftLeg', 'thigh_01.L', 'foot.L'), ('RightLeg', 'thigh_01.R', 'foot.R')]
    tgt = make_rig('IKR_FleshBrute', FB, 'root', FBC)
    log('IK rigs made')
    rp = D + '/RTG_Zombie_to_FleshBrute'
    rtg = unreal.load_asset(rp) if EAL.does_asset_exist(rp) else tools.create_asset('RTG_Zombie_to_FleshBrute', D, unreal.IKRetargeter, unreal.IKRetargetFactory())
    rc = unreal.IKRetargeterController.get_controller(rtg)
    rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt)
    try: rc.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    except Exception as ex: log('auto map: %s' % ex)
    EAL.save_asset(rp); log('retargeter made')
    todo = anims + abps
    out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(todo, zmesh, FB, rtg, '', '', 'FB_', '', True)
    log('retargeted %d assets -> %s' % (len(todo), [o.get_name() for o in out][:40] if out else out))
except BaseException:
    log(traceback.format_exc()[-1500:])
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); log('SAVED')
