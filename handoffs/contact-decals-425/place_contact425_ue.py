# #425 contact decals, step 2 (i5, 2026-11-02): put a contact decal batch on the wall behind every wall-mounted prop.
#   py place_contact425_ue.py                      DRY RUN (default): finds the props and their wall hits, writes place_report.txt
#   py place_contact425_ue.py --preview <i> <dir>  spawns the decals for prop #i of the report TEMPORARILY, renders
#                                                  <dir>/cd425_<i>_before.png + _after.png, destroys them (nothing saved)
#   py place_contact425_ue.py --apply              spawns them for real (tag CD425, folder ContactDecals425). Owner's OK first!
#   py place_contact425_ue.py --remove             deletes every actor tagged CD425 (the undo)
# Props: SM_IronTorch / SM_Torch_01a (iron mount + soot plume, soot skipped when a TorchSoot card is within 90 cm),
#        SM_Sign_* (wood mount, no soot), Castle_BannerRod (wood mount). Wall = the closest blocking hit of 8 horizontal
#        traces (<= 70 cm) from the prop's bounds centre that is NOT the prop itself and faces it (normal . dir < -0.5).
import math, os, sys, unreal

D = '/Game/CastleDefender/Environment/ContactDecals425/'
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
SL = unreal.SystemLibrary
args = sys.argv[1:]
RULES = [('SM_IronTorch', 'Iron', True), ('SM_Torch_01a', 'Iron', True), ('SM_Sign_', 'Wood', False), ('BannerRod', 'Wood', False)]


def mesh_names(a):
    return [c.get_editor_property('static_mesh').get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_editor_property('static_mesh')]


def wall_hit(a):
    o, e = a.get_actor_bounds(False)
    best = None
    for k in range(8):
        ang = math.radians(k * 45.0); d = unreal.Vector(math.cos(ang), math.sin(ang), 0)
        h = SL.line_trace_single(W, o, o + d * 70.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
        t = h.to_tuple() if h else None
        if not t or not t[0] or t[1]: continue
        loc, nrm = t[4], t[6]
        if nrm.dot(d) > -0.5 or abs(nrm.z) > 0.35: continue      # must face the prop and be a wall, not a floor/ceiling
        dist = (loc - o).length()
        if best is None or dist < best[0]: best = (dist, loc, nrm)
    return o, e, best


def plan():
    acts = EAS.get_all_level_actors()
    soots = [x.get_actor_location() for x in acts if x.get_actor_label().startswith('TorchSoot')]
    rows = []
    for a in acts:
        if not isinstance(a, unreal.StaticMeshActor): continue
        names = ' '.join(mesh_names(a)) + ' ' + a.get_actor_label()
        rule = next((r for r in RULES if r[0] in names), None)
        if not rule: continue
        o, e, hit = wall_hit(a)
        # mounted = actually touching the wall: torches within 35 cm (free-standing trail torches 60+ cm off a wall are
        # not mounted), projecting signs / banner rods within 60 cm
        if hit and hit[0] > (35.0 if rule[1] == 'Iron' else 60.0): hit = None
        if not hit: rows.append((a, rule, o, e, None, False)); continue
        # old TorchSoot planes hang well above the flame: match on wall-plane distance, up to 3 m above the torch
        has_card = any(math.hypot(s.x - o.x, s.y - o.y) < 80.0 and -50.0 < s.z - o.z < 300.0 for s in soots)
        rows.append((a, rule, o, e, hit, rule[2] and not has_card))
    return rows


PLANE = '/Engine/BasicShapes/Plane'          # 100 x 100 cm, normal +Z


def card(at, nrm, w, h, mi, label):
    # Stain card instead of a DBuffer decal: about half the castle walls have Receives Decals OFF (owner's setting).
    rot = unreal.MathLibrary.make_rot_from_zx(nrm, unreal.Vector(0, 0, 1))     # card faces out of the wall, local X = up
    c = EAS.spawn_actor_from_class(unreal.StaticMeshActor, at + nrm * 0.4, rot)
    smc = c.static_mesh_component
    smc.set_static_mesh(unreal.load_asset(PLANE)); smc.set_material(0, unreal.load_asset(D + mi))
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); smc.set_cast_shadow(False)
    smc.set_editor_property('receives_decals', False)
    c.set_actor_scale3d(unreal.Vector(h / 100.0, w / 100.0, 1.0))
    c.tags = [unreal.Name('CD425')]; c.set_folder_path('ContactDecals425'); c.set_actor_label(label)
    return c


def spawn(row):
    a, rule, o, e, (dist, loc, nrm), soot = row
    # iron wall brackets are all about one size; actor bounds (Tower9 torches, trail torches) would blow the card up
    foot = 16.0 if rule[1] == 'Iron' else max(12.0, min(45.0, max(e.x, e.y, e.z) * 0.9))
    wall = loc + unreal.Vector(0, 0, 0)
    made = [card(wall + unreal.Vector(0, 0, -foot * 0.55), nrm, foot * 3.2, foot * 5.2, 'MI_MountCard425_' + rule[1],
                 'CD425_%s_Mount' % a.get_actor_label())]
    if soot:
        flame_z = o.z + e.z * 0.9                                   # top of the torch head
        made.append(card(unreal.Vector(wall.x, wall.y, flame_z + 0.32 * 170.0), nrm, 80.0, 170.0, 'MI_SootCard425_Torch',
                         'CD425_%s_Soot' % a.get_actor_label()))
    return made


def shot(path, o, nrm):
    # locked exposure (lookdev_cap.py: manual EV, no TAA / motion blur), camera on the wall normal, slightly off-axis
    sys.path.insert(0, HERE); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
    cam = o + nrm * 170.0 + unreal.Vector(0, 0, 10.0) + unreal.Vector(-nrm.y, nrm.x, 0) * 45.0
    lookdev_cap.shot(path, cam, o + unreal.Vector(0, 0, 15.0), 1.5, 50.0)


if '--remove' in args:
    gone = [x for x in EAS.get_all_level_actors() if 'CD425' in [str(t) for t in x.tags]]
    for x in gone: EAS.destroy_actor(x)
    print('removed', len(gone), 'CD425 decals')
else:
    rows = plan()
    rep = ['%3d %-34s %-5s %s %s' % (i, r[0].get_actor_label()[:34], r[1][1], ('wall %.0f cm' % r[4][0]) if r[4] else 'NO WALL (skipped)',
                                    '+soot' if r[5] else '') for i, r in enumerate(rows)]
    ok = [r for r in rows if r[4]]
    rep.append('%d props, %d with a wall, %d soot plumes, %d decals' % (len(rows), len(ok), sum(r[5] for r in ok), len(ok) + sum(r[5] for r in ok)))
    open(HERE + '/place_report.txt', 'w', encoding='utf-8').write('\n'.join(rep))
    print(rep[-1])
    if '--preview' in args:
        i = int(args[args.index('--preview') + 1]); out = args[args.index('--preview') + 2]
        r = rows[i]
        if not r[4]: raise SystemExit('prop %d has no wall' % i)
        shot('%s/cd425_%d_before.png' % (out, i), r[2], r[4][2])
        made = spawn(r)
        try: shot('%s/cd425_%d_after.png' % (out, i), r[2], r[4][2])
        finally:
            for x in made: EAS.destroy_actor(x)
        print('preview', i, r[0].get_actor_label(), 'decals', len(made), '(destroyed again)')
    elif '--apply' in args:
        n = sum(len(spawn(r)) for r in ok)
        print('APPLIED: %d decals (tag CD425). Save the level on the Master.' % n)
