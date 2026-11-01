# #411 castle scroll, step 3 (i5 core, 2026-11-01). UE 5.8 Python. Run AFTER pasting build/ZombieHUD_ScrollHook_graph.txt
# into BP_ZombieHUD's EventGraph.
#   py ".../rewire_hook411_ue.py" --dry-run   reports the nodes and their current links
#   py ".../rewire_hook411_ue.py"             UX_CallFunction_23.then -> CsHookDraw -> K2Node_IfThenElse_H296 (the old
#                                             ORE / FOOD DrawText chain orDrawOre32 -> hfDrawFood14 is left unlinked),
#                                             compiles and saves BP_ZombieHUD
#   py ".../rewire_hook411_ue.py" --revert    puts the old text chain back (UX -> orDrawOre32 ... hfDrawFood14 -> H296)
import sys, unreal
A = sys.argv[1:]
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
bp = unreal.load_asset(ZHUD)
G = ZHUD + '.BP_ZombieHUD:EventGraph.'
def node(n): return unreal.find_object(None, G + n)
N = {k: node(k) for k in ('UX_CallFunction_23', 'orDrawOre32', 'hfDrawFood14', 'K2Node_IfThenElse_H296', 'CsHookDraw')}
log = ['#411 rewire' + (' (DRY RUN)' if '--dry-run' in A else '')]
for k, n in N.items(): log.append('%-24s %s' % (k, 'found' if n else 'MISSING'))
def links(pin): return ['%s.%s' % (p.get_owning_node().get_name(), PL.get_pin_name(p)) for p in PL.list_connected_pins(pin)] if pin else None
if all(N[k] for k in ('UX_CallFunction_23', 'orDrawOre32', 'hfDrawFood14', 'K2Node_IfThenElse_H296')):
    ux_then, ifh_exec = BEL.find_then_pin(N['UX_CallFunction_23']), BEL.find_execute_pin(N['K2Node_IfThenElse_H296'])
    or_exec, hf_then = BEL.find_execute_pin(N['orDrawOre32']), BEL.find_then_pin(N['hfDrawFood14'])
    log.append('UX.then -> %s ; hfDrawFood14.then -> %s' % (links(ux_then), links(hf_then)))
    if '--revert' in A:
        PL.break_pin_links(ux_then); PL.try_create_connection(ux_then, or_exec); PL.try_create_connection(hf_then, ifh_exec)
        if N['CsHookDraw']: PL.break_pin_links(BEL.find_then_pin(N['CsHookDraw']))
        log.append('reverted to the text lines')
    elif '--dry-run' not in A:
        hk = N['CsHookDraw']
        if not hk: raise SystemExit('paste ZombieHUD_ScrollHook_graph.txt first (node CsHookDraw not found)')
        PL.break_pin_links(ux_then); PL.break_pin_links(hf_then)
        ok1 = PL.try_create_connection(ux_then, BEL.find_execute_pin(hk))
        ok2 = PL.try_create_connection(BEL.find_then_pin(hk), ifh_exec)
        log.append('wired UX -> CsHookDraw %s, CsHookDraw -> H296 %s' % (ok1, ok2))
    if '--dry-run' not in A:
        BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(ZHUD, only_if_is_dirty=False)
        log.append('compiled + saved; UX.then -> %s' % links(ux_then))
out = '\n'.join(log); unreal.log(out); print(out)
open('C:/Users/hossam.rabea/agent-office/handoffs/castle-scroll-411/rewire_hook411.txt', 'w').write(out)
