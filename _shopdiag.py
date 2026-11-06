import unreal, traceback
r = []
try:
    w = unreal.UnrealEditorSubsystem().get_game_world() if hasattr(unreal, 'UnrealEditorSubsystem') else None
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    r.append('pie world %s' % w)
    mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
    r.append('Shop %s' % unreal.KismetMaterialLibrary.get_vector_parameter_value(w, mpc, 'Shop'))
    r.append('paused %s' % unreal.GameplayStatics.is_game_paused(w))
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    hud = pc.get_hud() if pc else None
    r.append('HUD class %s' % (hud.get_class().get_name() if hud else None))
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.HUD): r.append('  hud actor %s' % a.get_class().get_name())
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    r.append('pawn %s' % (p.get_class().get_name() if p else None))
    oc = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet').generated_class()
    c = p.get_component_by_class(oc) if p else None
    r.append('obs comp %s' % c)
    if c:
        for k in ('AvailMask','PieceId','Owned','Worn','OwnMask','WearMask','Bought','PanelOpen','Sel','Hover'):
            try: r.append('  %s = %s' % (k, c.get_editor_property(k)))
            except Exception: pass
except BaseException:
    r.append(traceback.format_exc()[-800:])
open(r'C:/Users/hossa/Documents/agent-office/_shopdiag.txt', 'w').write('\n'.join(r))
