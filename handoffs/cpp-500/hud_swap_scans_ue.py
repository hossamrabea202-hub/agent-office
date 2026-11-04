# #500 C++ round 2 (i5 for i9): swap the HUD chain's world scans for ACDHudBase's cached versions, in place, one Blueprint at a time.
#   GetActorOfClass -> GetCachedActorOfClass,  GetAllActorsOfClass -> GetCachedActorsOfClass,  GetAllActorsWithTag -> GetCachedActorsWithTag
# Same pin names: every link (exec in / out, inputs, outputs) and every pin value (class, tag) moves to the new node; the old node is removed.
# Needs: the C++ module built, and BP_ZombieHUD reparented to CDHudBase first (reparent_hud_ue.py), so every HUD level inherits the cached functions.
#   py hud_swap_scans_ue.py                      dry run: lists every node it would swap, per Blueprint; changes nothing
#   py hud_swap_scans_ue.py --apply [--only BP_CommanderHUD]   backup Saved/bak500/<BP>.uasset.hud2, swap, compile, save ONLY if no new errors
#   --skip <NodeName,...>   leave these nodes on the engine version (where a result must be exact this frame)
# Revert: close the editor, copy Saved/bak500/<BP>.uasset.hud2 back over Content/CastleDefender/Gameplay/Castle/<BP>.uasset.
import os, shutil, sys, unreal
A = sys.argv[1:]
APPLY = '--apply' in A
ONLY = A[A.index('--only') + 1] if '--only' in A else None
SKIP = set(A[A.index('--skip') + 1].split(',')) if '--skip' in A else set()
BEL, PL, GE, EA = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Gameplay/Castle/'
HUDS = ['BP_ZombieHUD', 'BP_MinimapHUD', 'BP_SkillTreeHUD', 'BP_BarracksHUD', 'BP_ArmyHUD', 'BP_ControlsHUD', 'BP_QueueHUD', 'BP_HeroHUD',
        'BP_CommanderHUD', 'BP_ArmoryHUD', 'BP_NoticeHUD']
MAP = {  # engine title -> (cached function, input pins, output pins)
    'GetActorOfClass': ('GetCachedActorOfClass', ['ActorClass'], ['ReturnValue']),
    'GetAllActorsOfClass': ('GetCachedActorsOfClass', ['ActorClass'], ['OutActors']),
    'GetAllActorsWithTag': ('GetCachedActorsWithTag', ['Tag'], ['OutActors']),
}
BASE = unreal.load_class(None, '/Script/CastleDefender.CDHudBase')
if not BASE: print('STOP: /Script/CastleDefender.CDHudBase not loaded. Build the C++ module first. Nothing changed.'); raise SystemExit

def inherits(bp):
    return unreal.MathLibrary.class_is_child_of(bp.generated_class(), BASE)

def pin(n, name, out):
    p = BEL.find_output_pin(n, name) if out else BEL.find_input_pin(n, name)
    return p if p and PL.is_valid(p) else None

def title(n): return str(n.get_node_title()).replace(' ', '').replace('\n', '')

def errors(bp):
    BEL.compile_blueprint(bp)
    return sorted(x.get_name() for x in GE.get_graph_editor(BEL.find_event_graph(bp)).list_nodes_with_errors())

total = 0
for h in HUDS:
    if ONLY and h != ONLY: continue
    bp = unreal.load_asset(P + h)
    if not bp: print(h, 'missing'); continue
    ge = GE.get_graph_editor(BEL.find_event_graph(bp))
    targets = [n for n in ge.list_all_nodes() if n.get_class().get_name() == 'K2Node_CallFunction' and title(n) in MAP and n.get_name() not in SKIP]
    print('%-16s %d to swap: %s' % (h, len(targets), ', '.join('%s(%s)' % (n.get_name(), title(n)) for n in targets)))
    total += len(targets)
    if not APPLY or not targets: continue
    if not inherits(bp):
        print('   STOP %s: does not inherit CDHudBase yet (run reparent_hud_ue.py on BP_ZombieHUD first). Nothing changed here.' % h); continue
    before = errors(bp)
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + (P + h)[len('/Game/'):] + '.uasset'
    dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak500/' + h + '.uasset.hud2'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(src, dst)
    fails = []
    for old in targets:
        fn, ins, outs = MAP[title(old)]
        new = ge.add_call_function_node('/Script/CastleDefender.CDHudBase:' + fn)
        if not new: fails.append(old.get_name() + ' (could not create ' + fn + ')'); continue
        try: BEL.set_node_pos(new, unreal.IntPoint(old.get_editor_property('node_pos_x'), old.get_editor_property('node_pos_y') + 40))
        except Exception: pass
        for name in ins:                                   # value or link of the class / tag pin first: it types the outputs
            op, np = pin(old, name, False), pin(new, name, False)
            if not op or not np: fails.append('%s.%s (no pin)' % (old.get_name(), name)); continue
            src_links = PL.list_connected_pins(op)
            if src_links:
                for s in src_links:
                    if not PL.try_create_connection(s, np): fails.append('%s.%s (in link)' % (old.get_name(), name))
            elif not PL.set_pin_value(np, PL.get_pin_value(op)):
                fails.append('%s.%s = %s (value refused)' % (old.get_name(), name, PL.get_pin_value(op)))
        ex_old, ex_new = pin(old, 'execute', False), pin(new, 'execute', False)
        if ex_old and ex_new:
            for s in PL.list_connected_pins(ex_old):
                if not PL.try_create_connection(s, ex_new): fails.append(old.get_name() + '.execute (link)')
        elif ex_old and PL.list_connected_pins(ex_old):
            fails.append(old.get_name() + '.execute (new node has no exec pin)')
        for name in ['then'] + outs:
            op, np = pin(old, name, True), pin(new, name, True)
            if not op: continue
            if not np: fails.append('%s.%s (no out pin)' % (old.get_name(), name)); continue
            for t in PL.list_connected_pins(op):
                PL.break_single_pin_link(op, t)
                if not PL.try_create_connection(np, t): fails.append('%s.%s -> %s (out link)' % (old.get_name(), name, PL.get_owning_node(t).get_name()))
        ge.remove_nodes([old])
    after = errors(bp); new_err = [e for e in after if e not in before]
    print('   RESULT %s | link/value failures %s | new errors %s | old errors %d' % (h, fails, new_err, len(before)))
    if fails or new_err:
        print('   NOT SAVED: reload %s without saving (or restart the editor) and send i5 this output.' % h); continue
    EA.save_asset(P + h, only_if_is_dirty=False); print('   saved', h, '(backup', dst + ')')
print('total nodes %s: %d' % ('swapped' if APPLY else 'to swap', total))
if not APPLY: print('dry run, nothing changed')
