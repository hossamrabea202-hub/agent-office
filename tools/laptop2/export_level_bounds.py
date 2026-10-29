# #29 player boundaries: export the open level's layout for laptop2 (2026-10-29). Read-only: changes nothing in the level.
# Run in the Unreal editor with the game level open (Output Log, Python):
#   py "<repo>/tools/laptop2/export_level_bounds.py"
# Writes to <repo>/handoffs/exports/laptop2/bounds29/:
#   level.json      landscape / nav / fog / kill-Z / player start, big actors with their mesh, blocker-like meshes in the project
#   height.png      top-down ground height (8-bit, min/max in level.json), traced on a grid over the landscape
#   nav.png         white = on the NavMesh (walkable), black = not
#   grid.json       the same grid as numbers (height cm, nav 0/1), for building the border line
import json, os, struct, zlib
import unreal

REPO = r''   # your office-repo checkout; empty = two folders up from this script
N = 192      # grid cells per side (N*N traces, ~20-60 s)
try:
    ROOT = REPO or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    ROOT = REPO
if not ROOT:
    raise RuntimeError('set REPO at the top of this script to your office-repo checkout')
OUT = os.path.join(ROOT, 'handoffs', 'exports', 'laptop2', 'bounds29')
os.makedirs(OUT, exist_ok=True)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
v3 = lambda v: [round(v.x, 1), round(v.y, 1), round(v.z, 1)]

def bounds(a):
    o, e = a.get_actor_bounds(False)
    return {'origin': v3(o), 'extent': v3(e)}

info = {'level': world.get_path_name(), 'landscape': [], 'nav_bounds': [], 'fog': [], 'blocking': [], 'player_start': [],
        'kill_z': None, 'big_actors': [], 'blocker_meshes': []}
try:
    info['kill_z'] = world.get_world_settings().get_editor_property('kill_z')
except Exception as e:
    info['kill_z'] = 'n/a: %s' % e

lo = unreal.Vector(1e9, 1e9, 1e9); hi = unreal.Vector(-1e9, -1e9, -1e9)
for a in actors:
    cls = a.get_class().get_name()
    rec = dict(label=a.get_actor_label(), cls=cls, **bounds(a))
    if 'Landscape' in cls and 'Gizmo' not in cls:
        info['landscape'].append(rec)
        o, e = a.get_actor_bounds(False)
        lo = unreal.Vector(min(lo.x, o.x - e.x), min(lo.y, o.y - e.y), min(lo.z, o.z - e.z))
        hi = unreal.Vector(max(hi.x, o.x + e.x), max(hi.y, o.y + e.y), max(hi.z, o.z + e.z))
    elif cls == 'NavMeshBoundsVolume': info['nav_bounds'].append(rec)
    elif 'Fog' in cls: info['fog'].append(rec)
    elif cls in ('BlockingVolume', 'KillZVolume', 'PainCausingVolume'): info['blocking'].append(rec)
    elif cls == 'PlayerStart': info['player_start'].append(rec)
    else:
        o, e = a.get_actor_bounds(False)
        if max(e.x, e.y) > 400 and cls not in ('Landscape', 'WorldSettings'):
            meshes = []
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                m = c.get_editor_property('static_mesh')
                if m: meshes.append(m.get_path_name().split('.')[0])
            rec['meshes'] = sorted(set(meshes))[:6]
            info['big_actors'].append(rec)
info['big_actors'] = sorted(info['big_actors'], key=lambda r: -max(r['extent'][:2]))[:400]
if not info['landscape']:
    raise RuntimeError('no Landscape in the open level: open the game level first')
info['grid_box'] = {'min': v3(lo), 'max': v3(hi), 'n': N}

# blocker-like meshes already in the project (to reuse: rocks, ruins, fences, logs, spikes ...)
reg = unreal.AssetRegistryHelpers.get_asset_registry()
words = ('rock', 'cliff', 'boulder', 'wall', 'ruin', 'fence', 'palisade', 'barricade', 'spike', 'log', 'tree', 'stump', 'cart', 'debris', 'stone')
for ad in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh')):
    p = str(ad.package_name)
    if p.startswith('/Game/') and any(w in p.lower().split('/')[-1] for w in words):
        info['blocker_meshes'].append(p)
info['blocker_meshes'] = sorted(info['blocker_meshes'])[:300]

# ---- grid: ground height by line trace, nav by projecting onto the NavMesh ----
H = [[None] * N for _ in range(N)]; NV = [[0] * N for _ in range(N)]
top, bot = hi.z + 5000, lo.z - 5000
def trace(x, y):
    r = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, top), unreal.Vector(x, y, bot),
                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    hit = r[0] if isinstance(r, tuple) else r
    if hit is None: return None
    t = hit.to_tuple() if hasattr(hit, 'to_tuple') else None
    if t is not None:
        if not t[0]: return None
        return t[4].z   # (blocking_hit, initial_overlap, time, distance, location, ...)
    return hit.location.z if hit.blocking_hit else None
nav_ok = True
for j in range(N):
    for i in range(N):
        x = lo.x + (i + 0.5) * (hi.x - lo.x) / N; y = lo.y + (j + 0.5) * (hi.y - lo.y) / N
        z = trace(x, y); H[j][i] = z
        if z is not None and nav_ok:
            try:
                p = unreal.NavigationSystemV1.project_point_to_navigation(world, unreal.Vector(x, y, z), None, None, unreal.Vector(60, 60, 250))
                p = p[0] if isinstance(p, tuple) else p
                NV[j][i] = 1 if p is not None and abs(p.x - x) < 80 and abs(p.y - y) < 80 else 0
            except Exception as e:
                nav_ok = False; info['nav_error'] = str(e)
zs = [z for row in H for z in row if z is not None]
info['height_min'], info['height_max'] = (min(zs), max(zs)) if zs else (0, 0)
info['nav_cells'] = sum(map(sum, NV))

def png(path, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 0, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))
zr = max(info['height_max'] - info['height_min'], 1)
# rows from +Y (top of the image) to -Y, columns -X to +X; documented in level.json
png(os.path.join(OUT, 'height.png'), [[0 if z is None else int(1 + 254 * (z - info['height_min']) / zr) for z in H[j]] for j in range(N - 1, -1, -1)])
png(os.path.join(OUT, 'nav.png'), [[255 * NV[j][i] for i in range(N)] for j in range(N - 1, -1, -1)])
info['image_axes'] = 'image row 0 = max Y, column 0 = min X; cell size = (max - min) / n'
json.dump(info, open(os.path.join(OUT, 'level.json'), 'w'), indent=1)
json.dump({'h': [[None if z is None else round(z) for z in r] for r in H], 'nav': NV}, open(os.path.join(OUT, 'grid.json'), 'w'))
unreal.log('#29 level bounds exported to %s (%d landscape, %d nav cells of %d, %d big actors, %d blocker meshes)'
           % (OUT, len(info['landscape']), info['nav_cells'], N * N, len(info['big_actors']), len(info['blocker_meshes'])))
