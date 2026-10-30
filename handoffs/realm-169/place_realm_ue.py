# #169 stage 1: the closed tentacle realm (laptop2, 2026-10-30). Run in the editor with the game level open:
#   py "<repo>/handoffs/realm-169/place_realm_ue.py"
# Idempotent: every actor tagged laptop2_realm (all labelled Realm_*) is deleted first, then everything is placed again.
# Nothing else is touched: PPV_Realm and the Master's Realm_Bubble stay (the new dome is Realm_Dome; hide the old sphere
# when the dome looks right). Needs: SiegeKit, SiegeGate (assets/laptop2/SiegeGate), FloraKit, CampKit (torch posts),
# RealmKit (SM_RealmDome + make_realm_bubble.py). Missing meshes are skipped with a warning, the rest still goes in.
#
# Layout (Unreal cm; the owner's box X -20112..-8230, Y 2099..8427; the road is south of it, -Y):
#   wall   P4 (-20112, 2099) -> P1 (-8230, 2744): palisades every 4 m, spikes to -Y, watchtowers at both ends, chevals
#          in front of the gate; the gate gap (6 m) centred at X -15000; the breach pair (Realm_Wall_Breach_A/B) at X -10500
#   gate   SM_SiegeGate_Frame/LeafL/LeafR/Bar/Lever at the gap, hinge pivots; Lever/Bar/Leaves movable (BP_RealmGate, Codex)
#   dome   SM_RealmDome over the box (half-ellipsoid), MI_RealmBubble2, one purple point light inside, 2 fill spots
#   inside corrupt patches (the ground), realm flora (bloodcap / spore stalk / tentacle fern), blob mines, egg clusters,
#          TargetPoints Realm_Spawn_Zombie_NN (12) and Realm_Spawn_Giant_NN (2), Realm_Spawn_Wasp (mountain crack, north)
#   outside torch posts every 12 m along the road side of the wall
import math, random
import unreal

KIT = '/Game/CastleDefender/Environment/Boundaries/SiegeKit/'
GATE = '/Game/CastleDefender/Environment/Boundaries/SiegeGate/'
FLORA = '/Game/CastleDefender/Environment/Flora/'
CAMP = '/Game/CastleDefender/Environment/Camp/'
REALM = '/Game/CastleDefender/Realm/'
FOLDER = 'Gameplay/Realm'; TAG = 'laptop2_realm'
P1, P2, P3, P4 = (-8230.0, 2744.0), (-8230.0, 7136.0), (-19208.0, 8427.0), (-20112.0, 2099.0)
GATE_X, BREACH_X = -15000.0, -10500.0
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
random.seed(169)

old = [a for a in eas.get_all_level_actors() if TAG in [str(t) for t in a.tags]]
for a in old: eas.destroy_actor(a)
unreal.log('#169: removed %d old realm actors' % len(old))

def ground_z(x, y):
    r = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -30000),
                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    hit = next((h for h in r if isinstance(h, unreal.HitResult)), None) if isinstance(r, tuple) else r
    if hit is None: return None
    t = hit.to_tuple()
    return t[4].z if t[0] else None

placed = []
def finish(a, label):
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]; placed.append(a); return a
def place(mesh_path, label, x, y, yaw, scale=1.0, sink=15.0, z=None, pitch=0.0, roll=0.0, movable=False, material=None):
    m = unreal.load_asset(mesh_path)
    if m is None: unreal.log_warning('missing ' + mesh_path); return None
    gz = ground_z(x, y) if z is None else z
    if gz is None: return None
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, gz - sink), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw))
    if movable: a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    a.static_mesh_component.set_static_mesh(m); a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    if material is not None: a.static_mesh_component.set_material(0, material)
    return finish(a, label)
def point(label, x, y, z):
    a = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x, y, z), unreal.Rotator(0, 0, 0)); return finish(a, label)
def inside(x, y):
    """inside the owner's quad (convex), 6 m in from the wall edge."""
    poly = [P1, P2, P3, P4]; s = 0
    for i in range(4):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % 4]
        c = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if c == 0: return False
        if s == 0: s = 1 if c > 0 else -1
        elif (c > 0) != (s > 0): return False
    return True

# ---- 1. the wall P4 -> P1 (120 m): palisades every 4 m, outside = -Y side (the road) ----
dx, dy = P1[0] - P4[0], P1[1] - P4[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
wall_yaw = math.degrees(math.atan2(dy, dx))            # along the wall; the palisade mesh's face is -Y, so spikes out = yaw
out = (uy, -ux)                                        # the -Y side (right-hand normal of P4->P1 points to +Y: flip)
if out[1] > 0: out = (-out[0], -out[1])
n_pal = int(L / 400); gate_half = 320.0; breach = []
for k in range(n_pal + 1):
    s = k * 400.0 + 200.0
    if s > L: break
    x, y = P4[0] + ux * s, P4[1] + uy * s
    if abs(x - GATE_X) < gate_half: continue                      # the gate gap
    label = 'Realm_Wall_%03d' % k
    if abs(x - BREACH_X) < 400: label = 'Realm_Wall_Breach_%s' % ('A' if x < BREACH_X else 'B'); breach.append(label)
    place(KIT + 'SM_SiegeBarricade_Palisade', label, x + random.uniform(-15, 15), y + random.uniform(-15, 15), wall_yaw + random.uniform(-6, 6), random.uniform(0.95, 1.1), sink=25.0)
for k, s in enumerate((150.0, L - 150.0)):                        # watchtowers at both ends, 2 m inside
    x, y = P4[0] + ux * s - out[0] * 200, P4[1] + uy * s - out[1] * 200
    place(KIT + 'SM_SiegeBarricade_Watchtower', 'Realm_Tower_%d' % k, x, y, wall_yaw + random.uniform(-8, 8), 1.0, sink=20.0)
unreal.log('#169: breach palisades = %s (Codex swaps these for SM_SiegeBarricade_Breach at the breach wave)' % breach)

# ---- 2. the gate at X -15000 on the wall line (outside = -Y in the gate meshes -> yaw = wall_yaw) ----
sg = (GATE_X - P4[0]) / ux; gx, gy = P4[0] + ux * sg, P4[1] + uy * sg
gz = ground_z(gx, gy)
if unreal.load_asset(GATE + 'SM_SiegeGate_Frame') is not None and gz is not None:
    gyaw = wall_yaw
    place(GATE + 'SM_SiegeGate_Frame', 'Realm_Gate_Frame', gx, gy, gyaw, 1.0, sink=35.0, z=gz)
    pieces = {'LeafL': (-2.88, -0.035, 0.0), 'LeafR': (2.88, -0.035, 0.0), 'Bar': (0.0, 0.21, 1.75), 'Lever': (-4.03, 0.4, 1.18)}   # gate_meta.json pivots (m)
    r = math.radians(gyaw); cs, sn = math.cos(r), math.sin(r)
    for piece, (px, py, pz) in pieces.items():
        px, py, pz = px * 100, py * 100, pz * 100
        wx, wy = gx + px * cs - py * sn, gy + px * sn + py * cs
        place(GATE + 'SM_SiegeGate_' + piece, 'Realm_Gate_' + piece, wx, wy, gyaw, 1.0, sink=0.0, z=gz - 35.0 + pz, movable=True)
    for s in (-1, 1):   # chevals flanking the gate on the road side
        place(KIT + 'SM_SiegeBarricade_Cheval', 'Realm_Gate_Chev_%d' % (s > 0), gx + ux * s * 480 + out[0] * 260, gy + uy * s * 480 + out[1] * 260, gyaw + random.uniform(-10, 10), 1.0, sink=12.0)
    point('Realm_Gate_Trigger', gx + out[0] * 150, gy + out[1] * 150, (gz or 0) + 100)          # where the E prompt fires (BP_RealmGate)
else:
    unreal.log_warning('#169: SiegeGate meshes not imported (assets/laptop2/SiegeGate/import_kit_ue.py); the gap at X %.0f is left open' % GATE_X)

# ---- 3. the dome: SM_RealmDome scaled to the box (unit half-ellipsoid), MI_RealmBubble2, lights inside ----
cx, cy = (P1[0] + P3[0]) / 2, (P1[1] + P3[1]) / 2 + 150
rx, ry = (P1[0] - P4[0]) / 2 * 1.08, (P2[1] - P1[1]) / 2 * 1.25
base_z = min(v for v in (ground_z(cx, cy), ground_z(P4[0] + 600, P4[1] + 600), ground_z(P2[0] - 600, P2[1] - 600)) if v is not None) if ground_z(cx, cy) is not None else -1200.0
dome_h = 5200.0
mi = unreal.load_asset(REALM + 'MI_RealmBubble2')
dome = place(REALM + 'SM_RealmDome', 'Realm_Dome', cx, cy, 0.0, 1.0, sink=0.0, z=base_z - 150.0, movable=True, material=mi)
if dome:
    dome.set_actor_scale3d(unreal.Vector(rx, ry, dome_h)); dome.static_mesh_component.set_cast_shadow(False)
    dome.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
else:
    unreal.log_warning('#169: SM_RealmDome not imported (assets/laptop2/RealmKit/import_realm_ue.py)')
lt = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(cx, cy, base_z + 1800), unreal.Rotator(0, 0, 0)); finish(lt, 'Realm_Light_Core')
lc = lt.point_light_component; lc.set_intensity(60000.0); lc.set_light_color(unreal.LinearColor(0.55, 0.12, 0.9, 1)); lc.set_attenuation_radius(9000.0); lc.set_source_radius(600.0); lc.set_cast_shadows(False)
for k, (fx, fy) in enumerate(((cx - rx * 0.5, cy), (cx + rx * 0.5, cy))):
    s = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(fx, fy, base_z + 700), unreal.Rotator(0, 0, 0)); finish(s, 'Realm_Light_Fill_%d' % k)
    s.point_light_component.set_intensity(12000.0); s.point_light_component.set_light_color(unreal.LinearColor(0.7, 0.1, 0.35, 1)); s.point_light_component.set_attenuation_radius(4000.0); s.point_light_component.set_cast_shadows(False)

# ---- 4. inside: corrupt ground patches, realm flora, blob mines, egg clusters, spawn points ----
def rnd_inside(margin=700.0):
    for _ in range(200):
        x = random.uniform(P4[0] + margin, P1[0] - margin); y = random.uniform(P1[1] + margin, P3[1] - margin)
        if inside(x, y) and abs(x - GATE_X) + abs(y - gy) > 1200: return x, y
    return None
counts = {'CorruptPatch': 26, 'TentacleFern': 40, 'SporeStalk': 28, 'Bloodcap': 34, 'BlobMine': 22, 'EggCluster': 7}
for sp, n in counts.items():
    for k in range(n):
        p = rnd_inside(600 if sp != 'CorruptPatch' else 900)
        if not p: continue
        sc = random.uniform(0.85, 1.25) if sp != 'CorruptPatch' else random.uniform(0.9, 1.8)
        place(FLORA + sp + '/SM_Flora_' + sp, 'Realm_%s_%02d' % (sp, k), p[0], p[1], random.uniform(0, 360), sc, sink=2.0 if sp == 'CorruptPatch' else 1.0)
for k in range(12):
    p = rnd_inside(900)
    if p: point('Realm_Spawn_Zombie_%02d' % k, p[0], p[1], (ground_z(*p) or base_z) + 100)
for k, (fx, fy) in enumerate(((cx - 2200, cy + 900), (cx + 2600, cy + 1500))):
    point('Realm_Spawn_Giant_%02d' % k, fx, fy, (ground_z(fx, fy) or base_z) + 100)
point('Realm_Spawn_Wasp', cx + 1500, P3[1] + 2200, (ground_z(cx + 1500, P3[1] + 2200) or base_z) + 1500)   # the mountain crack, north of the realm
point('Realm_Breach_Point', BREACH_X, P4[1] + uy * (BREACH_X - P4[0]) / ux, (gz or base_z) + 100)

# ---- 5. torch posts outside along the road side, every 12 m (the night lighting of the wall) ----
for k in range(int(L / 1200) + 1):
    s = k * 1200.0 + 600.0
    if s > L: break
    x, y = P4[0] + ux * s + out[0] * 320, P4[1] + uy * s + out[1] * 320
    if abs(x - GATE_X) < 700: continue
    place(CAMP + 'TorchPost/SM_Camp_TorchPost', 'Realm_Torch_%02d' % k, x, y, wall_yaw + 180 + random.uniform(-10, 10), 1.0, sink=8.0)
unreal.log('#169 stage 1: placed %d actors in %s (tag %s). Next: Codex BP_RealmGate on Realm_Gate_* + Realm_Gate_Trigger; breach pair %s.' % (len(placed), FOLDER, TAG, breach))
