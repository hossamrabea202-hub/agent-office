# F1 "WEAPONSMITH list draws over Vesna's shop" (i5, 2026-11-04). BP_ArmoryHUD skips DrawArmoury while VesnaTrade.Covering (TradeObsIfC), but DrawWeapons hangs off
# another Sequence output (Muster -> Reveal -> WeaponHookIf) with no such check. This gives the weapon list the same guard, with 2 Branches. Nothing else changes.
#   py f1_fix_ue.py --dry-run     checks every node + pin, changes nothing
#   py f1_fix_ue.py --apply       adds the guard, compiles, saves ONLY if clean. Backup in Saved/bak472/
#   py f1_fix_ue.py --apply --copy <folder>     i5 test on a duplicate in a NEW folder, never saved
# Revert: restart without saving; after a save, copy Saved/bak472/BP_ArmoryHUD.uasset.fixF1 back with the editor closed. Aborts in PIE.
import os, shutil, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
PATH = '/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD'
if '--copy' in A:
    T_ = A[A.index('--copy') + 1] + '/ArmoryF1'
    if not E.does_asset_exist(T_): E.duplicate_asset(PATH, T_)
    PATH = T_
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
NEED = {'WeaponHookIf': ('then', True), 'whHookWeapons5': ('execute', False), 'thIsValid8': ('ReturnValue', True), 'thGetCovering9': ('Covering', True)}
bad = [k for k, (p, out) in NEED.items() if k not in live or not (BEL.find_output_pin(live[k], p) if out else BEL.find_input_pin(live[k], p))]
if bad: print('STOP, nothing changed. Missing:', bad); raise SystemExit
now = PL.list_connected_pins(BEL.find_output_pin(live['WeaponHookIf'], 'then'))
if not now or PL.get_owning_node(now[0]).get_name() != 'whHookWeapons5': print('STOP: WeaponHookIf.then does not go straight to whHookWeapons5, already fixed? Nothing changed'); raise SystemExit
print('check OK: WeaponHookIf -> whHookWeapons5 has no Covering check')
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if '--copy' not in A:
    s = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + PATH[len('/Game/'):] + '.uasset'
    d = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d + os.path.basename(s) + '.fixF1'): shutil.copy2(s, d + os.path.basename(s) + '.fixF1')
fails = []
def link(p, q, label):
    if not p or not q or not PL.try_create_connection(p, q): fails.append(label)
b1 = ge.add_branch_node(); b2 = ge.add_branch_node()
out = lambda n, p: BEL.find_output_pin(n, p); inp = lambda n, p: BEL.find_input_pin(n, p)
PL.break_pin_links(out(live['WeaponHookIf'], 'then'))
link(out(live['WeaponHookIf'], 'then'), inp(b1, 'execute'), 'hook -> valid branch')
link(out(live['thIsValid8'], 'ReturnValue'), inp(b1, 'Condition'), 'IsValid -> b1')
link(out(b1, 'then'), inp(b2, 'execute'), 'b1 -> b2')
link(out(live['thGetCovering9'], 'Covering'), inp(b2, 'Condition'), 'Covering -> b2')
link(out(b2, 'else'), inp(live['whHookWeapons5'], 'execute'), 'not covering -> weapons')
link(out(b1, 'else'), inp(live['whHookWeapons5'], 'execute'), 'no trade component -> weapons')
ok = BEL.compile_blueprint(bp); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); err = [n.get_name() for n in ge.list_nodes_with_errors()]
print('RESULT compile', ok, '| link failures', fails, '| errors', err)
if '--copy' in A: print('test copy, not saved'); raise SystemExit
if fails or err or not ok: print('NOT SAVED. Do not save; restart the editor and send i5 this output.')
else: print('saved', E.save_asset(PATH, only_if_is_dirty=False))
