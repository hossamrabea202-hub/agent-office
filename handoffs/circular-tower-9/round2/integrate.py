"""Replace the two FRONT corner towers (50,50) and (50,3450) with tower #9 round 2 (checkking 2026-10-28, owner approved:
'continue until the castle is AAA and the two front towers are replaced correctly'). Map backup: backup_map_pre_towers/.
integrate.cfg: DRY or GO. DRY only writes the plan to integrate.txt."""
import unreal, os, math
D = r'C:\Unreal Backups\Castle Defender\Tools\Tower9_R2'
GO = open(os.path.join(D, 'integrate.cfg')).read().strip() == 'GO'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
R = 505.0
CORNERS = {'A': ((50.0, 50.0), 0.0, 80.0), 'B': ((50.0, 3450.0), -90.0, 3420.0)}   # centre, yaw, side-wall stair line y
STAIRISH = ('SM_StairTread', 'StairRamp', 'Cube_', 'SM_StoneModule', 'Blend_Contact')
out = []
acts = [a for a in eas.get_all_level_actors() if not a.get_actor_label().startswith(('TOWER9', 'Tower9_'))]


def inside_all(o, e, C, r):
    return all(math.hypot(x - C[0], y - C[1]) < r for x in (o.x - e.x, o.x + e.x) for y in (o.y - e.y, o.y + e.y))


dele, trims, moves = {}, [], []
for key, (C, yaw, sy) in CORNERS.items():
    for a in acts:
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        lab = a.get_actor_label(); o, e = a.get_actor_bounds(False); loc = a.get_actor_location()
        dc = math.hypot(loc.x - C[0], loc.y - C[1])
        why = None
        if lab.startswith('Castle_CornerTower') and dc < 30: why = 'old tower'
        elif lab.startswith(('SM_WalkSlab', 'Cube_')) and dc < 30 and loc.z > 1000: why = 'old roof slab'
        elif lab.startswith(STAIRISH) and abs(o.y - sy) < 25 and 290 < o.x < 1110 and o.z > 300: why = 'side-wall roof stair'
        elif lab.startswith(STAIRISH) and abs(o.x - 65) < 25 and dc < R + 10 and o.z > 300: why = 'front stair step inside drum'
        elif 'Buttress' in lab and inside_all(o, e, C, R): why = 'buttress inside drum'
        elif o.z - e.z > 300 and o.z + e.z < 1260 and inside_all(o, e, C, R): why = 'inside drum'
        elif lab.startswith(('SM_WalkSlab', 'Cube_')) and 650 < o.z < 700 and e.z < 20 and math.hypot(o.x - C[0], o.y - C[1]) < R + max(e.x, e.y):
            trims.append((a, C))
        if why:
            dele[a.get_path_name()] = (a, key, why)

for a, k, why in dele.values():
    o = a.get_actor_location(); out.append('DEL %s %s | %s (%.0f,%.0f,%.0f)' % (k, why, a.get_actor_label(), o.x, o.y, o.z))

# wall-walk slabs (top 680) and their paving caps (top 682) that run into the drum would z-fight / poke through the tower's
# 680 floor: drop them 3 cm (the tower floor covers them inside; the 3 cm step at the drum face is invisible)
for a, C in trims:
    if a.get_path_name() in dele: continue
    loc = a.get_actor_location()
    out.append('LOWER %s (%.0f,%.0f,%.1f) -3 cm' % (a.get_actor_label(), loc.x, loc.y, loc.z))
    if GO:
        a.modify(); a.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z - 3.0), False, False)

# props / pickups that the tower B drum would swallow + the two roof cannons
MOVE = {'Prop_barrel_24': (210, -350), 'Prop_barrel_25': (210, -350), 'Dust_Prop_barrel_24': (210, -350), 'Dust_Prop_barrel_25': (210, -350),
        'Blend_PropBlob_Prop_barrel_24_11': (210, -350), 'Blend_PropBlob_Prop_barrel_25_15': (210, -350), 'SkillBookPickup': (150, -130)}
SETLOC = {'Cannon_old_field_cannon3': ((95, 190, 1075), None), 'Cannon_old_field_cannon4': ((200, 3450, 1075), 90.0)}
for a in acts:
    lab = a.get_actor_label(); loc = a.get_actor_location()
    if lab in MOVE:
        d = MOVE[lab]; out.append('MOVE %s (%.0f,%.0f) +%s' % (lab, loc.x, loc.y, d))
        if GO: a.modify(); a.set_actor_location(unreal.Vector(loc.x + d[0], loc.y + d[1], loc.z), False, False)
    if lab in SETLOC:
        p, y = SETLOC[lab]; out.append('SET %s (%.0f,%.0f,%.0f) -> %s yaw %s' % (lab, loc.x, loc.y, loc.z, p, y))
        if GO:
            a.modify(); a.set_actor_location(unreal.Vector(*p), False, False)
            if y is not None:
                r = a.get_actor_rotation(); a.set_actor_rotation(unreal.Rotator(r.roll, r.pitch, y), False)

if GO:
    for a, k, why in dele.values():
        eas.destroy_actor(a)
    for key, (C, yaw, sy) in CORNERS.items():
        for part in ('Drum', 'Floors', 'Stairs', 'Iron', 'Parapet', 'Portals'):
            sm = unreal.load_asset('/Game/Review/Tower9_R2/SM_Tower09_' + part)
            t = eas.spawn_actor_from_object(sm, unreal.Vector(C[0], C[1], 0), unreal.Rotator(0, 0, yaw))
            t.set_actor_label('Tower9_%s_%s' % (key, part)); t.set_folder_path('Castle/Tower9_%s' % key)
    out.append('placed 12 parts')
out.append('deleted %d, lowered %d' % (len(dele), len([l for l in out if l.startswith('LOWER')])))
open(os.path.join(D, 'integrate.txt'), 'w').write('\n'.join(out))
