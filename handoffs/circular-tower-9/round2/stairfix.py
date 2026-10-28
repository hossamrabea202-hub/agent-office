"""Gatehouse stairs (front wall, x = 65) started inside the tower doorway. Compress each run along Y so its top end
(at the gatehouse) stays put and its bottom end starts 50 cm in front of the enlarged drum (r 606).
stairfix.cfg: DRY or GO."""
import unreal, os, math
D = r'C:\Unreal Backups\Castle Defender\Tools\Tower9_R2'
GO = open(os.path.join(D, 'stairfix.cfg')).read().strip() == 'GO'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
STAIRISH = ('SM_StairTread', 'StairRamp', 'Cube_', 'SM_StoneModule', 'Blend_Contact')
# run: (y window, new bottom-edge y). A climbs +Y away from the tower, B climbs -Y away from it.
RUNS = {'A': ((450.0, 1200.0), 700.0, +1), 'B': ((2300.0, 3050.0), 2800.0, -1)}
out = []
for key, ((ylo, yhi), newb, sgn) in RUNS.items():
    grp = []
    for a in eas.get_all_level_actors():
        lab = a.get_actor_label()
        if not lab.startswith(STAIRISH) or lab.startswith('Tower9'): continue
        o, e = a.get_actor_bounds(False)
        if abs(o.x - 65) < 25 and ylo < o.y < yhi and o.z > 300:
            grp.append(a)
    bounds = [a.get_actor_bounds(False) for a in grp]
    if sgn > 0:
        bot = min(o.y - e.y for o, e in bounds); top = max(o.y + e.y for o, e in bounds)
    else:
        bot = max(o.y + e.y for o, e in bounds); top = min(o.y - e.y for o, e in bounds)
    k = (newb - top) / (bot - top)
    remap = lambda y: top + (y - top) * k
    out.append('%s: %d actors, bottom %.0f -> %.0f, top %.0f kept, k %.3f' % (key, len(grp), bot, newb, top, k))
    for a in grp:
        lab = a.get_actor_label(); loc = a.get_actor_location(); rot = a.get_actor_rotation(); sc = a.get_actor_scale3d()
        if lab.startswith('StairRamp'):
            f = a.get_actor_forward_vector(); half = sc.x * 50.0
            p0 = loc - f * half; p1 = loc + f * half
            q0 = unreal.Vector(p0.x, remap(p0.y), p0.z); q1 = unreal.Vector(p1.x, remap(p1.y), p1.z)
            c = (q0 + q1) * 0.5; d = q1 - q0
            L = d.length(); pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))); yaw = math.degrees(math.atan2(d.y, d.x))
            out.append('  RAMP %s len %.0f->%.0f pitch %.1f->%.1f' % (lab, half * 2, L, rot.pitch, pitch))
            if GO:
                a.modify(); a.set_actor_location(c, False, False); a.set_actor_rotation(unreal.Rotator(rot.roll, pitch, yaw), False)
                a.set_actor_scale3d(unreal.Vector(L / 100.0, sc.y, sc.z))
            continue
        # which local axis lies along world Y?
        yaw = ((rot.yaw % 180.0) + 180.0) % 180.0
        along_x = abs(yaw - 90.0) < 1.0
        if abs(rot.pitch) > 1.0 and not lab.startswith('Blend_Contact'):
            out.append('  SKIP pitched %s rot %s' % (lab, rot)); continue
        if GO:
            a.modify()
            a.set_actor_location(unreal.Vector(loc.x, remap(loc.y), loc.z), False, False)
            if lab.startswith('Blend_Contact') and abs(rot.pitch) > 1.0:
                pass                                          # vertical contact cards: move only
            elif along_x:
                a.set_actor_scale3d(unreal.Vector(sc.x * k, sc.y, sc.z))
            else:
                a.set_actor_scale3d(unreal.Vector(sc.x, sc.y * k, sc.z))
if GO:
    out.append('save %s' % unreal.EditorLoadingAndSavingUtils.save_current_level())
open(os.path.join(D, 'stairfix.txt'), 'w').write('\n'.join(out))
