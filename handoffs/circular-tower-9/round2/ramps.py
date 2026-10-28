"""Hidden nav/movement ramps over the tower stair flights (castle convention: StairRamp_* = hidden Cube, Custom collision).
Local tower frame (yaw 0, base centre): flight A y -280 rises +X from (-190, 680) to (176, 870); flight B y -145 rises -X
from (190, 870) to (-176, 1070). Width 110, 8 cm thick, ramp top on the tread nosings."""
import unreal, os, math
D = r'C:\Unreal Backups\Castle Defender\Tools\Tower9_R2'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = eas.get_all_level_actors()
tpl = next(a for a in acts if a.get_actor_label() == 'StairRamp_09')
for a in acts:
    if a.get_actor_label().startswith('Tower9_StairRamp'): eas.destroy_actor(a)
FLIGHTS = (('A', -280.0, (-190.0, 680.0), (176.0, 870.0)), ('B', -145.0, (190.0, 870.0), (-176.0, 1070.0)))
out = []
for key, (cx, cy, tyaw) in (('A', (50.0, 50.0, 0.0)), ('B', (50.0, 3450.0, -90.0))):
    c, s = math.cos(math.radians(tyaw)), math.sin(math.radians(tyaw))
    for fl, ly, (x0, z0), (x1, z1) in FLIGHTS:
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(dx, dz); pitch = math.degrees(math.atan2(dz, abs(dx)))
        fyaw = (0.0 if dx > 0 else 180.0) + tyaw
        mx, mz = (x0 + x1) / 2.0, (z0 + z1) / 2.0 - 4.0 / math.cos(math.radians(pitch))
        wx, wy = cx + mx * c - ly * s, cy + mx * s + ly * c
        n = eas.duplicate_actor(tpl)
        n.set_actor_label('Tower9_StairRamp_%s_%s' % (key, fl)); n.set_folder_path('Castle/Tower9_%s' % key)
        n.set_actor_rotation(unreal.Rotator(0.0, pitch, fyaw), False)
        n.set_actor_scale3d(unreal.Vector(L / 100.0, 1.10, 0.08))
        n.set_actor_location(unreal.Vector(wx, wy, mz), False, False)
        out.append('%s %s at (%.0f,%.0f,%.0f) yaw %.0f pitch %.1f len %.0f' % (key, fl, wx, wy, mz, fyaw, pitch, L))
open(os.path.join(D, 'ramps.txt'), 'w').write('\n'.join(out))
