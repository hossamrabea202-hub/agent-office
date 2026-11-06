# #544 Round back towers (adjustedfilm, 2026-11-06). Duplicates the two round front towers (every piece of Castle/Tower9_A and _B) onto the back corners and hides the square bailey towers.
# Editor idle, not in Play, main level open with the castle loaded.
#   py round_back_towers_ue.py --dry-run | (no flag: apply, then save the level) | --revert (then save the level)
# Nothing is deleted except the copies on --revert. The squares and loose pieces inside the drums are hidden with collision off; the list is in back_towers_backup.json next to this script.
# Layout: walls cross at (4600, 50) and (4600, 3315). The bailey's north wall is at Y 3315, not 3450, so the back is not a plain mirror of the front.
#   Front A at (50, 50): walls go +X and +Y. Turned +90: they go +Y and -X, which is the back-left corner.
#   Front B at (50, 3450): walls go +X and -Y. Turned -90: they go -Y and -X, which is the back-right corner.
# Rebuild the navigation after applying: crews must reach the cannons through the new stairs.
import json, math, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); DRY, REV = '--dry-run' in A, '--revert' in A; BK = os.path.join(HERE, 'back_towers_backup.json')
TAG = 'BackTowers544'; INNER = 585.0
MAP = {'Castle/Tower9_A': dict(drum='Tower9_A_Drum', to=(4600.0, 50.0), yaw=90.0, out='Castle/TowerBack_A', pre='BackTower_A_'), 'Castle/Tower9_B': dict(drum='Tower9_B_Drum', to=(4600.0, 3315.0), yaw=-90.0, out='Castle/TowerBack_B', pre='BackTower_B_')}
ALSO_HIDE = ('Stair279_04', 'StairRamp_03')          # the old walk-to-roof stair at the back-right: it would run into the new drum; the copied tower has its own stairs
MOVE_DY = -430.0; STAIR_BR = (4389.0, 4811.0, 3420.0, 3720.0)   # a rooftop cannon on the back-right copy's stair well moves this far along Y
KEEP = ('Cannon', 'Tower9', 'BackTower', 'Landscape', 'Castle_Wall', 'Castle_Bailey', 'CastleStones', 'NavMesh', 'Blocking', 'Torch')       # never hidden by the inside-the-drum rule
ES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def say(*a): print('TOWER544', ' '.join(str(x) for x in a))
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise SystemExit('TOWER544 stop Play first')
actors = ES.get_all_level_actors(); mine = [a for a in actors if a.get_actor_label().startswith('BackTower_')]
def hide(a, h):
    a.set_actor_hidden_in_game(h); a.set_is_temporarily_hidden_in_editor(h); a.set_actor_enable_collision(not h)
if REV:
    for a in mine: ES.destroy_actor(a)
    bk = json.load(open(BK)) if os.path.exists(BK) else {'hidden': [], 'moved': {}}; n = m = 0
    for a in actors:
        pth = a.get_path_name()
        if pth in bk['hidden']: hide(a, False); n += 1
        if pth in bk['moved']: q = bk['moved'][pth]; a.set_actor_location(unreal.Vector(q[0], q[1], q[2]), False, True); m += 1
    say('removed', len(mine), 'copies, showed', n, 'of', len(bk['hidden']), 'hidden actors, moved back', m, 'cannons; save the level; rebuild navigation'); raise SystemExit(0)
if mine: raise SystemExit('TOWER544 already applied (%d copies): --revert first' % len(mine))
fam = {k: [] for k in MAP}
for a in actors:
    f = str(a.get_folder_path())
    if f in fam: fam[f].append(a)
for f, v in MAP.items():
    if not any(a.get_actor_label() == v['drum'] for a in fam[f]): raise SystemExit('TOWER544 no %s in folder %s: the castle changed or is not loaded' % (v['drum'], f))
hidden = []
def bounds(a):
    o, e = a.get_actor_bounds(False); return o, e
for f, v in MAP.items():
    tx, ty = v['to']
    for a in actors:
        lab = a.get_actor_label(); o, e = bounds(a); d = math.hypot(o.x - tx, o.y - ty)
        if lab.startswith(('Castle_BaileyTower',)) and d < 950: hidden.append(a); continue
        if a in fam[f] or lab.startswith(KEEP) or str(a.get_folder_path()).startswith('Castle/Tower9'): continue
        if not isinstance(a, unreal.StaticMeshActor): continue
        if d + max(e.x, e.y) < INNER and o.z - e.z > 600: hidden.append(a)                # loose walk slabs, trims and contact decals that would poke into the chamber
    say(f, 'pieces', len(fam[f]), 'to', v['to'], 'yaw', v['yaw'])
for a in actors:
    if a.get_actor_label() in ALSO_HIDE: hidden.append(a)
movers = []
for a in actors:
    if 'cannon' in a.get_actor_label().lower() and not a.get_actor_label().startswith(('Tower9', 'BackTower')):
        o, e = bounds(a)
        if o.z + e.z > 1000 and o.z < 1500 and o.x + e.x > STAIR_BR[0] and o.x - e.x < STAIR_BR[1] and o.y + e.y > STAIR_BR[2] and o.y - e.y < STAIR_BR[3]: movers.append(a)
say('cannons to move', [a.get_actor_label() for a in movers])
say('would hide' if DRY else 'hide', len(hidden), sorted({a.get_actor_label().rstrip('0123456789_') for a in hidden})[:24])
if DRY: say('DONE dry-run'); raise SystemExit(0)
for f, v in MAP.items():
    dr = next(a for a in fam[f] if a.get_actor_label() == v['drum']); oc, _ = bounds(dr); cx, cy = oc.x, oc.y; tx, ty = v['to']; r = math.radians(v['yaw']); c_, s_ = math.cos(r), math.sin(r)
    turn = unreal.Rotator(0.0, 0.0, v['yaw'])
    for a in fam[f]:
        n = ES.duplicate_actor(a); p = a.get_actor_location(); dx, dy = p.x - cx, p.y - cy
        n.set_actor_location(unreal.Vector(tx + dx * c_ - dy * s_, ty + dx * s_ + dy * c_, p.z), False, True); n.set_actor_rotation(unreal.MathLibrary.compose_rotators(a.get_actor_rotation(), turn), True)
        n.set_actor_label(v['pre'] + a.get_actor_label()); n.set_folder_path(v['out']); n.tags = list(n.tags) + [TAG]
moved = {}
for a in movers:
    p = a.get_actor_location(); moved[a.get_path_name()] = [p.x, p.y, p.z]; a.set_actor_location(unreal.Vector(p.x, p.y + MOVE_DY, p.z), False, True)
json.dump({'hidden': [a.get_path_name() for a in hidden], 'moved': moved}, open(BK, 'w'), indent=0)
hidden = [a for a in hidden if 'CDLock' not in [str(x) for x in a.tags]]   # Master: the four locked Mason towers are never hidden (owner's lock, 11-06)
for a in hidden: hide(a, True)
say('DONE applied; save the level and rebuild navigation')
