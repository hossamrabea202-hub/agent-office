# #500 step 3 (i5 for i9): make the C++ class AZombieBase the parent of BP_Zombie (was Character). BP_Zombie keeps every variable, component and graph.
# Needs the C++ module compiled first (README_CPP.md steps 1-2). Editor idle, not in Play.
#   py reparent_zombie_ue.py --dry-run     checks: C++ class loaded, BP_Zombie's parent is Character, compile errors now
#   py reparent_zombie_ue.py --apply       backup Saved/bak472/BP_Zombie.uasset.fix500, reparent, compile, save only if no NEW errors
#   --bp <path>  another Blueprint (test on a copy: --bp /Game/_i5tmpX/Zc0 --apply --nosave)
# Revert: close the editor, copy the backup back over Content/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.uasset.
import os, shutil, sys, unreal
A = sys.argv[1:]
BP = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
BEL, GE, EA = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
cls = unreal.load_class(None, '/Script/CastleDefender.ZombieBase')
if not cls: print('STOP: /Script/CastleDefender.ZombieBase is not loaded. Build the C++ module first (README_CPP.md). Nothing changed.'); raise SystemExit
bp = unreal.load_asset(BP); parent = bp.get_editor_property('parent_class')
print('BP', BP, '| parent now', parent.get_name() if parent else None, '| new parent', cls.get_name())
if parent == cls: print('STOP: already reparented. Nothing changed.'); raise SystemExit
if not parent or parent.get_name() != 'Character': print('STOP: expected parent Character. Nothing changed.'); raise SystemExit
def errors():
    BEL.compile_blueprint(bp); return sorted(n.get_name() for n in GE.get_graph_editor(BEL.find_event_graph(bp)).list_nodes_with_errors())
before = errors(); print('errors before:', before)
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if '--nosave' not in A:
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + BP[len('/Game/'):] + '.uasset'
    dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/' + os.path.basename(src) + '.fix500'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(src, dst); print('backup', dst)
BEL.reparent_blueprint(bp, cls)
after = errors(); new = [e for e in after if e not in before]
print('RESULT parent', bp.get_editor_property('parent_class').get_name(), '| new errors', new, '| old errors', [e for e in after if e in before])
if new: print('NOT SAVED: new errors. Reload BP_Zombie without saving (or restart the editor), send i5 this output.'); raise SystemExit
if '--nosave' in A: print('reparented, not saved (--nosave)')
else: EA.save_asset(BP, only_if_is_dirty=False); print('saved', BP)
