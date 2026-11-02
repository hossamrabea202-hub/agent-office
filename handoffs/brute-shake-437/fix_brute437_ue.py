# #437 P1: brute gate-slam shake + booms become a one-shot per brute, and stay local (i5 / adjustedfilm, 2026-11-02).
# Built on handoffs/exports/adjustedfilm/brute-322/BP_FleshBrute_EventGraph.txt (10-31). UE 5.8 Python.
#   py fix_brute437_ue.py --dry-run     report nodes, links and current pin values; change nothing
#   py fix_brute437_ue.py --values      ONLY the pin values (no paste needed): shake radii + boom volumes
#   py fix_brute437_ue.py               values + one-shot: adds bool var GateShook (if missing), then wires the pasted
#                                       nodes GtIfShook / GtSetShook (paste build/FleshBrute_GateShookOnce_graph.txt
#                                       first); compile, save BP_FleshBrute
#   py fix_brute437_ue.py --revert      CX_85 -> CX_88 link + the old values back (checks the new values are there first)
import json, os, sys, unreal
A = sys.argv[1:]
HERE = os.path.dirname(os.path.abspath(__file__))
BEL, PL, EAL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.EditorAssetLibrary
PATH = '/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute'
VALUES = [  # node, pin, value in the 10-31 export, new value, why
    ('CX_88', 'InnerRadius', 2500.0, 200.0, 'gate slam: full shake only right at the brute'),
    ('CX_88', 'OuterRadius', 12000.0, 1800.0, 'gate slam: felt up to 18 m, not castle-wide (120 m)'),
    ('CX_462', 'InnerRadius', 1500.0, 300.0, 'big slam'),
    ('CX_462', 'OuterRadius', 9000.0, 2500.0, 'big slam: 25 m, not 90 m'),
    ('CX_89', 'VolumeMultiplier', 1.6, 0.8, 'gate-slam boom (Explosion_Cue, no attenuation)'),
    ('CX_90', 'VolumeMultiplier', 1.6, 0.8, 'gate-slam metal hit (no attenuation)'),
    ('CX_460', 'VolumeMultiplier', 2.0, 1.0, 'big-slam wood impact'),
]
bp = unreal.load_asset(PATH)
eg = BEL.find_event_graph(bp)
want = {'CX_85', 'CX_88', 'CX_89', 'CX_90', 'CX_91', 'CX_460', 'CX_462', 'GtIfShook', 'GtSetShook', 'g437GetGateShook1'}
N = {n.get_name(): n for n in unreal.ObjectIterator(unreal.K2Node) if n.get_outer() == eg and n.get_name() in want}
DRY, REV, VAL_ONLY = '--dry-run' in A, '--revert' in A, '--values' in A
log = ['#437 brute shake' + (' DRY RUN' if DRY else ' REVERT' if REV else ' VALUES ONLY' if VAL_ONLY else '')]
for k in sorted(want): log.append('  %-18s %s' % (k, 'found' if k in N else 'missing'))


def links(p): return ['%s.%s' % (q.get_owning_node().get_name(), PL.get_pin_name(q)) for q in PL.list_connected_pins(p)] if p else None


ok = True
for n, pin, old, new, why in VALUES:
    p = BEL.find_input_pin(N[n], pin) if n in N else None
    cur = float(PL.get_pin_value(p)) if p else None
    expect = new if REV else old
    good = cur is not None and abs(cur - expect) < 1e-3
    ok &= good
    log.append('  %-7s %-16s = %s (expected %s -> %s) %s' % (n, pin, cur, expect, old if REV else new, 'ok' if good else 'MISMATCH'))
if 'CX_85' in N: log.append('  CX_85.then -> %s' % links(BEL.find_then_pin(N['CX_85'])))
if not ok:
    log.append('NOT CHANGED: values differ from the 10-31 export (ask i5 for a rebuild on a fresh export)')
elif not DRY:
    for n, pin, old, new, why in VALUES: PL.set_pin_value(BEL.find_input_pin(N[n], pin), '%f' % (old if REV else new))
    log.append('values %s' % ('restored' if REV else 'set'))
    if not VAL_ONLY:
        then85 = BEL.find_then_pin(N['CX_85'])
        if REV:
            PL.break_pin_links(then85); PL.try_create_connection(then85, BEL.find_execute_pin(N['CX_88'])); log.append('  CX_85.then -> CX_88 again')
        elif all(k in N for k in ('GtIfShook', 'GtSetShook')):
            if 'GateShook' not in [str(v) for v in (BEL.get_member_variable_names(bp) if hasattr(BEL, 'get_member_variable_names') else [])]:
                BEL.add_member_variable(bp, 'GateShook', BEL.get_basic_type_by_name('bool'))
            PL.break_pin_links(then85)
            for a, b_ in ((then85, BEL.find_execute_pin(N['GtIfShook'])), (BEL.find_then_pin(N['GtIfShook']), BEL.find_execute_pin(N['CX_91'])),
                          (BEL.find_then_pin(N['GtSetShook']), BEL.find_execute_pin(N['CX_88']))):
                log.append('  link %s' % PL.try_create_connection(a, b_))
            log.append('  one-shot wired: CX_85 -> GtIfShook (true -> CX_91, false -> GtSetShook -> CX_88)')
        else:
            log.append('  one-shot SKIPPED: paste build/FleshBrute_GateShookOnce_graph.txt first (values were set)')
    BEL.compile_blueprint(bp); EAL.save_asset(PATH); log.append('compiled + saved')
print('\n'.join(log))
