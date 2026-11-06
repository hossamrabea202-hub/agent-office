# #530 strike: BPC_TentacleStrike plays AM_Tentacle_Strike in the post-process ABP's slot when a strike starts, under the FABRIK.
# RUN ../tentacle-anim-457/fix_pp_input_ue.py FIRST (the #457 slot fix): without the slot no montage shows. Editor idle, not in Play. No paste.
#   py wire_strike_ue.py --dry-run | --apply | --revert        (--bp <asset path>: test on a copy)
# Graph: K2Node_VariableSet_11 (State = 1) .then -> Mesh -> GetPostProcessInstance -> IsValid -> Branch -> Montage_Play -> CX_55 (RevengePending).
# Defaults: StrikeTime 0.21 (5 frames), RecoverTime 3.0 (long settle), WindupTime = 4.0 - WobbleTime - 0.21, so the hit stays on the clip's frame 96.
# The old defaults go to wire_strike_backup.json; --revert removes the nodes, relinks and puts them back. The script STOPS if a node name is missing.
import json, os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
PATH = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleStrike'
MON = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530/AM_Tentacle_Strike'
BK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wire_strike_backup.json')
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
Y = 9700; FROM, TO = 'K2Node_VariableSet_11', 'CX_55'; KEYS = ('WobbleTime', 'WindupTime', 'StrikeTime', 'RecoverTime')
def say(*a): print('WIRE530', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y == Y]
missing = [k for k in (FROM, TO) if k not in nodes]
if missing: raise SystemExit('WIRE530 nodes missing: %s; BPC_TentacleStrike changed, send i5 a fresh export' % missing)
def cdo(): return unreal.get_default_object(bp.generated_class())
def errs(): return sorted(n.get_name() for n in ge.list_nodes_with_errors())
if '--revert' in A:
    if not mine: say('nothing to revert')
    else:
        ge.remove_nodes(mine); say('relink', PL.try_create_connection(BEL.find_then_pin(nodes[FROM]), BEL.find_execute_pin(nodes[TO])))
        say('compile', BEL.compile_blueprint(bp), 'errors', errs())
        if os.path.exists(BK):
            for k, v in json.load(open(BK)).items(): cdo().set_editor_property(k, v)
            os.remove(BK)
        say('defaults', {k: round(cdo().get_editor_property(k), 3) for k in KEYS}); say('saved', E.save_asset(PATH, only_if_is_dirty=False)); say('removed', len(mine), 'nodes')
    raise SystemExit(0)
if mine: say('already wired,', len(mine), 'nodes'); raise SystemExit(0)
if not E.does_asset_exist(MON): raise SystemExit('WIRE530 montage missing: %s (run style_install_ue.py first)' % MON)
old = {k: float(cdo().get_editor_property(k)) for k in KEYS}; windup = round(4.0 - old['WobbleTime'] - 0.21, 3)
if windup < 0.3: raise SystemExit('WIRE530 WobbleTime %s leaves no windup; the clip cannot stay on frame 96, tell i5' % old['WobbleTime'])
new = {'WindupTime': windup, 'StrikeTime': 0.21, 'RecoverTime': 3.0}
if '--apply' not in A:
    say('WOULD add: %s.then -> [Mesh -> GetPostProcessInstance -> IsValid -> Branch -> Montage_Play(AM_Tentacle_Strike)] -> %s.execute' % (FROM, TO))
    say('WOULD set defaults', new, 'now', old); raise SystemExit(0)
base = errs(); X = [100]
def place(n): BEL.set_node_pos(n, unreal.IntPoint(X[0], Y)); X[0] += 320; return n
def lnk(a, pa, b, pb):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), BEL.find_input_pin(b, pb)): raise SystemExit('WIRE530 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
then_s, ex_d = BEL.find_then_pin(nodes[FROM]), BEL.find_execute_pin(nodes[TO])
mesh = place(ge.add_get_member_variable_node('Mesh'))
pp = place(ge.add_call_function_node('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance')); lnk(mesh, 'Mesh', pp, 'self')
iv = place(ge.add_call_function_node('/Script/Engine.KismetSystemLibrary:IsValid')); lnk(pp, 'ReturnValue', iv, 'Object')
br = place(ge.add_branch_node()); lnk(iv, 'ReturnValue', br, 'Condition')
mp = place(ge.add_call_function_node('/Script/Engine.AnimInstance:Montage_Play')); lnk(pp, 'ReturnValue', mp, 'self')
PL.set_pin_value(BEL.find_input_pin(mp, 'MontageToPlay'), unreal.load_asset(MON).get_path_name())
PL.break_pin_links(then_s)
ok = [PL.try_create_connection(then_s, BEL.find_execute_pin(br)), PL.try_create_connection(BEL.find_output_pin(br, 'then'), BEL.find_execute_pin(mp)),
      PL.try_create_connection(BEL.find_then_pin(mp), ex_d), PL.try_create_connection(BEL.find_output_pin(br, 'else'), ex_d)]
say('exec links', ok)
if not all(ok): raise SystemExit('WIRE530 an exec link failed: run --revert, tell i5')
say('compile', BEL.compile_blueprint(bp), 'errors before', base, 'after', errs())
if set(errs()) - set(base): raise SystemExit('WIRE530 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(errs()) - set(base)))
json.dump({k: old[k] for k in new}, open(BK, 'w'))
for k, v in new.items(): cdo().set_editor_property(k, v)
say('defaults', {k: round(cdo().get_editor_property(k), 3) for k in KEYS}, 'hit at', round(cdo().get_editor_property('WobbleTime') + cdo().get_editor_property('WindupTime') + cdo().get_editor_property('StrikeTime'), 3), 's')
say('saved', E.save_asset(PATH, only_if_is_dirty=False))
