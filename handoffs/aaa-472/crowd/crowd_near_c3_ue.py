# #493 C3 (i5 for i9): each soldier fights from a list of the zombies near it instead of looping over every zombie every frame.
# New component BPC_NearZombies on BP_SoldierSword (BP_SoldierXbow inherits it): 5 x a second one native sphere query, 12 m, BP_Zombie only -> NearZombies.
# The soldier's fight loop CX_145 reads NearZombies. Its conditions only act within 7 m (1.75 / 2.4-4.5 / 7 m), so 12 m loses no fight.
#   py crowd_near_c3_ue.py --dry-run          checks the soldier (CX_145 there, not done yet); changes nothing
#   py crowd_near_c3_ue.py --apply            backup Saved/bak472/BP_SoldierSword.uasset.fixC3, makes BPC_NearZombies, attaches it, rewires CX_145, compiles, saves if clean
#   test on i5: --folder /Game/_i5tmpX --soldier /Game/_i5tmpX/X472c --apply --nosave
# Revert: close the editor, copy the backup over Content/CastleDefender/Characters/Knight/BP_SoldierSword.uasset, reopen (BPC_NearZombies can stay, unused).
import json, os, shutil, sys, unreal
A = sys.argv[1:]
def arg(k, d): return A[A.index(k) + 1] if k in A else d
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
if not os.path.exists(os.path.join(HERE, 'ops_C3_nearcomp.json')): HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/crowd'
GOPS = os.path.join(os.path.dirname(HERE), 'ops', 'graph_ops_ue.py')
EA, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
COMP = arg('--folder', '/Game/CastleDefender/Gameplay/Crowd') + '/BPC_NearZombies'
SOLD = arg('--soldier', '/Game/CastleDefender/Characters/Knight/BP_SoldierSword')
SAVED = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir())
def run_ops(ops, tag, extra):
    out = SAVED + 'ops_%s_resolved.json' % tag; json.dump(ops, open(out, 'w', encoding='utf-8'), indent=1)
    keep = sys.argv; sys.argv = [GOPS, out] + extra
    try: exec(compile(open(GOPS, encoding='utf-8').read(), GOPS, 'exec'), {'__file__': GOPS, '__name__': '__main__'})
    except SystemExit as e:
        if e.code: sys.argv = keep; print('STOP: graph_ops stopped on', tag, ':', e.code); raise SystemExit
    sys.argv = keep
# ---- check the soldier first
sbp = unreal.load_asset(SOLD); ge = GE.get_graph_editor(BEL.find_event_graph(sbp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
if 'CX_145' not in live: print('STOP: CX_145 (the fight loop) is not on', SOLD, '- send i5 an export. Nothing changed.'); raise SystemExit
src = PL.list_connected_pins(BEL.find_input_pin(live['CX_145'], 'Array'))
feed = PL.get_owning_node(src[0]) if src else None
print('C3: CX_145 reads', feed and str(feed.get_node_title()), '| component', COMP, '| soldier', SOLD)
if feed and 'NearZombies' in str(feed.get_node_title()): print('STOP: C3 is applied already. Nothing changed.'); raise SystemExit
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
# ---- backup the soldier before anything touches it
if '--nosave' not in A:
    s = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + SOLD[len('/Game/'):] + '.uasset'
    d = SAVED + 'bak472/' + os.path.basename(s) + '.fixC3'; os.makedirs(os.path.dirname(d), exist_ok=True)
    if not os.path.exists(d): shutil.copy2(s, d); print('backup', d)
# ---- the component
if not EA.does_asset_exist(COMP):
    c = BEL.create_blueprint_asset_with_parent(COMP, unreal.ActorComponent); BEL.compile_blueprint(c); EA.save_asset(COMP, only_if_is_dirty=False)
cbp = unreal.load_asset(COMP)
if len(GE.get_graph_editor(BEL.find_event_graph(cbp)).list_all_nodes()) <= 3:
    ops = json.load(open(os.path.join(HERE, 'ops_C3_nearcomp.json'), encoding='utf-8')); ops['bp'] = COMP
    run_ops(ops, 'C3comp', ['--apply', '--nobackup'] + (['--nosave'] if '--nosave' in A else []))
cbp = unreal.load_asset(COMP); BEL.compile_blueprint(cbp)
cerr = [n.get_name() for n in GE.get_graph_editor(BEL.find_event_graph(cbp)).list_nodes_with_errors()]
print('BPC_NearZombies errors:', cerr)
if cerr: print('STOP: component has errors; soldier not touched.'); raise SystemExit
if '--nosave' not in A: EA.save_asset(COMP, only_if_is_dirty=False)
# ---- attach to the soldier
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); hs = sds.k2_gather_subobject_data_for_blueprint(sbp)
if not any(str(SDL.get_variable_name(SDL.get_data(h))).startswith('NearZombies') for h in hs):
    h, why = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=cbp.generated_class(), blueprint_context=sbp))
    if not SDL.is_handle_valid(h): print('STOP: attach failed', why); raise SystemExit
    sds.rename_subobject(h, unreal.Text('NearZombies')); print('attached NearZombies to', SOLD)
BEL.compile_blueprint(sbp)
# ---- rewire the fight loop
cls = COMP + '.BPC_NearZombies_C'
ops = json.loads(open(os.path.join(HERE, 'ops_C3_soldier.json'), encoding='utf-8').read().replace('@NEARCLS', cls)); ops['bp'] = SOLD
run_ops(ops, 'C3soldier', ['--apply', '--nobackup'] + (['--nosave'] if '--nosave' in A else []))
