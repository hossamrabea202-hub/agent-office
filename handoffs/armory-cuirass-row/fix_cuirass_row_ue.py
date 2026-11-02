# Hide the lone "Obsidian Sovereign Cuirass" from Vesna's WEAPONS rack (i5 / adjustedfilm, 2026-11-02, i9's queue item 2).
# UE 5.8 Python. Built on handoffs/exports/adjustedfilm/shop-v2/BP_ArmoryHUD_EventGraph.txt (11-01 20:03).
# The rack is a carousel over MPC Shop.G = 0..4 (0 Noble Crossbow, 1 Golden Breastplate, 2 Golden Sovereign,
# 3 Knight's Great Helm, 4 Obsidian Sovereign Cuirass). Up/down wrap at "> 4.5 -> 0" and "< -0.5 -> 4". The cuirass now
# comes with the Obsidian Torso bundle (#424), so the rack wraps over 0..3 instead: three pin defaults, no links changed.
#   CX_1988.B  (down wrap, G-1 > 4.5)  4.5 -> 3.5
#   CX_2001.B  (up wrap,   G+1 > 4.5)  4.5 -> 3.5
#   CX_1993.B  (wrap target from -1)    4.0 -> 3.0
# The 3D chest piece on the showcase stays (the Torso bundle preview uses it).
#   py fix_cuirass_row_ue.py --dry-run | (apply) | --revert
import sys, unreal
A = sys.argv[1:]
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
PATH = '/Game/CastleDefender/Gameplay/Castle/BP_ArmoryHUD'
bp = unreal.load_asset(PATH)
G = PATH + '.BP_ArmoryHUD:EventGraph.'
CHANGES = [('CX_1988', 'B', 4.5, 3.5), ('CX_2001', 'B', 4.5, 3.5), ('CX_1993', 'B', 4.0, 3.0)]
REV = '--revert' in A
log = ['ArmoryHUD cuirass row' + (' (DRY RUN)' if '--dry-run' in A else ' (REVERT)' if REV else '')]
pins, ok = [], True
for name, pn, old, new in CHANGES:
    node = unreal.find_object(None, G + name)
    pin = BEL.find_input_pin(node, pn) if node else None
    cur = float(PL.get_pin_value(pin)) if pin else None
    want = new if REV else old
    good = cur is not None and abs(cur - want) < 1e-4
    ok &= good
    log.append('%-8s %s = %s (expected %s) %s' % (name, pn, cur, want, 'ok' if good else 'MISMATCH'))
    pins.append((pin, old if REV else new))
if not ok:
    log.append('NOT CHANGED: the graph differs from the 11-01 export (ask i5 for a rebuild on a fresh export)')
elif '--dry-run' not in A:
    for pin, v in pins: PL.set_pin_value(pin, '%.6f' % v)
    BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(PATH)
    log.append('set, compiled, saved: rack wraps over %s' % ('0..4 (cuirass back)' if REV else '0..3'))
print('\n'.join(log))
