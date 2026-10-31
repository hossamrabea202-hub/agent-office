# #8 Treasure chest, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/chest-8/setup_chest8_ue.py" --dry-run        only reports (lists the chest meshes it would use)
#   py "<repo>/handoffs/chest-8/setup_chest8_ue.py"                  makes the assets + BP_TreasureChest components
#        options: --body <StaticMesh path> --lid <StaticMesh path>   pick the meshes by hand (else: searched in /Game/AncientTreasures,
#                 then the whole project; "chest" in the name, the lid has lid/top/cover in its name)
#   py ".../setup_chest8_ue.py" --place [--dry-run]                 puts one chest (label TreasureChest_8) in the middle of the
#        East Front tunnel (EF_Tun_Floor_*), on the floor, facing the castle end; logged. --unplace removes it again.
# Makes in /Game/CastleDefender/Gameplay/Chest: SFX_ChestOpen, SFX_GoldCash (from assets/adjustedfilm/Chest8/sfx),
#   M_ChestRays (additive light shafts with drifting gold sparkles; Grow 0..1 reveals them upward, Fade 0..1),
#   M_ChestGlint (additive 4-point star glint, slow twinkle), BP_TreasureChest:
#   Body (chest mesh, BlockAll) / Hinge (tag ChestHinge, at the lid's back-bottom edge) -> Lid / Glow (point light 2700 K,
#   candela, tag ChestGlow, in front of the lid seam) / Glint (material billboard, tag ChestGlint) / Rays (cylinder, tag ChestRays)
import os, sys, math, unreal

A = sys.argv[1:]
DRY, PLACE, UNPLACE = '--dry-run' in A, '--place' in A, '--unplace' in A
arg = lambda k: A[A.index(k) + 1] if k in A and A.index(k) + 1 < len(A) else None
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\chest-8'
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Chest8', 'sfx'))
DST = '/Game/CastleDefender/Gameplay/Chest'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#8 treasure chest setup' + (' (DRY RUN, nothing written)' if DRY else '')]
LABEL = 'TreasureChest_8'


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


# ------------------------------------------------------------------------------------------------ placement
def place():
    floors = sorted([a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith('EF_Tun_Floor_')], key=lambda a: a.get_actor_label())
    if not floors: raise SystemExit('no EF_Tun_Floor_* actors in this level')
    mid, first = floors[len(floors) // 2], floors[0]
    o, e = mid.get_actor_bounds(False)
    loc = unreal.Vector(o.x, o.y, o.z + e.z)
    to = first.get_actor_location() - loc
    yaw = math.degrees(math.atan2(to.y, to.x))
    log.append('place %s on %s at (%.0f, %.0f, %.0f), facing the castle end (yaw %.0f)' % (LABEL, mid.get_actor_label(), loc.x, loc.y, loc.z, yaw))
    if DRY: return
    old = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == LABEL]
    if old: log.append('already placed: moving it'); act = old[0]; act.set_actor_location(loc, False, True); act.set_actor_rotation(unreal.Rotator(0, 0, yaw), True)
    else:
        cls = unreal.load_class(None, DST + '/BP_TreasureChest.BP_TreasureChest_C')
        if not cls: raise SystemExit('BP_TreasureChest missing: run the setup without --place first')
        act = EAS.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, yaw)); act.set_actor_label(LABEL)
    unreal.EditorLevelLibrary.save_current_level()


def unplace():
    old = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == LABEL]
    log.append('unplace: %d actor(s)' % len(old))
    if not DRY:
        for a in old: EAS.destroy_actor(a)
        unreal.EditorLevelLibrary.save_current_level()


# ------------------------------------------------------------------------------------------------ meshes
def find_meshes():
    if arg('--body'): return unreal.load_asset(arg('--body')), (unreal.load_asset(arg('--lid')) if arg('--lid') else None)
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh')], package_paths=['/Game'], recursive_paths=True)
    cands = [ad for ad in AR.get_assets(flt) if 'chest' in str(ad.asset_name).lower()
             and not any(w in str(ad.package_path).lower() for w in ('knight', 'obsidian', 'sovereign', 'equipment', 'armor', 'armour', 'hero'))]
    cands.sort(key=lambda ad: (not str(ad.package_path).startswith('/Game/AncientTreasures'), str(ad.package_name)))
    for ad in cands[:20]: log.append('  chest mesh candidate: %s' % ad.package_name)
    lids = [ad for ad in cands if any(w in str(ad.asset_name).lower() for w in ('lid', 'top', 'cover', 'cap'))]
    bodies = [ad for ad in cands if ad not in lids]
    if not bodies: return None, None
    body = bodies[0]
    # the lid that shares the most of the body's name
    stem = str(body.asset_name).lower().replace('base', '').replace('body', '').replace('bottom', '')
    lid = max(lids, key=lambda ad: len(os.path.commonprefix([str(ad.asset_name).lower(), stem]))) if lids else None
    log.append('  picked body %s, lid %s' % (body.package_name, lid.package_name if lid else '(none: the lid will not open)'))
    return unreal.load_asset(str(body.package_name)), (unreal.load_asset(str(lid.package_name)) if lid else None)


# ------------------------------------------------------------------------------------------------ materials
RAYS = r'''
float hz = saturate(LP.z / 100.0 + 0.5);                       // engine cylinder: 100 units tall, pivot in the middle
float ang = atan2(LP.y, LP.x);
float s = 0.5 + 0.5 * sin(ang * 13.0 + sin(ang * 5.0 + T * 0.7) * 2.0);
s = pow(s, 5.0) * 0.8 + 0.2;
float v = pow(1.0 - hz, 1.6) * smoothstep(0.0, 0.08, hz);
float m = 1.0 - smoothstep(Grow - 0.15, Grow, hz);              // reveal upward
float e = pow(saturate(abs(dot(normalize(CV), normalize(NW)))), 1.5);   // soft cylinder edges
float2 g = float2(ang * 7.0, hz * 22.0 - T * 1.6);              // drifting sparkles
float2 c = floor(g); float2 f = frac(g) - 0.5;
float h = frac(sin(dot(c, float2(12.9898, 78.233))) * 43758.5453);
float sp = step(0.86, h) * smoothstep(0.18, 0.0, length(f)) * (0.5 + 0.5 * sin(T * 9.0 + h * 40.0));
return float3(1.0, 0.62, 0.22) * Intensity * (s * v * e + sp * 1.5 * v) * m * Fade;
'''
GLINT = r'''
float2 d = UV - 0.5;
float r = length(d);
float core = exp(-r * r * 140.0);
float rays = exp(-abs(d.x) * 60.0) * exp(-abs(d.y) * 6.0) + exp(-abs(d.y) * 60.0) * exp(-abs(d.x) * 6.0);
float tw = 0.65 + 0.35 * sin(T * 3.1) * sin(T * 1.7 + 1.3);
return float3(1.0, 0.72, 0.32) * Intensity * (core + rays * 0.6) * tw;
'''


def custom(m, code, ins, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3'))
    cis = []
    for n, _ in ins:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); cis.append(ci)
    e.set_editor_property('inputs', cis)
    for n, src in ins: MEL.connect_material_expressions(src, '', e, n)
    return e


def scalar(m, n, v, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', v); return e


def material(name, kind):
    path = DST + '/' + name
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); log.append('rebuild ' + path)
        if DRY: return None
        MEL.delete_all_material_expressions(m)
    else:
        log.append('create ' + path)
        if DRY: return None
        m = AT.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_UNLIT'))
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_ADDITIVE'))
    m.set_editor_property('two_sided', True)
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 300)
    if kind == 'rays':
        ins = [('LP', MEL.create_material_expression(m, unreal.MaterialExpressionLocalPosition, -900, 0)), ('T', t),
               ('CV', MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, 400)),
               ('NW', MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 500)),
               ('Grow', scalar(m, 'Grow', 0.0, -900, 600)), ('Fade', scalar(m, 'Fade', 0.0, -900, 700)), ('Intensity', scalar(m, 'Intensity', 12.0, -900, 800))]
        c = custom(m, RAYS, ins, -400, 200)
    else:
        m.set_editor_property('used_with_particle_sprites', True)
        ins = [('UV', MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)), ('T', t),
               ('Intensity', scalar(m, 'Intensity', 6.0, -900, 600))]
        c = custom(m, GLINT, ins, -400, 200)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(path)
    return m


# ------------------------------------------------------------------------------------------------ blueprint
def handles(bp):
    hs = SDS.k2_gather_subobject_data_for_blueprint(bp)
    return hs, {str(SDL.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in hs}


def comp(h): return SDL.get_object(SDS.k2_find_subobject_data_from_handle(h))


def build(body_mesh, lid_mesh, rays_m, glint_m):
    path = DST + '/BP_TreasureChest'
    if EAL.does_asset_exist(path): bp = unreal.load_asset(path); log.append('reusing ' + path)
    else:
        log.append('create ' + path)
        if DRY: return
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = AT.create_asset('BP_TreasureChest', DST, unreal.Blueprint, f)
    if DRY: return
    hs, by = handles(bp); root = hs[0]

    def add(name, cls, parent):
        if name in by: return comp(by[name])
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
        if not SDL.is_handle_valid(h): raise RuntimeError('%s: %s' % (name, fail))
        SDS.rename_subobject(h, unreal.Text(name)); by[name] = h; log.append('  + ' + name); return comp(h)

    b = add('Body', unreal.StaticMeshComponent, root)
    if body_mesh: b.set_editor_property('static_mesh', body_mesh)
    b.set_collision_profile_name('BlockAll')
    lo = body_mesh.get_bounding_box().min if body_mesh else unreal.Vector(-50, -35, 0)
    hi = body_mesh.get_bounding_box().max if body_mesh else unreal.Vector(50, 35, 60)
    if lid_mesh:
        llo, lhi = lid_mesh.get_bounding_box().min, lid_mesh.get_bounding_box().max
        hinge = unreal.Vector(llo.x, 0.0, llo.z)                 # back-bottom edge of the lid (front = +X)
        log.append('  lid bounds %s .. %s -> hinge at %s' % (llo, lhi, hinge))
    else:
        hinge = unreal.Vector(lo.x, 0.0, hi.z); log.append('  no lid mesh: the lid will not open')
    hg = add('Hinge', unreal.SceneComponent, root)
    hg.set_editor_property('relative_location', hinge); hg.set_editor_property('component_tags', [unreal.Name('ChestHinge')])
    if lid_mesh:
        ld = add('Lid', unreal.StaticMeshComponent, by['Hinge'])
        ld.set_editor_property('static_mesh', lid_mesh)
        ld.set_editor_property('relative_location', unreal.Vector(-hinge.x, -hinge.y, -hinge.z))
        ld.set_collision_profile_name('NoCollision')
    top = max(hi.z, lid_mesh.get_bounding_box().max.z if lid_mesh else hi.z)
    gl = add('Glow', unreal.PointLightComponent, root)
    gl.set_editor_property('relative_location', unreal.Vector(hi.x + 15, 0, (lo.z + top) * 0.55))
    gl.set_editor_property('component_tags', [unreal.Name('ChestGlow')])
    gl.set_editor_property('intensity_units', enum(unreal.LightUnits, 'CANDELAS')); gl.set_editor_property('intensity', 60.0)
    gl.set_editor_property('use_temperature', True); gl.set_editor_property('temperature', 2700.0)
    gl.set_editor_property('attenuation_radius', 600.0); gl.set_editor_property('source_radius', 8.0); gl.set_editor_property('cast_shadows', False)
    gt = add('Glint', unreal.MaterialBillboardComponent, root)
    gt.set_editor_property('relative_location', unreal.Vector(hi.x + 2, 0, hi.z))
    gt.set_editor_property('component_tags', [unreal.Name('ChestGlint')])
    if glint_m:
        el = unreal.MaterialSpriteElement(); el.set_editor_property('material', glint_m)
        el.set_editor_property('base_size_x', 40.0); el.set_editor_property('base_size_y', 40.0)
        gt.set_editor_property('elements', [el])
    ry = add('Rays', unreal.StaticMeshComponent, root)
    ry.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    w, d = max(hi.x - lo.x, 20.0), max(hi.y - lo.y, 20.0)
    ry.set_editor_property('relative_scale3d', unreal.Vector(w / 100 * 0.85, d / 100 * 0.85, 2.2))
    ry.set_editor_property('relative_location', unreal.Vector((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 110))
    ry.set_editor_property('component_tags', [unreal.Name('ChestRays')])
    ry.set_collision_profile_name('NoCollision'); ry.set_editor_property('cast_shadow', False)
    if rays_m: ry.set_editor_property('override_materials', [rays_m])
    BEL.compile_blueprint(bp); EAL.save_asset(path)


if PLACE: place()
elif UNPLACE: unplace()
else:
    tasks = []
    for n in ('SFX_ChestOpen', 'SFX_GoldCash'):
        f = os.path.join(SFX, n + '.wav')
        if not os.path.exists(f): log.append('MISSING ' + f); continue
        log.append('import ' + n)
        t = unreal.AssetImportTask()
        for k, v in (('filename', f), ('destination_path', DST), ('destination_name', n), ('replace_existing', True), ('automated', True), ('save', True)):
            t.set_editor_property(k, v)
        tasks.append(t)
    if tasks and not DRY: AT.import_asset_tasks(tasks)
    rays_m, glint_m = material('M_ChestRays', 'rays'), material('M_ChestGlint', 'glint')
    body_mesh, lid_mesh = find_meshes()
    if not body_mesh: log.append('NO chest mesh found: run again with --body <path> [--lid <path>]')
    build(body_mesh, lid_mesh, rays_m, glint_m)
out = '\n'.join(log) + ('\nNext: README step 2 (21 BPVar lines on BP_TreasureChest, Compile), step 3 (paste BP_TreasureChest_graph.txt).' if not (PLACE or UNPLACE) else '')
if not DRY: open(os.path.join(HERE, 'setup_chest8.txt'), 'a').write(out + '\n')
unreal.log(out)
