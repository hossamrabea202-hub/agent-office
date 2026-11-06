# #334 risen soldiers, part A v2 (adjustedfilm, 2026-11-06): the retarget done right, in UE 5.8.
#   py "<repo>/handoffs/risen-334/rt334_risen_fix_ue.py" --dry-run     report; changes nothing
#   py "<repo>/handoffs/risen-334/rt334_risen_fix_ue.py"               apply (about 20 s)
# Why the risen soldier still looked silly: RTG_Zombie_to_Knight mapped a 6-chain zombie rig onto the knight's 18 chains
# with an unverified map and no alignment (UE 5.3 at the time had no auto_align). Verified in a scratch copy: with the
# zombie rig given the same 18 chains (neck, clavicles, fingers), FUZZY auto-map + auto-align on both sides, every knight
# chain maps (18/18) and the new ZW_ clips retargeted onto the knight walk with a normal neck, no twist (preview/).
# What "apply" does:
#   1. IKR_Zombie_Src: adds the missing chains (Neck, LeftClavicle, RightClavicle, 10 finger chains); existing ones kept
#   2. RTG_Zombie_to_Knight: source IKR_Zombie_Src, target IK_ShadowKnight, auto-map FUZZY, auto-align source + target,
#      prints the map and STOPS if a knight chain is unmapped; saves
#   3. BP_ZombieRisen: KnightMesh = Animation Blueprint / ABP_RisenKnight, UseLeaderPose default = false; compile, save
#   ABP_RisenKnight must still hold its "Retarget Pose From Mesh" node (pasted 10-31, RTG_Zombie_to_Knight); the test
#   list in README.md says what to look at.
import unreal, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:] + os.environ.get('RT334_ARGS', '').split()
DRY = '--dry-run' in args
EAL = unreal.EditorAssetLibrary
KN = '/Game/CastleDefender/Characters/Knight'
ZR = '/Game/CastleDefender/Characters/Enemies/FleshBrute/IKR_Zombie_Src'
RTG, KRIG, ABP, RISEN = KN + '/Retarget/RTG_Zombie_to_Knight', KN + '/Retarget/IK_ShadowKnight', KN + '/ABP_RisenKnight', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieRisen'
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print('RT334', s); log.append(s)
say('mode', 'DRY-RUN' if DRY else 'APPLY')
for p in (ZR, RTG, KRIG, ABP, RISEN):
    if not EAL.does_asset_exist(p): raise SystemExit('RT334 missing %s' % p)

# 1. the zombie rig's chains
WANT = [('Neck', 'Neck', 'Neck'), ('LeftClavicle', 'LeftShoulder', 'LeftShoulder'), ('RightClavicle', 'RightShoulder', 'RightShoulder'),
        ('LeftArm', 'LeftArm', 'LeftHand'), ('RightArm', 'RightArm', 'RightHand'), ('LeftLeg', 'LeftUpLeg', 'LeftFoot'), ('RightLeg', 'RightUpLeg', 'RightFoot'),
        ('Spine', 'Spine', 'Spine2')] + [('%s%s' % (s, f), '%sHand%s1' % (s, f), '%sHand%s3' % (s, f)) for s in ('Left', 'Right') for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')]
zr = unreal.load_asset(ZR); zc = unreal.IKRigController.get_controller(zr)
have = [str(ch.get_editor_property('chain_name')) for ch in zc.get_retarget_chains()]
say('IKR_Zombie_Src chains now:', have, 'root', str(zc.get_retarget_root()))
for nm, a, b in WANT:
    if nm in have: continue
    say('  add chain %s: %s -> %s' % (nm, a, b))
    if not DRY:
        if not zc.add_retarget_chain(nm, a, b, ''): say('  WARNING could not add', nm)
if not DRY: EAL.save_loaded_asset(zr)

# 2. the retargeter
kr = unreal.load_asset(KRIG); kc = unreal.IKRigController.get_controller(kr)
kchains = [str(ch.get_editor_property('chain_name')) for ch in kc.get_retarget_chains()]
say('IK_ShadowKnight chains:', kchains, 'root', str(kc.get_retarget_root()), 'mesh', kc.get_skeletal_mesh().get_name() if kc.get_skeletal_mesh() else '?')
rtg = unreal.load_asset(RTG); rc = unreal.IKRetargeterController.get_controller(rtg)
S, T = unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET
if DRY:
    say('would set rigs (source IKR_Zombie_Src, target IK_ShadowKnight), auto-map FUZZY, auto-align both sides, save')
else:
    rc.set_ik_rig(S, zr); rc.set_ik_rig(T, kr)
    rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    for side, nm in ((S, 'source'), (T, 'target')):
        try: rc.auto_align_all_bones(side); say('auto-aligned', nm)
        except Exception as e: say('auto_align', nm, 'ERR', str(e)[:80])
    mapping = {}
    for t in kchains:
        try: mapping[t] = str(rc.get_source_chain(t))
        except Exception as e: mapping[t] = 'ERR'
    say('chain map (knight <- zombie):', json.dumps(mapping))
    bad = [t for t, s_ in mapping.items() if s_ in ('None', '', 'ERR')]
    if bad: raise SystemExit('RT334 unmapped knight chains %s: nothing saved for the retargeter' % bad)
    EAL.save_loaded_asset(rtg); say('RTG_Zombie_to_Knight saved: %d/%d chains mapped' % (len(mapping) - len(bad), len(kchains)))

# 3. BP_ZombieRisen: the knight mesh runs ABP_RisenKnight, no leader pose
bp = unreal.load_asset(RISEN); cls = unreal.load_class(None, ABP + '.ABP_RisenKnight_C')
if not cls: raise SystemExit('RT334 ABP_RisenKnight is not compiled (open it, compile, save, then re-run)')
SDS, LIB, BEL = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem), unreal.SubobjectDataBlueprintFunctionLibrary, unreal.BlueprintEditorLibrary
found = False
for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
    d = SDS.k2_find_subobject_data_from_handle(h)
    if str(LIB.get_variable_name(d)) == 'KnightMesh':
        km = LIB.get_object(d); found = True
        say('KnightMesh: mode %s, anim class %s -> AnimationBlueprint / ABP_RisenKnight' % (km.get_editor_property('animation_mode'), km.get_editor_property('anim_class')))
        if not DRY:
            km.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT); km.set_editor_property('anim_class', cls)
if not found: say('WARNING: no KnightMesh component found on BP_ZombieRisen')
cdo = unreal.get_default_object(bp.generated_class())
try:
    say('UseLeaderPose default: %s -> False' % cdo.get_editor_property('UseLeaderPose'))
    if not DRY: cdo.set_editor_property('UseLeaderPose', False)
except Exception as e: say('UseLeaderPose', str(e)[:80])
if not DRY:
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp); say('BP_ZombieRisen compiled + saved (check the compiler log: 0 errors expected on the game project; the scratch copy lacks its dependencies)')
json.dump(log, open(os.path.join(HERE, 'rt334_apply_log.json'), 'w'), indent=1)
say('DONE', 'dry-run, nothing changed' if DRY else 'applied')
