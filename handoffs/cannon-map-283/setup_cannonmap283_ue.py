# #283 Cannon scroll map, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/cannon-map-283/setup_cannonmap283_ue.py" --dry-run     (only reports)
#   py "<repo>/handoffs/cannon-map-283/setup_cannonmap283_ue.py"
# Makes in /Game/CastleDefender/UI/CannonMap:
#   RT_CannonMap    1024x1024 LDR render target (the live top-down map)
#   BP_MapCapture   actor: SceneCapture2D, orthographic 40000 cm (400 m) wide, looking straight down from 150 m, captures once
#                   on demand (no every-frame cost), tag MapCapture
#   M_ScrollMap     UI material: the parchment scroll (procedural paper fibres, stains, burnt edges, wooden rods with
#                   gold caps) that unrolls from the middle (Unroll 0..1) and shows RT_CannonMap inked and aged (sepia,
#                   Sobel ink lines) in its map area
#   M_MapRing       UI material: a pulsing ring + dot (colour, Age), used for the click demo, the marker and cannon icons
#   SFX_Scroll_Open / SFX_Scroll_Close / SFX_Map_Mark / SFX_Map_Confirm   (assets/adjustedfilm/CannonMap283/sfx)
#   BPC_CannonMap   ActorComponent, added to the hero as "CannonMap"
# Nothing else is changed.
import os, sys, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(REPO, 'handoffs', 'cannon-map-283')
DRY = '--dry-run' in sys.argv
SFX = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'CannonMap283', 'sfx'))
DST = '/Game/CastleDefender/UI/CannonMap'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#283 cannon map setup' + (' (DRY RUN, nothing written)' if DRY else '')]


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


def custom(m, code, inputs, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT4'))
    e.set_editor_property('description', 'CannonMap283')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def scalar(m, name, dv, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', dv); return e


def finish(m, cu, path):
    for i, (rgba, prop) in enumerate((((True, True, True, False), unreal.MaterialProperty.MP_EMISSIVE_COLOR), ((False, False, False, True), unreal.MaterialProperty.MP_OPACITY))):
        mk = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, 0, i * 200)
        for k, v in zip('rgba', rgba): mk.set_editor_property(k, v)
        MEL.connect_material_expressions(cu, '', mk, ''); MEL.connect_material_property(mk, '', prop)
    MEL.recompile_material(m); EAL.save_asset(path)


SCROLL_HLSL = r'''
// layout in the quad: rods at 0.5 -+ 0.47*Unroll; map area x 0.08..0.92, y 0.12..0.88 (inside the unrolled paper)
float2 uv = UV;
float half_ = 0.47 * saturate(Unroll);
float l = 0.5 - half_, r = 0.5 + half_;
float rodW = 0.028;
float4 o = 0;
// paper between the rods
if (uv.x > l && uv.x < r && uv.y > 0.06 && uv.y < 0.94)
{
    float2 p = uv * float2(Aspect, 1.0) * 6.0;
    float n = 0;
    float a = 0.5;
    for (int i = 0; i < 5; i++)
    {
        float2 ip = floor(p), fp = frac(p);
        float2 w = fp * fp * (3.0 - 2.0 * fp);
        float h00 = frac(sin(dot(ip, float2(127.1, 311.7))) * 43758.5453);
        float h10 = frac(sin(dot(ip + float2(1, 0), float2(127.1, 311.7))) * 43758.5453);
        float h01 = frac(sin(dot(ip + float2(0, 1), float2(127.1, 311.7))) * 43758.5453);
        float h11 = frac(sin(dot(ip + float2(1, 1), float2(127.1, 311.7))) * 43758.5453);
        n += a * lerp(lerp(h00, h10, w.x), lerp(h01, h11, w.x), w.y);
        p *= 2.03; a *= 0.5;
    }
    float fib = frac(sin(dot(floor(uv * float2(900.0 * Aspect, 140.0)), float2(12.9898, 78.233))) * 43758.5453);
    float3 paper = float3(0.80, 0.69, 0.50) * (0.86 + 0.22 * n) * (0.97 + 0.03 * fib);
    float edge = min(min(uv.x - l, r - uv.x) * Aspect, min(uv.y - 0.06, 0.94 - uv.y));
    paper *= lerp(0.45, 1.0, smoothstep(0.0, 0.06, edge + (n - 0.5) * 0.02));           // burnt, darkened edges
    paper *= lerp(0.88, 1.0, smoothstep(0.25, 0.75, n));                                  // stains
    float3 col = paper;
    // the map, inked and aged
    float2 mu = float2((uv.x - 0.08) / 0.84, (uv.y - 0.12) / 0.76);
    if (mu.x > 0 && mu.x < 1 && mu.y > 0 && mu.y < 1)
    {
        float2 tuv = float2(mu.x, 0.5 + (mu.y - 0.5) / MapAspect);
        float3 m = Texture2DSample(MapT, MapTSampler, tuv).rgb;
        float lum = dot(m, float3(0.299, 0.587, 0.114));
        float px = 1.0 / 1024.0;
        float lx = dot(Texture2DSample(MapT, MapTSampler, tuv + float2(px, 0)).rgb - Texture2DSample(MapT, MapTSampler, tuv - float2(px, 0)).rgb, 0.333);
        float ly = dot(Texture2DSample(MapT, MapTSampler, tuv + float2(0, px)).rgb - Texture2DSample(MapT, MapTSampler, tuv - float2(0, px)).rgb, 0.333);
        float ink = saturate(length(float2(lx, ly)) * 6.0);
        float3 tint = paper * lerp(0.55, 1.08, pow(saturate(lum * 1.4), 0.8));
        tint = lerp(tint, float3(0.22, 0.14, 0.08), ink * 0.85);
        float fadeIn = smoothstep(0.0, 0.04, min(min(mu.x, 1 - mu.x), min(mu.y, 1 - mu.y)));
        col = lerp(col, tint, fadeIn * saturate(Reveal));
        // thin ink frame
        float fr = min(min(mu.x, 1 - mu.x) * Aspect, min(mu.y, 1 - mu.y));
        col = lerp(col, float3(0.25, 0.16, 0.09), (1.0 - smoothstep(0.0, 0.003, abs(fr - 0.004))) * 0.8);
    }
    o = float4(col, 1);
}
// the two wooden rods with gold caps
float rods[2] = { l, r };
for (int k = 0; k < 2; k++)
{
    float dx = (uv.x - rods[k]) * Aspect / (rodW * Aspect);
    if (abs(dx) < 1.0 && uv.y > 0.02 && uv.y < 0.98)
    {
        float s = sqrt(1.0 - dx * dx);
        float grain = 0.85 + 0.15 * sin(uv.y * 220.0 + sin(uv.y * 31.0) * 3.0);
        float3 wood = float3(0.30, 0.17, 0.08) * (0.35 + 0.85 * s) * grain;
        float cap = step(uv.y, 0.065) + step(0.935, uv.y);
        float3 gold = float3(1.0, 0.72, 0.30) * (0.3 + 1.1 * s * s);
        o = float4(lerp(wood, gold, cap), 1);
    }
}
o.a *= saturate(Fade);
return o;
'''

RING_HLSL = r'''
float2 d = UV - 0.5;
float r = length(d) * 2.0;
float rr = 0.35 + 0.55 * frac(Age);
float ring = exp(-pow((r - rr) / 0.06, 2.0)) * (1.0 - frac(Age));
float ring2 = exp(-pow((r - 0.5) / 0.05, 2.0)) * Solid;
float dot_ = 1.0 - smoothstep(0.14, 0.2, r);
float a = saturate(max(max(ring, ring2), dot_)) * Col.a;
return float4(Col.rgb, a);
'''

rt, _ = fresh('RT_CannonMap', unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
if rt:
    rt.set_editor_property('size_x', 1024); rt.set_editor_property('size_y', 1024)
    rt.set_editor_property('render_target_format', enum(unreal.TextureRenderTargetFormat, 'RTF_RGBA8'))
    EAL.save_asset(DST + '/RT_CannonMap')

m, made = fresh('M_ScrollMap', unreal.Material, unreal.MaterialFactoryNew())
if m:
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_UI')); m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    cu = custom(m, SCROLL_HLSL, ['UV', 'MapT', 'Unroll', 'Reveal', 'Aspect', 'MapAspect', 'Fade'], -300, 0)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -800, -200), '', cu, 'UV')
    to = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -800, -100)
    to.set_editor_property('parameter_name', 'MapT')
    if rt: to.set_editor_property('texture', rt)
    MEL.connect_material_expressions(to, '', cu, 'MapT')
    y = 0
    for n, dv in (('Unroll', 0.0), ('Reveal', 0.0), ('Aspect', 1.7), ('MapAspect', 1.7), ('Fade', 1.0)):
        MEL.connect_material_expressions(scalar(m, n, dv, -800, y), '', cu, n); y += 100
    finish(m, cu, DST + '/M_ScrollMap')

m, made = fresh('M_MapRing', unreal.Material, unreal.MaterialFactoryNew())
if m:
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_UI')); m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    cu = custom(m, RING_HLSL, ['UV', 'Age', 'Solid', 'Col'], -300, 0)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -800, -200), '', cu, 'UV')
    MEL.connect_material_expressions(scalar(m, 'Age', 0.0, -800, 0), '', cu, 'Age')
    MEL.connect_material_expressions(scalar(m, 'Solid', 1.0, -800, 100), '', cu, 'Solid')
    vc = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -800, 200)
    vc.set_editor_property('parameter_name', 'Col'); vc.set_editor_property('default_value', unreal.LinearColor(1.0, 0.72, 0.3, 1.0))
    ap = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -550, 250)
    MEL.connect_material_expressions(vc, '', ap, 'A'); MEL.connect_material_expressions(vc, 'A', ap, 'B')
    MEL.connect_material_expressions(ap, '', cu, 'Col')
    finish(m, cu, DST + '/M_MapRing')

tasks = []
for n in ('SFX_Scroll_Open', 'SFX_Scroll_Close', 'SFX_Map_Mark', 'SFX_Map_Confirm'):
    f = os.path.join(SFX, n + '.wav')
    if not os.path.exists(f): log.append('MISSING ' + f); continue
    t = unreal.AssetImportTask()
    for k, v in (('filename', f), ('destination_path', DST), ('destination_name', n), ('replace_existing', True), ('automated', True), ('save', True)):
        t.set_editor_property(k, v)
    tasks.append(t); log.append('import ' + n)
if tasks and not DRY: AT.import_asset_tasks(tasks)


def make_bp(name, parent):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


def names(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


mc = make_bp('BP_MapCapture', unreal.Actor)
if mc and 'Capture' not in names(mc):
    h, reason = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(mc)[0], new_class=unreal.SceneCaptureComponent2D, blueprint_context=mc))
    SDS.rename_subobject(h, unreal.Text('Capture')); log.append('  + BP_MapCapture.Capture')
    c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
    c.set_editor_property('component_tags', [unreal.Name('MapCapture')])
    c.set_editor_property('projection_type', enum(unreal.CameraProjectionMode, 'ORTHOGRAPHIC'))
    c.set_editor_property('ortho_width', 40000.0)
    c.set_editor_property('relative_rotation', unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0))
    if rt: c.set_editor_property('texture_target', rt)
    c.set_editor_property('capture_source', enum(unreal.SceneCaptureSource, 'SCS_FINAL_COLOR_LDR'))
    c.set_editor_property('capture_every_frame', False); c.set_editor_property('capture_on_movement', False)
    BEL.compile_blueprint(mc); EAL.save_asset(DST + '/BP_MapCapture')
comp = make_bp('BPC_CannonMap', unreal.ActorComponent)
if comp: BEL.compile_blueprint(comp); EAL.save_asset(DST + '/BPC_CannonMap')
hero = unreal.load_asset(HERO)
if 'CannonMap' in names(hero): log.append('hero already has CannonMap')
else:
    log.append('hero: + CannonMap (BPC_CannonMap)')
    if comp and not DRY:
        h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0],
                                                                     new_class=comp.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add CannonMap: %s' % fail)
        SDS.rename_subobject(h, unreal.Text('CannonMap')); BEL.compile_blueprint(hero); EAL.save_asset(HERO)
out = '\n'.join(log) + '\nNext: README step 3 (BPVar lines, graph paste, then the two manifests).'
if not DRY: open(os.path.join(HERE, 'setup_cannonmap283.txt'), 'w').write(out)
unreal.log(out)
