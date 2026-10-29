# #31 + #68 step 1 (laptop2, 2026-10-29): adds the variables the two pastes use. Safe to re-run.
# Run in the editor:  py "<repo>/handoffs/notice-banner-31/bp/add_vars_31_68.py"
import unreal

BEL, EAL = unreal.BlueprintEditorLibrary, unreal.EditorAssetLibrary
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
        have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
    except Exception:
        have = set()
    for n, t in vars_.items():
        if n in have: continue
        try:
            if isinstance(t, str):
                pt = BEL.get_basic_type_by_name(t)
                if t == 'real': pt.set_editor_property('pin_sub_category', 'double')
            else:
                pt = BEL.get_object_reference_type(t)
            ok = BEL.add_member_variable(bp, n, pt)
        except Exception as e:
            ok = False; log.append('  %s: %s' % (n, e))
        (log if ok else manual).append('%s %s.%s' % ('+' if ok else 'ADD BY HAND', path.split('/')[-1], n))
    BEL.compile_blueprint(bp)
    EAL.save_asset(path)
unreal.log('#31/#68 variables:\n' + '\n'.join(log + manual))
