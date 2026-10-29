# #29 border placement v4 (laptop2, 2026-10-30), from the owner's marked map (owner_marks.webp -> placement_v4.json).
# Run in the editor with the game level open:   py "<repo>/handoffs/player-boundaries-29/place_border_v4.py"
# It REPLACES the Master's first placement: every actor in the outliner folder Boundaries_29 (labels B29_*) is deleted,
# then it places, snapped to the ground by line trace:
#   SM_SiegeBarricade_Palisade   every ~3.8 m along the owner's red line, spikes facing out (away from the castle), yaw jitter
#   SM_SiegeBarricade_Cheval     in front of every gap wider than 4.5 m between palisades (outside), and at both gate sides
#   SM_SiegeBarricade_Watchtower every ~50 m, 2 m inside the line
#   the gate (SM_SiegeGate_Frame, _LeafL, _LeafR, _Bar, _Lever) in the owner's blue gap, if the gate meshes are imported
# Everything goes in Boundaries_29 again; collision is the meshes' own box. Nothing else in the level is touched.
import os, json, math, random
import unreal

REPO = r''
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'player-boundaries-29')
P = json.load(open(os.path.join(HERE, 'placement_v4.json')))
KIT = '/Game/CastleDefender/Environment/Boundaries/SiegeKit/'
GATE = '/Game/CastleDefender/Environment/Boundaries/SiegeGate/'
FOLDER = 'Boundaries_29'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
random.seed(29)

# clear the old placement
old = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('B29_')]
for a in old: eas.destroy_actor(a)
unreal.log('#29: removed %d old B29_ actors' % len(old))

def ground_z(x, y):
    r = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -30000),
                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    hit = next((h for h in r if isinstance(h, unreal.HitResult)), None) if isinstance(r, tuple) else r
    if hit is None: return None
    t = hit.to_tuple()
    return t[4].z if t[0] else None

placed = []
def place(mesh_path, label, x, y, yaw, scale=1.0, sink=15.0, z=None):
    m = unreal.load_asset(mesh_path)
    if m is None: unreal.log_warning('missing ' + mesh_path); return None
    gz = ground_z(x, y) if z is None else z
    if gz is None: return None
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, gz - sink), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    a.static_mesh_component.set_static_mesh(m); a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(label); a.set_folder_path(FOLDER); placed.append(a); return a

# 1. palisades along the line (the wall's face looks toward -Y in the mesh: rotate so -Y = outward = the json yaw)
walls = P['walls']
for k, (x, y, yaw) in enumerate(walls):
    place(KIT + 'SM_SiegeBarricade_Palisade', 'B29_Pal_%03d' % k, x, y, yaw + 90 + random.uniform(-7, 7), random.uniform(0.92, 1.12), sink=25.0)

# 2. chevals: gaps between neighbouring palisades (sorted along the line by nearest-neighbour chaining)
pts = [(x, y, yaw) for x, y, yaw in walls]
def gaps():
    out = []
    for i, (x, y, yaw) in enumerate(pts):
        best = None
        for j, (x2, y2, _) in enumerate(pts):
            if j == i: continue
            d = math.hypot(x2 - x, y2 - y)
            if 450 < d < 1400 and (best is None or d < best[0]):
                # only count it as a gap if nothing else sits between
                mx, my = (x + x2) / 2, (y + y2) / 2
                if all(math.hypot(px - mx, py - my) > 250 for q, (px, py, _) in enumerate(pts) if q not in (i, j)):
                    best = (d, mx, my, yaw, j)
        if best and i < best[4]: out.append(best[:4])
    return out
for k, (d, mx, my, yaw) in enumerate(gaps()):
    ox, oy = math.cos(math.radians(yaw)) * 180, math.sin(math.radians(yaw)) * 180       # 1.8 m outside the line
    place(KIT + 'SM_SiegeBarricade_Cheval', 'B29_Chev_%03d' % k, mx + ox, my + oy, yaw + 90 + random.uniform(-15, 15), random.uniform(0.9, 1.1), sink=12.0)

# 3. watchtowers every ~50 m, 2 m inside
acc, nt = 0.0, 0
prev = None
for x, y, yaw in walls:
    if prev: acc += math.hypot(x - prev[0], y - prev[1])
    prev = (x, y)
    if acc >= 5000:
        acc = 0; ix, iy = x - math.cos(math.radians(yaw)) * 200, y - math.sin(math.radians(yaw)) * 200
        place(KIT + 'SM_SiegeBarricade_Watchtower', 'B29_Tower_%02d' % nt, ix, iy, yaw + 90 + random.uniform(-10, 10), 1.0, sink=20.0); nt += 1

# 4. the gate (outside = -Y in the meshes: yaw so that -Y points along the json gate yaw)
g = P['gate']; gyaw = g['yaw'] + 90
gz = ground_z(g['x'], g['y'])
if unreal.load_asset(GATE + 'SM_SiegeGate_Frame') is not None and gz is not None:
    frame = place(GATE + 'SM_SiegeGate_Frame', 'B29_Gate_Frame', g['x'], g['y'], gyaw, 1.0, sink=35.0, z=gz)
    # the pieces' pivots (gate_meta.json) are in the frame's local space: leaf hinges at x = +-2.88 m, bar, lever
    meta = json.load(open(os.path.join(HERE, 'gate_meta.json')))['pieces']
    r = math.radians(gyaw); cs, sn = math.cos(r), math.sin(r)
    for piece in ('LeafL', 'LeafR', 'Bar', 'Lever'):
        px, py, pz = [v * 100 for v in meta[piece]]
        wx, wy = g['x'] + px * cs - py * sn, g['y'] + px * sn + py * cs
        a = place(GATE + 'SM_SiegeGate_' + piece, 'B29_Gate_' + piece, wx, wy, gyaw, 1.0, sink=0.0, z=gz - 35.0 + pz)
        if a and piece in ('LeafL', 'LeafR', 'Bar', 'Lever'): a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    # chevals flanking the gate, outside
    for s in (-1, 1):
        fx, fy = g['x'] + (s * 420) * cs - (-250) * sn, g['y'] + (s * 420) * sn + (-250) * cs
        place(KIT + 'SM_SiegeBarricade_Cheval', 'B29_Gate_Chev_%d' % (s > 0), fx, fy, gyaw + random.uniform(-10, 10), 1.0, sink=12.0)
else:
    unreal.log_warning('#29: gate meshes not imported yet (assets/laptop2/SiegeGate); the gap is left open at (%.0f, %.0f)' % (g['x'], g['y']))
unreal.log('#29 v4 placed %d actors in %s' % (len(placed), FOLDER))
