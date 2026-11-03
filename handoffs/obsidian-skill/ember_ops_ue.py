# #477 (i5, 2026-11-03): applies ember_ops.json to the live BPC_ObsidianSet. Copy of aaa-472/ops/graph_ops_ue.py (the crowd session's runner) + Sequence and Cast nodes.
# Run setup_ember_ue.py --apply first (variables + defaults).
#   py ember_ops_ue.py --dry-run                checks every node + pin it needs; changes nothing
#   py ember_ops_ue.py --apply                  adds nodes, rewires, compiles; saves ONLY if there are no errors. Backup in Saved/bak472/
#   py ember_ops_ue.py --apply --bp <path> --copy   i5 test on a temp copy, never saved
# Revert: restart without saving; or after a save close the editor, copy Saved/bak472/BPC_ObsidianSet.uasset.fix477 over Content/.../BPC_ObsidianSet.uasset.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/obsidian-skill/', 'C:/Users/hossa/Documents/agent-office/handoffs/obsidian-skill/') if os.path.isdir(h))
RAW = open(HERE + 'ember_ops.json', encoding='utf-8').read()
if '--bp' in A:
    T_ = A[A.index('--bp') + 1]; B0 = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
    RAW = RAW.replace(B0 + '.BPC_ObsidianSet_C', T_ + '.' + T_.split('/')[-1] + '_C').replace('"' + B0 + '"', '"' + T_ + '"')
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
    print('STOP, the live graph differs, nothing changed. Send i5 this line. Missing:', sorted(set(bad))); raise SystemExit
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
    elif k == 'seq': o = ge.create_node_from_name('Utilities|FlowControl|Sequence', pos, [])
    elif k == 'cast':
        src = [fr for fr, to, rep in OPS['links'] if to == n['id'] + '.Object'][0]; sn, sp = split(src)
        want = [x for x in map(str, ge.list_available_nodes([pin(made[sn], sp, True)])) if 'Cast' in x and 'ThirdPersonCharacter' in x.replace(' ', '')]
        if not want: raise SystemExit('no cast node found')
        o = ge.create_node_from_name(want[0], pos, [pin(made[sn], sp, True)])
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
