# Medieval ground (i5, 2026-11-04, card #482): M_MountainBackdrop draws car TYRE TREAD on the castle roads (chevron blocks every 11 cm in the rut normals).
# This sets the tread height to 0. The cart ruts themselves, their depth, mud and puddles stay exactly as they are. One line in one Custom node.
#   py no_tread_ue.py --dry-run     finds the line (must be exactly 1), changes nothing
#   py no_tread_ue.py --apply       replaces it, recompiles, saves the material. No map save. The landscape shaders recompile: can take minutes
#   py no_tread_ue.py --revert      puts the old line back, recompiles, saves
# Aborts in PIE.
import sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Environment/Mountains/Materials/M_MountainBackdrop'
OLD = 'float tA = 1.3 * tread * gx * step(abs(x), tw * 1.1) * dep / 9.0;'
NEW = 'float tA = 0.0;   // #482: no tyre tread on medieval cart ruts. Was: 1.3 * tread * gx * step(abs(x), tw * 1.1) * dep / 9.0'
m = unreal.load_asset(P); pp = m.get_path_name()
nodes = [x for x in unreal.ObjectIterator(unreal.MaterialExpressionCustom) if x.get_path_name().startswith(pp + ':') or x.get_path_name().startswith(pp + '.')]
frm, to = (NEW, OLD) if '--revert' in A else (OLD, NEW)
hits = [(x, x.get_editor_property('code').count(frm)) for x in nodes]
total = sum(n for _, n in hits)
print('custom nodes', len(nodes), '| lines to change', total, '| already other way', sum(x.get_editor_property('code').count(to) for x in nodes))
if total != 1: print('STOP: expected exactly 1, nothing changed'); raise SystemExit
if '--apply' not in A and '--revert' not in A: print('dry run: nothing changed'); raise SystemExit
for x, n in hits:
    if n: x.set_editor_property('code', x.get_editor_property('code').replace(frm, to))
MEL.recompile_material(m)
print('saved', EAL.save_loaded_asset(m), '| look at the gate road close up: ruts stay, no chevron pattern')
