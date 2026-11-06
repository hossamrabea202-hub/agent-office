# #553 gate: gives BP_CastleGateControl two callable events and a state flag. No paste. Editor idle, not in Play.
#   py wire_gate_ue.py --dry-run | --apply | --revert     (--bp <asset path>: test on a copy)
# Adds: variable bGateOpen; CmdGateOpen / CmdGateClose (custom events) -> if the state differs -> AnimationLock (the same entry E at the
# lever uses, so doors, lever, prompts and the 1.65 s lock are unchanged); ToggleGate.A sets bGateOpen true, ToggleGate.B sets it false.
# Built on the 11-06 export (handoffs/exports/checkking/gate-506). STOPS if a node is missing: then send i5 a fresh export.
import sys, unreal
A = sys.argv[1:]
PATH = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
Y = 7700
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y == Y]
need = ['AnimationLock', 'ToggleGate', 'PromptOpened', 'PromptClosed']
miss = [k for k in need if k not in nodes]
if miss: raise SystemExit('nodes missing: %s; BP_CastleGateControl changed, send i5 a fresh export' % miss)
def pin(n, name, out=False):
    p = BEL.find_output_pin(n, name) if out else BEL.find_input_pin(n, name)
    if not p or not PL.is_valid(p): raise SystemExit('no pin %s on %s' % (name, n.get_name()))
    return p
if '--revert' in A:
    if not mine: print('GATE nothing to revert'); raise SystemExit
    ge.remove_nodes(mine)
    print('relink', PL.try_create_connection(pin(nodes['ToggleGate'], 'A', True), BEL.find_execute_pin(nodes['PromptOpened'])), PL.try_create_connection(pin(nodes['ToggleGate'], 'B', True), BEL.find_execute_pin(nodes['PromptClosed'])))
    print('GATE compile', BEL.compile_blueprint(bp)); E.save_asset(PATH, only_if_is_dirty=False); raise SystemExit
if mine: print('GATE already wired,', len(mine), 'nodes'); raise SystemExit
if '--apply' not in A:
    print('GATE WOULD add bGateOpen, CmdGateOpen, CmdGateClose; ToggleGate.A/B through Set bGateOpen; all nodes present:', need); raise SystemExit
X = [100]
def place(n): BEL.set_node_pos(n, unreal.IntPoint(X[0], Y)); X[0] += 320; return n
t = BEL.get_basic_type_by_name('bool')
print('var', BEL.add_member_variable(bp, 'bGateOpen', t))
BEL.compile_blueprint(bp)
def setter(val, tail):
    s = place(ge.add_set_member_variable_node('bGateOpen'))
    PL.set_pin_value(pin(s, 'bGateOpen'), 'true' if val else 'false')
    print('set link', PL.try_create_connection(BEL.find_then_pin(s), BEL.find_execute_pin(tail))); return s
def insert(pinname, val, tail):
    src = pin(nodes['ToggleGate'], pinname, True); PL.break_pin_links(src)
    s = setter(val, nodes[tail]); print(pinname, PL.try_create_connection(src, BEL.find_execute_pin(s)))
insert('A', True, 'PromptOpened'); insert('B', False, 'PromptClosed')
lock_in = pin(nodes['AnimationLock'], 'execute')
def cmd(name, want):
    ev = place(ge.add_custom_event_node(name))
    g_ = place(ge.add_get_member_variable_node('bGateOpen'))
    br = place(ge.add_branch_node())
    print(name, PL.try_create_connection(BEL.find_then_pin(ev), BEL.find_execute_pin(br)), PL.try_create_connection(pin(g_, 'bGateOpen', True), pin(br, 'Condition')),
          PL.try_create_connection(pin(br, 'else' if want else 'then', True), lock_in))
cmd('CmdGateOpen', True); cmd('CmdGateClose', False)
print('GATE errors', [n.get_name() for n in ge.list_nodes_with_errors()])
print('GATE compile', BEL.compile_blueprint(bp)); E.save_asset(PATH, only_if_is_dirty=False); print('GATE saved')
