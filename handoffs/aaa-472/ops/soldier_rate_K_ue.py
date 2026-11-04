# #487 fix K (i5 for i9): BP_SoldierSword AI at 15 Hz instead of every frame for soldiers near the player or on screen, with its two per-tick counters made per-second.
# Needs fix D on the Blueprint (D's rate select picks 0 s = every frame for near / seen soldiers; K makes that 1/15 s). Editor idle, not in Play.
#   py soldier_rate_K_ue.py --dry-run          finds D's rate select, checks every node and pin K needs; changes nothing
#   py soldier_rate_K_ue.py --apply            backup to Saved/bak472/BP_SoldierSword.uasset.fixK, change, compile, save only if no new errors
#   --bp <path>  test on a copy (with --apply --nosave --nobackup);  --rate <s>  near / seen tick interval (default 0.066667 = 15 Hz)
# Revert: close the editor, copy Saved/bak472/BP_SoldierSword.uasset.fixK over Content/CastleDefender/Characters/Knight/BP_SoldierSword.uasset, reopen.
import json, os, sys, unreal
A = sys.argv[1:]
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.'
if not os.path.exists(os.path.join(HERE, 'ops_K_soldier.json')): HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/aaa-472/ops'   # run from an inbox copy
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
ops = json.load(open(os.path.join(HERE, 'ops_K_soldier.json'), encoding='utf-8'))
if '--bp' in A: ops['bp'] = A[A.index('--bp') + 1]
if '--rate' in A: ops['set_live'][0][2] = A[A.index('--rate') + 1]
ge = GE.get_graph_editor(BEL.find_event_graph(unreal.load_asset(ops['bp'])))
def src(n, p):
    q = BEL.find_input_pin(n, p)
    c = PL.list_connected_pins(q) if q and PL.is_valid(q) else []
    return PL.get_owning_node(c[0]) if c else None
# fix D's actor rate: SetActorTickInterval <- SelectFloat(A = near / seen, B = 0.2 far + unseen)
dsel = []
for n in ge.list_all_nodes():
    if 'SetActorTickInterval' in str(n.get_node_title()).replace(' ', ''):
        s = src(n, 'TickInterval')
        if s and 'Select' in str(s.get_node_title()) and abs(float(PL.get_pin_value(BEL.find_input_pin(s, 'B')) or 0) - 0.2) < 1e-4: dsel.append(s)
if len(dsel) != 1:
    print('STOP: fix D\'s rate select not found exactly once on', ops['bp'], '(found %d). Apply fix D first. Nothing changed.' % len(dsel)); raise SystemExit
a_now = PL.get_pin_value(BEL.find_input_pin(dsel[0], 'A'))
print('fix D rate select:', dsel[0].get_name(), '| near / seen interval now', a_now, '-> K sets', ops['set_live'][0][2])
if 'skDt60' in [n.get_name() for n in ge.list_all_nodes()] or any(PL.list_connected_pins(BEL.find_input_pin(n, 'B')) for n in ge.list_all_nodes() if n.get_name() in ('CX_176', 'CX_579')):
    print('STOP: K looks applied already (CX_176 / CX_579 B is wired). Nothing changed.'); raise SystemExit
ops['set_live'][0][0] = dsel[0].get_name()
out = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'ops_K_resolved.json'
json.dump(ops, open(out, 'w', encoding='utf-8'), indent=1)
sys.argv = [os.path.join(HERE, 'graph_ops_ue.py'), out] + [x for i, x in enumerate(A) if x not in ('--bp', '--rate') and (i == 0 or A[i - 1] not in ('--bp', '--rate'))]
exec(compile(open(sys.argv[0], encoding='utf-8').read(), sys.argv[0], 'exec'), {'__file__': sys.argv[0], '__name__': '__main__'})
