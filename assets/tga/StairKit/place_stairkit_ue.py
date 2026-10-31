# MASTER ONLY (UE 5.3). #279: replace the castle's box stairs with the AAA stair kit (TGA, 2026-10-31). Game level open.
#   py "<repo>/assets/tga/StairKit/place_stairkit_ue.py"         DRY_RUN = True only prints the flights it found.
# 1. Finds every SM_StairTread_* actor and chains them into flights (same yaw, each next tread 8-30 cm higher and
#    15-60 cm further along, < 25 cm sideways). It measures each flight: steps, rise, going, width, direction.
# 2. Old actors of a flight (its treads plus the Cube_* / SM_StoneModule_* blocks under them) are moved to the folder
#    Stairs_Old_279, hidden (editor + game) with collision off, tagged Stair279_Old. StairRamp_* nav ramps are kept.
# 3. Places SM_Stair_W<class>_Solid_N<steps> (flights over 16 steps are split) at the same spot, scaled to the measured
#    rise / going / width, label Stair279_<k>, folder Stairs_279, tag Stair279_New.
# UNDO = True deletes the Stair279_New actors and restores the old ones. Save the level afterwards.
# It writes Saved/stair279_report.json: post it on #279 so TGA can check the fit.
import unreal, math, re, json, os
DRY_RUN = True
UNDO = False
STYLE = 'Solid'                    # 'Soffit' = floating flights with a sloped underside (needs supports to look right)
KIT = '/Game/CastleDefender/Props/StairKit/SM_Stair_W%03d_%s_N%02d'
R0, G0 = 18.0, 30.0                # kit rise / going, cm
CLASSES = (120, 200, 300, 400)     # kit widths, cm
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = lambda m: unreal.log('[stair279%s] %s' % (' DRY' if DRY_RUN else '', m))
actors = eas.get_all_level_actors()
tagged = lambda t: [a for a in actors if t in [str(x) for x in a.tags]]
if UNDO:
    for a in tagged('Stair279_New'):
        if not DRY_RUN: eas.destroy_actor(a)
    for a in tagged('Stair279_Old'):
        if not DRY_RUN:
            a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False); a.set_actor_enable_collision(True)
            a.tags = [t for t in a.tags if str(t) != 'Stair279_Old']
    log('undone: %d new removed, %d old restored - save the level' % (len(tagged('Stair279_New')), len(tagged('Stair279_Old')))); raise SystemExit
if tagged('Stair279_New'): log('already placed (set UNDO = True to redo)'); raise SystemExit

def info(a):
    o, e = a.get_actor_bounds(False); yaw = a.get_actor_rotation().yaw
    sm = a.static_mesh_component.static_mesh if hasattr(a, 'static_mesh_component') and a.static_mesh_component else None
    ext = sm.get_bounds().box_extent if sm else e; sc = a.get_actor_scale3d()
    return dict(a=a, c=o, top=o.z + e.z, yaw=yaw, ex=abs(ext.x * sc.x), ey=abs(ext.y * sc.y))
treads = [info(a) for a in actors if re.match(r'^SM_StairTread', a.get_actor_label())]
blocks = [info(a) for a in actors if re.match(r'^(Cube_|SM_StoneModule)', a.get_actor_label())]
log('%d treads, %d candidate blocks' % (len(treads), len(blocks)))
def yd(a, b): return min((a - b) % 180, 180 - (a - b) % 180)            # yaw difference, boxes are symmetric
nxt = {}
for i, t in enumerate(treads):
    best = None
    for j, u in enumerate(treads):
        dz = u['top'] - t['top']
        if not (8 <= dz <= 30) or yd(t['yaw'], u['yaw']) > 5: continue
        dx, dy = u['c'].x - t['c'].x, u['c'].y - t['c'].y; h = math.hypot(dx, dy)
        if not (15 <= h <= 60): continue
        if best is None or h < best[0]: best = (h, j)
    if best: nxt[i] = best[1]
prev = {}
for i, j in nxt.items(): prev.setdefault(j, []).append(i)
flights = []
for i in range(len(treads)):
    if i in prev: continue
    ch = [i]
    while ch[-1] in nxt and nxt[ch[-1]] not in ch: ch.append(nxt[ch[-1]])
    if len(ch) >= 2: flights.append(ch)
# straightness: drop a chain's sideways outliers (> 25 cm off the line from first to last)
rep, k = [], 0
for ch in flights:
    T = [treads[i] for i in ch]; n = len(T)
    d = unreal.Vector(T[-1]['c'].x - T[0]['c'].x, T[-1]['c'].y - T[0]['c'].y, 0); run = d.length(); d = d.normal()
    side = max(abs((t['c'].x - T[0]['c'].x) * -d.y + (t['c'].y - T[0]['c'].y) * d.x) for t in T)
    if side > 25: log('skipped a %d-step chain (bends %.0f cm): fix by hand' % (n, side)); continue
    rise = (T[-1]['top'] - T[0]['top']) / (n - 1); going = run / (n - 1)
    ang = math.radians(T[0]['yaw']); ax = (math.cos(ang), math.sin(ang))
    width = 2 * (T[0]['ey'] if abs(ax[0] * d.x + ax[1] * d.y) > 0.7 else T[0]['ex'])   # tread size across the climb
    wc = min(CLASSES, key=lambda c: abs(math.log(width / c)))
    w = unreal.Vector(-d.y, d.x, 0)                                        # kit +X (width) in the world
    yaw = math.degrees(math.atan2(d.x, -d.y))                              # kit climbs -Y (FBX: Blender +Y -> UE -Y)
    z0 = T[0]['top'] - rise; front = T[0]['c'] - d * (going / 2) - w * (width / 2)
    olds = [t['a'] for t in T]
    for b in blocks:                                                       # the boxes under these treads
        for t in T:
            rel = b['c'] - t['c']
            if abs(rel.x * d.x + rel.y * d.y) < going * 0.6 and abs(rel.x * w.x + rel.y * w.y) < width / 2 + 5 and b['top'] <= t['top'] + 2:
                olds.append(b['a']); break
    pieces, s0 = [], 0
    while s0 < n:
        m = min(16, n - s0)
        if n - s0 - m == 1: m -= 1                                         # never leave a 1-step piece
        pieces.append((s0, m)); s0 += m
    for (s0, m) in pieces:
        path = KIT % (wc, STYLE, max(m, 2)); k += 1
        loc = front + d * (s0 * going); loc.z = z0 + s0 * rise
        scale = unreal.Vector(width / wc, going / G0, rise / R0)
        rep.append(dict(label='Stair279_%02d' % k, mesh=path.split('/')[-1], steps=m, rise=round(rise, 1), going=round(going, 1),
                        width=round(width, 1), scale=[round(scale.x, 3), round(scale.y, 3), round(scale.z, 3)], yaw=round(yaw, 1),
                        loc=[round(loc.x), round(loc.y), round(loc.z)], old=len(olds)))
        log('%s: %s steps=%d rise %.1f going %.1f width %.0f -> scale %.2f/%.2f/%.2f' % (rep[-1]['label'], rep[-1]['mesh'], m, rise, going, width, scale.x, scale.y, scale.z))
        if DRY_RUN: continue
        sm = unreal.load_asset(path)
        if not sm: log('missing %s (run import_stairkit_ue.py)' % path); continue
        a = eas.spawn_actor_from_object(sm, loc, unreal.Rotator(0, 0, yaw)); a.set_actor_scale3d(scale)
        a.set_actor_label(rep[-1]['label']); a.set_folder_path('Stairs_279'); a.tags = [unreal.Name('Stair279_New')]
    if not DRY_RUN:
        for o in olds:
            o.set_folder_path('Stairs_Old_279'); o.set_actor_hidden_in_game(True); o.set_is_temporarily_hidden_in_editor(True)
            o.set_actor_enable_collision(False); o.tags = list(o.tags) + [unreal.Name('Stair279_Old')]
out = os.path.join(unreal.Paths.project_saved_dir(), 'stair279_report.json')
json.dump(dict(flights=rep, treads=len(treads), chained=sum(r['steps'] for r in rep)), open(out, 'w'), indent=1)
log('%d kit flights for %d of %d treads; report %s%s' % (len(rep), sum(r['steps'] for r in rep), len(treads), out, '' if DRY_RUN else ' - save the level'))
