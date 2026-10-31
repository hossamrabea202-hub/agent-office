# #268 AAA pickup reveal, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/reveal-aaa-268/setup_reveal268_ue.py" --dry-run     (only reports what it would do)
#   py "<repo>/handoffs/reveal-aaa-268/setup_reveal268_ue.py"               (does it)
# Makes, under /Game/CastleDefender/UI/Reveal (next to the v1 textures, which stay untouched):
#   RT_Reveal          1024x1024 RGBA16F render target (the live 3D item)
#   MPC_Reveal         one scalar "Blur" (0..1) the reveal writes every frame
#   M_RevealItem       UI material: the captured item (HDR -> ACES fit, alpha from the capture)
#   M_RevealScreen     UI material: vignette scrim, warm glow, contact shadow, gold dust, light burst, ring, dock pulse
#   M_RevealBlur       post-process material (after tonemapping): 28-tap blur + desaturate + darken, driven by MPC_Reveal.Blur
#   SFX_Reveal_Whoosh / SFX_Reveal_Hit / SFX_Reveal_Shimmer   (assets/adjustedfilm/Reveal268/sfx/*.wav)
# and /Game/CastleDefender/UI/Reveal/BP_RevealStage: an actor with the real book and satchel meshes (copied from
#   BP_SkillBookPickup / BP_BagPickup), a SceneCapture2D, and a warm key / cool rim / weak fill on lighting channel 1 only.
# It also adds M_RevealBlur to the post-process blendables of every camera on the hero (weight 1; Blur = 0 is a no-op).
# Nothing else is changed: no level edits, no decal or live material edits, the pickups themselves are only read.
# Writes setup_reveal268.txt next to itself.
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'reveal-aaa-268')
DRY = '--dry-run' in sys.argv
SFX_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'Reveal268', 'sfx'))
DEST = '/Game/CastleDefender/UI/Reveal'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
PICKUPS = {'RevealBook': '/Game/CastleDefender/Gameplay/SkillBook/BP_SkillBookPickup',
           'RevealBag': '/Game/CastleDefender/Gameplay/BagPickup/BP_BagPickup'}
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#268 reveal setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    """first enum member that exists (names differ a little between engine versions)."""
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    """create the asset, or return the existing one (re-run)."""
    path = '%s/%s' % (DEST, name)
    if EAL.does_asset_exist(path):
        log.append('reusing ' + path); return unreal.load_asset(path), False
    log.append('create ' + path)
    if DRY: return None, True
    return AT.create_asset(name, DEST, cls, factory), True


# ------------------------------------------------------------------------------------------------ HLSL
SCREEN_HLSL = r'''
float2 uv = UV;
float asp = Aspect;
float2 c = Center.xy;
float2 d = (uv - c) * float2(asp, 1.0);
float r = length(d);
float3 gold = float3(1.0, 0.70, 0.32);
float3 add = 0;
float scrim = 0;
float3 dust = 0;
int l0 = Layer < 0.5 ? 0 : 2;
int l1 = Layer < 0.5 ? 2 : 3;
for (int l = l0; l < l1; l++)
{
    float fl = (float)l;
    float sc = (l == 2) ? 4.5 : (12.0 + fl * 9.0);
    float2 p = float2(uv.x * asp, uv.y) * sc;
    p.y += T * (0.016 + 0.010 * fl) * sc;
    p.x += sin(T * 0.35 + fl * 1.7 + p.y * 0.15) * 0.35;
    float2 id = floor(p);
    float2 f = frac(p) - 0.5;
    float h = frac(sin(dot(id + fl * 19.13, float2(127.1, 311.7))) * 43758.5453);
    float h2 = frac(h * 13.37 + 0.71);
    float h3 = frac(h2 * 7.77 + 0.13);
    float2 o = (float2(h2, h3) - 0.5) * 0.6;
    float dd = length(f - o);
    float sz = (l == 2) ? (0.10 + 0.10 * h3) : (0.035 + 0.05 * h3);
    float tw = 0.55 + 0.45 * sin(T * (1.5 + 3.0 * h2) + h * 50.0);
    float m = saturate(1.0 - dd / sz);
    m = (l == 2) ? m * m : m * m * m;
    dust += m * step(0.62, h) * tw * lerp(gold, float3(1.0, 0.92, 0.75), h3) * ((l == 2) ? 0.30 : 0.9);
}
add += dust * Dust * (exp(-r * r * 2.2) * 0.85 + 0.15);
if (Layer < 0.5)
{
    float2 vv = (uv - 0.5) * float2(asp, 1.0);
    float vig = lerp(0.62, 1.0, smoothstep(0.25, 1.0, length(vv)));
    scrim = Bg * 0.55 * vig;
    float g = exp(-(r * r) / max(Rad * Rad * 1.4, 1e-4));
    add += gold * g * Glow * 0.55;
    float2 sd = (uv - (c + float2(0.0, Rad * 0.92))) * float2(asp, 1.0);
    sd /= float2(max(Rad * 0.95, 1e-4), max(Rad * 0.11, 1e-4));
    float sh = exp(-dot(sd, sd)) * 0.6 * ItemA;
    scrim = 1.0 - (1.0 - scrim) * (1.0 - sh);
}
else
{
    float an = atan2(d.y, d.x);
    float rays = pow(saturate(0.5 + 0.5 * sin(an * 13.0 + T * 0.5)), 6.0) * 0.6
               + pow(saturate(0.5 + 0.5 * sin(an * 21.0 - T * 0.8 + 1.3)), 10.0) * 0.4;
    float fall = exp(-r / max(Rad * 1.6, 1e-3));
    float core = exp(-r * r / max(Rad * Rad * 0.12, 1e-5));
    float streak = exp(-abs(d.y) / max(Rad * 0.018, 1e-4)) * exp(-abs(d.x) / max(Rad * 2.2, 1e-3));
    add += (gold * rays * fall * 0.55 + float3(1.0, 0.9, 0.75) * core * 0.8 + float3(1.0, 0.8, 0.55) * streak * 0.55) * Burst;
    float rr = Rad * (0.6 + 2.2 * Ring);
    float ring = exp(-pow((r - rr) / max(Rad * 0.035, 1e-4), 2.0)) * saturate(1.0 - Ring) * step(0.001, Ring);
    add += gold * ring * 0.7;
    float2 dk = (uv - Dock.xy) * float2(asp, 1.0);
    float dr = length(dk);
    float dring = exp(-pow((dr - DockR) / 0.004, 2.0));
    float dglow = exp(-dr * dr / 0.0009);
    add += gold * (dring * 0.9 + dglow * 0.6) * Dock.z;
}
float la = max(max(add.r, add.g), add.b);
float a = saturate(max(scrim, la));
float3 col = (a > 1e-4) ? add / a : float3(0, 0, 0);
return float4(saturate(col), a);
'''

ITEM_HLSL = r'''
float3 c = max(Tex.rgb, 0.0) * Exposure;
c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14);
c = saturate(c);
c = lerp(c, float3(1.0, 0.86, 0.62), saturate(Flash) * 0.35);
float a = saturate(1.0 - Tex.a) * Alpha;
return float4(c, a);
'''

BLUR_HLSL = r'''
float2 uv = GetDefaultSceneTextureUV(Parameters, 14);
float a = saturate(Amt);
float3 base = SceneTextureLookup(uv, 14, false).rgb + Dummy.rgb * 0.0;
if (a < 0.002) return base;
float s = Rad * a / (1080.0 * max(Inv.y, 1e-6));
float2 px = Inv.xy * s;
float3 acc = 0;
for (int i = 0; i < 28; i++)
{
    float k = (i + 0.5) / 28.0;
    float an = i * 2.39996323;
    acc += SceneTextureLookup(uv + float2(cos(an), sin(an)) * sqrt(k) * px, 14, true).rgb;
}
float3 col = acc / 28.0;
float lum = dot(col, float3(0.2126, 0.7152, 0.0722));
col = lerp(col, lum * float3(1.03, 0.98, 0.90), 0.5 * a);
col *= lerp(1.0, 0.6, a);
return lerp(base, col, smoothstep(0.0, 0.35, a));
'''


# ------------------------------------------------------------------------------------------------ material helpers
def custom(m, code, inputs, otype, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code)
    e.set_editor_property('output_type', otype)
    e.set_editor_property('description', 'Reveal268')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins)
    return e


def scalar(m, name, default, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', default); return e


def vector(m, name, rgba, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', unreal.LinearColor(*rgba)); return e


def mask(m, src, out, rgba, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, x, y)
    for k, v in zip('rgba', rgba): e.set_editor_property(k, v)
    MEL.connect_material_expressions(src, out, e, ''); return e


def new_material(name):
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if m is None: return None
    if not made:
        MEL.delete_all_material_expressions(m)          # rebuilt from scratch on a re-run (our own asset)
    return m


F4 = enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT4')
F3 = enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3')
UI = enum(unreal.MaterialDomain, 'MD_UI')
PP = enum(unreal.MaterialDomain, 'MD_POST_PROCESS')
TRANS = enum(unreal.BlendMode, 'BLEND_TRANSLUCENT')
EMIS, OPAC = unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_OPACITY

# ---- RT_Reveal
rt, _ = fresh('RT_Reveal', unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
if rt:
    rt.set_editor_property('size_x', 1024); rt.set_editor_property('size_y', 1024)
    rt.set_editor_property('render_target_format', enum(unreal.TextureRenderTargetFormat, 'RTF_RGBA16F'))
    rt.set_editor_property('clear_color', unreal.LinearColor(0, 0, 0, 1))
    rt.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); rt.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    EAL.save_asset(DEST + '/RT_Reveal')

# ---- MPC_Reveal (Blur)
mpc, _ = fresh('MPC_Reveal', unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
if mpc:
    names = [str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')]
    if 'Blur' not in names:
        p = unreal.CollectionScalarParameter()
        p.set_editor_property('parameter_name', 'Blur'); p.set_editor_property('default_value', 0.0)
        mpc.set_editor_property('scalar_parameters', list(mpc.get_editor_property('scalar_parameters')) + [p])
    EAL.save_asset(DEST + '/MPC_Reveal')

# ---- M_RevealItem
m = new_material('M_RevealItem')
if m:
    m.set_editor_property('material_domain', UI); m.set_editor_property('blend_mode', TRANS)
    tx = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    tx.set_editor_property('parameter_name', 'RT')
    tx.set_editor_property('sampler_type', enum(unreal.MaterialSamplerType, 'SAMPLERTYPE_LINEAR_COLOR'))
    if rt: tx.set_editor_property('texture', rt)
    cu = custom(m, ITEM_HLSL, ['Tex', 'Exposure', 'Alpha', 'Flash'], F4, -300, 0)
    MEL.connect_material_expressions(tx, 'RGBA', cu, 'Tex')
    MEL.connect_material_expressions(scalar(m, 'Exposure', 1.0, -700, 300), '', cu, 'Exposure')
    MEL.connect_material_expressions(scalar(m, 'Alpha', 0.0, -700, 400), '', cu, 'Alpha')
    MEL.connect_material_expressions(scalar(m, 'Flash', 0.0, -700, 500), '', cu, 'Flash')
    MEL.connect_material_property(mask(m, cu, '', (True, True, True, False), 0, 0), '', EMIS)
    MEL.connect_material_property(mask(m, cu, '', (False, False, False, True), 0, 200), '', OPAC)
    MEL.recompile_material(m); EAL.save_asset(DEST + '/M_RevealItem')

# ---- M_RevealScreen
m = new_material('M_RevealScreen')
if m:
    m.set_editor_property('material_domain', UI); m.set_editor_property('blend_mode', TRANS)
    ins = ['UV', 'T', 'Aspect', 'Center', 'Rad', 'Bg', 'Glow', 'Burst', 'Ring', 'Dust', 'Layer', 'Dock', 'DockR', 'ItemA']
    cu = custom(m, SCREEN_HLSL, ins, F4, -300, 0)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -800, -200), '', cu, 'UV')
    y = -100
    for n, dv in (('T', 0.0), ('Aspect', 1.7778), ('Rad', 0.25), ('Bg', 0.0), ('Glow', 0.0), ('Burst', 0.0), ('Ring', 0.0),
                  ('Dust', 0.0), ('Layer', 0.0), ('DockR', 0.02), ('ItemA', 0.0)):
        MEL.connect_material_expressions(scalar(m, n, dv, -800, y), '', cu, n); y += 100
    MEL.connect_material_expressions(vector(m, 'Center', (0.5, 0.47, 0, 0), -800, y), '', cu, 'Center')
    MEL.connect_material_expressions(vector(m, 'Dock', (0.93, 0.88, 0, 0), -800, y + 150), '', cu, 'Dock')
    MEL.connect_material_property(mask(m, cu, '', (True, True, True, False), 0, 0), '', EMIS)
    MEL.connect_material_property(mask(m, cu, '', (False, False, False, True), 0, 200), '', OPAC)
    MEL.recompile_material(m); EAL.save_asset(DEST + '/M_RevealScreen')

# ---- M_RevealBlur (post process, after tonemapping)
m = new_material('M_RevealBlur')
if m:
    m.set_editor_property('material_domain', PP)
    m.set_editor_property('blendable_location', enum(unreal.BlendableLocation, 'BL_AFTER_TONEMAPPING', 'BL_SCENE_COLOR_AFTER_TONEMAPPING'))
    st_ = MEL.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -800, 0)
    st_.set_editor_property('scene_texture_id', enum(unreal.SceneTextureId, 'PPI_POST_PROCESS_INPUT0'))
    cp = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -800, 300)
    if mpc: cp.set_editor_property('collection', mpc)
    cp.set_editor_property('parameter_name', 'Blur')
    cu = custom(m, BLUR_HLSL, ['Dummy', 'Inv', 'Amt', 'Rad'], F3, -300, 0)
    MEL.connect_material_expressions(st_, 'Color', cu, 'Dummy')
    MEL.connect_material_expressions(st_, 'InvSize', cu, 'Inv')
    MEL.connect_material_expressions(cp, '', cu, 'Amt')
    MEL.connect_material_expressions(scalar(m, 'Rad', 22.0, -800, 450), '', cu, 'Rad')
    MEL.connect_material_property(cu, '', EMIS)
    MEL.recompile_material(m); EAL.save_asset(DEST + '/M_RevealBlur')

# ---- sounds
tasks = []
for n in ('SFX_Reveal_Whoosh', 'SFX_Reveal_Hit', 'SFX_Reveal_Shimmer'):
    f = os.path.join(SFX_DIR, n + '.wav')
    if not os.path.exists(f): log.append('MISSING ' + f); continue
    t = unreal.AssetImportTask()
    for k, v in (('filename', f), ('destination_path', DEST), ('destination_name', n), ('replace_existing', True), ('automated', True), ('save', True)):
        t.set_editor_property(k, v)
    tasks.append(t); log.append('import ' + n)
if tasks and not DRY: AT.import_asset_tasks(tasks)


# ------------------------------------------------------------------------------------------------ stage actor
def handles_of(bp):
    hs = sds.k2_gather_subobject_data_for_blueprint(bp)
    return hs, {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in hs}


def comp(h): return SDL.get_object(sds.k2_find_subobject_data_from_handle(h))


def pickup_mesh(path):
    """the biggest mesh component of a pickup Blueprint: (component class, mesh, materials, scale) or None."""
    if not EAL.does_asset_exist(path): log.append('MISSING pickup ' + path); return None
    bp = unreal.load_asset(path)
    cands = [comp(h) for h in handles_of(bp)[0]]
    try:
        cdo = unreal.get_default_object(bp.generated_class())
        cands += list(cdo.get_components_by_class(unreal.MeshComponent))
    except Exception as e:
        log.append('  (no CDO components: %s)' % e)
    best = None
    for c in cands:
        if isinstance(c, unreal.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
        elif isinstance(c, unreal.SkeletalMeshComponent):
            mesh = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else c.get_editor_property('skeletal_mesh')
        else:
            continue
        if mesh is None: continue
        sc = c.get_editor_property('relative_scale3d')
        r = mesh.get_bounds().sphere_radius * max(abs(sc.x), abs(sc.y), abs(sc.z))
        if best is None or r > best[4]:
            best = (type(c), mesh, list(c.get_editor_property('override_materials')), sc, r)
    if best: log.append('  %s: %s %s (radius %.1f cm)' % (path.split('/')[-1], best[0].__name__, best[1].get_path_name(), best[4]))
    else: log.append('  %s: NO mesh component found' % path)
    return best


CH1 = unreal.LightingChannels(); CH1.set_editor_property('channel0', False); CH1.set_editor_property('channel1', True)
look = lambda loc: unreal.MathLibrary.find_look_at_rotation(loc, unreal.Vector(0, 0, 0))
LIGHTS = [  # name, location (cm from the item), candela, Kelvin, source radius: warm key, cool rim, weak fill (rule 5)
    ('KeyLight', unreal.Vector(-120, -110, 95), 13.0, 3600, 18.0),
    ('RimLight', unreal.Vector(110, 95, 70), 30.0, 8500, 6.0),
    ('FillLight', unreal.Vector(-105, 130, -15), 2.5, 6000, 40.0)]
STAGE = DEST + '/BP_RevealStage'
if EAL.does_asset_exist(STAGE):
    stage = unreal.load_asset(STAGE); log.append('reusing ' + STAGE)
else:
    log.append('create ' + STAGE)
    stage = None
    if not DRY:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        stage = AT.create_asset('BP_RevealStage', DEST, unreal.Blueprint, f)
meshes = {tag: pickup_mesh(p) for tag, p in PICKUPS.items()}
if stage:
    hs, by = handles_of(stage)
    root = hs[0]

    def add(name, cls, parent):
        if name in by: return by[name], False
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=stage))
        if not fail.is_empty(): raise RuntimeError('add %s: %s' % (name, fail))
        sds.rename_subobject(h, unreal.Text(name)); by[name] = h; log.append('  stage + ' + name); return h, True
    piv, _ = add('Pivot', unreal.SceneComponent, root)
    comp(piv).set_editor_property('component_tags', [unreal.Name('RevealPivot')])
    for tag, info in meshes.items():
        if info is None: continue
        cls_, mesh, mats, sc, _r = info
        h, _ = add(tag, cls_, piv)
        c = comp(h)
        if cls_ is unreal.StaticMeshComponent or issubclass(cls_, unreal.StaticMeshComponent):
            c.set_editor_property('static_mesh', mesh)
        else:
            try: c.set_editor_property('skeletal_mesh_asset', mesh)
            except Exception: c.set_editor_property('skeletal_mesh', mesh)
        if mats: c.set_editor_property('override_materials', mats)
        c.set_editor_property('relative_scale3d', sc)
        c.set_editor_property('component_tags', [unreal.Name(tag)])
        c.set_editor_property('lighting_channels', CH1)
        c.set_editor_property('visible_in_scene_capture_only', True)
        c.set_editor_property('visible', False)
        c.set_editor_property('cast_shadow', True)
        c.set_collision_profile_name('NoCollision')
    hc, _ = add('Capture', unreal.SceneCaptureComponent2D, root)
    cap = comp(hc)
    cap.set_editor_property('component_tags', [unreal.Name('RevealCapture')])
    if rt: cap.set_editor_property('texture_target', rt)
    cap.set_editor_property('capture_source', enum(unreal.SceneCaptureSource, 'SCS_SCENE_COLOR_HDR'))
    cap.set_editor_property('primitive_render_mode', enum(unreal.SceneCapturePrimitiveRenderMode, 'PRM_USE_SHOW_ONLY_LIST'))
    cap.set_editor_property('capture_every_frame', False); cap.set_editor_property('capture_on_movement', False)
    cap.set_editor_property('always_persist_rendering_state', True)
    cap.set_editor_property('fov_angle', 30.0)
    flags = []
    for n in ('Atmosphere', 'Fog', 'VolumetricFog', 'Cloud', 'SkyLighting', 'Bloom', 'MotionBlur', 'LensFlares', 'EyeAdaptation',
              'LumenGlobalIllumination', 'LumenReflections', 'GlobalIllumination', 'ScreenSpaceReflections', 'Decals'):
        fs = unreal.EngineShowFlagsSetting(); fs.set_editor_property('show_flag_name', n); fs.set_editor_property('enabled', False); flags.append(fs)
    cap.set_editor_property('show_flag_settings', flags)
    pp = cap.get_editor_property('post_process_settings')
    for k, v in (('override_auto_exposure_method', True), ('auto_exposure_method', enum(unreal.AutoExposureMethod, 'AEM_MANUAL')),
                 ('override_auto_exposure_bias', True), ('auto_exposure_bias', 0.0),
                 ('override_auto_exposure_apply_physical_camera_exposure', True), ('auto_exposure_apply_physical_camera_exposure', False),
                 ('override_dynamic_global_illumination_method', True), ('dynamic_global_illumination_method', enum(unreal.DynamicGlobalIlluminationMethod, 'NONE')),
                 ('override_reflection_method', True), ('reflection_method', enum(unreal.ReflectionMethod, 'NONE'))):
        try: pp.set_editor_property(k, v)
        except Exception as e: log.append('  (capture pp %s skipped: %s)' % (k, e))
    cap.set_editor_property('post_process_settings', pp); cap.set_editor_property('post_process_blend_weight', 1.0)
    for name, loc, cd, kelvin, srad in LIGHTS:
        h, _ = add(name, unreal.SpotLightComponent, root)
        L = comp(h)
        L.set_editor_property('relative_location', loc); L.set_editor_property('relative_rotation', look(loc))
        L.set_editor_property('intensity_units', enum(unreal.LightUnits, 'CANDELAS')); L.set_editor_property('intensity', cd)
        L.set_editor_property('use_temperature', True); L.set_editor_property('temperature', float(kelvin))
        L.set_editor_property('attenuation_radius', 600.0); L.set_editor_property('inner_cone_angle', 10.0); L.set_editor_property('outer_cone_angle', 40.0)
        L.set_editor_property('source_radius', srad); L.set_editor_property('soft_source_radius', srad)
        L.set_editor_property('lighting_channels', CH1); L.set_editor_property('cast_shadows', name == 'KeyLight')
    unreal.BlueprintEditorLibrary.compile_blueprint(stage); EAL.save_asset(STAGE)

# ------------------------------------------------------------------------------------------------ hero cameras: blur blendable
blur = unreal.load_asset(DEST + '/M_RevealBlur') if EAL.does_asset_exist(DEST + '/M_RevealBlur') else None
hero = unreal.load_asset(HERO)
cams = [c for c in (comp(h) for h in handles_of(hero)[0]) if isinstance(c, unreal.CameraComponent)]
log.append('hero cameras: %s' % [c.get_name() for c in cams])
for c in cams:
    pps = c.get_editor_property('post_process_settings')
    wb = pps.get_editor_property('weighted_blendables')
    arr_ = list(wb.get_editor_property('array'))
    if any(b.get_editor_property('object') == blur for b in arr_) and blur:
        log.append('  %s already has M_RevealBlur' % c.get_name()); continue
    log.append('  %s + M_RevealBlur blendable' % c.get_name())
    if DRY or blur is None: continue
    w = unreal.WeightedBlendable(); w.set_editor_property('weight', 1.0); w.set_editor_property('object', blur)
    wb.set_editor_property('array', arr_ + [w]); pps.set_editor_property('weighted_blendables', wb)
    c.set_editor_property('post_process_settings', pps)
if cams and not DRY:
    unreal.BlueprintEditorLibrary.compile_blueprint(hero); EAL.save_asset(HERO)

out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines on BPC_MotionFX, then the graph paste).'
if not DRY: open(os.path.join(HERE, 'setup_reveal268.txt'), 'w').write(out)
unreal.log(out)
