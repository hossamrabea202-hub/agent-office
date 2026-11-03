# #472 (i5, 2026-11-03): apply a graph fix directly on the live Blueprint with UE 5.8's Python graph editing, instead of a whole-graph paste. No stale export can
# overwrite newer work: everything is looked up on the live graph, and if a node or pin the fix needs is missing, nothing changes.
#   py graph_ops_ue.py <ops.json> --dry-run         checks every node, pin and variable the fix needs; changes nothing
#   py graph_ops_ue.py <ops.json> --apply           adds variables + nodes, rewires, removes, compiles; saves ONLY if there are no errors
#   add --nosave to test without saving. Editor idle, not in Play.
# Revert: before --apply the script copies the .uasset to Saved/bak472/. To go back: close the editor, copy it over Content/... (remove the .fixX ending), reopen.
import json, os, sys, unreal
A = sys.argv[1:]
RAW = open(A[0] if os.path.isabs(A[0]) else os.path.join(os.path.dirname(os.path.abspath(__file__)), A[0]), encoding='utf-8').read()
# --copy <folder>: i5's test mode. BP_Zombie becomes a temporary copy, and BP_ZombieWaveManager a clean stub with only the new variables. Never a copy of the manager:
# compiling a broken copy of a Blueprint that references its own class crashed the editor twice. Links into live nodes typed to the real manager then fail by design.
if '--copy' in A:
    C_ = A[A.index('--copy') + 1]; EA = unreal.EditorAssetLibrary
    WMP, ZP = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager', '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
    if not EA.does_asset_exist(C_ + '/WMstub'):
        st = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(C_ + '/WMstub', unreal.Actor); B_ = unreal.BlueprintEditorLibrary
        ob_ = lambda p: B_.get_object_reference_type(unreal.load_asset(p).generated_class())
        for nm, ty in (('ZombieReg', B_.get_array_type(ob_(ZP))), ('SoldierCache', B_.get_array_type(ob_('/Game/CastleDefender/Characters/Knight/BP_SoldierSword'))),
                       ('FarmerCache', B_.get_array_type(ob_('/Game/CastleDefender/Gameplay/Farm/BP_Farmer'))), ('GateCache', ob_('/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl'))):
            B_.add_member_variable(st, nm, ty)
        B_.compile_blueprint(st); EA.save_asset(C_ + '/WMstub', only_if_is_dirty=False)
    if not EA.does_asset_exist(C_ + '/Z472c'): EA.duplicate_asset(ZP, C_ + '/Z472c')
    RAW = RAW.replace(WMP + '.BP_ZombieWaveManager_C', C_ + '/WMstub.WMstub_C').replace('"' + WMP + '"', '"' + C_ + '/WMstub"')
    RAW = RAW.replace(ZP + '.BP_Zombie_C', C_ + '/Z472c.Z472c_C').replace('"' + ZP + '"', '"' + C_ + '/Z472c"')
    SP = '/Game/CastleDefender/Characters/Knight/BP_SoldierSword'
    if '"' + SP + '"' in RAW:
        if not EA.does_asset_exist(C_ + '/S472c'): EA.duplicate_asset(SP, C_ + '/S472c')
        RAW = RAW.replace('"' + SP + '"', '"' + C_ + '/S472c"')
OPS = json.loads(RAW)
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
PATH = OPS['bp']; bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
live = {n.get_name(): n for n in ge.list_all_nodes()}
BEL.compile_blueprint(bp); base_err = {n.get_name() for n in ge.list_nodes_with_errors()}
print('errors before the fix:', sorted(base_err))
new_ids = {n['id'] for n in OPS['nodes']}
print('%s: %d live nodes, fix adds %d, removes %d, %d links' % (PATH.split('/')[-1], len(live), len(OPS['nodes']), len(OPS['remove']), len(OPS['links'])))
def split(ref):
    i = ref.index('.'); return ref[:i], ref[i + 1:]
def pin(node, name, out):
    p = BEL.find_output_pin(node, name) if out else BEL.find_input_pin(node, name)
    return p if p and PL.is_valid(p) else None
# ---- check first: nothing is touched if the live graph is not what the fix was built on
bad = [r for r in OPS['remove'] if r not in live]
for fr, to, rep in OPS['links']:
    for ref, out in ((fr, True), (to, False)):
        n, p = split(ref)
        if n in new_ids: continue
        if n not in live: bad.append(ref)
        elif not pin(live[n], p, out): bad.append(ref + ' (pin)')
for n, p, v in OPS.get('set_live', []):
    if n not in live or not pin(live[n], p, False): bad.append('%s.%s (set)' % (n, p))
if bad:
    print('STOP, the live graph differs, nothing changed. Send i5 an export. Missing:', sorted(set(bad))); raise SystemExit
print('check OK: every live node and pin the fix needs is there')
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
# ---- backup
if '--copy' not in A:
    import shutil
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + PATH[len('/Game/'):] + '.uasset'
    dst_dir = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(dst_dir, exist_ok=True)
    dst = dst_dir + os.path.basename(src) + '.fix' + OPS['fix']
    if not os.path.exists(dst): shutil.copy2(src, dst); print('backup', dst)
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
# ---- variables
have = [str(x) for x in BEL.list_member_variable_names(bp, False)]
def vtype(t):
    if t.get('array'): return BEL.get_array_type(vtype({k: v for k, v in t.items() if k != 'array'}))
    if 'basic' in t: return BEL.get_basic_type_by_name(t['basic'])
    c = unreal.Actor if t['object'] == 'Actor' else unreal.load_asset(t['object']).generated_class()
    return BEL.get_object_reference_type(c)
for name, t in OPS.get('vars', []):
    if name not in have: print('var', name, BEL.add_member_variable(bp, name, vtype(t)))
if OPS.get('vars'): BEL.compile_blueprint(bp); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
# ---- new nodes
made = {}
for n in OPS['nodes']:
    k, pos = n['kind'], unreal.Vector2D(n['x'] + OPS.get('dx', 0), n['y'] + OPS.get('dy', 0))
    if k == 'call': o = ge.add_call_function_node(n['path'])
    elif k == 'get' and n.get('cls', '').split('.')[0] == PATH:
        # a variable of ANOTHER instance of this same class: add_get_member_variable_node would make it a self read. Create it from the object pin instead.
        src = [fr for fr, to, rep in OPS['links'] if to == n['id'] + '.self'][0]; sn, sp = split(src)
        ctx = pin(made[sn], sp, True); want = [x for x in map(str, ge.list_available_nodes([ctx])) if x.endswith('|Get' + n['var'])]
        if not want: raise SystemExit('no targeted getter for ' + n['var'])
        o = ge.create_node_from_name(want[0], pos, [ctx])
    elif k == 'get': o = ge.add_get_member_variable_node(n['var'], n.get('cls', ''))
    elif k == 'set': o = ge.add_set_member_variable_node(n['var'], n.get('cls', ''))
    elif k == 'branch': o = ge.add_branch_node()
    elif k == 'custom': o = ge.add_custom_event_node(n['name'])
    elif k == 'override': o = BEL.add_event_override(bp, n['member'], unreal.IntPoint(int(pos.x), int(pos.y)))
    elif k == 'named': o = ge.create_node_from_name(n['name'], pos, [])
    else: raise SystemExit('unknown kind ' + k)
    if not o: raise SystemExit('could not create %s %s' % (n['id'], n))
    BEL.set_node_pos(o, unreal.IntPoint(int(pos.x), int(pos.y))); made[n['id']] = o
def node(ref): return made[ref] if ref in made else live[ref]
fails = []
# ---- pin values. Class / asset pins now: they type the outputs the links need. The rest after the links: a math operator is a wildcard until something is wired to it.
def set_values(paths):
    for n in OPS['nodes']:
        for pname, val in n.get('defaults', []):
            if val.startswith('/') != paths: continue
            p = pin(made[n['id']], pname, False)
            if not p: fails.append('%s.%s (no pin for value)' % (n['id'], pname)); continue
            if PL.list_connected_pins(p): continue
            if not PL.set_pin_value(p, val): fails.append('%s.%s = %s (value refused)' % (n['id'], pname, val))
set_values(True)
for nm, pname, val in OPS.get('set_live', []): PL.set_pin_value(pin(live[nm], pname, False), val)
# ---- links in order. replace: the one-link end (exec output, data input) lets go first
for fr, to, rep in OPS['links']:
    a, pa = split(fr); b, pb = split(to)
    p, q = pin(node(a), pa, True), pin(node(b), pb, False)
    if not p or not q: fails.append('%s -> %s (no pin)' % (fr, to)); continue
    if rep:
        exec_out = 'exec' in str(PL.get_pin_type_display_string(p)).lower() or pa in ('then', 'else', 'LoopBody', 'Completed', 'CastFailed') or pa.startswith('then_')
        PL.break_pin_links(p if exec_out else q)
    if not PL.try_create_connection(p, q): fails.append('%s -> %s (%s vs %s)' % (fr, to, PL.get_pin_type_display_string(p), PL.get_pin_type_display_string(q)))
set_values(False)
# ---- removals, then pure helpers left with no consumer
feeders = set()
for r in OPS['remove']:
    for p in BEL.list_input_pins(live[r]):
        for q in PL.list_connected_pins(p): feeders.add(PL.get_owning_node(q).get_name())
if OPS['remove']: ge.remove_nodes([live[r] for r in OPS['remove']])
all_now = {n.get_name(): n for n in ge.list_all_nodes()}
gone = 0
for _ in range(4):
    drop = []
    for f in list(feeders):
        n = all_now.get(f)
        if not n or any('exec' in str(PL.get_pin_type_display_string(x)).lower() for x in BEL.list_all_pins(n)): continue
        if not any(PL.list_connected_pins(p) for p in BEL.list_output_pins(n)): drop.append(n); all_now.pop(f)
    if not drop: break
    more = set()
    for n in drop:
        for p in BEL.list_input_pins(n):
            for q in PL.list_connected_pins(p): more.add(PL.get_owning_node(q).get_name())
    ge.remove_nodes(drop); gone += len(drop); feeders = more
print('removed %d + %d pure helpers' % (len(OPS['remove']), gone))
if '--nocompile' in A: print('RESULT links only | link/value failures', fails); raise SystemExit
ok = BEL.compile_blueprint(bp)
ge = GE.get_graph_editor(BEL.find_event_graph(bp))
err = [(n.get_name(), n.get_editor_property('error_msg') if False else '') for n in ge.list_nodes_with_errors()]
warn = [n.get_name() for n in ge.list_nodes_with_warnings()]
newerr = [e[0] for e in err if e[0] not in base_err]
print('RESULT compile', ok, '| link/value failures', fails, '| new errors', newerr, '| old errors', [e[0] for e in err if e[0] in base_err], '| warnings', warn)
if '--copy' in A: print('test copy, not saved'); raise SystemExit
if fails or err or not ok: print('NOT SAVED. The Blueprint in memory is wrong: do not save it; reload it or restart the editor. Send i5 this output.')
elif '--nosave' in A: print('compiled clean, not saved (--nosave)')
else: print('saved', E.save_asset(PATH, only_if_is_dirty=False))
