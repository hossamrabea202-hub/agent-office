# #269 bug "no 3D reveal shows on pickup" (adjustedfilm, 2026-10-31): READ-ONLY check of every link of the reveal chain.
# Run it WHILE PLAYING (PIE), after picking up the book (or any time):
#   py "<repo>/handoffs/reveal-aaa-268/diag_reveal268_ue.py"              (only reports)
#   py "<repo>/handoffs/reveal-aaa-268/diag_reveal268_ue.py" --replay     (also forces the book reveal to play again now)
# Writes <repo>/handoffs/reveal-aaa-268/diag_reveal268.txt -> commit + push it (or paste the Output Log lines on #269).
# Changes nothing in assets. --replay only touches the running game (BookOpened = false, MPC_SkillTree.BookAge = 0.1).
import os, sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
REPLAY = '--replay' in sys.argv
out = ['#269 reveal diagnostic' + (' (+ replay)' if REPLAY else '')]
P = lambda *a: out.append(' '.join(str(x) for x in a))

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not world:
    P('NOT PLAYING: start Play (PIE) first, then run this again.')
else:
    GS = unreal.GameplayStatics
    hero = GS.get_player_character(world, 0)
    P('hero:', hero.get_class().get_name() if hero else None)
    fxc = unreal.load_class(None, '/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX.BPC_MotionFX_C')
    fx = hero.get_component_by_class(fxc) if hero and fxc else None
    P('BPC_MotionFX on hero:', bool(fx))
    if fx:
        for v in ('RvStage', 'RvCap', 'RvPivot', 'RvBook', 'RvBag', 'RvItemMID', 'RvBackMID', 'RvFrontMID',
                  'RvKind', 'RvT0', 'RvBookPend', 'RvBagPend', 'BookOpened', 'BagOpened', 'RvR', 'RvFlat'):
            try:
                val = fx.get_editor_property(v)
                P('  %-11s %s' % (v, val.get_name() if hasattr(val, 'get_name') else val))
            except Exception as e:
                P('  %-11s MISSING VARIABLE (%s)' % (v, e))
        cap = None
        try: cap = fx.get_editor_property('RvCap')
        except Exception: pass
        if cap:
            P('  capture target RT:', cap.get_editor_property('texture_target'))
            P('  capture show-only count:', len(cap.get_editor_property('show_only_components')))
    st = unreal.load_class(None, '/Game/CastleDefender/UI/Reveal/BP_RevealStage.BP_RevealStage_C')
    stages = GS.get_all_actors_of_class(world, st) if st else []
    P('BP_RevealStage class loaded:', bool(st), '| stages in world:', len(stages))
    for s in stages[:2]:
        P('  stage at', s.get_actor_location())
        for c in s.get_components_by_class(unreal.ActorComponent):
            P('   comp %-12s tags=%s' % (c.get_name(), [str(t) for t in c.get_editor_property('component_tags')]))
    mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
    for p in ('BookAge', 'BagAge'):
        P('MPC_SkillTree.%s =' % p, unreal.KismetMaterialLibrary.get_scalar_parameter_value(world, mpc, p) if mpc else 'MPC missing')
    rmpc = unreal.load_asset('/Game/CastleDefender/UI/Reveal/MPC_Reveal')
    P('MPC_Reveal.Blur =', unreal.KismetMaterialLibrary.get_scalar_parameter_value(world, rmpc, 'Blur') if rmpc else 'MPC_Reveal missing')
    pc = GS.get_player_controller(world, 0)
    hud = pc.get_hud() if pc else None
    P('HUD class:', hud.get_class().get_name() if hud else None)
    if REPLAY and fx and mpc:
        fx.set_editor_property('BookOpened', False)
        unreal.KismetMaterialLibrary.set_scalar_parameter_value(world, mpc, 'BookAge', 0.1)
        P('REPLAY: BookOpened = false, BookAge = 0.1 -> the book reveal should start on the next HUD frame.')
        P('  If it does not: DrawReveal is not being called (the ArmoryHUD hook HookReveal is missing or not linked).')

txt = '\n'.join(out)
open(os.path.join(HERE, 'diag_reveal268.txt'), 'w').write(txt)
unreal.log(txt)
