# Realm mountain crack (#169 stage 3; TGA, 2026-10-30): import + place in UE 5.3. Original work, all in this repo.
#   py "<repo>/assets/tga/RealmCrack/place_realmcrack_ue.py"
# 1. Imports SM_RealmCrack + textures into /Game/CastleDefender/Realm/MountainCrack and builds M_RealmCrack:
#    BaseColor / ORM / Normal + an emissive glow = EmissiveMask * GlowColor * GlowStrength * slow pulse (PulseSpeed).
# 2. Places, in Outliner folder Gameplay/Realm (idempotent: it deletes its own Realm_* actors first):
#    Realm_MountainCrack   on the mountain north of the realm, found by line traces, facing the realm, sunk into the slope
#    Realm_CrackLight      an orange point light in the mouth (Lumen needs a real light behind an emissive)
#    Realm_SwarmSpawn      a TargetPoint 6 m out of the crack, 5 m up: where the stage-3 swarm logic spawns the wasps
# If the traces miss (no landscape collision there), set CRACK_AT below by hand and re-run. Save the level afterwards.
import os, math
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Realm/MountainCrack'
REALM_MIN, REALM_MAX = unreal.Vector(-20112, 2099, -1200), unreal.Vector(-8230, 8427, -220)   # owner-marked box (#169)
CRACK_AT = None          # e.g. unreal.Vector(-14000, 10800, 900) to skip the search
SINK_CM = 300            # pushed this far into the slope so the curled edges bury
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

# ---- import ---------------------------------------------------------------------------------------------------------
TEX = [('T_RealmCrack_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('T_RealmCrack_ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
       ('T_RealmCrack_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP), ('T_RealmCrack_E', False, unreal.TextureCompressionSettings.TC_GRAYSCALE)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)
    EAL.save_loaded_asset(t)
f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = False; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
f.import_materials = False; f.import_textures = False
f.static_mesh_import_data.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
f.static_mesh_import_data.set_editor_property('combine_meshes', True)
tools.import_asset_tasks([task(os.path.join(SRC, 'SM_RealmCrack.fbx'), f)])

MAT = DST + '/M_RealmCrack'
if not EAL.does_asset_exist(MAT):
    m = tools.create_asset('M_RealmCrack', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1000, -300, DST + '/T_RealmCrack_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1000, 0, DST + '/T_RealmCrack_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1000, 300, DST + '/T_RealmCrack_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    em = p(unreal.MaterialExpressionTextureSampleParameter2D, 'EmissiveMask', -1000, 600, DST + '/T_RealmCrack_E', unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE)
    gc = p(unreal.MaterialExpressionVectorParameter, 'GlowColor', -1000, 850); gc.set_editor_property('default_value', unreal.LinearColor(1.0, 0.32, 0.05, 1))
    gs = p(unreal.MaterialExpressionScalarParameter, 'GlowStrength', -1000, 950); gs.set_editor_property('default_value', 14.0)
    ps = p(unreal.MaterialExpressionScalarParameter, 'PulseSpeed', -1000, 1050); ps.set_editor_property('default_value', 0.35)
    # pulse = 0.8 + 0.2 * sin(Time * PulseSpeed): the fissure breathes slowly, as if something moves inside
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -800, 1100)
    tps = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -650, 1080); MEL.connect_material_expressions(tm, '', tps, 'A'); MEL.connect_material_expressions(ps, '', tps, 'B')
    sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -500, 1080); MEL.connect_material_expressions(tps, '', sn, '')
    sc = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -380, 1080); MEL.connect_material_expressions(sn, '', sc, 'A'); sc.set_editor_property('const_b', 0.2)
    pl = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -260, 1080); MEL.connect_material_expressions(sc, '', pl, 'A'); pl.set_editor_property('const_b', 0.8)
    a = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -650, 700); MEL.connect_material_expressions(em, 'R', a, 'A'); MEL.connect_material_expressions(gc, '', a, 'B')
    b = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 750); MEL.connect_material_expressions(a, '', b, 'A'); MEL.connect_material_expressions(gs, '', b, 'B')
    c = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 800); MEL.connect_material_expressions(b, '', c, 'A'); MEL.connect_material_expressions(pl, '', c, 'B')
    MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(MAT)
mesh = unreal.load_asset(DST + '/SM_RealmCrack')
mesh.set_material(0, unreal.load_asset(MAT)); EAL.save_loaded_asset(mesh)

# ---- placement --------------------------------------------------------------------------------------------------------
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ('Realm_MountainCrack', 'Realm_CrackLight', 'Realm_SwarmSpawn'): eas.destroy_actor(a)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 60000), unreal.Vector(x, y, -60000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if not hit: return None
    t = hit.to_tuple(); return t[4] if t[0] else None      # (blocking, initial overlap, time, distance, location, ...)
centre = unreal.Vector((REALM_MIN.x + REALM_MAX.x) / 2, (REALM_MIN.y + REALM_MAX.y) / 2, -700)
pos = CRACK_AT
if pos is None:
    # the mountain north of the realm: the highest ground in a band beyond the box's north edge
    best = None
    for yi in range(0, 9):
        for xi in range(0, 9):
            x = REALM_MIN.x + (REALM_MAX.x - REALM_MIN.x) * (0.15 + 0.7 * xi / 8); y = REALM_MAX.y + 500 + yi * 700
            g = ground(x, y)
            if g and (best is None or g.z > best.z): best = g
    if best is not None:
        # walk from the summit back toward the realm and stop on the slope ~45 % of the way up from the realm floor
        target = centre.z + 0.45 * (best.z - centre.z); pos = best
        for k in range(1, 41):
            s = k / 40.0; x = best.x + (centre.x - best.x) * s; y = best.y + (centre.y - best.y) * s; g = ground(x, y)
            if g is None: continue
            pos = g
            if g.z <= target: break
if pos is None:
    pos = unreal.Vector(centre.x, REALM_MAX.y + 2500, 600); unreal.log_warning('Realm crack: traces found no ground, placed at a guess. Set CRACK_AT and re-run.')
d = unreal.Vector(centre.x - pos.x, centre.y - pos.y, 0); L = max(math.hypot(d.x, d.y), 1.0); d = unreal.Vector(d.x / L, d.y / L, 0)
yaw = math.degrees(math.atan2(d.y, d.x)) - 90.0                     # the mesh's front is local +Y
loc = unreal.Vector(pos.x - d.x * SINK_CM, pos.y - d.y * SINK_CM, pos.z - 60)
crack = eas.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, 0, yaw))
crack.set_actor_label('Realm_MountainCrack'); crack.set_folder_path('Gameplay/Realm')
mouth = unreal.Vector(loc.x + d.x * 150, loc.y + d.y * 150, loc.z + 380)
light = eas.spawn_actor_from_class(unreal.PointLight, mouth, unreal.Rotator(0, 0, 0))
light.set_actor_label('Realm_CrackLight'); light.set_folder_path('Gameplay/Realm')
lc = light.get_editor_property('point_light_component')
lc.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); lc.set_editor_property('intensity', 60000.0)
lc.set_editor_property('light_color', unreal.Color(255, 110, 30, 255)); lc.set_editor_property('attenuation_radius', 3500.0)
lc.set_editor_property('source_radius', 120.0); lc.set_editor_property('cast_shadows', True)
sp = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(loc.x + d.x * 600, loc.y + d.y * 600, loc.z + 500), unreal.Rotator(0, 0, yaw + 90))
sp.set_actor_label('Realm_SwarmSpawn'); sp.set_folder_path('Gameplay/Realm')
# tell the wave manager where the swarm comes out (SwarmSpawnLocation, from the realm-wasp BP hand-off), if it has it
swarm_at = sp.get_actor_location(); told = 0
for a in eas.get_all_level_actors():
    if a.get_class().get_name() == 'BP_ZombieWaveManager_C':
        for prop in ('SwarmSpawnLocation', 'swarm_spawn_location'):
            try: a.set_editor_property(prop, swarm_at); told += 1; break
            except Exception: pass
unreal.log('Realm crack placed at %s yaw %.0f (facing the realm). Light + Realm_SwarmSpawn added; SwarmSpawnLocation set on %d wave manager(s). Save the level.' % (loc, yaw, told))
