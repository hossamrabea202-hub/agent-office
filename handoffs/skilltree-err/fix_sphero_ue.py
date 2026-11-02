# BP_SkillTreeHUD leftover "Accessed None ... AsBP_Third_Person_Character_2" (i5 / adjustedfilm, 2026-11-02). UE 5.8 Python.
# Built on i9's export handoffs/exports/adjustedfilm/skilltree-err/BP_SkillTreeHUD_EventGraph.txt (10:36).
# Cause: the hero cast spAsHero2 runs LAST in its chain, but its output (spGetLevel3 -> Level) is read BEFORE it by the
# level-up Branch spIfLevelUp7 and by Set SPN (spSetSPN12). Each tick they read the PREVIOUS tick's cast result, which
# is None on the first frames and whenever the hero is missing (menu, death, respawn).
# Fix (4 links, no nodes added or removed): run the cast first.
#   SPTickIn.then_0      -> spAsHero2.execute            (was -> spIfLevelUp7)
#   spAsHero2.then       -> spIfLevelUp7.execute         (was -> spSetSPPrevLevel13)
#   spIfNotFirst8.else   -> spSetSPPrevLevel13.execute   (was -> spAsHero2)
#   spSetSPN12.then      -> spSetSPPrevLevel13.execute   (was -> spAsHero2)
#   CastFailed stays unlinked: no hero, no level-up check this tick (same as before when the cast failed).
#   py fix_sphero_ue.py --dry-run    report the 5 nodes and their current links, change nothing
#   py fix_sphero_ue.py              rewire, compile, save
#   py fix_sphero_ue.py --revert     put the old 4 links back, compile, save
import sys, unreal
A = sys.argv[1:]
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
PATH = '/Game/CastleDefender/Gameplay/Castle/BP_SkillTreeHUD'
bp = unreal.load_asset(PATH)
G = PATH + '.BP_SkillTreeHUD:EventGraph.'
N = {k: unreal.find_object(None, G + k) for k in ('SPTickIn', 'spAsHero2', 'spIfLevelUp7', 'spIfNotFirst8', 'spSetSPN12', 'spSetSPPrevLevel13')}
log = ['SkillTreeHUD spAsHero2 fix' + (' (DRY RUN)' if '--dry-run' in A else ' (REVERT)' if '--revert' in A else '')]
for k, n in N.items(): log.append('%-20s %s' % (k, 'found' if n else 'MISSING'))


def pin(node, name):
    return BEL.find_else_pin(node) if name == 'else' else BEL.find_output_pin(node, name)


def links(p): return ['%s.%s' % (q.get_owning_node().get_name(), PL.get_pin_name(q)) for q in PL.list_connected_pins(p)] if p else None


if all(N.values()):
    P = {'seq0': pin(N['SPTickIn'], 'then_0'), 'cast_in': BEL.find_execute_pin(N['spAsHero2']), 'cast_then': BEL.find_then_pin(N['spAsHero2']),
         'lvl_in': BEL.find_execute_pin(N['spIfLevelUp7']), 'nf_else': pin(N['spIfNotFirst8'], 'else'),
         'spn_then': BEL.find_then_pin(N['spSetSPN12']), 'prev_in': BEL.find_execute_pin(N['spSetSPPrevLevel13'])}
    for k, p in P.items(): log.append('  %-10s %-6s -> %s' % (k, 'ok' if p else 'NO PIN', links(p)))
    if '--dry-run' not in A and all(P.values()):
        for k in ('seq0', 'cast_then', 'nf_else', 'spn_then'): PL.break_pin_links(P[k])
        if '--revert' in A:
            pairs = (('seq0', 'lvl_in'), ('cast_then', 'prev_in'), ('nf_else', 'cast_in'), ('spn_then', 'cast_in'))
        else:
            pairs = (('seq0', 'cast_in'), ('cast_then', 'lvl_in'), ('nf_else', 'prev_in'), ('spn_then', 'prev_in'))
        for a, b in pairs: log.append('  link %s -> %s: %s' % (a, b, PL.try_create_connection(P[a], P[b])))
        BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(PATH)
        log.append('compiled + saved')
        for k, p in P.items(): log.append('  after %-10s -> %s' % (k, links(p)))
else:
    log.append('a node is MISSING: the graph changed since the 10:36 export, nothing done')
print('\n'.join(log))
