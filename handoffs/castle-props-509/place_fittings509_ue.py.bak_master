# #509 steps 3-5 (i5 checkking, 2026-11-05): timber hoarding over the gate, drain spouts, iron tie rings, torch brackets, tie-rod
# anchor plates. Finds the places from the real wall geometry (the wall-walk finder of place_stores509 and the wall-foot finder of
# place_foot509), so nothing floats and nothing is placed on a face that is not there.
#   py place_fittings509_ue.py            DRY RUN: writes fittings_report509.txt
#   py place_fittings509_ue.py --apply    spawns (tag FX509, outliner folder CastleFittings509), one ISM actor per mesh
#   py place_fittings509_ue.py --remove   deletes every FX509 actor (the undo)
#   --only hoarding,spouts,rings,brackets,anchors   pick parts;  --temp  meshes from /Game/_i5tmpWS509/ (i5 lookdev)
# Where and why (INDUSTRY_SECRETS 4.5, KB rule 3):
#   HOARDING  over the gate only: it was put up where the assault comes, the gate first. 3 bays (9 m) centred on the gate passage.
#   SPOUTS    through the parapet foot at wall-walk level on the OUTER face, every ~9 m: the walk drains outward. Each gets a #504
#             sill streak under its lip (the water falls clear, but the wall right below still stains and greens).
#   RINGS     1.3 m up the wall near the gate, the stables, the barracks and the well: where horses and carts stop.
#   BRACKETS  2 m up beside doors (one side), burnt-out stub in it: light where people pass at night.
#   ANCHORS   tie-rod plates, in pairs 4 m apart, ~4.5 m up on a few long faces: the period repair that holds a bulging wall.
import math, random, sys, unreal
args = sys.argv[1:]
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-props-509'
TAG = 'FX509'
ONLY = set(args[args.index('--only') + 1].split(',')) if '--only' in args else {'hoarding', 'spouts', 'rings', 'brackets', 'anchors'}
CAMP = '/Game/_i5tmpWS509/' if '--temp' in args else '/Game/CastleDefender/Environment/Camp/'
MESH = {k: CAMP + '%s/SM_Camp_%s' % (k, k) for k in ('HoardingBay', 'HoardingEnd', 'DrainSpout', 'TieRing', 'WallBracket', 'AnchorPlate')}
STREAK_MI = ('/Game/_i5tmpCW504/' if '--temp' in args else '/Game/CastleDefender/Environment/CastleWeather504/') + 'MI_RainStreak504_Sill'
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): print('PIE RUNNING: abort'); raise SystemExit


def load_ns(path):
    code = open(path, encoding='utf-8').read(); ns = {'__name__': 'fx509'}; old = sys.argv; sys.argv = ['x'] + [a for a in args if a == '--temp']
    try: exec(compile(code[:code.rindex("if '--remove' in args:")], path, 'exec'), ns)
    finally: sys.argv = old
    return ns


ST = load_ns(HERE + '/place_stores509_ue.py'); FT = load_ns(HERE + '/place_foot509_ue.py')
V, trace, EAS = ST['V'], ST['trace'], ST['EAS']
random.seed(5097)


def yaw_out(n): return math.degrees(math.atan2(-n.x, n.y))        # the meshes' +Y (out of the wall) onto n


def face_at(p, n, reach=300.0):
    """the wall face behind point p along -n: (point, normal) or None."""
    h = trace(p + n * reach, p - n * reach)
    return (h['loc'], h['n']) if h and abs(h['n'].z) < 0.3 and h['n'].dot(n) > 0.8 else None


def plan():
    put = []                                                    # (mesh key, transform, note)
    streaks = []
    sites, _clusters, gate = ST['plan']()
    gp = gate[1] if gate else None
    # ---- hoarding over the gate
    if 'hoarding' in ONLY and gp is not None:
        near = sorted([s for s in sites if (V(s[0].x, s[0].y, 0) - V(gp.x, gp.y, 0)).length() < 900.0], key=lambda s: (V(s[0].x, s[0].y, 0) - V(gp.x, gp.y, 0)).length())
        B = ST['BOX']; cen = V((B[0] + B[2]) / 2, (B[1] + B[3]) / 2, 0)
        og = V(gp.x - cen.x, gp.y - cen.y, 0); og = og * (1.0 / max(og.length(), 1e-3))
        og = max([V(1, 0, 0), V(-1, 0, 0), V(0, 1, 0), V(0, -1, 0)], key=lambda a: a.dot(og)) if abs(og.x) > 0.9 or abs(og.y) > 0.9 else og
        for P, d, dp, free in near[:6]:
            # the gate-top walk has parapets both ways (and merlons): take the face that looks OUT of the castle, through the gate
            f = face_at(P + og * 500.0 + V(0, 0, -35), og, 500.0)        # just under the walk floor: the coping / parapet foot face
            if not f: continue
            F, n = f; n = V(n.x, n.y, 0); n = n * (1.0 / max(n.length(), 1e-3)); r = V(-n.y, n.x, 0)
            c0 = F + r * (V(gp.x - F.x, gp.y - F.y, 0).dot(r))
            bays = []
            for nb in (3, 2, 1):            # the gate face between its towers may only take 2 bays, or 1: all of a run must sit on one face
                run = []
                for i in range(nb):
                    off = (i - (nb - 1) / 2.0) * 300.0
                    ok = all((lambda f_: f_ and abs((f_[0] - F).dot(n)) < 30.0)(face_at(c0 + r * (off + e_), n, 300.0)) for e_ in (-140.0, 0.0, 140.0))
                    if not ok: break
                    fk = face_at(c0 + r * off, n, 300.0); run.append(V(fk[0].x, fk[0].y, P.z))
                if len(run) == nb: bays = run; break
            if not bays: continue
            for b in bays: put.append(('HoardingBay', unreal.Transform(b, unreal.Rotator(0, 0, yaw_out(n)), V(1, 1, 1)), 'bay'))
            yw = math.radians(yaw_out(n)); ax = V(math.cos(yw), math.sin(yw), 0)          # the bays' local +X in the world
            bays.sort(key=lambda b: b.dot(ax))
            put.append(('HoardingEnd', unreal.Transform(bays[-1] + ax * 150.0, unreal.Rotator(0, 0, yaw_out(n)), V(1, 1, 1)), 'end (+X)'))
            put.append(('HoardingEnd', unreal.Transform(bays[0] - ax * 150.0, unreal.Rotator(0, 0, yaw_out(n)), V(-1, 1, 1)), 'end (-X, mirrored)'))
            break
    # ---- drain spouts at the walk's outer face
    if 'spouts' in ONLY:
        picked = []
        B = ST['BOX']; cen = V((B[0] + B[2]) / 2, (B[1] + B[3]) / 2, 0)
        for P, d, dp, free in sorted(sites, key=lambda s: random.random()):
            if gp is not None and (V(P.x, P.y, 0) - V(gp.x, gp.y, 0)).length() < 700.0: continue        # the hoarding is there
            if d.dot(V(P.x - cen.x, P.y - cen.y, 0)) <= 0.0: continue        # the walk drains OUT of the castle, not into the yard
            if any((P - q).length() < 900.0 for q in picked): continue
            f = face_at(P + d * (dp + 250.0) + V(0, 0, 8), d, 300.0)
            if not f: continue
            F, n = f; picked.append(P)
            put.append(('DrainSpout', unreal.Transform(V(F.x, F.y, P.z - 8.0), unreal.Rotator(0, 0, yaw_out(n)), V(1, 1, 1)), 'spout'))
            streaks.append((V(F.x, F.y, P.z - 22.0), n, random.uniform(40, 60), random.uniform(160, 320)))
    # ---- the wall feet: rings, brackets, anchors
    FT['plan'](); feet = FT['FEET']
    hubs = [a.get_actor_location() for a in EAS.get_all_level_actors() if any(w in a.get_actor_label().lower() for w in ('stable', 'barrack', 'gate', 'well'))]
    if 'rings' in ONLY:
        done = []
        for F, n, gz, shade, kind in sorted(feet, key=lambda x: random.random()):
            if kind != 'foot' or len(done) >= 12: continue
            if not any((V(F.x, F.y, 0) - V(h.x, h.y, 0)).length() < 1500.0 for h in hubs): continue
            if any((F - q).length() < 300.0 for q in done): continue
            f = face_at(V(F.x, F.y, gz + 130.0), n, 60.0)
            if not f: continue
            done.append(F); put.append(('TieRing', unreal.Transform(f[0], unreal.Rotator(0, 0, yaw_out(f[1])), V(1, 1, 1)), 'ring'))
    if 'brackets' in ONLY:
        doors = []
        for F, n, gz, shade, kind in feet:
            if kind == 'door' and all((F - q[0]).length() > 250.0 for q in doors): doors.append((F, n, gz))
        for F, n, gz in doors[:10]:
            r = V(-n.y, n.x, 0); side = random.choice((1, -1))
            for sd in (side, -side):
                hit = None
                for off in range(60, 260, 20):
                    f = face_at(V(F.x, F.y, gz + 200.0) + r * (off * sd), n, 80.0)
                    if f: hit = (f, off); break
                if hit:
                    (fp, fn), off = hit
                    put.append(('WallBracket', unreal.Transform(fp + r * (35.0 * sd), unreal.Rotator(0, 0, yaw_out(fn)), V(1, 1, 1)), 'bracket'))
                    break
    if 'anchors' in ONLY:
        pairs = []
        for F, n, gz, shade, kind in sorted(feet, key=lambda x: random.random()):
            if kind != 'foot' or len(pairs) >= 3 or any((F - q).length() < 2000.0 for q in pairs): continue
            r = V(-n.y, n.x, 0); a = face_at(V(F.x, F.y, gz + 450.0), n, 60.0); b = face_at(V(F.x, F.y, gz + 450.0) + r * 400.0, n, 60.0)
            if not a or not b or abs((a[0] - b[0]).dot(n)) > 15.0: continue
            pairs.append(F)
            for fp, fn in (a, b): put.append(('AnchorPlate', unreal.Transform(fp, unreal.Rotator(0, 0, yaw_out(fn)), V(1, 1, 1)), 'anchor'))
    return put, streaks, gate


def spawn(put, streaks):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); BFL = unreal.SubobjectDataBlueprintFunctionLibrary
    made = []

    def ism_actor(label, mesh):
        act = EAS.spawn_actor_from_class(unreal.Actor, V(0, 0, 0))
        act.set_actor_label('FX509_' + label); act.tags = [unreal.Name(TAG)]; act.set_folder_path('CastleFittings509')
        root = sub.k2_gather_subobject_data_for_instance(act)[0]
        hnd, why = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent))
        ism = BFL.get_object(BFL.get_data(hnd)); ism.set_static_mesh(mesh); ism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        ism.set_editor_property('can_ever_affect_navigation', False); return ism
    by = {}
    for k, t, note in put: by.setdefault(k, []).append(t)
    for k, ts in by.items():
        sm = unreal.load_asset(MESH[k])
        if not sm: print('MISSING', MESH[k]); continue
        ism = ism_actor(k, sm)
        for t in ts: ism.add_instance(t, True)
        made.append((k, len(ts)))
    if streaks:
        mi = unreal.load_asset(STREAK_MI)
        if not mi: print('no #504 MI (%s): spouts placed without their streak cards; run #504 build first' % STREAK_MI)
        else:
            ism = ism_actor('SpoutStreak', unreal.load_asset('/Engine/BasicShapes/Plane')); ism.set_material(0, mi); ism.set_cast_shadow(False)
            ism.set_editor_property('receives_decals', False); ism.set_editor_property('num_custom_data_floats', 1)
            for loc, n, w, h in streaks:
                i = ism.add_instance(FT['g']['card_xform']('MI_RainStreak504_Sill', loc, n, w, h, 0.0, False), True)
                ism.set_custom_data_value(i, 0, random.uniform(0, 97.0), True)
            made.append(('SpoutStreak', len(streaks)))
    return made


if '--remove' in args:
    gone = [x for x in EAS.get_all_level_actors() if TAG in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('removed', len(gone), 'FX509 actors'); raise SystemExit
if any(TAG in [str(t) for t in x.tags] for x in EAS.get_all_level_actors()): print('FX509 already in the level: --remove first'); raise SystemExit
put, streaks, gate = plan()
cnt = {}
for k, t, note in put: cnt[k] = cnt.get(k, 0) + 1
head = 'fittings %s | spout streak cards %d | gate %s' % (cnt, len(streaks), gate[0] if gate else None)
open(HERE + '/fittings_report509.txt', 'w').write(head + '\n' + '\n'.join('%-12s %8.0f %8.0f %7.0f yaw %4.0f  %s' % (k, t.translation.x, t.translation.y, t.translation.z, t.rotation.rotator().yaw, note) for k, t, note in put) + '\n')
print(head)
if '--apply' in args: print('spawned', spawn(put, streaks))
else: print('dry run: nothing placed')
