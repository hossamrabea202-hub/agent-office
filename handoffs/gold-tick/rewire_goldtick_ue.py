# Gold ticks up, step 3 (i5 / adjustedfilm, 2026-11-02). UE 5.8 Python. Run AFTER pasting
# build/SkillTreeHUD_GoldTickHook_graph.txt into BP_SkillTreeHUD's EventGraph.
#   py rewire_goldtick_ue.py --dry-run   report CX_1882 / CX_1883 / GtHookShownInt and their links
#   py rewire_goldtick_ue.py             CX_1883.InInt <- GtHookShownInt.ShownInt (the digits show the ticking value),
#                                        compile, save. Only this one input changes; every other Gold read stays.
#   py rewire_goldtick_ue.py --revert    CX_1883.InInt <- CX_1882.Gold again
import sys, unreal
A = sys.argv[1:]
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
PATH = '/Game/CastleDefender/Gameplay/Castle/BP_SkillTreeHUD'
bp = unreal.load_asset(PATH)
eg = BEL.find_event_graph(bp)
N = {n.get_name(): n for n in unreal.ObjectIterator(unreal.K2Node) if n.get_outer() == eg and n.get_name() in ('CX_1882', 'CX_1883', 'GtHookShownInt')}
log = ['gold tick rewire' + (' (DRY RUN)' if '--dry-run' in A else ' (REVERT)' if '--revert' in A else '')]
for k in ('CX_1882', 'CX_1883', 'GtHookShownInt'): log.append('%-15s %s' % (k, 'found' if k in N else 'MISSING'))


def links(p): return ['%s.%s' % (q.get_owning_node().get_name(), PL.get_pin_name(q)) for q in PL.list_connected_pins(p)] if p else None


need = ('CX_1882', 'CX_1883') + (() if '--revert' in A else ('GtHookShownInt',))
if all(k in N for k in need):
    inint = BEL.find_input_pin(N['CX_1883'], 'InInt')
    gold = BEL.find_output_pin(N['CX_1882'], 'Gold')
    shown = BEL.find_output_pin(N['GtHookShownInt'], 'ShownInt') if 'GtHookShownInt' in N else None
    log.append('CX_1883.InInt <- %s' % links(inint))
    if '--dry-run' not in A:
        PL.break_pin_links(inint)
        log.append('link: %s' % PL.try_create_connection(gold if '--revert' in A else shown, inint))
        BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(PATH)
        log.append('compiled + saved; CX_1883.InInt <- %s' % links(inint))
else:
    log.append('a node is MISSING: paste the hook first (or the graph changed since the 10:36 export)')
print('\n'.join(log))
