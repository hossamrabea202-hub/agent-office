# #31 + #68 step 1 (laptop2, 2026-10-29): adds the variables the two pastes use. Safe to re-run.
# Run in the editor:  py "<repo>/handoffs/notice-banner-31/bp/add_vars_31_68.py"
import unreal

BEL, EAL = unreal.BlueprintEditorLibrary, unreal.EditorAssetLibrary
def _var_names(bp, wanted):
    """UE 5.8: Blueprint.new_variables is not readable from Python (#380). Compile, then probe the class default object."""
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have
C = '/Game/CastleDefender/Gameplay/Castle/'
WANT = {
    C + 'BP_ZombieHUD': {'PromptVesnaEnv': 'real', 'PromptVesnaShown': 'real', 'PromptVesnaVis': 'bool', 'PromptLastT': 'real'},
    C + 'BP_NoticeHUD': {'NoticeQ': 'string', 'NoticeCur': 'string', 'NoticeTier': 'real', 'NoticeT0': 'real', 'NoticeHold': 'real',
                         'NoticeOn': 'bool', 'NoticeNext': 'real', 'NoticeLastT': 'real', 'NoticeMID': unreal.MaterialInstanceDynamic},
}
log, manual = [], []
for path, vars_ in WANT.items():
    bp = unreal.load_asset(path)
    try:
        have = _var_names(bp, vars_)
    except Exception:
        have = set()
    for n, t in vars_.items():
        if n in have: continue
        try:
            if isinstance(t, str):
                pt = BEL.get_basic_type_by_name(t)
                pass  # UE 5.8: 'real' is already double; EdGraphPinType fields can't be set from Python
            else:
                pt = BEL.get_object_reference_type(t)
            ok = BEL.add_member_variable(bp, n, pt)
        except Exception as e:
            ok = False; log.append('  %s: %s' % (n, e))
        (log if ok else manual).append('%s %s.%s' % ('+' if ok else 'ADD BY HAND', path.split('/')[-1], n))
    BEL.compile_blueprint(bp)
    EAL.save_asset(path)
unreal.log('#31/#68 variables:\n' + '\n'.join(log + manual))
