# #440 (i5, 2026-11-03): READ-ONLY dump for the grass re-layout. Aborts in PIE.
#   py grass_dump_ue.py      -> grass_dump.csv (one row per grass / flower instance), road_cells.csv, mesh_heights.csv
# road_cells() is copied from meadow-351/place_meadow_ue.py (decal roads, Road/Path actors, the hand-cleared gate band).
import math, os, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/grass-440/'
CELL, ROAD_PAD, ROAD_HW, ROAD_MAX_HALF = 100.0, 0.0, 450.0, 2500.0      # pad 0 here: verges are decided offline
ROAD_WORDS = ('road', 'path', 'worn', 'trail', 'track', 'dirt')
BANDS = [(-7000.0, 300.0, 1750.0, 450.0)]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ACTORS = ('Env_GrassTall', 'Env_BaseRubble', 'Meadow351')

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
            if 'wornground' in name:                                  # #440: the worn apron is its own mask, not a road
                WORN_DECALS.append(d); continue
            xf = d.get_world_transform(); o, sc = xf.translation, xf.scale3d
            r = xf.rotation.rotator()
            ax = [unreal.MathLibrary.get_forward_vector(r), unreal.MathLibrary.get_right_vector(r), unreal.MathLibrary.get_up_vector(r)]
            sz = d.get_editor_property('decal_size')
            half = [abs(sz.x * sc.x) + 500.0, abs(sz.y * sc.y) + ROAD_PAD, abs(sz.z * sc.z) + ROAD_PAD]   # depth axis kept loose
            def inside(x, y, o=o, ax=ax, half=half):
                dx, dy = x - o.x, y - o.y                                  # ground point, z taken at the decal centre
                return all(abs(dx * v.x + dy * v.y) <= h for v, h in zip(ax, half))
            if min(half[0], half[1]) > ROAD_MAX_HALF:
                zones.append('skip decal %s: %.0f x %.0f cm too wide for a road' % (label, 2 * half[0], 2 * half[1])); continue
            ext = sum(half[1:]) + 10
            n = box(o.x - ext, o.x + ext, o.y - ext, o.y + ext, inside)
            zones.append('decal %s (%s): %d cells' % (label, mat.get_name() if mat else '-', n))
        if not any(w in label.lower() for w in ('road', 'path')) or a.get_components_by_class(unreal.DecalComponent): continue
        cls = a.get_class().get_name()
        if 'Volume' in cls or 'Bounds' in label:   # #375 (5.8): NavBounds_PortalRoad is a nav volume, not a road; it bared the whole map
            zones.append('skip %s (%s): a volume, not a road' % (label, cls)); continue
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
            if min(e.x, e.y) > ROAD_MAX_HALF:          # a road is long and narrow; a box this wide on both sides is not one
                zones.append('skip %s: bounds %.0f x %.0f cm too wide for a road' % (label, 2 * e.x, 2 * e.y)); continue
            zones.append('road bounds %s: %d cells' % (label, box(o.x - e.x - ROAD_PAD, o.x + e.x + ROAD_PAD, o.y - e.y - ROAD_PAD, o.y + e.y + ROAD_PAD)))
    return cells, zones

WORN_DECALS = []
ROADS, zones = road_cells()
ZONES = zones
WORN = set()
for d in WORN_DECALS:                                                 # same rotated-box test as roads, no slack
    xf = d.get_world_transform(); o, sc = xf.translation, xf.scale3d; r = xf.rotation.rotator()
    ax = [unreal.MathLibrary.get_forward_vector(r), unreal.MathLibrary.get_right_vector(r), unreal.MathLibrary.get_up_vector(r)]
    sz = d.get_editor_property('decal_size'); half = [abs(sz.x * sc.x), abs(sz.y * sc.y), abs(sz.z * sc.z)]
    ext = max(half) + 10
    for ix in range(int((o.x - ext) // CELL), int((o.x + ext) // CELL) + 1):
        for iy in range(int((o.y - ext) // CELL), int((o.y + ext) // CELL) + 1):
            x, y = (ix + 0.5) * CELL - o.x, (iy + 0.5) * CELL - o.y
            if all(abs(x * v.x + y * v.y) <= h for v, h in zip(ax, half)): WORN.add((ix, iy))
open(OUT + 'worn_cells.csv', 'w').write(chr(10).join('%d,%d' % c for c in sorted(WORN)))
print('worn cells', len(WORN))
open(OUT + 'road_cells.csv', 'w').write('\n'.join('%d,%d' % c for c in sorted(ROADS)))
print('road cells', len(ROADS)); [print('  ' + z) for z in zones]
rows, heights = [], {}
for a in EAS.get_all_level_actors():
    if a.get_actor_label() not in ACTORS: continue
    for ci, c in enumerate(a.get_components_by_class(unreal.InstancedStaticMeshComponent)):
        m = c.get_editor_property('static_mesh')
        if not m: continue
        mp = m.get_path_name()
        if mp not in heights:
            b = m.get_bounding_box(); heights[mp] = (b.max.z - b.min.z, b.max.x - b.min.x, b.max.y - b.min.y)
        n = c.get_instance_count()
        for i in range(n):
            t = c.get_instance_transform(i, True); p, r, s = t.translation, t.rotation.rotator(), t.scale3d
            rows.append('%s,%d,%s,%d,%.0f,%.0f,%.0f,%.1f,%.1f,%.1f,%.3f' % (a.get_actor_label() + '#' + a.get_name(), ci, mp.split('.')[-1], i, p.x, p.y, p.z, r.roll, r.pitch, r.yaw, s.z))
        print('%-15s comp %2d %-34s %6d inst  cull %s-%s shadow %s' % (a.get_actor_label(), ci, mp.split('.')[-1], n, c.get_editor_property('instance_start_cull_distance'), c.get_editor_property('instance_end_cull_distance'), c.get_editor_property('cast_shadow')))
open(OUT + 'grass_dump.csv', 'w').write('actor,comp,mesh,idx,x,y,z,roll,pitch,yaw,sz\n' + '\n'.join(rows))
open(OUT + 'mesh_heights.csv', 'w').write('\n'.join('%s,%.1f,%.1f,%.1f' % ((k.split('.')[-1],) + v) for k, v in heights.items()))
print('instances', len(rows))
# #440: decal footprints (exact, no slack) so the worn ground can be told apart from roads offline
dec = []
for a in EAS.get_all_level_actors():
    for d in a.get_components_by_class(unreal.DecalComponent):
        mat = d.get_editor_property('decal_material'); xf = d.get_world_transform(); r = xf.rotation.rotator(); sz = d.get_editor_property('decal_size'); sc = xf.scale3d
        dec.append('%s,%s,%.0f,%.0f,%.1f,%.0f,%.0f' % (a.get_actor_label(), mat.get_name() if mat else '-', xf.translation.x, xf.translation.y, r.yaw, abs(sz.x * sc.x), abs(sz.y * sc.y)))
open(OUT + 'decals.csv', 'w').write('\n'.join(dec))
print('decals', len(dec))
