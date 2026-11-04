# BP_CommanderHUD searched the whole world by tag EVERY frame to find the commander (K2Node_CallFunction_7; audit row E1). Now: a valid CommanderRef skips the search; with no commander
# it searches once a second. A commander bought or spawned shows up to 1 s later on the panel. Nothing else changes. Works with fix H: values only, other nodes. Card #487.
#   py commander_scan_fix_ue.py --dry-run               checks nodes, changes nothing
#   py commander_scan_fix_ue.py --apply                 compiles, saves ONLY if clean. Backup in Saved/bak472/
#   py commander_scan_fix_ue.py --apply --copy <folder> i5 test on a duplicate in a NEW folder, never saved
# Revert: restart without saving; after a save, copy Saved/bak472/BP_CommanderHUD.uasset.fixScan back with the editor closed. Aborts in PIE.
import os, shutil, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
PATH = '/Game/CastleDefender/Gameplay/Castle/BP_CommanderHUD'
if '--copy' in A:
    T_ = A[A.index('--copy') + 1] + '/CommanderF'
    if not E.does_asset_exist(T_): E.duplicate_asset(PATH, T_)
    PATH = T_
bp = unreal.load_asset(PATH)
def graph():
    g = GE.get_graph_editor(BEL.find_event_graph(bp))
    if any(n.get_name() == 'K2Node_CallFunction_7' for n in g.list_all_nodes()): return g
    return g
ge = graph(); L = {n.get_name(): n for n in ge.list_all_nodes()}
out = lambda n, p: BEL.find_output_pin(n, p); inp = lambda n, p: BEL.find_input_pin(n, p)
need = ('K2Node_VariableSet_5', 'K2Node_CallFunction_7', 'K2Node_ExecutionSequence_0')
bad = [k for k in need if k not in L]
if bad: print('STOP, nothing changed. Missing:', bad); raise SystemExit
c = PL.list_connected_pins(out(L['K2Node_VariableSet_5'], 'then'))
if not c or PL.get_owning_node(c[0]).get_name() != 'K2Node_CallFunction_7': print('STOP: the search is not right after PanelY, already fixed? Nothing changed'); raise SystemExit
print('check OK: PanelY -> GetAllActorsWithTag(Commander) every frame')
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if '--copy' not in A:
    s = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + PATH[len('/Game/'):] + '.uasset'
    d = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d + os.path.basename(s) + '.fixScan'): shutil.copy2(s, d + os.path.basename(s) + '.fixScan')
if 'CmdScanNext' not in [str(x) for x in BEL.list_member_variable_names(bp, False)]:
    print('var', BEL.add_member_variable(bp, 'CmdScanNext', BEL.get_basic_type_by_name('real'))); BEL.compile_blueprint(bp)
    ge = graph(); L = {n.get_name(): n for n in ge.list_all_nodes()}
fails = []
def link(p, q, label):
    if not p or not q or not PL.try_create_connection(p, q): fails.append(label)
LIB = '/Script/Engine.KismetSystemLibrary:'; MATH = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'
pan, scan, seq = L['K2Node_VariableSet_5'], L['K2Node_CallFunction_7'], L['K2Node_ExecutionSequence_0']
ref = ge.add_get_member_variable_node('CommanderRef', ''); val = ge.add_call_function_node(LIB + 'IsValid'); b1 = ge.add_branch_node()
now = ge.add_call_function_node(GS + 'GetTimeSeconds'); nx = ge.add_get_member_variable_node('CmdScanNext', ''); ge_n = ge.add_call_function_node(MATH + 'GreaterEqual_DoubleDouble'); b2 = ge.add_branch_node()
add = ge.add_call_function_node(MATH + 'Add_DoubleDouble'); st = ge.add_set_member_variable_node('CmdScanNext', '')
link(out(ref, 'CommanderRef'), inp(val, 'Object'), 'ref -> valid'); link(out(val, 'ReturnValue'), inp(b1, 'Condition'), 'valid -> b1')
link(out(now, 'ReturnValue'), inp(ge_n, 'A'), 'now -> ge'); link(out(nx, 'CmdScanNext'), inp(ge_n, 'B'), 'next -> ge'); link(out(ge_n, 'ReturnValue'), inp(b2, 'Condition'), 'ge -> b2')
link(out(now, 'ReturnValue'), inp(add, 'A'), 'now -> add')
PL.set_pin_value(inp(add, 'B'), '1.0')
link(out(add, 'ReturnValue'), inp(st, 'CmdScanNext'), 'add -> set')
PL.break_pin_links(out(pan, 'then')); link(out(pan, 'then'), inp(b1, 'execute'), 'panel -> b1')
link(out(b1, 'then'), inp(seq, 'execute'), 'valid -> skip search')
link(out(b1, 'else'), inp(b2, 'execute'), 'none -> time gate')
link(out(b2, 'then'), inp(st, 'execute'), 'due -> set next'); link(out(st, 'then'), inp(scan, 'execute'), 'set next -> search')
link(out(b2, 'else'), inp(seq, 'execute'), 'not due -> skip')
ok = BEL.compile_blueprint(bp); ge = graph(); err = [n.get_name() for n in ge.list_nodes_with_errors()]
print('RESULT compile', ok, '| link failures', fails, '| errors', err)
if '--copy' in A: print('test copy, not saved'); raise SystemExit
if fails or err or not ok: print('NOT SAVED. Restart without saving and send i5 this.')
else: print('saved', E.save_asset(PATH, only_if_is_dirty=False))
