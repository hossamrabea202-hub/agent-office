# #545 step 2: outdoor-only gate and inert switch, BPC_TentacleStrike + BPC_TentacleSpit (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste. Needs #534 and #536 (applied).
#   py wire_outdoor_gate_ue.py --dry-run | --apply | --revert
# Why: in #542 buried copies struck the hero inside the barracks. An arm must never appear indoors.
# New variable on both components: Inert (bool, default false, instance editable, exposed on spawn).
#   BP_TentacleEruption spawns its tentacle's vitals with Inert = true and sets it false when the rise ends: SetBoolPropertyByName(component, 'Inert', false).
# Strike: every path into a strike (cannon, soldier pack, revenge) passes one gate. It strikes only if
#   not Inert, AND the target is outside the castle box, AND a trace from 300 m above the target does not first meet a castle mesh (a StaticMeshActor that is not the target itself).
# Spit: nothing happens while Inert (no hit logic, no rage, no spit), and no spit at the hero while he is inside the castle box. The catapult still throws into the castle: that is the owner's order.
# Consequence: cannons inside the castle box can no longer be struck. Set GateCannons false on BPC_TentacleStrike to let cannons skip the box test.
# New nodes sit at y >= 16000. --revert removes them and the variables and restores every link. The script STOPS if a node name is missing.
import os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); G = '/Game/CastleDefender/Gameplay/Tentacle/'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; YMIN = 16000
BOX = (-1900.0, 6500.0, -1900.0, 5350.0)      # castle bounds from the level scan: x min, x max, y min, y max
def say(*a): print('GATE545', ' '.join(str(x) for x in a))
class W:
    def __init__(s, path):
        s.path = path; s.bp = unreal.load_asset(path); s.ge = GE.get_graph_editor(BEL.find_event_graph(s.bp)); s.n = {x.get_name(): x for x in s.ge.list_all_nodes()}; s.p = [0, YMIN]
        s.mine = [x for x in s.ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]
    def place(s, x):
        BEL.set_node_pos(x, unreal.IntPoint(s.p[0], s.p[1])); s.p[0] += 300
        if s.p[0] > 6000: s.p[0] = 0; s.p[1] += 300
        return x
    def i(s, x, p):
        r = BEL.find_input_pin(x, p)
        if not r: raise SystemExit('GATE545 no input pin %s.%s' % (x.get_name(), p))
        return r
    def o(s, x, p):
        r = BEL.find_output_pin(x, p)
        if not r: raise SystemExit('GATE545 no output pin %s.%s' % (x.get_name(), p))
        return r
    def call(s, path, **lit):
        x = s.place(s.ge.add_call_function_node(path))
        for k, v in lit.items(): PL.set_pin_value(s.i(x, k), str(v))
        return x
    def link(s, a, pa, b, pb):
        if not PL.try_create_connection(s.o(a, pa), s.i(b, pb)): raise SystemExit('GATE545 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
    def get(s, v): return s.place(s.ge.add_get_member_variable_node(v))
    def branch(s, c, pc='ReturnValue'):
        x = s.place(s.ge.add_branch_node()); s.link(c, pc, x, 'Condition'); return x
    def nt(s, c, pc='ReturnValue'):
        x = s.call(M + 'Not_PreBool'); s.link(c, pc, x, 'A'); return x
    def both(s, a, b_):
        x = s.call(M + 'BooleanAND'); s.link(a, 'ReturnValue', x, 'A'); s.link(b_, 'ReturnValue', x, 'B'); return x
    def outside(s, loc):                      # True when the location is outside the castle box
        b = s.call(M + 'BreakVector'); s.link(loc, 'ReturnValue', b, 'InVec'); ins = None
        for pin, lo, hi in (('X', BOX[0], BOX[1]), ('Y', BOX[2], BOX[3])):
            g = s.call(M + 'Greater_DoubleDouble', B=lo); s.link(b, pin, g, 'A'); l = s.call(M + 'Less_DoubleDouble', B=hi); s.link(b, pin, l, 'A'); x = s.both(g, l); ins = x if ins is None else s.both(ins, x)
        return s.nt(ins)
    def ex_to(s, src_pin, node):
        if not PL.try_create_connection(src_pin, BEL.find_execute_pin(node)): raise SystemExit('GATE545 exec failed into ' + node.get_name())
def add_vars(w, extra=()):
    have = [str(v) for v in BEL.list_member_variable_names(w.bp)]
    for v in ('Inert',) + tuple(extra):
        if v not in have: BEL.add_member_variable(w.bp, v, BEL.get_basic_type_by_name('bool'))
    BEL.set_blueprint_variable_instance_editable(w.bp, 'Inert', True); BEL.set_blueprint_variable_expose_on_spawn(w.bp, 'Inert', True); BEL.compile_blueprint(w.bp)
def finish(w, before):
    ok = BEL.compile_blueprint(w.bp); now = sorted(x.get_name() for x in w.ge.list_nodes_with_errors()); say(w.path.rsplit('/', 1)[1], 'compile', ok, 'errors before', before, 'after', now)
    if set(now) - set(before): raise SystemExit('GATE545 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(now) - set(before)))
    say('saved', E.save_asset(w.path, only_if_is_dirty=False), 'new nodes', len([x for x in w.ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]))
def do_strike():
    w = W(G + 'BPC_TentacleStrike'); n = w.n; k = 'K2Node_CallArrayFunction_1'
    if k not in n or 'K2Node_CustomEvent_0' not in n: raise SystemExit('GATE545 strike nodes missing; send i5 a fresh export of BPC_TentacleStrike')
    if '--revert' in A:
        if not w.mine: say('strike: nothing to revert'); return
        # the gate's incoming links are the original links into the tag node
        into = [PL.get_owning_node(p) for p in PL.list_connected_pins(BEL.find_execute_pin(n[k]))]; gate = into[0]; trace = PL.get_owning_node(list(PL.list_connected_pins(BEL.find_execute_pin(gate)))[0])
        src = list(PL.list_connected_pins(BEL.find_execute_pin(trace))); w.ge.remove_nodes(w.mine)
        say('strike relink', [PL.try_create_connection(p, BEL.find_execute_pin(n[k])) for p in src])
        for v in ('Inert', 'GateCannons'): w.ge.remove_member_variable(v)
        say('compile', BEL.compile_blueprint(w.bp)); say('saved', E.save_asset(w.path, only_if_is_dirty=False)); return
    if w.mine: say('strike: already wired', len(w.mine)); return
    if '--apply' not in A: say('WOULD gate all paths into', k, 'links now', len(list(PL.list_connected_pins(BEL.find_execute_pin(n[k]))))); return
    BEL.compile_blueprint(w.bp); before = sorted(x.get_name() for x in w.ge.list_nodes_with_errors()); add_vars(w, ('GateCannons',)); w.n = n = {x.get_name(): x for x in w.ge.list_all_nodes()}
    src = list(PL.list_connected_pins(BEL.find_execute_pin(n[k]))); PL.break_pin_links(BEL.find_execute_pin(n[k]))
    tl = w.call(AC + 'K2_GetActorLocation'); w.link(w.get('TargetCannon'), 'TargetCannon', tl, 'self'); out = w.outside(tl)
    # a cannon target may skip the box test when GateCannons is false; PackStrike tells a soldier pack from a cannon
    skip = w.both(w.nt(w.get('GateCannons'), 'GateCannons'), w.nt(w.get('PackStrike'), 'PackStrike')); okb = w.call(M + 'BooleanOR'); w.link(out, 'ReturnValue', okb, 'A'); w.link(skip, 'ReturnValue', okb, 'B')
    up = w.call(M + 'Add_VectorVector', B='0.000000,0.000000,30000.000000'); tl2 = w.call(AC + 'K2_GetActorLocation'); w.link(w.get('TargetCannon'), 'TargetCannon', tl2, 'self'); w.link(tl2, 'ReturnValue', up, 'A')
    tr = w.call(KS + 'LineTraceSingle', bTraceComplex='false', bIgnoreSelf='true'); w.link(up, 'ReturnValue', tr, 'Start'); tl3 = w.call(AC + 'K2_GetActorLocation'); w.link(w.get('TargetCannon'), 'TargetCannon', tl3, 'self'); w.link(tl3, 'ReturnValue', tr, 'End')
    br = w.call(GS + 'BreakHitResult'); w.link(tr, 'OutHit', br, 'Hit'); cl = w.call(GS + 'GetObjectClass'); w.link(br, 'HitActor', cl, 'Object'); isa = w.call(M + 'ClassIsChildOf'); w.link(cl, 'ReturnValue', isa, 'TestClass'); PL.set_pin_value(w.i(isa, 'ParentClass'), '/Script/Engine.StaticMeshActor')
    same = w.call(M + 'EqualEqual_ObjectObject'); w.link(br, 'HitActor', same, 'A'); w.link(w.get('TargetCannon'), 'TargetCannon', same, 'B'); roof = w.both(isa, w.nt(same))
    cond = w.both(w.both(w.nt(w.get('Inert'), 'Inert'), okb), w.nt(roof)); gate = w.branch(cond)
    for p in src: w.ex_to(p, tr)              # the trace is an executed node: it runs first, then the gate reads its result
    w.ex_to(BEL.find_then_pin(tr), gate)
    w.ex_to(BEL.find_output_pin(gate, 'then'), n[k])
    clr = w.place(w.ge.add_set_member_variable_node('PackStrike')); PL.set_pin_value(w.i(clr, 'PackStrike'), 'false'); w.ex_to(BEL.find_output_pin(gate, 'else'), clr)
    unreal.get_default_object(w.bp.generated_class()).set_editor_property('GateCannons', True); finish(w, before)
def do_spit():
    w = W(G + 'BPC_TentacleSpit'); n = w.n
    if not all(q in n for q in ('OnHit', 'Tick', 'SetNext')): raise SystemExit('GATE545 spit nodes missing; send i5 a fresh export of BPC_TentacleSpit')
    if '--revert' in A:
        if not w.mine: say('spit: nothing to revert'); return
        saved = {}
        for name in ('OnHit', 'Tick', 'SetNext'):
            g = next((PL.get_owning_node(p) for p in PL.list_connected_pins(BEL.find_then_pin(n[name])) if BEL.get_node_pos(PL.get_owning_node(p)).y >= YMIN), None)
            saved[name] = [q for q in PL.list_connected_pins(BEL.find_output_pin(g, 'then'))] if g else []
        w.ge.remove_nodes(w.mine)
        for name, qs in saved.items(): say('spit relink', name, [PL.try_create_connection(BEL.find_then_pin(n[name]), q) for q in qs])
        w.ge.remove_member_variable('Inert'); say('compile', BEL.compile_blueprint(w.bp)); say('saved', E.save_asset(w.path, only_if_is_dirty=False)); return
    if w.mine: say('spit: already wired', len(w.mine)); return
    if '--apply' not in A: say('WOULD add Inert branches after OnHit and Tick, and an indoor test after SetNext'); return
    BEL.compile_blueprint(w.bp); before = sorted(x.get_name() for x in w.ge.list_nodes_with_errors()); add_vars(w); w.n = n = {x.get_name(): x for x in w.ge.list_all_nodes()}
    def gate_after(name, cond):
        th = BEL.find_then_pin(n[name]); nx = list(PL.list_connected_pins(th))
        if len(nx) != 1: raise SystemExit('GATE545 %s.then has %d links, expected 1' % (name, len(nx)))
        PL.break_pin_links(th); g = w.branch(cond); w.ex_to(th, g)
        if not PL.try_create_connection(BEL.find_output_pin(g, 'then'), nx[0]): raise SystemExit('GATE545 relink failed after ' + name)
        return g
    gate_after('OnHit', w.nt(w.get('Inert'), 'Inert')); gate_after('Tick', w.nt(w.get('Inert'), 'Inert'))
    pw = w.call(GS + 'GetPlayerPawn'); lc = w.call(AC + 'K2_GetActorLocation'); w.link(pw, 'ReturnValue', lc, 'self'); gate_after('SetNext', w.outside(lc)); finish(w, before)
do_strike(); do_spit(); say('DONE')
