# MASTER ONLY (UE 5.3). #279 v2 (after the #301 revert): replace the castle's box stairs with the AAA stair kit. Game level open.
#   py "<repo>/assets/tga/StairKit/place_stairkit_ue.py"         DRY_RUN = True only checks and reports (always run it first).
# v2 fixes (owner findings on #301):
#  - orientation is READ from each imported kit mesh's bounds (which way it climbs / widens), never assumed; v1 assumed
#    the FBX mirrored Blender +Y to UE -Y and its flights climbed backwards (half stairs, poking through walls);
#  - every flight is VERIFIED before it is placed: each kit step must land on its old tread (<= 8 cm), otherwise the flight
#    is skipped and its old actors stay;
#  - only actors fully inside a placed flight's own volume are hidden: its treads, and Cube_* / SM_StoneModule_* /
#    SM_Cube_Nanite* blocks whose footprint lies inside the flight and whose height lies between its base and its treads.
#    Walls, towers, wall walks and anything else are never touched;
#  - the report (Saved/stair279_report.json) lists every flight, its fit error and every actor it would hide.
# UNDO = True deletes the Stair279_New actors and restores everything tagged Stair279_Old. Save the level afterwards.
import unreal, math, re, json, os
DRY_RUN = True
UNDO = False
STYLE = 'Solid'
KIT = '/Game/CastleDefender/Props/StairKit/SM_Stair_W%03d_%s_N%02d'
R0, G0 = 18.0, 30.0                 # kit rise / going, cm
CLASSES = (120, 200, 300, 400)      # kit widths, cm
TOL = 8.0                           # max step misfit, cm
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = lambda m: unreal.log('[stair279 v2%s] %s' % (' DRY' if DRY_RUN else '', m))
actors = eas.get_all_level_actors()
tagged = lambda t: [a for a in actors if t in [str(x) for x in a.tags]]
if UNDO:
    new, old = tagged('Stair279_New'), tagged('Stair279_Old')
    if not DRY_RUN:
        for a in new: eas.destroy_actor(a)
        for a in old:
            a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False); a.set_actor_enable_collision(True)
            a.tags = [t for t in a.tags if str(t) != 'Stair279_Old']
    log('undo: %d new removed, %d old restored - save the level' % (len(new), len(old))); raise SystemExit
if tagged('Stair279_New'): log('already placed (set UNDO = True first)'); raise SystemExit

def box(a):
    o, e = a.get_actor_bounds(False); return (o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z)
def info(a):
    b = box(a); sm = a.static_mesh_component.static_mesh if getattr(a, 'static_mesh_component', None) else None
    ext = sm.get_bounds().box_extent if sm else unreal.Vector((b[3] - b[0]) / 2, (b[4] - b[1]) / 2, (b[5] - b[2]) / 2); sc = a.get_actor_scale3d()
    return dict(a=a, lab=a.get_actor_label(), c=unreal.Vector((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2), top=b[5], bot=b[2],
                box=b, yaw=a.get_actor_rotation().yaw, ex=abs(ext.x * sc.x), ey=abs(ext.y * sc.y))
treads = [info(a) for a in actors if re.match(r'^SM_StairTread', a.get_actor_label())]
blocks = [info(a) for a in actors if re.match(r'^(Cube_|SM_StoneModule|SM_Cube_Nanite)', a.get_actor_label())]
log('%d treads, %d candidate blocks' % (len(treads), len(blocks)))
def yd(a, b): return min((a - b) % 180, 180 - (a - b) % 180)
nxt = {}
for i, t in enumerate(treads):
    best = None
    for j, u in enumerate(treads):
        dz = u['top'] - t['top']
        if not (8 <= dz <= 30) or yd(t['yaw'], u['yaw']) > 5: continue
        h = math.hypot(u['c'].x - t['c'].x, u['c'].y - t['c'].y)
        if 15 <= h <= 60 and (best is None or h < best[0]): best = (h, j)
    if best: nxt[i] = best[1]
heads = set(range(len(treads))) - set(nxt.values())
chains = []
for i in sorted(heads):
    ch = [i]
    while ch[-1] in nxt and nxt[ch[-1]] not in ch: ch.append(nxt[ch[-1]])
    if len(ch) >= 2: chains.append(ch)

orient = {}
def kit_orient(path):
    """(sx, sy): +1/-1 = which way the imported mesh widens (local X) and climbs (local Y), read from its bounds."""
    if path in orient: return orient[path]
    sm = unreal.load_asset(path)
    if not sm: orient[path] = None; return None
    b = sm.get_bounds(); orient[path] = (1 if b.origin.x >= 0 else -1, 1 if b.origin.y >= 0 else -1, sm); return orient[path]

rep, k, hide_all = [], 0, []
for ch in chains:
    T = [treads[i] for i in ch]; n = len(T)
    d = unreal.Vector(T[-1]['c'].x - T[0]['c'].x, T[-1]['c'].y - T[0]['c'].y, 0); run = d.length(); d = d.normal()
    side = max(abs((t['c'].x - T[0]['c'].x) * -d.y + (t['c'].y - T[0]['c'].y) * d.x) for t in T)
    if side > 25: log('SKIP %s..%s: bends %.0f cm, left as is' % (T[0]['lab'], T[-1]['lab'], side)); continue
    rise = (T[-1]['top'] - T[0]['top']) / (n - 1); going = run / (n - 1)
    ang = math.radians(T[0]['yaw']); along_x = abs(math.cos(ang) * d.x + math.sin(ang) * d.y) > 0.7
    width = 2 * (T[0]['ey'] if along_x else T[0]['ex'])
    wc = min(CLASSES, key=lambda c: abs(math.log(width / c)))
    w = unreal.Vector(-d.y, d.x, 0)
    pieces, s0 = [], 0
    while s0 < n:
        m = min(32 if wc == 200 else 16, n - s0)                                   # 2 m kit goes to 32 steps: one piece
        if n - s0 - m == 1: m -= 1
        pieces.append((s0, m)); s0 += m
    plan, ok = [], True
    for (s0, m) in pieces:
        path = KIT % (wc, STYLE, max(m, 2)); o = kit_orient(path)
        if o is None: log('missing %s (run import_stairkit_ue.py)' % path); ok = False; break
        sxs, sys_, sm = o
        # yaw so local (sys_ * Y) points up the flight; then local (sxs * X) points to +w or -w
        yaw = math.degrees(math.atan2(-sys_ * d.x, sys_ * d.y))
        th = math.radians(yaw); lx_dir = unreal.Vector(math.cos(th) * sxs, math.sin(th) * sxs, 0)    # world dir of the mesh's width
        start = T[s0]['c'] - d * (going / 2)                                       # front edge centre of this piece's first tread
        loc = start - lx_dir * (width / 2); loc.z = T[s0]['top'] - rise
        scale = unreal.Vector(width / wc, going / G0, rise / R0)
        err = 0.0                                                                  # verify: the MESH's own step centres, through the
        bb = sm.get_bounds(); ext = bb.box_extent                                  # real rotation + scale, against the old treads
        if abs(ext.y * 2 - m * G0) > 2 or abs(ext.z * 2 - m * R0) > 2: err = 999.0  # mesh is not the flight we think it is
        for i in range(m):
            lxv, lyv, lzv = sxs * wc / 2 * scale.x, sys_ * (i + 0.5) * G0 * scale.y, (i + 1) * R0 * scale.z
            p = unreal.Vector(loc.x + lxv * math.cos(th) - lyv * math.sin(th), loc.y + lxv * math.sin(th) + lyv * math.cos(th), loc.z + lzv)
            t = T[s0 + i]; err = max(err, math.hypot(p.x - t['c'].x, p.y - t['c'].y), abs(p.z - t['top']))
        plan.append((path, sm, loc, yaw, scale, m, err))
        if err > TOL: ok = False
    if not ok:
        log('SKIP %s..%s: kit misfit %.0f cm > %.0f, left as is' % (T[0]['lab'], T[-1]['lab'], max(p[6] for p in plan) if plan else -1, TOL)); continue
    base, ztop = T[0]['top'] - rise, T[-1]['top']                                  # this flight's own volume
    reach = (plan[0][5] - 0.5) * going                                             # blocks only under the FIRST piece (its solid
                                                                                   # body reaches the ground; later pieces only replace treads)
    def inside(b):
        if b['bot'] < base - 5 or b['top'] > ztop + 2: return False
        for cx, cy in ((b['box'][0], b['box'][1]), (b['box'][3], b['box'][4]), (b['box'][0], b['box'][4]), (b['box'][3], b['box'][1])):
            rx, ry = cx - T[0]['c'].x, cy - T[0]['c'].y
            a_ = rx * d.x + ry * d.y; s_ = rx * w.x + ry * w.y
            if not (-going / 2 - 5 <= a_ <= reach + 5 and abs(s_) <= width / 2 + 5): return False
        return True
    olds = [t for t in T] + [b for b in blocks if inside(b)]
    for (path, sm, loc, yaw, scale, m, err) in plan:
        k += 1; lab = 'Stair279_%02d' % k
        rep.append(dict(label=lab, mesh=path.split('/')[-1], steps=m, rise=round(rise, 1), going=round(going, 1), width=round(width, 1),
                        yaw=round(yaw, 1), loc=[round(loc.x), round(loc.y), round(loc.z)], scale=[round(scale.x, 3), round(scale.y, 3), round(scale.z, 3)],
                        fit_err_cm=round(err, 1), hides=[o_['lab'] for o_ in olds] if (path, m) == (plan[0][0], plan[0][5]) else []))
        log('%s %s steps=%d fit %.1f cm, hides %d' % (lab, rep[-1]['mesh'], m, err, len(rep[-1]['hides'])))
        if not DRY_RUN:
            a = eas.spawn_actor_from_object(sm, loc, unreal.Rotator(0, 0, yaw)); a.set_actor_scale3d(scale)
            a.set_actor_label(lab); a.set_folder_path('Stairs_279'); a.tags = [unreal.Name('Stair279_New')]
    hide_all += olds
    if not DRY_RUN:
        for o_ in olds:
            a = o_['a']; a.set_folder_path('Stairs_Old_279'); a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_enable_collision(False); a.tags = list(a.tags) + [unreal.Name('Stair279_Old')]
out = os.path.join(unreal.Paths.project_saved_dir(), 'stair279_report.json')
json.dump(dict(version=2, flights=rep, treads=len(treads), hidden=len(hide_all), orient={p.split('/')[-1]: o[:2] for p, o in orient.items() if o}), open(out, 'w'), indent=1)
log('%d kit pieces, %d actors %s; report %s%s' % (len(rep), len(hide_all), 'would be hidden' if DRY_RUN else 'hidden', out, '' if DRY_RUN else ' - save the level, rebuild paths'))
