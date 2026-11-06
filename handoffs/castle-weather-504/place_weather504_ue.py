# #504 castle weathering, step 2 (i5 checkking, 2026-11-04): find where weathering physically happens on the castle
import os
# stone and put instanced stain cards there.
#   py place_weather504_ue.py                     DRY RUN (default): probes the stone, writes place_report504.txt
#   py place_weather504_ue.py --probe             only lists the stone components found (materials, counts)
#   py place_weather504_ue.py --preview <x> <y> <z> <dir>   places the cards within 12 m of (x,y,z) TEMPORARILY, renders
#                                                 <dir>/cw504_before.png + _after.png (locked exposure), removes them
#   py place_weather504_ue.py --apply             spawns the cards for real (tag CW504, outliner folder CastleWeather504)
#   py place_weather504_ue.py --remove            deletes every actor tagged CW504 (the undo; nothing else is touched)
# Physical causes (KB README rule 3, INDUSTRY_SECRETS 0.3 + 4.5):
#   LEDGE  a face that steps back under an overhang (cap, cornice, string course): water drips off the edge -> run-off
#          streaks below it.                                                                           MI_RainStreak504_Ledge
#   SILL   the bottom of an opening in a face (arrow slit, window, crenel in one piece): water collects and runs out over
#          the sill -> the strongest streaks, a little algae.                                           MI_RainStreak504_Sill
#   TOP    the top edge of a face with no overhang: rain washes over it -> faint streaks.              MI_RainStreak504_Top
#   CRACK  from the lower corners of openings (stress concentrates there; settlement) and a few on big faces (frost),
#          with a stain trail below.                                                                   MI_Crack504
#   CAP    up-facing stone tops (caps, merlon tops, ledges): lichen colonies.                           MI_Lichen504_Cap
#   SHADE  faces turned away from the sun, lower and upper zones: lichen + dark algae film.             MI_Lichen504_Shade
# NOT added: a base dirt band (family C has one in the material; no doubling, PERFECT_CASTLE #7).
# Cards hover 0.6 cm in front of the MOST protruding point of their footprint (carved stones bulge), no collision, no
# shadow, one InstancedStaticMeshComponent per MI on one actor per MI (a handful of draw calls for the whole castle).
import math, os, random, sys, unreal

D = '/Game/_i5tmpCW504/' if '--temp' in sys.argv else '/Game/CastleDefender/Environment/CastleWeather504/'
HERE = 'C:/Users/hossa/Documents/agent-office/handoffs/castle-weather-504'   # Master: this PC's repo (scripts exec each other without __file__)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
SL = unreal.SystemLibrary
V = unreal.Vector
args = sys.argv[1:]
TAG = 'CW504'
BOX = (-1900.0, -1900.0, 6500.0, 5350.0)                       # castle box (#461 scan) + 15 m
STONE_WORDS = ('stone', 'ashlar', 'masonry', 'keepentrance', 'stair', 'castle_', 'curtain', 'mason', 'merlon', 'tower', 'wall')
NOT_WORDS = ('grime', 'card', 'soot', 'torch', 'water', 'glow', 'shadow', 'bubble', 'corruption', 'jelly', 'fountainwater',
             'iron', 'wood', 'drawbridge', 'lever', 'grass', 'decal', 'gridmaterial', 'cw504', 'cd425', 'algae', 'streak')
HARD_NOT = ('plank', 'fountain', 'walkflag', 'archweathering', 'flag')
STEP_Z = 10.0          # vertical probe step (cm)
COL = 110.0            # column spacing along a face (cm)
random.seed(504)

if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit


def mat_names(c):
    out = []
    for i in range(c.get_num_materials()):
        m = c.get_material(i)
        while m is not None:
            out.append(m.get_name().lower())
            m = m.get_editor_property('parent') if isinstance(m, unreal.MaterialInstance) else None
    return out


def stone_components():
    comps = []
    for a in EAS.get_all_level_actors():
        if a.is_hidden_ed() or TAG in [str(t) for t in a.tags] or 'CD425' in [str(t) for t in a.tags]: continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if isinstance(c, unreal.InstancedStaticMeshComponent) and c.get_instance_count() > 64: continue   # foliage
            if not c.is_visible() or c.get_editor_property('hidden_in_game'): continue
            sm = c.get_editor_property('static_mesh')
            if not sm: continue
            o, e, _r = SL.get_component_bounds(c)
            if not (BOX[0] < o.x < BOX[2] and BOX[1] < o.y < BOX[3]): continue
            if e.z < 40.0 or max(e.x, e.y) < 30.0: continue
            mn = mat_names(c); key = ' '.join(mn) + ' ' + sm.get_name().lower() + ' ' + a.get_actor_label().lower()
            if any(w in key for w in NOT_WORDS) and not any(w in ' '.join(mn) for w in ('stone', 'ashlar', 'masonry', 'keepentrance')): continue
            if not any(w in key for w in STONE_WORDS) or any(w in key for w in HARD_NOT): continue
            comps.append((a, c, o, e, mn[0] if mn else '?'))
    return comps


def trace(a, b):
    h = SL.line_trace_single(W, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0] or t[1]: return None
    # (blocking, initial overlap, time, distance, location, impact point, normal, impact normal, phys mat, actor, component)
    return {'loc': t[4], 'n': t[7], 'dist': t[3], 'comp': t[10] if len(t) > 10 else None}


def sun_dir():
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.DirectionalLight):
            f = a.get_actor_forward_vector(); return V(-f.x, -f.y, -f.z)      # towards the sun
    return V(0.3, -0.5, 0.8)


def probe_face(comp, o, e, nrm, tan):
    """Columns along one side of the box. For each column, rays from 3 m outside inward at every STEP_Z. Returns events."""
    half = abs(tan.x) * e.x + abs(tan.y) * e.y
    depth = abs(nrm.x) * e.x + abs(nrm.y) * e.y
    n_cols = max(1, int(2 * half / COL))
    ev = []
    for ci in range(n_cols):
        s = -half + (ci + 0.5) * (2 * half / n_cols) + random.uniform(-0.2, 0.2) * COL
        base = V(o.x, o.y, 0) + tan * s + nrm * (depth + 300.0)
        samples = []                                    # (z, hit or None) top -> bottom
        z = o.z + e.z - 2.0
        while z > o.z - e.z + 5.0:
            st = V(base.x, base.y, z); h = trace(st, st - nrm * (2 * depth + 300.0))
            ok = h and h['comp'] == comp and abs(h['n'].z) < 0.6 and h['n'].dot(nrm) > 0.35
            samples.append((z, st, h if ok else None)); z -= STEP_Z
        valid = sorted(x[2]['dist'] for x in samples if x[2])
        if len(valid) < 4: continue
        face = valid[len(valid) // 2]                   # the column's typical face depth (joints are only a few cm)
        first = next(i for i, x in enumerate(samples) if x[2])
        z0, st0, h0 = samples[first]
        # top edge: another piece overhanging it = LEDGE, a lintel above an open gap = SILL, open sky = TOP
        ab = trace(V(st0.x, st0.y, z0 + 12.0), V(st0.x, st0.y, z0 + 12.0) - nrm * (2 * depth + 300.0))
        if ab and ab['comp'] != comp and ab['dist'] < h0['dist'] - 5.0:
            ev.append(('LEDGE', h0['loc'], h0['n'], z0))
        else:
            lin = trace(h0['loc'] - nrm * 10.0 + V(0, 0, 15.0), h0['loc'] - nrm * 10.0 + V(0, 0, 320.0))
            ev.append(('SILL' if lin and lin['n'].z < -0.7 else 'TOP', h0['loc'], h0['n'], z0))
        d = [x[2]['dist'] if x[2] else None for x in samples]
        i = first + 1
        while i < len(samples) - 2:
            # LEDGE inside one mesh: the two samples above stand proud of the face (>= 7 cm), the two below sit on it
            if (d[i - 1] is not None and d[i - 1] < face - 7.0 and (i < 2 or d[i - 2] is None or d[i - 2] < face - 7.0)
                    and d[i] is not None and abs(d[i] - face) < 4.0 and d[i + 1] is not None and abs(d[i + 1] - face) < 4.0):
                ev.append(('LEDGE', samples[i][2]['loc'], samples[i][2]['n'], samples[i][0])); i += 3; continue
            # SILL: an opening = >= 5 samples (50 cm) with no face or far behind it (> 25 cm), face again below it
            if d[i] is None or d[i] > face + 25.0:
                j = i
                while j < len(samples) and (d[j] is None or d[j] > face + 25.0): j += 1
                if j - i >= 5 and j < len(samples) and abs(d[j] - face) < 6.0 and d[i - 1] is not None and abs(d[i - 1] - face) < 6.0:
                    ev.append(('SILL', samples[j][2]['loc'], samples[j][2]['n'], samples[j][0]))
                i = j + 1; continue
            i += 1
    return ev


def protrusion(loc, nrm, up, side, w, h):
    """Most protruding wall point within the card footprint (3 x 3 rays): returns the plane offset along nrm."""
    best = 0.0
    for u in (-0.4, 0.0, 0.4):
        for v in (-0.4, 0.0, 0.4):
            p = loc + side * (u * w) + up * (v * h) + nrm * 40.0
            r = trace(p, p - nrm * 80.0)
            if r and r['n'].dot(nrm) > 0.3:
                best = max(best, (r['loc'] - loc).dot(nrm))
    return min(best, 12.0)


def plan():
    sun = sun_dir(); cards = []; taken = set()
    comps = stone_components()

    def add(mi, loc, nrm, w, h, roll=0.0, horizontal=False):
        if -450 <= loc.x <= 650 and 1400 <= loc.y <= 2100: return   # Master 11-06: owner's rule, nothing at the castle entrance (gate passage + plinths)
        k = (mi, int(loc.x // 60), int(loc.y // 60), int(loc.z // 60))
        if k in taken: return
        taken.add(k); cards.append((mi, loc, nrm, w, h, roll, horizontal))

    for a, c, o, e, mat in comps:
        for nrm, tan in ((V(1, 0, 0), V(0, 1, 0)), (V(-1, 0, 0), V(0, 1, 0)), (V(0, 1, 0), V(1, 0, 0)), (V(0, -1, 0), V(1, 0, 0))):
            for kind, loc, n, z in probe_face(c, o, e, nrm, tan):
                if kind == 'TOP':
                    if random.random() < 0.35: add('MI_RainStreak504_Top', loc, n, random.uniform(60, 140), random.uniform(50, 200))
                    up = trace(loc + n * -8.0 + V(0, 0, 60), loc + n * -8.0 + V(0, 0, -20))        # the top surface
                    if up and up['n'].z > 0.8 and random.random() < 0.35:
                        add('MI_Lichen504_Cap', up['loc'], up['n'], random.uniform(40, 90), random.uniform(40, 90), random.uniform(0, 360), True)
                elif kind == 'LEDGE':
                    if random.random() < 0.45: add('MI_RainStreak504_Ledge', loc, n, random.uniform(60, 160), random.uniform(60, 340))
                elif kind == 'SILL':
                    add('MI_RainStreak504_Sill', loc, n, random.uniform(50, 90), random.uniform(120, 300))
                    if random.random() < 0.3:
                        sd = 1.0 if random.random() < 0.5 else -1.0
                        add('MI_Crack504', loc + V(-n.y, n.x, 0) * sd * 25.0 + V(0, 0, -40), n, 45.0, random.uniform(70, 140), sd * random.uniform(15, 35))
            # frost / settlement cracks on big faces, faces away from the sun get lichen + algae
            half = abs(tan.x) * e.x + abs(tan.y) * e.y; area = 2 * half * 2 * e.z / 10000.0
            for _ in range(int(area / 30.0 + random.random()) if area > 6.0 else 0):
                if random.random() > 0.5: continue
                s = random.uniform(-0.8, 0.8) * half; zz = o.z + random.uniform(-0.6, 0.5) * e.z
                st = V(o.x, o.y, zz) + tan * s + nrm * (abs(nrm.x) * e.x + abs(nrm.y) * e.y + 200.0)
                h = trace(st, st - nrm * 600.0)
                if h and h['comp'] == c and h['n'].dot(nrm) > 0.6:
                    add('MI_Crack504', h['loc'], h['n'], 50.0, random.uniform(80, 180), random.uniform(-25, 25))
            if nrm.dot(sun) < -0.15:
                for _ in range(int(area / 16.0 + random.random())):
                    s = random.uniform(-0.85, 0.85) * half
                    zz = o.z + (random.uniform(-0.95, -0.55) if random.random() < 0.6 else random.uniform(0.4, 0.9)) * e.z
                    st = V(o.x, o.y, zz) + tan * s + nrm * (abs(nrm.x) * e.x + abs(nrm.y) * e.y + 200.0)
                    h = trace(st, st - nrm * 600.0)
                    if h and h['comp'] == c and h['n'].dot(nrm) > 0.6:
                        add('MI_Lichen504_Shade', h['loc'], h['n'], random.uniform(60, 130), random.uniform(60, 130), random.uniform(0, 360))
    return comps, cards


def card_xform(mi, loc, nrm, w, h, roll, horizontal):
    if horizontal:
        rot = unreal.MathLibrary.make_rot_from_zx(V(0, 0, 1), V(math.cos(math.radians(roll)), math.sin(math.radians(roll)), 0))
        return unreal.Transform(loc + V(0, 0, 0.6), rot, V(h / 100.0, w / 100.0, 1.0))
    up = V(0, 0, 1)
    # tilt the card's "up" around the normal by roll (cracks run diagonally from opening corners)
    r = math.radians(roll); side = V(-nrm.y, nrm.x, 0)
    upr = V(up.x * math.cos(r) + side.x * math.sin(r), up.y * math.cos(r) + side.y * math.sin(r), math.cos(r))
    centre = loc + upr * (-h * 0.5 if mi.startswith('MI_RainStreak') else 0.0)        # streaks hang BELOW the edge
    off = protrusion(centre, nrm, upr, side, w, h) + 0.6
    rot = unreal.MathLibrary.make_rot_from_zx(nrm, upr)
    return unreal.Transform(centre + nrm * off, rot, V(h / 100.0, w / 100.0, 1.0))


def spawn(cards, only_near=None):
    by_mi = {}
    for cd in cards:
        if only_near and (cd[1] - only_near).length() > 1200.0: continue
        by_mi.setdefault(cd[0], []).append(cd)
    made = []
    plane = unreal.load_asset('/Engine/BasicShapes/Plane')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    BFL = unreal.SubobjectDataBlueprintFunctionLibrary
    for mi, lst in by_mi.items():
        act = EAS.spawn_actor_from_class(unreal.Actor, V(0, 0, 0))
        act.set_actor_label('CW504_' + mi[3:]); act.tags = [unreal.Name(TAG)]; act.set_folder_path('CastleWeather504')
        root = sub.k2_gather_subobject_data_for_instance(act)[0]
        hnd, why = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent))
        ism = BFL.get_object(BFL.get_data(hnd))
        ism.set_static_mesh(plane); ism.set_material(0, unreal.load_asset(D + mi))
        ism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); ism.set_cast_shadow(False)
        ism.set_editor_property('receives_decals', False)
        ism.set_editor_property('num_custom_data_floats', 1)
        for cd in lst:
            i = ism.add_instance(card_xform(*cd), True)
            ism.set_custom_data_value(i, 0, random.uniform(0, 97.0), True)
        made.append(act)
    return made


def shot(path, cam, tgt):
    sys.path.insert(0, 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425'); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
    lookdev_cap.shot(path, cam, tgt, 1.5, 50.0)


if '--remove' in args:
    gone = [x for x in EAS.get_all_level_actors() if TAG in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('removed', len(gone), 'CW504 actors')
elif '--probe' in args:
    cs = stone_components(); cnt = {}
    for a, c, o, e, m in cs: cnt[m] = cnt.get(m, 0) + 1
    print(len(cs), 'stone components'); print('\n'.join('%5d %s' % (v, k) for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:40]))
else:
    if any(str(t) == TAG for x in EAS.get_all_level_actors() for t in x.tags):
        raise SystemExit('CW504 cards already in the level: run --remove first')
    comps, cards = plan()
    cnt = {}
    for cd in cards: cnt[cd[0]] = cnt.get(cd[0], 0) + 1
    rep = ['%d stone components probed, %d cards' % (len(comps), len(cards))] + ['%5d %s' % (v, k) for k, v in sorted(cnt.items())]
    rep += ['%s %.0f %.0f %.0f  %.0fx%.0f roll %.0f n %.2f %.2f' % (cd[0], cd[1].x, cd[1].y, cd[1].z, cd[3], cd[4], cd[5], cd[2].x, cd[2].y) for cd in cards]
    open(HERE + '/place_report504.txt', 'w', encoding='utf-8').write('\n'.join(rep))
    print('\n'.join(rep[:8]))
    if '--preview' in args:
        i = args.index('--preview'); at = V(float(args[i + 1]), float(args[i + 2]), float(args[i + 3])); out = args[i + 4]
        near = sorted(cards, key=lambda cd: (cd[1] - at).length())
        if not near: raise SystemExit('no cards')
        tgt = near[0][1]; n = near[0][2]
        cam = tgt + V(n.x, n.y, 0) * 900.0 + V(-n.y, n.x, 0) * 350.0 + V(0, 0, 120.0)
        shot(out + '/cw504_before.png', cam, tgt)
        made = spawn(cards, tgt)
        print('preview: spawned', len(made), 'actors near', tgt, '(take after shot with a SEPARATE run: shaders compile async)')
        open(HERE + '/_preview_cam.txt', 'w').write('%f %f %f %f %f %f' % (cam.x, cam.y, cam.z, tgt.x, tgt.y, tgt.z))
    elif '--apply' in args:
        made = spawn(cards)
        print('APPLIED: %d cards on %d actors (tag CW504). Save the level on the Master.' % (len(cards), len(made)))
