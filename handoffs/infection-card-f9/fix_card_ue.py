# F9 INFECTED card (i5, 2026-11-04). The flat grey box is the FALLBACK rect: BPC_Infection's CreateDynamicMaterialInstance (iMakeMID1) has an empty Parent pin
# (asset default lost on paste, same family as F12), so CardMID is never valid and the designed M_HintCard card never draws. One pin.
#   py fix_card_ue.py --dry-run     shows the pin + a control pin, changes nothing
#   py fix_card_ue.py --apply       sets Parent = M_HintCard, compiles, saves only if clean. Backup in Saved/bak472/
#   py fix_card_ue.py --revert      clears the pin, compiles, saves. Aborts in PIE.
import os, shutil, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
BEL, PL, GE, E = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Gameplay/Castle/BPC_Infection'; HINT = '/Game/CastleDefender/UI/Hints/M_HintCard.M_HintCard'
bp = unreal.load_asset(P); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); nodes = {n.get_name(): n for n in ge.list_all_nodes()}
n = nodes.get('iMakeMID1'); p = BEL.find_input_pin(n, 'Parent') if n else None
if not p: print('STOP: iMakeMID1.Parent not found, nothing changed'); raise SystemExit
print('Parent value: [%s] connected %d | M_HintCard exists %s' % (PL.get_pin_value(p), len(PL.list_connected_pins(p)), E.does_asset_exist(HINT.split('.')[0])))
ctl = [(k, str(PL.get_pin_name(q)), PL.get_pin_value(q)) for k, m in nodes.items() for q in BEL.list_input_pins(m) if str(PL.get_pin_name(q)) in ('Collection', 'Sound', 'Font', 'Material') and PL.get_pin_value(q)][:3]
print('control object pins with a value:', ctl)
if '--apply' not in A and '--revert' not in A: print('dry run: nothing changed'); raise SystemExit
s = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + P[len('/Game/'):] + '.uasset'
d = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/'; os.makedirs(d, exist_ok=True)
if not os.path.exists(d + os.path.basename(s) + '.fixF9'): shutil.copy2(s, d + os.path.basename(s) + '.fixF9')
ok_set = PL.set_pin_value(p, '' if '--revert' in A else HINT)
ok = BEL.compile_blueprint(bp); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); err = [x.get_name() for x in ge.list_nodes_with_errors()]
print('RESULT set', ok_set, '| value now [%s] | compile %s | errors %s' % (PL.get_pin_value(BEL.find_input_pin(n, 'Parent')), ok, err))
if ok_set and ok and not err and '--nosave' not in A: print('saved', E.save_asset(P, only_if_is_dirty=False))
else: print('NOT SAVED')
