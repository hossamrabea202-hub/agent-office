# Shop keys that can never fire (i5, 2026-11-04, audit BP_AUDIT.md). Flares, Medics, Cavalry, Castle Upgrades do: Set KeyWas = key, THEN Branch(key AND NOT KeyWas).
# A pure getter reads the value just written, so the test is always false. Fix: a Sequence runs the Branch first, the Set second, so the Branch sees last frame's value.
# Nothing else changes. These buy actions have never fired from the key, so watch gold costs + balance in Play.
#   py shop_keys_fix_ue.py --dry-run                checks all 4, changes nothing
#   py shop_keys_fix_ue.py --apply                  fixes, compiles, saves each one ONLY if clean. Backup in Saved/bak472/
#   py shop_keys_fix_ue.py --apply --copy <folder>  i5 test on duplicates in a NEW folder, never saved
# Revert: restart without saving; after a save, copy Saved/bak472/<name>.uasset.fixKeys back with the editor closed. Aborts in PIE.
import os, shutil, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()
FIX = {'BPC_Flares': ('fxSetFWas32', 'fxIfBuy33'), 'BPC_Medics': ('mdSetMWas40', 'mdIfM41'), 'BPC_Cavalry': ('ccSetLWas49', 'ccIfL50'), 'BPC_CastleUpgrades': ('cuSetJWas62', 'cuIfJ63')}
out = lambda n, p: BEL.find_output_pin(n, p); inp = lambda n, p: BEL.find_input_pin(n, p)
def path_of(name):
    hits = [str(a.package_name) for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'Blueprint')) if str(a.asset_name) == name and '/_i5tmp' not in str(a.package_name)]
    return hits[0] if hits else None
for name, (s_name, b_name) in FIX.items():
    P = path_of(name)
    if not P: print(name, 'MISSING'); continue
    if '--copy' in A:
        T = A[A.index('--copy') + 1] + '/' + name + 'K'
        if not E.does_asset_exist(T): E.duplicate_asset(P, T)
        P = T
    bp = unreal.load_asset(P); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); L = {n.get_name(): n for n in ge.list_all_nodes()}
    s, b = L.get(s_name), L.get(b_name)
    if not s or not b: print(name, 'STOP, nodes missing:', s_name, b_name, '(changed since the 11-03 export?)'); continue
    prev = PL.list_connected_pins(inp(s, 'execute')); nxt = PL.list_connected_pins(out(s, 'then'))
    if len(nxt) != 1 or PL.get_owning_node(nxt[0]).get_name() != b_name: print(name, 'STOP: Set no longer goes straight to the Branch, already fixed?'); continue
    if not prev: print(name, 'STOP: nothing runs the Set'); continue
    print(name, 'check OK:', PL.get_owning_node(prev[0]).get_name(), '->', s_name, '->', b_name)
    if '--apply' not in A: continue
    if '--copy' not in A:
        src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + P[len('/Game/'):] + '.uasset'
        d = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(d, exist_ok=True)
        if not os.path.exists(d + os.path.basename(src) + '.fixKeys'): shutil.copy2(src, d + os.path.basename(src) + '.fixKeys')
    seq = ge.create_node_from_name('Utilities|FlowControl|Sequence', unreal.Vector2D(0, 0), [])
    srcs = list(prev); fails = []
    PL.break_pin_links(inp(s, 'execute')); PL.break_pin_links(out(s, 'then'))
    for q in srcs:
        if not PL.try_create_connection(q, inp(seq, 'execute')): fails.append('prev -> seq')
    if not PL.try_create_connection(out(seq, 'then_0'), inp(b, 'execute')): fails.append('seq -> branch')
    if not PL.try_create_connection(out(seq, 'then_1'), inp(s, 'execute')): fails.append('seq -> set')
    ok = BEL.compile_blueprint(bp); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); err = [x.get_name() for x in ge.list_nodes_with_errors()]
    print(name, 'RESULT compile', ok, '| failures', fails, '| errors', err)
    if '--copy' in A: continue
    if fails or err or not ok: print(name, 'NOT SAVED: restart without saving and send i5 this')
    else: print(name, 'saved', E.save_asset(P, only_if_is_dirty=False))
if '--apply' not in A: print('dry run, nothing changed')
