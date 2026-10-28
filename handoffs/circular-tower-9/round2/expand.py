"""Owner 2026-10-28: scale the two front towers up (players pass freely, gatehouse stairs clear of the doorway).
Placed actors scaled (S, S, 1) - heights must stay (wall walk 680, roof 1070). Clears what the bigger drum (R*S) swallows.
expand.cfg: DRY or GO."""
import unreal, os, math
D = r'C:\Unreal Backups\Castle Defender\Tools\Tower9_R2'
GO = open(os.path.join(D, 'expand.cfg')).read().strip() == 'GO'
S = 1.2
R = 505.0 * S
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CORNERS = {'A': (50.0, 50.0), 'B': (50.0, 3450.0)}
acts = eas.get_all_level_actors()
out = []


def inside_all(o, e, C, r):
    return all(math.hypot(x - C[0], y - C[1]) < r for x in (o.x - e.x, o.x + e.x) for y in (o.y - e.y, o.y + e.y))


dele, lower, near = [], [], []
for a in acts:
    lab = a.get_actor_label()
    if lab.startswith('Tower9_'):
        continue
    o, e = a.get_actor_bounds(False); loc = a.get_actor_location()
    for key, C in CORNERS.items():
        dc = math.hypot(loc.x - C[0], loc.y - C[1])
        gate_stair = abs(o.x - 65) < 25 and lab.startswith(('SM_StairTread', 'StairRamp', 'Cube_', 'SM_StoneModule', 'Blend_Contact'))
        if isinstance(a, unreal.StaticMeshActor) and not gate_stair:
            if o.z - e.z > 300 and o.z + e.z < 1260 and inside_all(o, e, C, R):
                dele.append((a, key)); break
            if lab.startswith(('SM_WalkSlab', 'Cube_')) and 650 < o.z < 700 and e.z < 20 and math.hypot(o.x - C[0], o.y - C[1]) < R + max(e.x, e.y) \
                    and (loc.z > 663.5 if lab.startswith('SM_WalkSlab') else loc.z > 680.0):
                lower.append((a, key)); break
        if dc < R + 120 and o.z < 300 and e.x < 400 and not isinstance(a, unreal.StaticMeshActor) or (dc < R + 60 and o.z < 300 and e.x < 300 and isinstance(a, unreal.StaticMeshActor) and not lab.startswith(('SM_Bevel', 'Cube_', 'Blend_Contact'))):
            near.append((a, key, dc))
for a, k in dele:
    o = a.get_actor_location(); out.append('DEL %s %s (%.0f,%.0f,%.0f)' % (k, a.get_actor_label(), o.x, o.y, o.z))
for a, k in lower:
    o = a.get_actor_location(); out.append('LOWER %s %s (%.0f,%.0f,%.1f)' % (k, a.get_actor_label(), o.x, o.y, o.z))
for a, k, dc in near:
    o = a.get_actor_location(); out.append('NEAR %s %s %s (%.0f,%.0f,%.0f) dc %.0f' % (k, a.get_actor_label(), a.get_class().get_name(), o.x, o.y, o.z, dc))
if GO:
    for a, k in dele: eas.destroy_actor(a)
    for a, k in lower:
        l = a.get_actor_location(); a.modify(); a.set_actor_location(unreal.Vector(l.x, l.y, l.z - 3.0), False, False)
    for a in acts:
        if a.get_actor_label().startswith(('Tower9_A_', 'Tower9_B_')) and not a.get_actor_label().startswith(('Tower9_A_Torch', 'Tower9_B_Torch')):
            a.modify(); a.set_actor_scale3d(unreal.Vector(S, S, 1.0))
    out.append('scaled')
    MOVE = {'Prop_sand_10': (150, 50), 'Prop_sand_11': (150, 50), 'Blend_PropBlob_Prop_sand_10_13': (150, 50), 'Blend_PropBlob_Prop_sand_11_1': (150, 50),
            'Prop_chest_201': (41, -174), 'Blend_PropBlob_Prop_chest_201_3': (41, -174), 'Dust_Prop_chest_201': (41, -174), 'Treasure_Lid': (41, -174),
            'Treasure_GlowFloor': (41, -174), 'Treasure_Shaft': (41, -174), 'Wares_crossbow': (41, -174), 'Wares_sovereign': (41, -174)}
    for a in acts:
        d = MOVE.get(a.get_actor_label())
        if d:
            l = a.get_actor_location(); a.modify(); a.set_actor_location(unreal.Vector(l.x + d[0], l.y + d[1], l.z), False, False)
            out.append('MOVED %s +%s' % (a.get_actor_label(), d))
out.append('del %d lower %d near %d' % (len(dele), len(lower), len(near)))
open(os.path.join(D, 'expand.txt'), 'w').write('\n'.join(out))
