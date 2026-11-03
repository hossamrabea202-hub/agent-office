# #477 fix 2 (i5, 2026-11-03): v1 only woke at Tier 4, but the Helm has no art, so the set stops at 3/4 and the skill could never show.
# "Complete" is now a class default, EmberMinTier (int): 3 today. When the helmet ships, set it to 4 and nothing else.
#   skill + badge:  Tier >= EmberMinTier
#   on-hit shock:   Tier >= 3 AND Tier < EmberMinTier (today never: at 3/4 the shock is on the key, no longer automatic)
# Run AFTER ember_ops_ue.py. Live node names of that step are generated, so everything is found by walking the wires from DrawArmoury.
#   py ember2_ue.py --dry-run          finds both spots, changes nothing
#   py ember2_ue.py --apply            adds the variable + 4 nodes, compiles, saves ONLY if clean. Backup in Saved/bak472/
#   py ember2_ue.py --apply --bp <path> --copy     i5 test on a temp copy, never saved
# Revert: restart without saving; after a save, copy Saved/bak472/BPC_ObsidianSet.uasset.fix477b back with the editor closed. Aborts in PIE.
import os, shutil, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
PATH = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
live = {n.get_name(): n for n in ge.list_all_nodes()}
ipin = lambda n, p: BEL.find_input_pin(n, p)
opin = lambda n, p: BEL.find_output_pin(n, p)
def src(n, p):
    q = ipin(n, p); c = PL.list_connected_pins(q) if q else []
    return PL.get_owning_node(c[0]) if c else None
def dst(n, p):
    q = opin(n, p); c = PL.list_connected_pins(q) if q else []
    return PL.get_owning_node(c[0]) if c else None
bad = []
seq = dst(live['DrawArmoury'], 'then') if 'DrawArmoury' in live else None
if not seq or not opin(seq, 'then_0'): bad.append('DrawArmoury.then -> Sequence (is ember_ops_ue.py applied?)')
br = dst(seq, 'then_0') if seq else None
andn = src(br, 'Condition') if br else None
if not andn: bad.append('Sequence.then_0 -> Branch.Condition <- AND')
was = src(andn, 'A') if andn else None
if not was: bad.append('AND.A (the Tier == 4 test)')
hit = live.get('oBooleanAND468'); gt3 = live.get('oGreaterEqual_I467')
if not hit: bad.append('oBooleanAND468')
if not gt3: bad.append('oGreaterEqual_I467')
if bad: print('STOP, nothing changed. Missing:', bad); raise SystemExit
if PL.get_owning_node(PL.list_connected_pins(ipin(hit, 'A'))[0]).get_name() == gt3.get_name(): print('STOP: on-hit test still on the old Tier >= 3, is ember_ops_ue.py applied?'); raise SystemExit
print('check OK: found', seq.get_name(), br.get_name(), andn.get_name(), was.get_name(), '| on-hit', hit.get_name(), gt3.get_name())
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if '--copy' not in A:
    s = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + PATH[len('/Game/'):] + '.uasset'
    d = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d + os.path.basename(s) + '.fix477b'): shutil.copy2(s, d + os.path.basename(s) + '.fix477b')
if 'EmberMinTier' not in [str(x) for x in BEL.list_member_variable_names(bp, False)]:
    print('var', BEL.add_member_variable(bp, 'EmberMinTier', BEL.get_basic_type_by_name('int'))); BEL.compile_blueprint(bp)
    ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
    seq = dst(live['DrawArmoury'], 'then'); br = dst(seq, 'then_0'); andn = src(br, 'Condition'); hit = live['oBooleanAND468']; gt3 = live['oGreaterEqual_I467']
M = '/Script/Engine.KismetMathLibrary:'
fails = []
def link(p, q, label):
    if not p or not q or not PL.try_create_connection(p, q): fails.append(label)
def tier_vs_min(fn, x, y):
    n = ge.add_call_function_node(M + fn); BEL.set_node_pos(n, unreal.IntPoint(x, y))
    t = ge.add_get_member_variable_node('Tier', ''); BEL.set_node_pos(t, unreal.IntPoint(x - 250, y))
    m = ge.add_get_member_variable_node('EmberMinTier', ''); BEL.set_node_pos(m, unreal.IntPoint(x - 250, y + 120))
    link(opin(t, 'Tier'), ipin(n, 'A'), fn + '.A'); link(opin(m, 'EmberMinTier'), ipin(n, 'B'), fn + '.B')
    return n
p0 = BEL.get_node_pos(andn) if hasattr(BEL, 'get_node_pos') else None
ge_n = tier_vs_min('GreaterEqual_IntInt', 0, 30000)
PL.break_pin_links(ipin(andn, 'A')); link(opin(ge_n, 'ReturnValue'), ipin(andn, 'A'), 'skill AND.A')
lt_n = tier_vs_min('Less_IntInt', 0, 30400)
a2 = ge.add_call_function_node(M + 'BooleanAND'); BEL.set_node_pos(a2, unreal.IntPoint(300, 30400))
link(opin(gt3, 'ReturnValue'), ipin(a2, 'A'), 'hit AND.A'); link(opin(lt_n, 'ReturnValue'), ipin(a2, 'B'), 'hit AND.B')
PL.break_pin_links(ipin(hit, 'A')); link(opin(a2, 'ReturnValue'), ipin(hit, 'A'), 'oBooleanAND468.A')
ok = BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property('EmberMinTier', 3)
ge = GE.get_graph_editor(BEL.find_event_graph(bp)); err = [n.get_name() for n in ge.list_nodes_with_errors()]; warn = [n.get_name() for n in ge.list_nodes_with_warnings()]
print('RESULT compile', ok, '| link failures', fails, '| errors', err, '| warnings', warn, '| EmberMinTier', cdo.get_editor_property('EmberMinTier'))
if '--copy' in A: print('test copy, not saved'); raise SystemExit
if fails or err or not ok: print('NOT SAVED. Do not save; restart the editor and send i5 this output.')
else: print('saved', E.save_asset(PATH, only_if_is_dirty=False))
