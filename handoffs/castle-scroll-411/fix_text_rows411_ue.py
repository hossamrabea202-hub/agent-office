# #411 fix (i5, 2026-11-02, from i9's Play test): the scroll's text rows were placed from the TOP OF THE SCREEN (y 47..204 U)
# instead of inside the scroll (which starts at y 240 U), so THE KEEP / Iron / Copper... drew over the portrait, XP and
# gate bars. This moves the 5 row heights down by 240 U on the pasted nodes (no re-paste), compiles and saves.
#   py ".../fix_text_rows411_ue.py" [--dry-run]
import sys, unreal
DRY = '--dry-run' in sys.argv
BEL, PL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
P = '/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll'
bp = unreal.load_asset(P)
G = P + '.BPC_CastleScroll:EventGraph.'
ROWS = {'csMultiply_Doubl95': 47.0, 'csMultiply_Doubl112': 90.0, 'csMultiply_Doubl137': 128.0, 'csMultiply_Doubl161': 166.0, 'csMultiply_Doubl185': 204.0}
SY0 = 240.0
for name, y in ROWS.items():
    n = unreal.find_object(None, G + name)
    if not n: print(name, 'MISSING'); continue
    pin = BEL.find_input_pin(n, 'B')
    cur = PL.get_pin_value(pin)
    new = y + SY0
    if abs(float(cur) - y) > 0.01: print(name, 'is', cur, '(already moved?) -> skip'); continue
    print(name, cur, '->', new)
    if not DRY: PL.set_pin_value(pin, '%.1f' % new)
if not DRY:
    BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(P, only_if_is_dirty=False); print('compiled + saved')
