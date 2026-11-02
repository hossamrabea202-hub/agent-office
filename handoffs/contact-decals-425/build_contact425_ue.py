# #425 contact decals, step 1 (i5, 2026-11-02). UE 5.8 editor Python, safe to re-run.   [--dry-run]
# Makes, ALL NEW, in /Game/CastleDefender/Environment/ContactDecals425 (no live material or decal is touched):
#   M_ContactSoot425   deferred decal (translucent: colour + roughness): soot plume above a flame. Procedural, no textures.
#   M_ContactMount425  deferred decal: contact grime halo + rust drips + bolt holes where an iron bracket meets the wall.
#   MI_Soot425_Torch, MI_Mount425_Iron, MI_Mount425_Wood   instances with the defaults below (tune live, no recompile).
# Decal UV: U across the wall, V DOWN the wall (UE decal TexCoord); FlipV = 1 if a lookdev shot shows it upside down,
# Swap = 1 if it lies sideways.
# Values (handoffs/knowledge INDUSTRY_SECRETS 1.1): charcoal albedo 0.02, roughness 1.0; rust 0.18/0.057/0.017, metallic 0,
# roughness 1.0; grime = dry soil 0.15 darkened by soot. Every layer has a physical cause: soot rises and spreads above the
# flame and thins with height; grime collects where hands and rain touch the bracket; rust runs DOWN from the iron (gravity).
import sys, unreal

DRY = '--dry-run' in sys.argv
DST = '/Game/CastleDefender/Environment/ContactDecals425'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
log = ['#425 contact decals build' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('rebuild ' + path); return (None if DRY else unreal.load_asset(path)), False
    log.append('create ' + path)
    return (None if DRY else AT.create_asset(name, DST, cls, factory)), True


def custom(m, code, inputs, otype, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', 'CD425')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def mask(m, src, rgba, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, x, y)
    for k, v in zip('rgba', rgba): e.set_editor_property(k, v)
    MEL.connect_material_expressions(src, '', e, ''); return e


def scalar(m, name, val, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', val); return e


def decal_material(name, body, params):
    """body: HLSL that sets float3 col, float a, float r from p (centred, x right, y UP) and the params."""
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if not m: return
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_DEFERRED_DECAL'))
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    try: m.set_editor_property('decal_blend_mode', enum(unreal.DecalBlendMode, 'DBM_TRANSLUCENT'))
    except Exception: pass
    head = ('float2 p = UV - 0.5; if (Swap > 0.5) p = p.yx; if (FlipV < 0.5) p.y = -p.y;\n' + NOISE)
    params = [('Swap', 0.0), ('FlipV', 0.0), ('Seed', 0.0), ('Strength', 1.0)] + params
    ins = ['UV'] + [p for p, _ in params]
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1000, 0)
    cc = custom(m, head + body + 'return float4(col, saturate(a * Strength));', ins, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -300, 0)
    cr = custom(m, head + body + 'return r;', ins, unreal.CustomMaterialOutputType.CMOT_FLOAT1, -300, 300)
    y = 150
    for p, v in params:
        s = scalar(m, p, v, -1000, y); y += 110
        for c in (cc, cr): MEL.connect_material_expressions(s, '', c, p)
    for c in (cc, cr): MEL.connect_material_expressions(uv, '', c, 'UV')
    MEL.connect_material_property(mask(m, cc, (True, True, True, False), 0, 0), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mask(m, cc, (False, False, False, True), 0, 150), '', unreal.MaterialProperty.MP_OPACITY)
    MEL.connect_material_property(cr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m); EAL.save_asset(DST + '/' + name)


# value noise (hash on a lattice, smooth-interpolated), fbm of 4 octaves; S = Seed offset
NOISE = '''float2 S = float2(Seed * 17.13, Seed * 31.7);
#define H21(q) frac(sin(dot(q, float2(127.1, 311.7))) * 43758.5453)
float2 i0, f0; float n1, fb = 0.0, amp = 0.5; float2 q = p;
[unroll] for (int o = 0; o < 4; o++) {
  float2 z = q * (6.0 * pow(2.0, o)) + S; i0 = floor(z); f0 = frac(z); f0 = f0 * f0 * (3.0 - 2.0 * f0);
  n1 = lerp(lerp(H21(i0), H21(i0 + float2(1, 0)), f0.x), lerp(H21(i0 + float2(0, 1)), H21(i0 + float2(1, 1)), f0.x), f0.y);
  fb += amp * n1; amp *= 0.5; }
'''

# Soot: flame sits at FlameY (from the decal centre, y up). Density falls off with height (exp), the plume widens upward,
# streaks are stretched vertically (convection), edges break up with fbm. Charcoal 0.02-0.035 linear, roughness 0.95.
SOOT = '''float t = saturate((p.y - FlameY) / (0.5 - FlameY));
float below = saturate(1.0 - (FlameY - p.y) / 0.06);
float w = 0.05 + Spread * pow(t, 0.7);
float core = exp(-pow(p.x / w, 2.0) * 2.2);
float2 qs = float2(p.x * 9.0, p.y * 1.6) + S;
float2 i1 = floor(qs), f1 = frac(qs); f1 = f1 * f1 * (3.0 - 2.0 * f1);
float st = lerp(lerp(H21(i1), H21(i1 + float2(1, 0)), f1.x), lerp(H21(i1 + float2(0, 1)), H21(i1 + float2(1, 1)), f1.x), f1.y);
float dens = exp(-Falloff * t) * (p.y >= FlameY ? 1.0 : below);
float a = core * dens * (0.55 + 0.6 * fb) * (0.75 + 0.5 * st);
a = saturate(a * 1.15 - 0.04) * MaxOpacity;
a *= saturate((0.5 - abs(p.x)) * 12.0) * saturate((0.5 - p.y) * 10.0);
float3 col = lerp(float3(0.035, 0.03, 0.026), float3(0.018, 0.016, 0.015), saturate(dens));
float r = 0.95;
'''

# Mount: footprint radius R around the centre. Grime halo (hands, rain splash, soot) darkest at the contact line, rust
# drips run DOWN from the iron only (gravity), irregular length per column, 4 bolt holes. Restrained: max opacity ~0.7.
MOUNT = '''float d = length(p / float2(1.0, 1.15));
float halo = (1.0 - smoothstep(R * 0.55, R * 1.7, d)) * (0.6 + 0.6 * fb);
float col24 = (p.x + 0.5) * Cols; float ci = floor(col24); float hc = H21(float2(ci, Seed));
float lane = 1.0 - smoothstep(0.10 + 0.12 * hc, 0.30 + 0.12 * hc, abs(frac(col24) - 0.5));
float top = -R * 0.35; float L = (0.08 + 0.32 * hc) * DripLen;
float run = (p.y < top && p.y > top - L) ? pow(1.0 - (top - p.y) / L, 1.6) : 0.0;
float near = 1.0 - smoothstep(R * 0.2, R * 1.25, abs(p.x));
float drip = lane * run * near * step(0.35, hc) * Rust;
float holes = 0.0;
[unroll] for (int k = 0; k < 4; k++) { float2 hp = float2((k & 1) ? 0.55 : -0.55, (k & 2) ? 0.55 : -0.55) * R * Holes;
  holes = max(holes, 1.0 - smoothstep(0.010, 0.016, length(p - hp))); }
holes *= step(0.01, Holes);
float3 grime = float3(0.055, 0.047, 0.040);
float3 rust = float3(0.18, 0.057, 0.017);
float3 col = lerp(grime, rust, saturate(drip * 1.4 + Rust * 0.35 * halo * (1.0 - d / (R * 1.7))));
col = lerp(col, float3(0.012, 0.010, 0.009), holes);
float a = saturate(max(max(halo * 0.55, drip * 0.8), holes * 0.9)) * MaxOpacity;
a *= saturate((0.5 - abs(p.x)) * 10.0) * saturate((0.5 - abs(p.y)) * 10.0);
float r = lerp(0.9, 1.0, drip);
'''

def card_material(name, body, params):
    """Stain card for walls with Receives Decals OFF (about half the castle; that flag is the owner's to change): a thin
    unlit MODULATE plane 0.5 cm off the wall. Same masks; it multiplies the wall by col / WallAlbedo where a > 0."""
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if not m: return
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_MODULATE'))
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_UNLIT'))
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_SURFACE'))
    head = ('float2 p = UV - 0.5; if (Swap > 0.5) p = p.yx; if (FlipV < 0.5) p.y = -p.y;\n' + NOISE)
    params = [('Swap', 0.0), ('FlipV', 0.0), ('Seed', 0.0), ('Strength', 1.0), ('WallAlbedo', 0.35)] + params
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1000, 0)
    cc = custom(m, head + body + 'return lerp(float3(1, 1, 1), saturate(col / WallAlbedo), saturate(a * Strength));',
                ['UV'] + [p for p, _ in params], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 0)
    MEL.connect_material_expressions(uv, '', cc, 'UV')
    y = 150
    for p, v in params:
        MEL.connect_material_expressions(scalar(m, p, v, -1000, y), '', cc, p); y += 110
    MEL.connect_material_property(cc, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(DST + '/' + name)


if not DRY and not EAL.does_directory_exist(DST): EAL.make_directory(DST)
card_material('M_ContactSootCard425', SOOT, [('FlameY', -0.32), ('Spread', 0.30), ('Falloff', 2.2), ('MaxOpacity', 0.85)])
card_material('M_ContactMountCard425', MOUNT, [('R', 0.16), ('Cols', 22.0), ('DripLen', 1.0), ('Rust', 1.0), ('Holes', 1.0), ('MaxOpacity', 0.7)])
decal_material('M_ContactSoot425', SOOT, [('FlameY', -0.32), ('Spread', 0.30), ('Falloff', 2.2), ('MaxOpacity', 0.85)])
decal_material('M_ContactMount425', MOUNT, [('R', 0.16), ('Cols', 22.0), ('DripLen', 1.0), ('Rust', 1.0), ('Holes', 1.0), ('MaxOpacity', 0.7)])

MIS = {'MI_Soot425_Torch': ('M_ContactSoot425', {}),
       'MI_Mount425_Iron': ('M_ContactMount425', {}),
       'MI_Mount425_Wood': ('M_ContactMount425', {'Rust': 0.15, 'Holes': 0.0, 'R': 0.2}),   # wooden posts / sign hooks: grime, little rust
       # cards (engine Plane: U runs up the wall -> Swap 1, FlipV 1). Values from the 2026-11-02 lookdev (restraint pass).
       'MI_SootCard425_Torch': ('M_ContactSootCard425', {'Swap': 1, 'FlipV': 1, 'Strength': 1.2, 'MaxOpacity': 0.6, 'Spread': 0.42, 'Falloff': 1.3}),
       'MI_MountCard425_Iron': ('M_ContactMountCard425', {'Swap': 1, 'FlipV': 1, 'Strength': 1.3, 'Holes': 0.0, 'DripLen': 0.45, 'Rust': 0.6}),
       'MI_MountCard425_Wood': ('M_ContactMountCard425', {'Swap': 1, 'FlipV': 1, 'Strength': 1.3, 'Rust': 0.15, 'Holes': 0.0, 'R': 0.2})}
for n, (parent, vals) in MIS.items():
    mi, made = fresh(n, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not mi: continue
    mi.set_editor_property('parent', unreal.load_asset(DST + '/' + parent))
    for k, v in vals.items(): MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    EAL.save_asset(DST + '/' + n)
print('\n'.join(log))
