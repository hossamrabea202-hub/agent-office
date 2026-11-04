# #500 C++ round 2 (i5 for i9): make ACDHudBase the parent of BP_ZombieHUD (the bottom of the HUD chain, parent HUD today).
# Every HUD level above it then inherits the cached scan functions. Nothing in any graph changes. Editor idle, not in Play.
#   py reparent_hud_ue.py --dry-run     checks: C++ class loaded, BP_ZombieHUD's parent is HUD, compile errors now
#   py reparent_hud_ue.py --apply       backup Saved/bak500/BP_ZombieHUD.uasset.hudbase, reparent, compile the whole chain, save only without NEW errors
#   --bp <path>  test on a copy first (reviewer's order): --bp /Game/_tmpX/BP_ZombieHUD_copy --apply --nosave
import os, shutil, sys, unreal
A = sys.argv[1:]
BP = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
CHAIN = ['BP_MinimapHUD', 'BP_SkillTreeHUD', 'BP_BarracksHUD', 'BP_ArmyHUD', 'BP_ControlsHUD', 'BP_QueueHUD', 'BP_HeroHUD', 'BP_CommanderHUD', 'BP_ArmoryHUD', 'BP_NoticeHUD']
BEL, GE, EA = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
cls = unreal.load_class(None, '/Script/CastleDefender.CDHudBase')
if not cls: print('STOP: /Script/CastleDefender.CDHudBase is not loaded. Build the C++ module first. Nothing changed.'); raise SystemExit
bp = unreal.load_asset(BP); parent = bp.get_editor_property('parent_class')
print('BP', BP, '| parent now', parent.get_name() if parent else None)
if parent == cls: print('STOP: already reparented. Nothing changed.'); raise SystemExit
if not parent or parent.get_name() != 'HUD': print('STOP: expected parent HUD. Nothing changed.'); raise SystemExit
def errs(b):
    # real compile status first (reviewer: not only error nodes in the main graph), plus error nodes for the report
    BEL.compile_blueprint(b)
    out = sorted(n.get_name() for n in GE.get_graph_editor(BEL.find_event_graph(b)).list_nodes_with_errors())
    try:
        st = str(b.get_editor_property('status'))
        if 'ERROR' in st.upper(): out.append('STATUS:' + st)
    except Exception: pass
    return out
chain = [unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/' + h) for h in CHAIN] if '--bp' not in A else []
before = {b.get_name(): errs(b) for b in [bp] + [c for c in chain if c]}
print('errors before:', {k: len(v) for k, v in before.items()})
if '--apply' not in A: print('dry run, nothing changed'); raise SystemExit
if '--nosave' not in A:
    src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + BP[len('/Game/'):] + '.uasset'
    dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak500/' + os.path.basename(src) + '.hudbase'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copy2(src, dst); print('backup', dst)
BEL.reparent_blueprint(bp, cls)
new = {}
for b in [bp] + [c for c in chain if c]:
    e = errs(b); n = [x for x in e if x not in before.get(b.get_name(), [])]
    if n: new[b.get_name()] = n
print('RESULT parent', bp.get_editor_property('parent_class').get_name(), '| new errors', new)
if new: print('NOT SAVED: new errors. Reload without saving (or restart the editor) and send i5 this output.'); raise SystemExit
if '--nosave' in A: print('reparented, not saved (--nosave)')
else: EA.save_asset(BP, only_if_is_dirty=False); print('saved', BP)
