# Owner (Alien, 2026-11-05): "on the potion icon x1 is down and Q up, switch their places. Also icon 7 (armor skill) is hiding the health value bar."
# i5 checkking (Claude) for i9. Live-graph edit, no paste: only 4 number literals in BPC_PotionBelt + 2 class defaults on BPC_ObsidianSet.
#   py hud_swap_ue.py --dry-run          finds the 4 literals + shows the 7-badge spot, changes nothing
#   py hud_swap_ue.py --apply            sets, compiles, saves (each BP only if it compiles clean)
#   options: --potion-only / --badge-only, --x 0.5922 --y 0.80 (another 7-badge spot), --copy <folder> (i5 test on a duplicate)
# Potion badge (gen_potion_polish.py, badge centre BXc/BYc, 1080p units): Q key cap at (-38,-40) top-left, xN at (+12,+10) bottom-right.
#   After: xN at (-38,-40) top-left, the 22 U Q cap at (+14,+18) bottom-right (inside the 84 U ring, like xN was).
# Revert: run again with --revert (puts the 4 literals back to 38 / 40 / 12 / 10).
import sys, unreal
A = sys.argv[1:]
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): print('PIE RUNNING: abort'); raise SystemExit
BEL, PL, GE, EA = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.EditorAssetLibrary
arg = lambda k, d: float(A[A.index(k) + 1]) if k in A else d
APPLY = '--apply' in A
POT = '/Game/CastleDefender/Gameplay/Castle/BPC_PotionBelt'
OBS = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
if '--copy' in A:
    C = A[A.index('--copy') + 1]
    if not EA.does_asset_exist(C + '/PotionBelt_t'): EA.duplicate_asset(POT, C + '/PotionBelt_t')
    POT = C + '/PotionBelt_t'

def ins(n): return {str(PL.get_pin_name(p)): p for p in BEL.list_input_pins(n)}
def outs(n): return {str(PL.get_pin_name(p)): p for p in BEL.list_output_pins(n)}
def src(p):
    c = PL.list_connected_pins(p); return PL.get_owning_node(c[0]) if c else None
def fn(n): return str(n.get_name())
def lit(p):
    try: return float(PL.get_pin_value(p))
    except Exception: return None
def is_op(n, op): return op in fn(n) or op in str(BEL.get_node_title(n)).replace(' ', '')
def px_lit(n):
    """n = Multiply(U, literal): the Multiply node and its literal pin, else None"""
    if not n or 'Multiply' not in fn(n): return None
    i = ins(n)
    if 'B' in i and not PL.list_connected_pins(i['B']): return i['B']
    return None

# ------------------------------------------------------------------ potion: swap Q cap and xN
def potion():
    bp = unreal.load_asset(POT); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); nodes = list(ge.list_all_nodes())
    # badge centre: BXc = Add(CX, Mul(U, Add(-177, shake))); BYc = Subtract(SYd, Mul(U, 73))
    bx = by = None
    for n in nodes:
        i = ins(n)
        if 'Add' in fn(n) and 'B' in i:
            m = src(i['B'])
            if m and 'Multiply' in fn(m):
                mb = ins(m).get('B'); a = src(mb) if mb else None
                if a and 'Add' in fn(a) and lit(ins(a).get('A')) == -177.0: bx = (bx or []) + [n]
        if 'Subtract' in fn(n) and 'B' in i:
            pb = px_lit(src(i['B']))
            if pb and lit(pb) == 73.0: by = (by or []) + [n]
    if not bx or not by or len(bx) != 1 or len(by) != 1:
        print('STOP potion: badge centre not found once (BXc %s, BYc %s). Send i5 an export of BPC_PotionBelt.' % (bx and len(bx), by and len(by))); return False
    bx, by = bx[0], by[0]
    # consumers of the centre whose other input is px(literal)
    want = {('X', 'Subtract'): (38.0, -14.0), ('Y', 'Subtract'): (40.0, -18.0), ('X', 'Add'): (12.0, -38.0), ('Y', 'Add'): (10.0, -40.0)}
    if '--revert' in A: want = {k: (b_, a_) for k, (a_, b_) in want.items()}
    found = {}
    for axis, c in (('X', bx), ('Y', by)):
        for p in PL.list_connected_pins(outs(c)['ReturnValue']):
            n = PL.get_owning_node(p)
            if str(PL.get_pin_name(p)) != 'A': continue
            for op in ('Subtract', 'Add'):
                if op in fn(n) and (axis, op) in want:
                    pb = px_lit(src(ins(n)['B']))
                    if pb is not None and lit(pb) == want[(axis, op)][0]: found.setdefault((axis, op), []).append(pb)
    bad = [k for k in want if len(found.get(k, [])) != 1]
    if bad:
        done = all(len(found.get(k, [])) == 0 for k in want)
        print('STOP potion: literals not found once:', {k: len(found.get(k, [])) for k in want}, '(already swapped?)' if done else '')
        return False
    for k, (old, new) in want.items(): print('potion %s %s offset %g -> %g  (%s)' % (k[0], 'Q cap' if k[1] == 'Subtract' else 'xN', old, new, fn(PL.get_owning_node(found[k][0]))))
    if not APPLY: return True
    for k, (old, new) in want.items():
        if not PL.set_pin_value(found[k][0], '%.1f' % new): print('STOP: value refused', k); return False
    ok = BEL.compile_blueprint(bp); err = [fn(n) for n in ge.list_nodes_with_errors()]
    print('potion compile', ok, '| errors', err)
    if err: print('NOT saved (errors). Reload the BP without saving.'); return False
    print('potion saved', EA.save_asset(POT, only_if_is_dirty=False)); return True

# ------------------------------------------------------------------ 7 badge: right of the HP bar (ember_pos_ue.py, now with a check)
def badge():
    if '--copy' in A: print('badge: skipped in --copy mode'); return True
    bp = unreal.load_asset(OBS); c = unreal.get_default_object(bp.generated_class())
    try: x0, y0 = c.get_editor_property('EmberX'), c.get_editor_property('EmberY')
    except Exception: print('STOP badge: BPC_ObsidianSet has no EmberX/EmberY (#477 not in this project)'); return False
    X, Y = arg('--x', 0.5922), arg('--y', 0.9324)
    if abs(x0 - X) < 1e-4 and abs(y0 - Y) < 1e-4 and '--x' not in A:
        print('badge: ALREADY at %.4f / %.4f (ember_pos was applied) and the owner still sees it on the HP value.' % (x0, y0))
        print('       Take a Play screenshot to i5, or try a higher spot: --x 0.5922 --y 0.80'); return True
    print('badge EmberX %.4f -> %.4f | EmberY %.4f -> %.4f' % (x0, X, y0, Y))
    if not APPLY: return True
    c.set_editor_property('EmberX', X); c.set_editor_property('EmberY', Y)
    ok = BEL.compile_blueprint(bp); c = unreal.get_default_object(bp.generated_class())
    print('badge compile', ok, '| now', c.get_editor_property('EmberX'), c.get_editor_property('EmberY'), '| saved', EA.save_asset(OBS, only_if_is_dirty=False)); return True

r1 = potion() if '--badge-only' not in A else True
r2 = badge() if '--potion-only' not in A else True
print('RESULT potion', r1, '| badge', r2, '|', 'applied' if APPLY else 'dry run, nothing changed')
