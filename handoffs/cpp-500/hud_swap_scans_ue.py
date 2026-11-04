# #500 C++ round 2 (i5 for i9): swap the HUD chain's world scans for ACDHudBase's cached versions, in place, ONE Blueprint at a time.
#   GetAllActorsOfClass -> GetCachedActorsOfClass,  GetAllActorsWithTag -> GetCachedActorsWithTag
#   GetActorOfClass -> GetCachedActorOfClass ONLY with --include-single (the cache keeps the first actor found: right for singletons, not in general)
# Reviewer's rules (11-04): every graph of the Blueprint, nodes found by their function reference (GameplayStatics), the swap is first done on a COPY,
# compiled and compared (compile status + every link and value), and only then on the original. Start with ONE Blueprint and Play-check it.
#   py hud_swap_scans_ue.py                                   dry run: every matching node per Blueprint and graph; changes nothing
#   py hud_swap_scans_ue.py --apply --only BP_CommanderHUD    copy test, then the real one: backup Saved/bak500/<BP>.uasset.hud2, save only if clean
#   --skip <NodeName,...>  keep these on the engine node     --include-single  also swap GetActorOfClass
# Needs: the C++ module built and BP_ZombieHUD reparented to CDHudBase (reparent_hud_ue.py). Editor idle, not in Play.
# Revert: close the editor, copy Saved/bak500/<BP>.uasset.hud2 back over Content/CastleDefender/Gameplay/Castle/<BP>.uasset.
import os, shutil, sys, time, unreal
A = sys.argv[1:]
APPLY = '--apply' in A
ONLY = A[A.index('--only') + 1] if '--only' in A else None
SKIP = set(A[A.index('--skip') + 1].split(',')) if '--skip' in A else set()
BEL, PL, GE, EA = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Gameplay/Castle/'
HUDS = ['BP_ZombieHUD', 'BP_MinimapHUD', 'BP_SkillTreeHUD', 'BP_BarracksHUD', 'BP_ArmyHUD', 'BP_ControlsHUD', 'BP_QueueHUD', 'BP_HeroHUD',
        'BP_CommanderHUD', 'BP_ArmoryHUD', 'BP_NoticeHUD']
MAP = {  # GameplayStatics function -> (cached function, input pins, output pins)
    'GetAllActorsOfClass': ('GetCachedActorsOfClass', ['ActorClass'], ['OutActors']),
    'GetAllActorsWithTag': ('GetCachedActorsWithTag', ['Tag'], ['OutActors']),
}
if '--include-single' in A:
    MAP['GetActorOfClass'] = ('GetCachedActorOfClass', ['ActorClass'], ['ReturnValue'])
if APPLY and not ONLY:
    print('STOP: --apply needs --only <Blueprint> (one at a time, Play-check between). Nothing changed.'); raise SystemExit
BASE = unreal.load_class(None, '/Script/CastleDefender.CDHudBase')
if not BASE: print('STOP: /Script/CastleDefender.CDHudBase not loaded. Build the C++ module first. Nothing changed.'); raise SystemExit

def graphs(bp):
    """Every graph we can reach; says which way it got them."""
    for fn in ('list_graphs', 'get_all_graphs'):
        f = getattr(BEL, fn, None)
        if f:
            try:
                g = list(f(bp))
                if g: return g, fn
            except Exception: pass
    out = [BEL.find_event_graph(bp)]
    for prop in ('ubergraph_pages', 'function_graphs', 'macro_graphs'):
        try: out += [g for g in bp.get_editor_property(prop) if g not in out]
        except Exception: pass
    return [g for g in out if g], 'properties' if len(out) > 1 else 'EVENT GRAPH ONLY (other graphs not reachable from Python here: check them by hand)'

def function_of(n):
    """(owner class name, function name) from the node's function reference; title only as a labelled fallback."""
    try:
        ref = n.get_editor_property('function_reference')
        name = str(ref.get_editor_property('member_name'))
        parent = ref.get_editor_property('member_parent')
        return (parent.get_name() if parent else '?'), name, 'ref'
    except Exception:
        t = str(n.get_node_title()).replace(' ', '').replace('\n', '')
        has_ctx = any(str(PL.get_pin_name(p)) == 'WorldContextObject' for p in BEL.list_all_pins(n))
        return ('GameplayStatics' if has_ctx else '?'), t, 'title'

def pin(n, name, out):
    p = BEL.find_output_pin(n, name) if out else BEL.find_input_pin(n, name)
    return p if p and PL.is_valid(p) else None

def links(n):
    return sum(len(PL.list_connected_pins(p)) for p in BEL.list_all_pins(n))

def compiled_ok(bp):
    BEL.compile_blueprint(bp)
    try:
        st = bp.get_editor_property('status')
        if st is not None: return 'ERROR' not in str(st).upper(), str(st)
    except Exception: pass
    bad = []
    for g, _ in [(g, 0) for g in graphs(bp)[0]]:
        bad += [x.get_name() for x in GE.get_graph_editor(g).list_nodes_with_errors()]
    return not bad, 'nodes with errors: %s' % bad

def find_targets(bp):
    gs, how = graphs(bp); found = []
    for g in gs:
        for n in GE.get_graph_editor(g).list_all_nodes():
            if n.get_class().get_name() != 'K2Node_CallFunction': continue
            owner, fn, via = function_of(n)
            if fn in MAP and owner.startswith('GameplayStatics') and n.get_name() not in SKIP:
                found.append((g, n, fn, via))
    return found, how

def swap(bp):
    """Swap every target in bp. Returns (count, failures)."""
    targets, _ = find_targets(bp); fails = []
    for g, old, fn, via in targets:
        ge = GE.get_graph_editor(g)
        cfn, ins, outs = MAP[fn]
        before = links(old)
        new = ge.add_call_function_node('/Script/CastleDefender.CDHudBase:' + cfn)
        if not new: fails.append('%s (could not create %s)' % (old.get_name(), cfn)); continue
        try: BEL.set_node_pos(new, unreal.IntPoint(old.get_editor_property('node_pos_x'), old.get_editor_property('node_pos_y') + 40))
        except Exception: pass
        for name in ins:                      # class / tag first: it types the outputs
            op, np = pin(old, name, False), pin(new, name, False)
            if not op or not np: fails.append('%s.%s (no pin)' % (old.get_name(), name)); continue
            srcs = PL.list_connected_pins(op)
            for s in srcs:
                if not PL.try_create_connection(s, np): fails.append('%s.%s (input link)' % (old.get_name(), name))
            if not srcs and not PL.set_pin_value(np, PL.get_pin_value(op)):
                fails.append('%s.%s = %s (value refused)' % (old.get_name(), name, PL.get_pin_value(op)))
        ex_old, ex_new = pin(old, 'execute', False), pin(new, 'execute', False)
        for s in (PL.list_connected_pins(ex_old) if ex_old else []):
            if not ex_new or not PL.try_create_connection(s, ex_new): fails.append(old.get_name() + '.execute (link)')
        for name in ['then'] + outs:
            op, np = pin(old, name, True), pin(new, name, True)
            if not op: continue
            for t in list(PL.list_connected_pins(op)):
                if not np or not PL.try_create_connection(np, t): fails.append('%s.%s -> %s (output link)' % (old.get_name(), name, PL.get_owning_node(t).get_name()))
        after = links(new)
        if after != before: fails.append('%s: %d links before, %d after on the new node' % (old.get_name(), before, after))
        ge.remove_nodes([old])
    return len(targets), fails

total = 0
for h in HUDS:
    if ONLY and h != ONLY: continue
    bp = unreal.load_asset(P + h)
    if not bp: print(h, 'missing'); continue
    targets, how = find_targets(bp)
    total += len(targets)
    print('%-16s graphs via %s | %d to swap: %s' % (h, how, len(targets), ', '.join('%s/%s(%s,%s)' % (g.get_name(), n.get_name(), fn, via) for g, n, fn, via in targets)))
    if not APPLY or not targets: continue
    if not unreal.MathLibrary.class_is_child_of(bp.generated_class(), BASE):
        print('   STOP: %s does not inherit CDHudBase yet (reparent_hud_ue.py first). Nothing changed.' % h); continue
    ok0, st0 = compiled_ok(bp)
    if not ok0: print('   STOP: %s does not compile cleanly BEFORE the swap (%s). Nothing changed.' % (h, st0)); continue
    # 1. on a copy (new folder per run: never delete a temp Blueprint and reuse it in the same editor session)
    tmp = '/Game/_hudswap_%s/%s_test' % (time.strftime('%H%M%S'), h)
    EA.duplicate_asset(P + h, tmp); cp = unreal.load_asset(tmp)
    n, fails = swap(cp); okc, stc = compiled_ok(cp)
    rest, _ = find_targets(cp)
    print('   COPY %s: swapped %d | failures %s | compile %s (%s) | matching nodes left %d' % (tmp, n, fails, okc, stc, len(rest)))
    if fails or not okc or rest:
        print('   STOP: the copy did not pass. The original is untouched.'); continue
    # 2. the original
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + (P + h)[len('/Game/'):] + '.uasset'
    dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak500/' + h + '.uasset.hud2'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(src, dst)
    n, fails = swap(bp); ok, st = compiled_ok(bp)
    print('   REAL %s: swapped %d | failures %s | compile %s (%s)' % (h, n, fails, ok, st))
    if fails or not ok:
        print('   NOT SAVED. The in-memory Blueprint is changed: File > Reload it (or restart the editor without saving) and send i5 this output.'); continue
    EA.save_asset(P + h, only_if_is_dirty=False); print('   saved %s (backup %s). Play-check it before the next one.' % (h, dst))
print('total matching nodes: %d' % total)
if not APPLY: print('dry run, nothing changed')
