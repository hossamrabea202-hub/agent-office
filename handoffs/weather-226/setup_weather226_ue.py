# #226 Weather, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/weather-226/setup_weather226_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/weather-226/setup_weather226_ue.py"
# Makes under /Game/CastleDefender/Environment/Weather:
#   MPC_Weather      scalars Rain, Fog, Storm, Wind, Wet, Flash (0..1) - any material can read them (wetness layer later)
#   M_Rain           translucent unlit two-sided rain streaks, procedural (no textures), on two camera-centred cylinders;
#                    dims at night (MPC_DayNight.Night) and slants with the storm wind
#   M_WeatherGrade   post-process blendable (after tonemapping): overcast grade (cooler, flatter, darker) + lightning flash
#   BP_RainCurtain   actor: two cylinders (8 m and 3 m radius, 24 m tall) with M_Rain, no collision, no shadows
#   SFX_Rain_Loop, SFX_Thunder_A, SFX_Thunder_B   (assets/adjustedfilm/Weather226/sfx)
#   BPC_Weather      ActorComponent, added to the hero as "Weather"
# and adds M_WeatherGrade to every hero camera's post-process blendables (weight 1; all channels 0 = untouched image).
# Nothing else is changed: no level edit, BP_DayNight is only driven through its own FogDay variable at runtime.
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'weather-226')
DRY = '--dry-run' in sys.argv
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Weather226', 'sfx'))
DST = '/Game/CastleDefender/Environment/Weather'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
MPC_DN = '/Game/CastleDefender/Environment/DayNight/MPC_DayNight'
CYL = '/Engine/BasicShapes/Cylinder'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#226 weather setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path), False
    log.append('create ' + path)
    if DRY: return None, True
    return AT.create_asset(name, DST, cls, factory), True


def custom(m, code, inputs, otype, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', 'Weather226')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def coll(m, mpc, name, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, x, y)
    if mpc: e.set_editor_property('collection', mpc)
    e.set_editor_property('parameter_name', name); return e


def mask(m, src, rgba, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, x, y)
    for k, v in zip('rgba', rgba): e.set_editor_property(k, v)
    MEL.connect_material_expressions(src, '', e, ''); return e


def new_material(name):
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if m and not made: MEL.delete_all_material_expressions(m)
    return m


F4 = enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT4'); F3 = enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3')
EMIS, OPAC = unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_OPACITY

RAIN_HLSL = r'''
// streaks around the cylinder axis: u = angle, v = height; world-anchored so they do not swim with the camera
float3 d = WP - OP;
float ang = atan2(d.y, d.x) / 6.2831853 + 0.5;
float cols = 900.0 * Layer;
float u = ang * cols;
float id = floor(u);
float h = frac(sin(id * 12.9898 + Layer * 78.233) * 43758.5453);
float h2 = frac(h * 17.31 + 0.13);
float speed = 1100.0 + 500.0 * h2;                       // cm/s (raindrops ~9 m/s, shortened by the camera)
float z = d.z + T * speed + h * 5000.0 + (WP.x + WP.y) * Wind * 0.15;
float seg = 90.0 + 80.0 * h2;
float f = frac(z / seg);
float len = 0.18 + 0.12 * h;
float streak = smoothstep(0.0, 0.02, f) * (1.0 - smoothstep(len - 0.05, len, f));
float w = 1.0 - saturate(abs(frac(u) - 0.5 - (h - 0.5) * 0.4) * 9.0);
float on = step(1.0 - saturate(Rain * (0.35 + 0.65 * Storm + 0.5)), h2 * 0.999);
float a = streak * w * on * Rain;
a *= saturate(1.0 - abs(d.z) / 1200.0);                  // fade top and bottom of the cylinder
float lum = lerp(0.55, 0.12, Night) + Flash * 2.0;
return float4(lum * float3(0.80, 0.85, 0.92), saturate(a * 0.45));
'''

GRADE_HLSL = r'''
float2 uv = GetDefaultSceneTextureUV(Parameters, 14);
float3 c = SceneTextureLookup(uv, 14, false).rgb + Dummy.rgb * 0.0;
float o = saturate(Rain * 0.25 + Storm * 0.35 + Fog * 0.15);
if (o < 0.001 && Flash < 0.001) return c;
float lum = dot(c, float3(0.2126, 0.7152, 0.0722));
float3 g = lerp(c, lum.xxx * float3(0.94, 0.98, 1.06), 0.45 * o);   // overcast: flatter, cooler
g = lerp(g, g * g * (3.0 - 2.0 * g), -0.25 * o);                   // less contrast
g *= lerp(1.0, 0.82, o);                                           // darker sky light
g += Flash * float3(0.62, 0.70, 0.85) * (0.35 + 0.65 * (1.0 - lum)); // lightning lifts the shadows most
return g;
'''

# ---- MPC_Weather
mpc, _ = fresh('MPC_Weather', unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
if mpc:
    have = [str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')]
    ps = list(mpc.get_editor_property('scalar_parameters'))
    for n in ('Rain', 'Fog', 'Storm', 'Wind', 'Wet', 'Flash'):
        if n in have: continue
        p = unreal.CollectionScalarParameter(); p.set_editor_property('parameter_name', n); p.set_editor_property('default_value', 0.0); ps.append(p)
    mpc.set_editor_property('scalar_parameters', ps); EAL.save_asset(DST + '/MPC_Weather')
mpc_dn = unreal.load_asset(MPC_DN) if EAL.does_asset_exist(MPC_DN) else None
if not mpc_dn: log.append('NOTE: MPC_DayNight not found - rain will not dim at night')

# ---- M_Rain
m = new_material('M_Rain')
if m:
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_UNLIT'))
    m.set_editor_property('two_sided', True)
    try: m.set_editor_property('translucency_lighting_mode', enum(unreal.TranslucencyLightingMode, 'TLM_SURFACE'))
    except Exception: pass
    cu = custom(m, RAIN_HLSL, ['WP', 'OP', 'T', 'Rain', 'Storm', 'Wind', 'Night', 'Flash', 'Layer'], F4, -300, 0)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -800, -300), '', cu, 'WP')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionObjectPositionWS, -800, -200), '', cu, 'OP')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -800, -100), '', cu, 'T')
    y = 0
    for n in ('Rain', 'Storm', 'Wind', 'Flash'):
        MEL.connect_material_expressions(coll(m, mpc, n, -800, y), '', cu, n); y += 100
    if mpc_dn: MEL.connect_material_expressions(coll(m, mpc_dn, 'Night', -800, y), '', cu, 'Night')
    lay = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -800, y + 100)
    lay.set_editor_property('parameter_name', 'Layer'); lay.set_editor_property('default_value', 1.0)
    MEL.connect_material_expressions(lay, '', cu, 'Layer')
    MEL.connect_material_property(mask(m, cu, (True, True, True, False), 0, 0), '', EMIS)
    MEL.connect_material_property(mask(m, cu, (False, False, False, True), 0, 200), '', OPAC)
    MEL.recompile_material(m); EAL.save_asset(DST + '/M_Rain')
    # inner layer instance: bigger, sparser drops close to the camera
    mi, _ = fresh('MI_Rain_Near', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if mi:
        mi.set_editor_property('parent', m)
        MEL.set_material_instance_scalar_parameter_value(mi, 'Layer', 0.35)
        EAL.save_asset(DST + '/MI_Rain_Near')

# ---- M_WeatherGrade
m = new_material('M_WeatherGrade')
if m:
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_POST_PROCESS'))
    m.set_editor_property('blendable_location', enum(unreal.BlendableLocation, 'BL_AFTER_TONEMAPPING', 'BL_SCENE_COLOR_AFTER_TONEMAPPING'))
    st_ = MEL.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -800, -200)
    st_.set_editor_property('scene_texture_id', enum(unreal.SceneTextureId, 'PPI_POST_PROCESS_INPUT0'))
    cu = custom(m, GRADE_HLSL, ['Dummy', 'Rain', 'Storm', 'Fog', 'Flash'], F3, -300, 0)
    MEL.connect_material_expressions(st_, 'Color', cu, 'Dummy')
    y = 0
    for n in ('Rain', 'Storm', 'Fog', 'Flash'):
        MEL.connect_material_expressions(coll(m, mpc, n, -800, y), '', cu, n); y += 100
    MEL.connect_material_property(cu, '', EMIS)
    MEL.recompile_material(m); EAL.save_asset(DST + '/M_WeatherGrade')

# ---- sounds
tasks = []
for n in ('SFX_Rain_Loop', 'SFX_Thunder_A', 'SFX_Thunder_B'):
    f = os.path.join(SFX, n + '.wav')
    if not os.path.exists(f): log.append('MISSING ' + f); continue
    t = unreal.AssetImportTask()
    for k, v in (('filename', f), ('destination_path', DST), ('destination_name', n), ('replace_existing', True), ('automated', True), ('save', True)):
        t.set_editor_property(k, v)
    tasks.append(t); log.append('import ' + n)
if tasks and not DRY:
    AT.import_asset_tasks(tasks)
    loop = unreal.load_asset(DST + '/SFX_Rain_Loop')
    if loop: loop.set_editor_property('looping', True); EAL.save_asset(DST + '/SFX_Rain_Loop')


# ---- Blueprints
def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add_comp(bp, cls, name):
    have = names(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(bp)[0], new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s failed: %s' % (bp.get_name(), name, reason))
    SDS.rename_subobject(h, unreal.Text(name)); log.append('  + %s.%s' % (bp.get_name(), name))
    return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


rc = make_bp('BP_RainCurtain', unreal.Actor)
if rc:
    cyl = unreal.load_asset(CYL)
    for name, mat, scale in (('RainFar', DST + '/M_Rain', (16.0, 16.0, 24.0)), ('RainNear', DST + '/MI_Rain_Near', (6.0, 6.0, 24.0))):
        c = add_comp(rc, unreal.StaticMeshComponent, name)
        c.set_editor_property('static_mesh', cyl)
        c.set_editor_property('relative_scale3d', unreal.Vector(*scale))
        # the engine cylinder is centred on its pivot: the actor sits on the camera, so the rain surrounds it
        c.set_editor_property('override_materials', [unreal.load_asset(mat)])
        c.set_editor_property('cast_shadow', False)
        c.set_collision_profile_name('NoCollision')
        c.set_editor_property('component_tags', [unreal.Name('RainLayer')])
    BEL.compile_blueprint(rc); EAL.save_asset(DST + '/BP_RainCurtain')
comp = make_bp('BPC_Weather', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_Weather')

hero = unreal.load_asset(HERO)
hn = names(hero)
if 'Weather' in hn: log.append('hero already has Weather')
else:
    log.append('hero: + Weather (BPC_Weather)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add Weather: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('Weather'))
grade = unreal.load_asset(DST + '/M_WeatherGrade') if EAL.does_asset_exist(DST + '/M_WeatherGrade') else None
cams = [LIB.get_object(SDS.k2_find_subobject_data_from_handle(h)) for h in SDS.k2_gather_subobject_data_for_blueprint(hero)]
cams = [c for c in cams if isinstance(c, unreal.CameraComponent)]
log.append('hero cameras: %s' % [c.get_name() for c in cams])
for c in cams:
    pps = c.get_editor_property('post_process_settings'); wb = pps.get_editor_property('weighted_blendables')
    arr_ = list(wb.get_editor_property('array'))
    if grade and any(x.get_editor_property('object') == grade for x in arr_): log.append('  %s already has M_WeatherGrade' % c.get_name()); continue
    log.append('  %s + M_WeatherGrade blendable' % c.get_name())
    if DRY or not grade: continue
    w = unreal.WeightedBlendable(); w.set_editor_property('weight', 1.0); w.set_editor_property('object', grade)
    wb.set_editor_property('array', arr_ + [w]); pps.set_editor_property('weighted_blendables', wb); c.set_editor_property('post_process_settings', pps)
if not DRY:
    BEL.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines on BPC_Weather, then the graph paste).'
if not DRY: open(os.path.join(HERE, 'setup_weather226.txt'), 'w').write(out)
unreal.log(out)
