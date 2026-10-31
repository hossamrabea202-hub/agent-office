# #297 part 3: the mine dungeon under Mine_01 (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/cave-296-297/place_mine297_ue.py" --dry-run     only reports (where everything would go, clashes)
#   py "<repo>/handoffs/cave-296-297/place_mine297_ue.py"               places it
#   py ".../place_mine297_ue.py" --remove [--dry-run]                    removes everything it placed (tag Mine297)
# Needs: TGA's #309 kit imported (assets/tga/MineKit/import_mine_ue.py, DRY_RUN = False) and BP_CaveDoor (hand-off #310).
# Does, in ThirdPersonMap:
#   1. an ALWAYS-LOADED sub-level ThirdPersonMap_MineDungeon with TGA's layout (assets/tga/MineKit/README + lookdev_mine.py,
#      Blender metres -> UE cm, Y mirrored like the FBX): chamber, 2 straights, T, dead end, turn, 6 timber sets, 6 rails,
#      cart, 2 ore veins, spoil heap, door frame, 5 lanterns each with a warm 400 lm PointLight on its 'Light' socket
#      (KB rule 6), and a NavMeshBoundsVolume for the workers. It sits 50 m under Mine_01 (DEPTH), checked against every
#      actor in the map (nothing may overlap the dungeon box) and against the World Settings Kill Z.
#   2. BP_CaveDoor's Door mesh -> TGA's SM_Mine_Door (pivot bottom centre, faces +X), scale 1.
#   3. two BP_CaveDoor in the PERSISTENT level (a hard Target reference can't cross levels):
#        MineDoor_Up   in Mine_01's tunnel, 30 cm before its inner rock end (found by a trace), facing the mouth;
#        MineDoor_Down at the dungeon's dead end, facing into the tunnel; Targets paired, prompt "[E] Climb back up ...".
# Every placed actor gets the tag Mine297 and is logged in place_mine297.txt.
import os, sys, unreal

A = sys.argv[1:]
DRY, REMOVE = '--dry-run' in A, '--remove' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\cave-296-297'
KIT = '/Game/CastleDefender/Environment/Mine'
DOORBP = '/Game/CastleDefender/Gameplay/Cave/BP_CaveDoor'
SUB = '/Game/ThirdPerson/Maps/ThirdPersonMap_MineDungeon'
TAG, DEPTH = 'Mine297', 5000.0
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#297 part 3 mine dungeon' + (' (DRY RUN, nothing written)' if DRY else '')]

# TGA's layout (lookdev_mine.py), Blender metres: (mesh, x, y, z, yaw)
LAYOUT = [('SM_Mine_Chamber', 0, 0, 0, 0), ('SM_Mine_Tunnel_Straight', 14, 0, 0, 0), ('SM_Mine_Tunnel_T', 18, 0, 0, 0),
          ('SM_Mine_Tunnel_DeadEnd', 22, 0, 0, 0), ('SM_Mine_Tunnel_Straight', -4, 0, 0, 0), ('SM_Mine_Tunnel_Turn', -4, 0, 0, 180)]
LAYOUT += [('SM_Mine_TimberSet', x, 0, 0, 0) for x in (15, 17, 19.0, 21, -1.5, -3.5)]
LAYOUT += [('SM_Mine_Rail_4m', x, 0, 0, 0) for x in (-2, 2, 6, 10, 14, 18)]
LAYOUT += [('SM_Mine_Cart', 8.5, 0, 0, 0), ('SM_Mine_OreVein', 6.5, -4.75, 0, 90), ('SM_Mine_OreVein', 3.6, -4.7, 0.2, 80),
           ('SM_Mine_SpoilHeap', 10.5, 3.2, 0, 0), ('SM_Mine_DoorFrame', 24.4, 0, 0, 180)]
LANTERNS = [((3.5, -3.6, 2.6), 90), ((10.5, 3.9, 2.4), -90), ((15.0, -1.25, 1.9), 90), ((20.9, 1.25, 1.9), -90), ((7.0, 4.2, 2.5), -90)]
BOX_MIN, BOX_MAX = unreal.Vector(-1000, -900, -100), unreal.Vector(2700, 900, 700)    # dungeon bounds around its origin (cm)


def ue(x, y, z): return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)      # Blender -> UE (the FBX mirrors Y)


def tagged():
    return [a for a in EAS.get_all_level_actors() if TAG in [str(t) for t in a.tags]]


def mark(a, label):
    a.set_actor_label(label); a.tags = list(a.tags) + [unreal.Name(TAG)]
    log.append('  %-24s %s' % (label, a.get_actor_location())); return a


if REMOVE:
    found = tagged(); log.append('remove %d tagged actors' % len(found))
    if not DRY:
        for a in found: EAS.destroy_actor(a)
        LES.save_all_dirty_levels()
    log.append('(the sub-level %s stays in the level list; remove it in Window > Levels if wanted)' % SUB)
else:
    missing = [m for m in {r[0] for r in LAYOUT} | {'SM_Mine_Lantern', 'SM_Mine_Door'} if not EAL.does_asset_exist(KIT + '/' + m)]
    if missing: raise SystemExit('import TGA\'s MineKit first (missing %s)' % ', '.join(sorted(missing)))
    if not EAL.does_asset_exist(DOORBP): raise SystemExit('BP_CaveDoor missing: hand-off #310 first')
    mine = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Mine_01']
    if not mine: raise SystemExit('Mine_01 not found in the level')
    mine = mine[0]
    old = tagged()
    if old:
        log.append('re-run: removing %d actors from the last run' % len(old))
        if not DRY:
            for a in old: EAS.destroy_actor(a)

    # ---- where: 50 m under Mine_01, world-aligned; nothing else may sit in that box
    m = mine.get_actor_location()
    O = unreal.Vector(m.x - 1200.0, m.y, m.z - DEPTH)
    lo, hi = O + BOX_MIN, O + BOX_MAX
    log.append('dungeon origin %s (box %s .. %s)' % (O, lo, hi))
    clash = []
    for a in EAS.get_all_level_actors():
        if a.get_class().get_name() in ('Landscape', 'LandscapeProxy', 'LandscapeStreamingProxy', 'WorldSettings', 'Brush') or 'Volume' in a.get_class().get_name():
            continue
        c, e = a.get_actor_bounds(False)
        if e.x <= 0 and e.y <= 0 and e.z <= 0: continue
        if all(c.__getattribute__(k) + e.__getattribute__(k) > lo.__getattribute__(k) and c.__getattribute__(k) - e.__getattribute__(k) < hi.__getattribute__(k) for k in 'xyz'):
            if e.x > 50000 or e.y > 50000: continue          # sky spheres, giant fog / water planes
            clash.append(a.get_actor_label())
    if clash: raise SystemExit('something already sits in the dungeon box: %s (raise DEPTH in the script)' % clash[:10])
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    kz = ws.get_editor_property('kill_z')
    log.append('Kill Z %.0f' % kz)
    if kz > lo.z - 2000:
        log.append('Kill Z %.0f would kill the hero in the dungeon -> set to %.0f' % (kz, lo.z - 20000))
        if not DRY: ws.set_editor_property('kill_z', lo.z - 20000)

    # ---- BP_CaveDoor's door mesh -> SM_Mine_Door
    bp = unreal.load_asset(DOORBP)
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        d = SDS.k2_find_subobject_data_from_handle(h)
        if str(LIB.get_variable_name(d)) == 'Door':
            comp = LIB.get_object(d)
            log.append('BP_CaveDoor.Door: %s -> SM_Mine_Door' % comp.get_editor_property('static_mesh').get_name())
            if not DRY:
                comp.set_editor_property('static_mesh', unreal.load_asset(KIT + '/SM_Mine_Door'))
                comp.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
                comp.set_editor_property('relative_location', unreal.Vector(0, 0, 0))
                BEL.compile_blueprint(bp); EAL.save_asset(DOORBP)

    # ---- the sub-level (always loaded), then the art into it
    if not DRY:
        if not EAL.does_asset_exist(SUB):
            unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingAlwaysLoaded, SUB, False)
            log.append('made sub-level ' + SUB + ' (always loaded)')
        sub = [l for l in unreal.EditorLevelUtils.get_levels(world) if SUB.split('/')[-1] in l.get_path_name()]
        if not sub: raise SystemExit('sub-level not found after creating it')
        unreal.EditorLevelUtils.make_level_current(sub[0])
    log.append('art (sub-level):')
    for i, (mesh, x, y, z, yaw) in enumerate(LAYOUT):
        loc = O + ue(x, y, z)
        if DRY: log.append('  %-24s %s yaw %d' % (mesh, loc, -yaw)); continue
        a = EAS.spawn_actor_from_object(unreal.load_asset(KIT + '/' + mesh), loc, unreal.Rotator(0, 0, -yaw))
        mark(a, 'Mine297_%s_%02d' % (mesh[8:], i))
    for i, ((x, y, z), yaw) in enumerate(LANTERNS):
        loc = O + ue(x, y, z)
        if DRY: log.append('  Lantern + 400 lm PointLight %s' % loc); continue
        lan = mark(EAS.spawn_actor_from_object(unreal.load_asset(KIT + '/SM_Mine_Lantern'), loc, unreal.Rotator(0, 0, -yaw)), 'Mine297_Lantern_%d' % i)
        smc = lan.static_mesh_component
        has = smc.does_socket_exist('Light')
        p = smc.get_socket_location('Light') if has else loc + unreal.Vector(0, 0, 20)
        L = mark(EAS.spawn_actor_from_class(unreal.PointLight, p, unreal.Rotator(0, 0, 0)), 'Mine297_LanternLight_%d' % i)
        lc = L.point_light_component
        lc.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); lc.set_editor_property('intensity', 400.0)
        lc.set_editor_property('light_color', unreal.Color(r=255, g=158, b=77, a=255))   # (1.0, 0.62, 0.3), KB warm lamp
        lc.set_editor_property('attenuation_radius', 900.0); lc.set_editor_property('source_radius', 2.0)
        L.attach_to_actor(lan, 'Light' if has else '', unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    if not DRY:
        nav = mark(EAS.spawn_actor_from_class(unreal.NavMeshBoundsVolume, O + (BOX_MIN + BOX_MAX) * 0.5, unreal.Rotator(0, 0, 0)), 'Mine297_NavBounds')
        nav.set_actor_scale3d((BOX_MAX - BOX_MIN) * (1.0 / 200.0))         # default brush is 200 cm
        pers = [l for l in unreal.EditorLevelUtils.get_levels(world) if l.get_path_name().endswith('PersistentLevel')]
        unreal.EditorLevelUtils.make_level_current(pers[0])        # back to the persistent level (the doors go there)

    # ---- the two doors (persistent level)
    ent = [c for c in mine.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('Entrance')]
    ent = ent[0] if ent else mine.root_component
    xf = ent.get_world_transform()
    inside = xf.transform_location(unreal.Vector(0, 0, 120))
    best = None
    for sgn in (1, -1):                       # the closed side of the tunnel is the one that hits rock first
        end = xf.transform_location(unreal.Vector(sgn * 900.0, 0, 120))
        hit = unreal.SystemLibrary.line_trace_single(world, inside, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None                     # (blocking, initial overlap, time, distance, location, ...)
        d = (t[4] - inside).length() if t and t[0] and not t[1] else 9999.0
        log.append('  tunnel trace %+d: %s' % (sgn, 'rock at %.0f cm' % d if d < 9999 else 'open'))
        if best is None or d < best[1]: best = (sgn, d)
    sgn, d = best
    if d >= 9999 or d < 80: sgn, d = -1, 280.0; log.append('  no clean rock hit either way: MANUAL check, door at -250 cm (local -X)')
    p_up = xf.transform_location(unreal.Vector(sgn * (d - 30.0), 0, 120))
    fl = unreal.SystemLibrary.line_trace_single(world, p_up, p_up - unreal.Vector(0, 0, 400), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if fl and fl.to_tuple()[0]: p_up = fl.to_tuple()[4]
    else: p_up = p_up - unreal.Vector(0, 0, 120)
    yaw_up = ent.get_world_rotation().yaw + (180.0 if sgn > 0 else 0.0)        # face the mouth (+X of the door = towards it)
    p_dn = O + ue(24.4, 0, 0)
    log.append('doors: MineDoor_Up %s yaw %.0f | MineDoor_Down %s yaw 180' % (p_up, yaw_up, p_dn))
    if not DRY:
        cls = unreal.load_class(None, DOORBP + '.BP_CaveDoor_C')
        up = mark(EAS.spawn_actor_from_class(cls, p_up, unreal.Rotator(0, 0, yaw_up)), 'MineDoor_Up')
        dn = mark(EAS.spawn_actor_from_class(cls, p_dn, unreal.Rotator(0, 0, 180)), 'MineDoor_Down')
        up.set_editor_property('Target', dn); dn.set_editor_property('Target', up)
        dn.set_editor_property('Prompt', '[E] Climb back up to the cave')
        LES.save_all_dirty_levels()

out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'place_mine297.txt'), 'w').write(out)
unreal.log(out); print(out)
