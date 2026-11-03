# #451 wall-to-tower junction fix (i5, 2026-11-03). Real masonry: a curtain wall is BONDED into the tower (quoins / toothing,
# RESEARCH_seams.md), so no wall end face ever shows beside a tower. In our castle the curtain, string-course and coping
# pieces stop short of the round corner towers: a dark notch + a flat, rounded-off end cap (shots/sc_sc_front.png).
# Fix (AAA modular practice: overlap, don't butt): extend each such piece along its long axis until its end sits INSIDE
# the tower drum (25 cm behind the drum surface), the far end stays where it is. World-aligned castle materials keep the
# stone pattern continuous. Round towers = meshes named *Drum* (cylinder: centre, radius from bounds). Never touches decals,
# gameplay actors or anything rotated off level. Does NOT save.
#   py junction_fix_ue.py --dry-run | --apply | --revert       (backup junction_fix_backup.json)
import json, math, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'junction_fix_backup.json'
INSET, MAXEXT, NEAR = 25.0, 140.0, 90.0     # end goes 25 cm inside the drum; extend at most 140 cm; only ends within 90 cm
WALL = ('curtain', 'stringcourse', 'string_course', 'coping', 'parapet', 'battlement', 'merlon', 'wallwalk', 'walkslab', '_sc_', 'cornice')
SKIP = ('decal', 'soot', 'grime', 'stain', 'card', 'moss', 'algae', 'gate', 'door', 'stair', 'cannon', 'breach', 'tower9')
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = EAS.get_all_level_actors()
by_path = {a.get_path_name(): a for a in acts}
if '--revert' in A:
    for path, t in json.load(open(BK)).items():
        a = by_path.get(path)
        if not a: print('missing', path); continue
        a.modify(); a.set_actor_scale3d(unreal.Vector(*t['scale'])); a.set_actor_location(unreal.Vector(*t['loc']), False, False)
        print('reverted', a.get_actor_label())
    raise SystemExit


def obb(c):
    m = c.get_editor_property('static_mesh'); bb = m.get_bounding_box()
    t = c.get_world_transform(); s = t.scale3d; r = t.rotation.rotator()
    cl = unreal.Vector((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, (bb.min.z + bb.max.z) / 2)
    hl = [(bb.max.x - bb.min.x) / 2, (bb.max.y - bb.min.y) / 2, (bb.max.z - bb.min.z) / 2]
    ax = [unreal.MathLibrary.get_forward_vector(r), unreal.MathLibrary.get_right_vector(r), unreal.MathLibrary.get_up_vector(r)]
    return dict(cen=unreal.MathLibrary.transform_location(t, cl), cl=cl, hl=hl, ext=[abs(hl[i] * [s.x, s.y, s.z][i]) for i in range(3)],
                ax=ax, s=s, r=r, t=t)


drums = []
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor': continue
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    if not m or 'drum' not in m.get_name().lower() or not c.is_visible(): continue
    o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
    drums.append(dict(label=a.get_actor_label(), comp=c, x=o.x, y=o.y, R=min(e.x, e.y), z0=o.z - e.z, z1=o.z + e.z))
log = ['drums: ' + ', '.join('%s R=%.0f at (%.0f,%.0f) z %.0f..%.0f' % (d['label'], d['R'], d['x'], d['y'], d['z0'], d['z1']) for d in drums)]
backup = json.load(open(BK)) if os.path.exists(BK) and '--apply' in A else {}
n = 0
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor': continue
    lab = a.get_actor_label(); ll = lab.lower()
    if any(k in ll for k in SKIP) or not any(k in ll for k in WALL): continue
    c = a.static_mesh_component
    if not c.get_editor_property('static_mesh') or not c.is_visible(): continue
    b = obb(c)
    if abs(b['r'].roll) > 0.5 or abs(b['r'].pitch) > 0.5: continue
    k = 0 if b['ext'][0] >= b['ext'][1] else 1                               # long horizontal axis
    u = b['ax'][k]; L = b['ext'][k]
    zlo, zhi = b['cen'].z - b['ext'][2], b['cen'].z + b['ext'][2]
    for sgn in (1, -1):
        E = b['cen'] + u * (sgn * L)
        for d in drums:
            if zhi < d['z0'] or zlo > d['z1']: continue
            dist = math.hypot(E.x - d['x'], E.y - d['y'])
            if dist > d['R'] + NEAR: continue
            # measure the real drum surface along the wall's own direction (complex trace against the drum only)
            v = u * sgn; zc = max(zlo, d['z0']) + min(zhi - zlo, d['z1'] - d['z0']) * 0.5
            Ez = unreal.Vector(E.x, E.y, zc)
            hit = d['comp'].line_trace_component(Ez - v * 150, Ez + v * (MAXEXT + 60), True, False, False)
            if not hit or not hit[3].to_tuple()[0]: continue                 # (location, normal, bone, HitResult)
            hl = hit[0]; th = (hl.x - Ez.x) * v.x + (hl.y - Ez.y) * v.y + (hl.z - Ez.z) * v.z
            if th < 0.5: continue                                            # end already in (or touching) the drum
            tt = th + INSET
            if tt > MAXEXT: continue
            dist = d['R'] + th                                               # for the log: cm from end to surface
            new_len = 2 * L + tt; f = new_len / (2 * L)
            s = b['s']; ns = [s.x, s.y, s.z]; ns[k] *= f
            new_cen = b['cen'] + u * (sgn * tt / 2)
            off = unreal.MathLibrary.transform_direction(unreal.Transform(unreal.Vector(0, 0, 0), b['r'], unreal.Vector(*ns)), b['cl'])
            new_loc = new_cen - off
            log.append('%s %-44s end %+d %s: %5.1f cm short of the drum -> extend %5.1f cm into %s' % ('EXTEND' if '--apply' in A else 'WOULD', lab[:44], sgn, 'XY'[k],
                       dist - d['R'], tt, d['label']))
            if '--apply' in A:
                old = a.get_actor_location(); osc = a.get_actor_scale3d()
                backup.setdefault(a.get_path_name(), {'label': lab, 'loc': [old.x, old.y, old.z], 'scale': [osc.x, osc.y, osc.z]})
                a.modify(); a.set_actor_scale3d(unreal.Vector(*ns)); a.set_actor_location(new_loc, False, False)
                b = obb(c); L = b['ext'][k]                                     # refresh for the other end
            n += 1
if '--apply' in A: json.dump(backup, open(BK, 'w'), indent=0)
out = '\n'.join(log) + '\n%s: %d wall ends %s' % ('APPLIED' if '--apply' in A else 'DRY RUN', n, 'extended (backup %s)' % BK if '--apply' in A else 'would be extended')
open(H + 'junction_fix_log.txt', 'w', encoding='utf-8').write(out)
print(out)
