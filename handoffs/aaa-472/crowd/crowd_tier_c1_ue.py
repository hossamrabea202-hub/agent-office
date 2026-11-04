# #493 C1 (i5 for i9): BPC_CrowdTier. Zombie body (mesh) collision only where it is needed: on screen, within 25 m of the player, or engaged by a soldier
# (soldiers mark their zombie with CustomTimeDilation 0.999). Everyone else: NoCollision. Dead zombies (ragdolls) are never touched. 4 checks a second, staggered.
# Measured on i5 (crowd/CROWD_PLAN.md): body collision off for 291 of 480 zombies saved ~55 ms of game thread.
#   py crowd_tier_c1_ue.py --dry-run            says what it would make; changes nothing
#   py crowd_tier_c1_ue.py --apply              makes /Game/CastleDefender/Gameplay/Crowd/BPC_CrowdTier, builds its graph, compiles, saves
#   py crowd_tier_c1_ue.py --apply --attach     also adds it to BP_Zombie (backup first: Saved/bak472/BP_Zombie.uasset.fixC1), compiles, saves
#   --folder <path>  build in another folder (i5 test: --folder /Game/_i5tmpC1x --apply --nosave), no --attach there
# Revert: remove the CrowdTier component from BP_Zombie (Components panel) and save; or restore the backup with the editor closed.
import json, os, shutil, sys, unreal
A = sys.argv[1:]
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
if not os.path.exists(os.path.join(HERE, 'ops_C1_crowdtier.json')): HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/crowd'
GOPS = os.path.join(os.path.dirname(HERE), 'ops', 'graph_ops_ue.py')
EA, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
ops = json.load(open(os.path.join(HERE, 'ops_C1_crowdtier.json'), encoding='utf-8'))
if '--folder' in A: ops['bp'] = A[A.index('--folder') + 1] + '/BPC_CrowdTier'
PATH, ZP = ops['bp'], '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
exists = EA.does_asset_exist(PATH)
print('C1:', PATH, 'exists' if exists else 'will be created', '| attach to BP_Zombie:', '--attach' in A)
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if exists:
    g = BEL.find_event_graph(unreal.load_asset(PATH))
    if g and len(unreal.BlueprintGraphEditor.get_graph_editor(g).list_all_nodes()) > 3:
        print('STOP:', PATH, 'already has a graph. Nothing changed.'); raise SystemExit
else:
    bp = BEL.create_blueprint_asset_with_parent(PATH, unreal.ActorComponent)
    if not bp: print('STOP: could not create', PATH); raise SystemExit
    BEL.compile_blueprint(bp); EA.save_asset(PATH, only_if_is_dirty=False)
out = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'ops_C1_resolved.json'
json.dump(ops, open(out, 'w', encoding='utf-8'), indent=1)
keep = sys.argv
sys.argv = [GOPS, out, '--apply', '--nobackup'] + (['--nosave'] if '--nosave' in A else [])
try: exec(compile(open(GOPS, encoding='utf-8').read(), GOPS, 'exec'), {'__file__': GOPS, '__name__': '__main__'})
except SystemExit as e:
    if e.code: print('STOP: graph_ops stopped:', e.code); raise SystemExit
sys.argv = keep
bp = unreal.load_asset(PATH); ge = unreal.BlueprintGraphEditor.get_graph_editor(BEL.find_event_graph(bp))
BEL.compile_blueprint(bp); errs = [n.get_name() for n in ge.list_nodes_with_errors()]
print('C1 component compile errors:', errs, '| nodes', len(ge.list_all_nodes()))
if errs: print('STOP: component has errors, not attached.'); raise SystemExit
if '--nosave' not in A: EA.save_asset(PATH, only_if_is_dirty=False)
if '--attach' in A and '--folder' not in A:
    zbp = unreal.load_asset(ZP); sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    hs = sds.k2_gather_subobject_data_for_blueprint(zbp)
    names = [str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))) for h in hs]
    if any(n.startswith('CrowdTier') for n in names): print('BP_Zombie already has CrowdTier, nothing to attach.'); raise SystemExit
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + ZP[len('/Game/'):] + '.uasset'
    dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/BP_Zombie.uasset.fixC1'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(src, dst); print('backup', dst)
    h, why = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=bp.generated_class(), blueprint_context=zbp))
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h): print('STOP: attach failed', why); raise SystemExit
    sds.rename_subobject(h, unreal.Text('CrowdTier'))
    BEL.compile_blueprint(zbp); print('attached CrowdTier to BP_Zombie')
    if '--nosave' not in A: EA.save_asset(ZP, only_if_is_dirty=False); print('saved BP_Zombie')
