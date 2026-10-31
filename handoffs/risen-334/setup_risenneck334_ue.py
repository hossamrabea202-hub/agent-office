# #334 part A: the risen soldier's "very long silly neck" (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
# Cause: BP_ZombieRisen (#41) makes the knight body follow the hidden zombie with Set Leader Pose. Leader pose copies
# bone transforms 1:1, and the zombie and knight skeletons have different proportions, so the knight's neck/head
# get the zombie's bone lengths (the #41 README listed this as its biggest risk). Fix: retarget instead of copying.
#   py "<repo>/handoffs/risen-334/setup_risenneck334_ue.py" --dry-run
#   py "<repo>/handoffs/risen-334/setup_risenneck334_ue.py"            step 1: RTG_Zombie_to_Knight + empty ABP_RisenKnight
#   py ".../setup_risenneck334_ue.py" --finish [--dry-run]             step 3 (after the AnimGraph paste + compile):
#        BP_ZombieRisen: UseLeaderPose = false, KnightMesh -> Use Animation Blueprint ABP_RisenKnight
# RTG_Zombie_to_Knight: source = IKR_Zombie_Src (the zombie rig already made for the Flesh Brute retarget), target = the
# knight's IK rig (read from RTG_UE5HeroToKnight), chains auto-mapped by name (fuzzy), then auto-aligned. The node in
# ABP_RisenKnight reads the pose from the attached parent (KnightMesh sits under the zombie Mesh).
import os, sys, unreal

A = sys.argv[1:]
DRY, FINISH = '--dry-run' in A, '--finish' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\risen-334'
KN = '/Game/CastleDefender/Characters/Knight'
RTG, RTG_HERO = KN + '/Retarget/RTG_Zombie_to_Knight', KN + '/Retarget/RTG_UE5HeroToKnight'
IKR_ZOMBIE = '/Game/CastleDefender/Characters/Enemies/FleshBrute/IKR_Zombie_Src'
ABP = KN + '/ABP_RisenKnight'
RISEN = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieRisen'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
SRC, TGT = unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET
log = ['#334 risen neck' + (' (DRY RUN, nothing written)' if DRY else '')]

if not FINISH:
    hero = unreal.load_asset(RTG_HERO); zr = unreal.load_asset(IKR_ZOMBIE)
    if not hero or not zr: raise SystemExit('missing %s or %s' % (RTG_HERO, IKR_ZOMBIE))
    knight_rig = unreal.IKRetargeterController.get_controller(hero).get_ik_rig(TGT)
    if not knight_rig: raise SystemExit('RTG_UE5HeroToKnight has no target IK rig')
    zc = unreal.IKRigController.get_controller(zr)
    kc = unreal.IKRigController.get_controller(knight_rig)
    log.append('source rig %s (mesh %s), %d chains' % (zr.get_name(), zc.get_skeletal_mesh().get_name() if zc.get_skeletal_mesh() else '?', len(zc.get_retarget_chains())))
    log.append('target rig %s (mesh %s), %d chains' % (knight_rig.get_name(), kc.get_skeletal_mesh().get_name() if kc.get_skeletal_mesh() else '?', len(kc.get_retarget_chains())))
    if EAL.does_asset_exist(RTG): log.append('RTG_Zombie_to_Knight already there: re-mapping it'); rtg = None if DRY else unreal.load_asset(RTG)
    else:
        log.append('create ' + RTG); rtg = None
        if not DRY: rtg = AT.create_asset('RTG_Zombie_to_Knight', KN + '/Retarget', unreal.IKRetargeter, unreal.IKRetargetFactory())
    if rtg:
        rc = unreal.IKRetargeterController.get_controller(rtg)
        rc.set_ik_rig(SRC, zr); rc.set_ik_rig(TGT, knight_rig)
        rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
        for side in (SRC, TGT):
            try: rc.auto_align_all_bones(side)
            except Exception as e: log.append('  auto-align %s skipped: %s' % (side, e))
        mapped = [(str(m.target_chain), str(m.source_chain)) for m in rc.get_chain_mappings()] if hasattr(rc, 'get_chain_mappings') else []
        for t, s_ in mapped: log.append('  chain %-14s <- %s' % (t, s_ or 'NONE (check by hand)'))
        EAL.save_asset(RTG)
    if EAL.does_asset_exist(ABP): log.append('ABP_RisenKnight already there: kept')
    else:
        sk = kc.get_skeletal_mesh().skeleton if kc.get_skeletal_mesh() else None
        log.append('create ' + ABP + ' (skeleton %s)' % (sk.get_name() if sk else '?'))
        if not DRY:
            f = unreal.AnimBlueprintFactory(); f.set_editor_property('target_skeleton', sk); f.set_editor_property('parent_class', unreal.AnimInstance)
            if not AT.create_asset('ABP_RisenKnight', KN, unreal.AnimBlueprint, f): raise SystemExit('could not create ABP_RisenKnight')
            EAL.save_asset(ABP)
else:
    bp = unreal.load_asset(RISEN); cls = unreal.load_class(None, ABP + '.ABP_RisenKnight_C')
    if not bp or not cls: raise SystemExit('missing BP_ZombieRisen or a compiled ABP_RisenKnight')
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        d = SDS.k2_find_subobject_data_from_handle(h)
        if str(LIB.get_variable_name(d)) == 'KnightMesh':
            km = LIB.get_object(d)
            log.append('KnightMesh: %s / %s -> Use Animation Blueprint / ABP_RisenKnight' % (km.get_editor_property('animation_mode'), km.get_editor_property('anim_class')))
            if not DRY:
                km.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT); km.set_editor_property('anim_class', cls)
    cdo = unreal.get_default_object(bp.generated_class())
    log.append('UseLeaderPose: %s -> False' % cdo.get_editor_property('UseLeaderPose'))
    if not DRY:
        cdo.set_editor_property('UseLeaderPose', False)
        BEL.compile_blueprint(bp); EAL.save_asset(RISEN)

out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_risenneck334.txt'), 'a').write(out + '\n')
unreal.log(out); print(out)
