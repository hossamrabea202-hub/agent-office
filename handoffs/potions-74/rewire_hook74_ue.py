# #74 health potions, step 3 (i5 core, 2026-11-01). Run AFTER pasting build/ZombieHUD_PotionHook_graph.txt into
# BP_ZombieHUD's EventGraph. Puts PtHookDraw into the DrawHUD chain right after the #411 scroll hook (CsHookDraw), or after
# UX_CallFunction_23 when #411 isn't in yet:  <prev>.then -> PtHookDraw -> (what <prev>.then went to). Compiles + saves.
#   py ".../rewire_hook74_ue.py" [--dry-run | --revert]
import sys, unreal
A = sys.argv[1:]
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
bp = unreal.load_asset(ZHUD)
G = ZHUD + '.BP_ZombieHUD:EventGraph.'
node = lambda n: unreal.find_object(None, G + n)
pt = node('PtHookDraw')
prev = node('CsHookDraw') or node('UX_CallFunction_23')
log = ['#74 rewire' + (' (DRY RUN)' if '--dry-run' in A else ''), 'PtHookDraw %s, after %s' % (bool(pt), prev.get_name() if prev else None)]
links = lambda pin: [p.get_owning_node().get_name() + '.' + PL.get_pin_name(p) for p in PL.list_connected_pins(pin)]
if not pt or not prev: print('\n'.join(log + ['MISSING node: paste the hook first'])); raise SystemExit
pthen, pexec = BEL.find_then_pin(pt), BEL.find_execute_pin(pt)
prev_then = BEL.find_then_pin(prev)
log.append('%s.then -> %s ; PtHookDraw.then -> %s' % (prev.get_name(), links(prev_then), links(pthen)))
if '--revert' in A:
    nxt = list(PL.list_connected_pins(pthen))
    PL.break_pin_links(pthen); PL.break_pin_links(pexec)
    for p in nxt: PL.try_create_connection(prev_then, p)
elif '--dry-run' not in A:
    nxt = [p for p in PL.list_connected_pins(prev_then) if p.get_owning_node() != pt]
    PL.break_pin_links(prev_then)
    PL.try_create_connection(prev_then, pexec)
    for p in nxt: PL.try_create_connection(pthen, p)
if '--dry-run' not in A:
    BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(ZHUD, only_if_is_dirty=False)
    log.append('saved; %s.then -> %s ; PtHookDraw.then -> %s' % (prev.get_name(), links(prev_then), links(pthen)))
print('\n'.join(log))
