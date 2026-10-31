# #351 A real meadow outside the castle: grass + flowers + bushes (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
# Owner: "the ground outside the castle is made of grass scattered, but nature has grass and flowers and bushes".
#   py "<repo>/handoffs/meadow-351/place_meadow_ue.py" --list        READ-ONLY: which plant meshes it found, by kind
#   py "<repo>/handoffs/meadow-351/place_meadow_ue.py" --dry-run     does the whole scatter, places nothing, prints counts
#   py "<repo>/handoffs/meadow-351/place_meadow_ue.py"               places ONE actor "Meadow351" (instanced meshes)
#   py ".../place_meadow_ue.py" --remove                             deletes it (= the undo; nothing else is touched)
# Options: --radius <cm> (default 22000 around the castle), --seed <n>, --band x0,x1,y,halfwidth (more road bands, repeatable),
#          --road-pad <cm> (default 150: bare verge beside each road)
# Roads (#351 fix, 2026-10-31 night): the gate road is a DECAL (Env_WornGround_Decal) on a landscape with no paint layers,
#   so a trace can't see it. Nothing grows on: (1) road-like decals (label or material has road/path/worn/trail/track/dirt),
#   tested in the decal's own rotated box; (2) actors labelled *Road* / *Path* (PortalRoad, HiddenRoad): along their splines
#   (half-width 450 cm) or, without a spline, in their bounds; (3) bands: the Master's hand-cleared gate road
#   (x -7000..300, y 1750 +- 450) plus any --band. --list / --dry-run print every road zone found.
# Ecology rules (handoffs/knowledge/research_notes/environment_vegetation.md: studios place by maps and rules, not by hand;
# Naughty Dog: "is there enough light / water for this plant here?"):
#   grass clumps   everywhere open, density follows a large-scale noise (meadow patches vs thin trampled ground)
#   flowers        each species in its own patches (seeds fall near the parent plant), only on gentle, open ground
#   bushes         at edges: near rocks, walls, trees, buildings (a horizontal probe finds them), rarely in the open
#   ferns          at edges too, in the shade side (north of the obstacle)
#   dead shrubs    on dry, steeper ground (slope 20-35 deg)
#   nothing        on slopes over 35 deg, on anything that is not the landscape (roads made of meshes, rocks, buildings),
#                  inside the castle box (+4 m)
# Plants are found by name anywhere in /Game (Megascans / Fab packs, TGA's flora kit #352 in Environment/Flora/Meadow):
#   grass: *Grass* (not Dead), flowers: *Flower* *Daisy* *Poppy* *Yarrow* *Knapweed* *Cornflower* *Clover* *Chamomile*
#   *Dandelion* *Buttercup*, bushes: *Bush* *Hawthorn* *Hazel* *Broom* *Gorse* *Shrub* (not Dead), ferns: *Fern* *Bracken*,
#   dead: *Dead_Shrub* *DeadShrub* *Dead*.  Re-run after new plants are imported: they join automatically.
import os, sys, math, random, unreal

A = sys.argv[1:]
DRY, LIST, REMOVE = '--dry-run' in A, '--list' in A, '--remove' in A
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A and A.index(k) + 1 < len(A) else d
RADIUS, SEED = arg('--radius', 22000.0), arg('--seed', 351)
ROAD_PAD, ROAD_HW, CELL = arg('--road-pad', 150.0), 450.0, 100.0
ROAD_WORDS = ('road', 'path', 'worn', 'trail', 'track', 'dirt')
BANDS = [(-7000.0, 300.0, 1750.0, 450.0)]                         # the gate road the Master cleared by hand (x0, x1, y, half-width)
BANDS += [tuple(float(v) for v in A[i + 1].split(',')) for i, k in enumerate(A) if k == '--band' and i + 1 < len(A)]
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\meadow-351'
LABEL = 'Meadow351'
CASTLE_MIN, CASTLE_MAX = (-400.0, -400.0), (5000.0, 3850.0)      # castle box (from #41) + 4 m
CENTRE = ((CASTLE_MIN[0] + CASTLE_MAX[0]) / 2, (CASTLE_MIN[1] + CASTLE_MAX[1]) / 2)
STEP = 110.0                                                      # sample grid (cm), jittered
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#351 meadow' + (' (DRY RUN, nothing placed)' if DRY else '') + ' radius %.0f cm' % RADIUS]
rng = random.Random(SEED)

KINDS = {  # kind: (name keys, cull start/end cm, cast shadow, scale range, align to slope 0..1)
    'grass': (('grass',), 3500, 5500, False, (0.75, 1.3), 0.6),
    'flower': (('flower', 'daisy', 'poppy', 'yarrow', 'knapweed', 'cornflower', 'clover', 'chamomile', 'dandelion', 'buttercup'), 2500, 4200, False, (0.8, 1.2), 0.3),
    'bush': (('bush', 'hawthorn', 'hazel', 'broom', 'gorse', 'shrub'), 9000, 15000, True, (0.7, 1.3), 0.2),
    'fern': (('fern', 'bracken'), 4000, 6500, False, (0.8, 1.25), 0.5),
    'dead': (('dead',), 6000, 9000, True, (0.7, 1.2), 0.4)}


def kind_of(path):
    n = path.lower()
    if 'blobmine' in n or 'realm' in n or 'tentacle' in n or '/ui/' in n: return None
    if 'dead' in n and ('shrub' in n or 'bush' in n or 'plant' in n or 'grass' in n): return 'dead'
    for k in ('flower', 'fern', 'bush', 'grass'):
        if any(w in n for w in KINDS[k][0]): return k
    return None


def plants():
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh')], package_paths=['/Game'], recursive_paths=True)
    out = {}
    for ad in AR.get_assets(flt):
        p = str(ad.package_name)
        if not any(w in p.lower() for w in ('plant', 'flora', 'foliage', 'meadow', 'grass', 'flower', 'bush', 'shrub', 'fern')): continue
        k = kind_of(p)
        if k: out.setdefault(k, []).append(p + '.' + str(ad.asset_name))
    return out


def vnoise(x, y, scale, seed):
    """smooth 2D value noise in world cm (patches of about `scale` cm)"""
    gx, gy = x / scale, y / scale; x0, y0 = math.floor(gx), math.floor(gy); fx, fy = gx - x0, gy - y0
    h = lambda i, j: (math.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


world = unreal.EditorLevelLibrary.get_editor_world()
old = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == LABEL]
if REMOVE:
    log.append('remove %d' % len(old))
    if not DRY:
        for a in old: EAS.destroy_actor(a)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print('\n'.join(log)); raise SystemExit


def road_cells():
    """set of (ix, iy) 1 m cells where nothing may grow: road decals, *Road* / *Path* actors, bands (+ ROAD_PAD)."""
    cells, zones = set(), []
    def box(x0, x1, y0, y1, test=None):
        n = 0
        for ix in range(int(math.floor(x0 / CELL)), int(math.floor(x1 / CELL)) + 1):
            for iy in range(int(math.floor(y0 / CELL)), int(math.floor(y1 / CELL)) + 1):
                if test is None or test((ix + 0.5) * CELL, (iy + 0.5) * CELL): cells.add((ix, iy)); n += 1
        return n
    for x0, x1, yc, hw in BANDS:
        zones.append('band x %.0f..%.0f y %.0f +- %.0f: %d cells' % (x0, x1, yc, hw, box(min(x0, x1), max(x0, x1), yc - hw - ROAD_PAD, yc + hw + ROAD_PAD)))
    for a in EAS.get_all_level_actors():
        label = a.get_actor_label()
        for d in a.get_components_by_class(unreal.DecalComponent):
            mat = d.get_editor_property('decal_material')
            name = (label + ' ' + (mat.get_name() if mat else '')).lower()
            if not any(w in name for w in ROAD_WORDS): continue
            xf = d.get_world_transform(); o, sc = xf.translation, xf.scale3d
            r = xf.rotation.rotator()
            ax = [unreal.MathLibrary.get_forward_vector(r), unreal.MathLibrary.get_right_vector(r), unreal.MathLibrary.get_up_vector(r)]
            sz = d.get_editor_property('decal_size')
            half = [abs(sz.x * sc.x) + 500.0, abs(sz.y * sc.y) + ROAD_PAD, abs(sz.z * sc.z) + ROAD_PAD]   # depth axis kept loose
            def inside(x, y, o=o, ax=ax, half=half):
                dx, dy = x - o.x, y - o.y                                  # ground point, z taken at the decal centre
                return all(abs(dx * v.x + dy * v.y) <= h for v, h in zip(ax, half))
            ext = sum(half[1:]) + 10
            n = box(o.x - ext, o.x + ext, o.y - ext, o.y + ext, inside)
            zones.append('decal %s (%s): %d cells' % (label, mat.get_name() if mat else '-', n))
        if not any(w in label.lower() for w in ('road', 'path')) or a.get_components_by_class(unreal.DecalComponent): continue
        splines = a.get_components_by_class(unreal.SplineComponent)
        if splines:
            n0 = len(cells); hw = ROAD_HW + ROAD_PAD
            for sp in splines:
                L = sp.get_spline_length(); k = 0.0
                while k <= L:
                    q = sp.get_location_at_distance_along_spline(k, unreal.SplineCoordinateSpace.WORLD)
                    box(q.x - hw, q.x + hw, q.y - hw, q.y + hw, lambda x, y, q=q: (x - q.x) ** 2 + (y - q.y) ** 2 <= hw * hw)
                    k += CELL
            zones.append('road spline %s: %d cells' % (label, len(cells) - n0))
        else:
            o, e = a.get_actor_bounds(False)
            zones.append('road bounds %s: %d cells' % (label, box(o.x - e.x - ROAD_PAD, o.x + e.x + ROAD_PAD, o.y - e.y - ROAD_PAD, o.y + e.y + ROAD_PAD)))
    return cells, zones


ROADS, zones = road_cells()
log += ['road zones (%d cells of 1 m):' % len(ROADS)] + ['  ' + z for z in zones]
P = plants()
for k in KINDS: log.append('%-6s %d meshes %s' % (k, len(P.get(k, [])), ', '.join(x.split('.')[-1] for x in P.get(k, [])[:8])))
if LIST:
    open(os.path.join(HERE, 'meadow_list.txt'), 'w').write('\n'.join(log)); print('\n'.join(log)); raise SystemExit
if not P.get('grass'): raise SystemExit('no grass meshes found (see --list)')

lands = [a for a in EAS.get_all_level_actors() if 'Landscape' in a.get_class().get_name()]
if not lands: raise SystemExit('no Landscape in the level')
lo = [min(a.get_actor_bounds(False)[0].x - a.get_actor_bounds(False)[1].x for a in lands), min(a.get_actor_bounds(False)[0].y - a.get_actor_bounds(False)[1].y for a in lands)]
hi = [max(a.get_actor_bounds(False)[0].x + a.get_actor_bounds(False)[1].x for a in lands), max(a.get_actor_bounds(False)[0].y + a.get_actor_bounds(False)[1].y for a in lands)]
ztop = max(a.get_actor_bounds(False)[0].z + a.get_actor_bounds(False)[1].z for a in lands) + 5000
zbot = min(a.get_actor_bounds(False)[0].z - a.get_actor_bounds(False)[1].z for a in lands) - 1000
log.append('landscape %s .. %s' % ([round(v) for v in lo], [round(v) for v in hi]))
TQ = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1


def trace(a, b):
    h = unreal.SystemLibrary.line_trace_single(world, a, b, TQ, True, [], unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    if not t or not t[0]: return None
    actor = t[9] if len(t) > 9 else None                         # (blocking, overlap, time, dist, loc, impact, normal, impactN, physmat, hitActor, ...)
    return t[4], t[7], actor


def is_land(actor):
    try: return actor is not None and 'Landscape' in actor.get_class().get_name()
    except Exception: return False


spec = {k: [] for k in KINDS}
patch_seed = {p: i * 13 + 5 for i, p in enumerate(P.get('flower', []))}
x = max(lo[0], CENTRE[0] - RADIUS)
n_samples = n_road = 0
while x < min(hi[0], CENTRE[0] + RADIUS):
    y = max(lo[1], CENTRE[1] - RADIUS)
    while y < min(hi[1], CENTRE[1] + RADIUS):
        px, py = x + rng.uniform(-STEP * 0.45, STEP * 0.45), y + rng.uniform(-STEP * 0.45, STEP * 0.45)
        y += STEP
        if (px - CENTRE[0]) ** 2 + (py - CENTRE[1]) ** 2 > RADIUS ** 2: continue
        if CASTLE_MIN[0] < px < CASTLE_MAX[0] and CASTLE_MIN[1] < py < CASTLE_MAX[1]: continue
        n_samples += 1
        if (int(math.floor(px / CELL)), int(math.floor(py / CELL))) in ROADS: n_road += 1; continue   # bare road + verge
        h = trace(unreal.Vector(px, py, ztop), unreal.Vector(px, py, zbot))
        if not h or not is_land(h[2]): continue                  # rocks, buildings, mesh roads, water: nothing grows there
        loc, nrm = h[0], h[1]
        slope = math.degrees(math.acos(max(-1.0, min(1.0, nrm.z))))
        if slope > 35: continue
        meadow = vnoise(px, py, 2400, 1) * 0.7 + vnoise(px, py, 600, 2) * 0.3      # lush vs trampled ground
        r = rng.random()
        # edge probe: something solid within 3.5 m sideways -> bushes / ferns like it here
        edge, north = False, False
        if r < 0.35:
            for dx, dy in ((350, 0), (-350, 0), (0, 350), (0, -350)):
                e = trace(loc + unreal.Vector(0, 0, 60), loc + unreal.Vector(dx, dy, 60))
                if e and not is_land(e[2]):
                    edge = True; north = north or dy < 0 or dx > 0
                    break
        pick = None
        if 20 <= slope <= 35 and P.get('dead') and r < 0.06: pick = 'dead'
        elif edge and P.get('bush') and r < 0.12: pick = 'bush'
        elif edge and north and P.get('fern') and r < 0.2: pick = 'fern'
        elif not edge and P.get('bush') and r < 0.004: pick = 'bush'
        elif slope < 18 and P.get('flower'):
            best, bv = None, 0.0
            for fp, sd in patch_seed.items():                    # each species in its own patches
                v = vnoise(px, py, 900, sd)
                if v > 0.66 and v > bv: best, bv = fp, v
            if best and r < 0.55 * (bv - 0.6) / 0.4 + 0.05: pick = ('flower', best)
        if pick is None and r < 0.12 + 0.55 * meadow: pick = 'grass'
        if pick is None: continue
        k, mesh = (pick if isinstance(pick, tuple) else (pick, rng.choice(P[pick])))
        _, cs, ce, shadow, (smin, smax), align = KINDS[k]
        up = unreal.Vector(0, 0, 1) * (1 - align) + nrm * align
        rot = unreal.MathLibrary.make_rot_from_z(up)
        rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(0, 0, rng.uniform(0, 360)), rot)
        s = rng.uniform(smin, smax) * (0.85 + 0.3 * meadow if k == 'grass' else 1.0)
        spec[k].append((mesh, unreal.Transform(loc - unreal.Vector(0, 0, 2), rot, unreal.Vector(s, s, s))))
    x += STEP
for k in KINDS: log.append('placed %-6s %6d' % (k, len(spec[k])))
log.append('samples %d (on roads, left bare: %d)' % (n_samples, n_road))

if not DRY:
    for a in old: EAS.destroy_actor(a)
    act = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))   # empty container
    act.set_actor_label(LABEL); act.tags = [unreal.Name(LABEL)]
    by_mesh = {}
    for k in KINDS:
        for mesh, xf in spec[k]: by_mesh.setdefault((k, mesh), []).append(xf)
    for (k, mesh), xfs in by_mesh.items():
        h, why = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_instance(act)[0], new_class=unreal.HierarchicalInstancedStaticMeshComponent, blueprint_context=None))
        if not LIB.is_handle_valid(h): log.append('  could not add a component for %s: %s' % (mesh, why)); continue
        c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
        _, cs, ce, shadow, _, _ = KINDS[k]
        c.set_static_mesh(unreal.load_asset(mesh)); c.set_collision_profile_name('NoCollision')
        c.set_editor_property('cast_shadow', shadow)
        c.set_editor_property('instance_start_cull_distance', cs); c.set_editor_property('instance_end_cull_distance', ce)
        c.add_instances(xfs, False, True)                         # world space
        log.append('  %-6s %-40s %d' % (k, mesh.split('.')[-1], len(xfs)))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

out = '\n'.join(log)
open(os.path.join(HERE, 'meadow351%s.txt' % ('_dry' if DRY else '')), 'w').write(out)
unreal.log(out); print(out)
