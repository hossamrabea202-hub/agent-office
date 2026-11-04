# #504 castle weathering, step 1 (i5 checkking, 2026-11-04). UE 5.8 editor Python, safe to re-run.   [--dry-run]
# Makes, ALL NEW, in /Game/CastleDefender/Environment/CastleWeather504 (no live material, MI or decal is touched):
#   M_RainStreakCard504  run-off streaks hanging under a ledge / sill / cap (gravity; dirt + biofilm carried by rain)
#   M_CrackCard504       settlement / frost crack with branches, a moisture halo and a stained trail below (water)
#   M_LichenCard504      crustose lichen + algae colonies (damp: up-facing caps, faces turned away from the sun)
#   MI_*504 instances with the lookdev values below.
# All three are unlit MODULATE stain cards (the #425 method, tested): they work on the walls that have Receives Decals off
# (about half the castle; that flag is the owner's) and multiply the wall by col / WallAlbedo where the mask is > 0.
# They are drawn as InstancedStaticMesh cards (3 draw calls for the whole castle); the per-instance custom data slot 0 is
# the random seed, so every card is different.
# Values (handoffs/knowledge INDUSTRY_SECRETS 1.1, 4.5): soil 0.15 dry, charcoal 0.02, grime ~0.06-0.09; wall granite
# albedo ~0.32 (measured off the merlon lookdev); lichen grey-green and Xanthoria yellow-orange are inferences (Baran's
# list is paid, 4.5 "still open"), kept restrained. Restraint over grunge (KB README rule 3).
# UV: engine Plane rotated MakeRotFromZX(wallNormal, up) -> U runs UP the wall: Swap 1, FlipV 1 (as #425).
import sys, unreal

DRY = '--dry-run' in sys.argv
TEMP = '--temp' in sys.argv               # lookdev only: build in /Game/_i5tmpCW504 and NEVER save (packages stay in memory)
DST = '/Game/_i5tmpCW504' if TEMP else '/Game/CastleDefender/Environment/CastleWeather504'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
log = ['#504 castle weathering build' + (' (DRY RUN, nothing written)' if DRY else '') + (' (TEMP, in memory, nothing saved)' if TEMP else '')]
SAVE = (lambda p: True) if TEMP else EAL.save_asset


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def fresh(name, cls, factory):
    path = DST + '/' + name
    if EAL.does_asset_exist(path):
        log.append('rebuild ' + path); return (None if DRY else unreal.load_asset(path)), False
    log.append('create ' + path)
    return (None if DRY else AT.create_asset(name, DST, cls, factory)), True


def custom(m, code, inputs, otype, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', 'CW504')
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def scalar(m, name, val, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', val); return e


# value noise + 4-octave fbm on p; S = seed offset. H21 = lattice hash.
NOISE = '''float2 S = float2(Seed * 17.13, Seed * 31.7);
#define H21(q) frac(sin(dot(q, float2(127.1, 311.7))) * 43758.5453)
float2 i0, f0; float n1, fb = 0.0, amp = 0.5; float2 q = p;
[unroll] for (int o = 0; o < 4; o++) {
  float2 z = q * (6.0 * pow(2.0, o)) + S; i0 = floor(z); f0 = frac(z); f0 = f0 * f0 * (3.0 - 2.0 * f0);
  n1 = lerp(lerp(H21(i0), H21(i0 + float2(1, 0)), f0.x), lerp(H21(i0 + float2(0, 1)), H21(i0 + float2(1, 1)), f0.x), f0.y);
  fb += amp * n1; amp *= 0.5; }
'''
# 1-D smooth value noise used for crack paths: n1d(t, k) in 0..1
N1D = '''#define N1D(t, k) lerp(H21(float2(floor(t), k)), H21(float2(floor(t) + 1.0, k)), smoothstep(0.0, 1.0, frac(t)))
'''

# Rain run-off under a ledge. Top edge of the card (p.y = +0.5) = the drip edge. y = distance down from it (0..1).
# Water leaves the ledge in irregular lanes; each lane carries dirt/biofilm a random length (gravity), densest just under
# the edge where the drip line keeps it wet, fading downward; a faint general wash sheet between lanes; vertical fine
# streak noise breaks the lanes up. Optional green (algae) on damp lanes.
STREAK = '''float y = 0.5 - p.y;
float xw = p.x + 0.05 * (N1D(y * 3.0, Seed + 2.0) - 0.5) + 0.08 * (fb - 0.5);
float cx = (xw + 0.5) * Cols;
float ci = floor(cx); float h = H21(float2(ci, Seed)); float h2 = H21(float2(ci, Seed + 7.0)); float h3 = H21(float2(ci, Seed + 9.0));
float d = abs(frac(cx) - (0.5 + 0.3 * (h3 - 0.5))) * 2.0;
float L = (0.2 + 0.8 * h) * Length;
float tt = saturate(y / max(L, 0.02));
float lw = (0.35 + 0.5 * h2) * (1.0 - 0.7 * tt);
float lane = 1.0 - smoothstep(lw * 0.45, lw, d);
float body = pow(1.0 - tt, 0.8) * (0.55 + 0.45 * N1D(y * 9.0, ci + Seed));
float2 qs = float2(xw * 14.0, y * 1.5) + S;
float2 i1 = floor(qs), f1 = frac(qs); f1 = f1 * f1 * (3.0 - 2.0 * f1);
float st = lerp(lerp(H21(i1), H21(i1 + float2(1, 0)), f1.x), lerp(H21(i1 + float2(0, 1)), H21(i1 + float2(1, 1)), f1.x), f1.y);
float streak = saturate(1.45 * lane * body * step(0.25, h + 0.3) * (0.75 + 0.35 * st));
float sheet = exp(-y * SheetFall) * Sheet * (0.5 + 0.6 * fb);
float lip = (1.0 - smoothstep(0.0, 0.05 + 0.04 * fb, y)) * Lip * (0.6 + 0.6 * fb);
float a = max(streak, sheet) + lip;
a *= saturate((0.5 - abs(p.x)) * 5.0) * saturate((0.5 + p.y) * 6.0) * saturate((0.5 - p.y) * 60.0);
a = saturate(a) * MaxOpacity;
float3 grime = float3(0.080, 0.072, 0.058);
float3 algae = float3(0.060, 0.072, 0.042);
float3 col = lerp(grime, algae, saturate(Green * (0.4 + fb) * lane));
'''

# Crack: a jagged main path top -> bottom (x wanders with two octaves of 1-D noise), width tapers to the ends; two short
# branches; a soft dark moisture halo around it; below the lower end a stained trail where water leaves the crack.
# Core = deep shadow 0.015, halo = grime 0.08 (restraint: halo opacity ~0.3).
CRACK = '''float t = 0.5 - p.y;
float xw = Wander * ((N1D(t * 4.0, Seed) - 0.5) * 0.55 + (N1D(t * 17.0, Seed + 3.0) - 0.5) * 0.18 + (N1D(t * 61.0, Seed + 5.0) - 0.5) * 0.05);
float taper = pow(saturate(1.0 - abs(t - 0.5) * 2.0), 0.6);
float dm = abs(p.x - xw) / max(Width * (0.25 + taper), 1e-4);
float core = (1.0 - smoothstep(0.6, 1.0, dm)) * step(0.02, t) * step(t, 0.98);
float halo = exp(-dm * 0.18) * taper * 0.9;
float br = 0.0;
[unroll] for (int k = 0; k < 2; k++) {
  float t0 = 0.25 + 0.5 * H21(float2(k, Seed + 11.0)); float dir = (H21(float2(k, Seed + 13.0)) > 0.5) ? 1.0 : -1.0;
  float bl = 0.10 + 0.18 * H21(float2(k, Seed + 17.0));
  float x0 = Wander * ((N1D(t0 * 4.0, Seed) - 0.5) * 0.55 + (N1D(t0 * 17.0, Seed + 3.0) - 0.5) * 0.18);
  float u = (t - t0) / bl;
  float bx = x0 + dir * u * bl * 0.9 + Wander * (N1D(t * 23.0, Seed + 19.0 + k) - 0.5) * 0.08;
  float bw = Width * 0.6 * saturate(1.0 - u);
  float bd = abs(p.x - bx) / max(bw, 1e-4);
  br = max(br, (1.0 - smoothstep(0.6, 1.0, bd)) * step(0.0, u) * step(u, 1.0) * Branches); }
float tb = saturate((t - 0.75) / 0.25);
float trail = (1.0 - smoothstep(0.02, 0.10 + 0.06 * fb, abs(p.x - xw))) * tb * Trail * (0.5 + 0.6 * fb);
float cr = max(core, br);
float a = max(max(cr, halo * HaloOp * (0.6 + 0.6 * fb)), trail * 0.4);
a *= saturate((0.5 - abs(p.x)) * 8.0) * saturate((0.5 - abs(p.y)) * 30.0);
a = saturate(a) * MaxOpacity;
float3 col = lerp(float3(0.08, 0.072, 0.060), float3(0.015, 0.013, 0.012), saturate(cr));
'''

# Lichen: colonies on a jittered grid (3x3 neighbourhood), each with its own radius, an fbm-broken outline, a slightly
# lighter growing rim (crustose rosettes), and a species colour by hash: grey-green (most), yellow-orange Xanthoria
# (rare, sunny caps), dark algae film (damp). Coverage picks how many cells hold a colony. Card edge fades in a soft disc.
LICHEN = '''float2 g = p * Cells; float2 gi = floor(g);
float best = 0.0; float3 bc = float3(1, 1, 1);
[unroll] for (int j = -1; j <= 1; j++) { [unroll] for (int i = -1; i <= 1; i++) {
  float2 c = gi + float2(i, j);
  float hp = H21(c + Seed * 3.1); if (hp > Coverage) continue;
  float2 ctr = c + 0.5 + (float2(H21(c + 5.3 + Seed), H21(c + 9.7 + Seed)) - 0.5) * 0.7;
  float r = 0.25 + 0.55 * H21(c + 2.2 + Seed);
  float dd = length(g - ctr) + (fb - 0.5) * 0.45 * r;
  float m = 1.0 - smoothstep(r * 0.82, r, dd);
  float rim = smoothstep(r * 0.55, r * 0.9, dd) * m;
  float hs = H21(c + 7.7 + Seed);
  float3 cc = hs < Yellow ? float3(0.50, 0.36, 0.11) : (hs > 1.0 - Dark ? float3(0.055, 0.062, 0.045) : float3(0.30, 0.31, 0.24));
  cc *= lerp(0.9, 1.12, rim);
  if (m > best) { best = m; bc = cc; } } }
float a = best * (0.75 + 0.35 * fb);
float2 e = p * 2.0; a *= saturate((1.0 - dot(e, e)) * 3.0);
a = saturate(a) * MaxOpacity;
float3 col = bc;
'''


def card_material(name, body, params, bright=1.0):
    """Thin unlit MODULATE plane ~0.5 cm off the wall: wall x lerp(1, col / WallAlbedo, a). bright > 1 lets light
    lichen lift a darker stone (modulate can only multiply)."""
    m, made = fresh(name, unreal.Material, unreal.MaterialFactoryNew())
    if not m: return
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_MODULATE'))
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_UNLIT'))
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_SURFACE'))
    m.set_editor_property('two_sided', False)
    for flag in ('used_with_instanced_static_meshes',):
        try: m.set_editor_property(flag, True)
        except Exception as ex: log.append('flag %s: %s' % (flag, ex))
    head = 'float Seed = SeedP + InstSeed;\nfloat2 p = UV - 0.5; if (Swap > 0.5) p = p.yx; if (FlipV < 0.5) p.y = -p.y;\n' + NOISE + N1D
    params = [('Swap', 1.0), ('FlipV', 1.0), ('SeedP', 0.0), ('Strength', 1.0), ('WallAlbedo', 0.32)] + params
    code = head + body + 'return clamp(lerp(float3(1, 1, 1), col / WallAlbedo, saturate(a * Strength)), 0.0, %.2f);' % bright
    cc = custom(m, code, ['UV', 'InstSeed'] + [p for p, _ in params], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -300, 0)
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1000, -150)
    MEL.connect_material_expressions(uv, '', cc, 'UV')
    pic = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData, -1000, -50)
    pic.set_editor_property('data_index', 0)
    MEL.connect_material_expressions(pic, '', cc, 'InstSeed')
    y = 150
    for p, v in params:
        MEL.connect_material_expressions(scalar(m, p, v, -1000, y), '', cc, p); y += 110
    MEL.connect_material_property(cc, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); SAVE(DST + '/' + name)


if not DRY and not TEMP and not EAL.does_directory_exist(DST): EAL.make_directory(DST)
card_material('M_RainStreakCard504', STREAK, [('Cols', 4.0), ('Length', 1.0), ('Sheet', 0.18), ('SheetFall', 3.0),
                                              ('Lip', 0.3), ('Green', 0.0), ('MaxOpacity', 0.68)])
card_material('M_CrackCard504', CRACK, [('Width', 0.012), ('Wander', 0.55), ('Branches', 1.0), ('HaloOp', 0.30),
                                        ('Trail', 1.0), ('MaxOpacity', 0.9)])
card_material('M_LichenCard504', LICHEN, [('Cells', 6.0), ('Coverage', 0.45), ('Yellow', 0.12), ('Dark', 0.15),
                                          ('MaxOpacity', 0.7)], bright=1.6)

MIS = {'MI_RainStreak504_Ledge': ('M_RainStreakCard504', {}),
       'MI_RainStreak504_Sill': ('M_RainStreakCard504', {'Cols': 3.0, 'Lip': 0.5, 'Sheet': 0.35, 'Green': 0.35, 'MaxOpacity': 0.7}),
       'MI_RainStreak504_Top': ('M_RainStreakCard504', {'Lip': 0.15, 'Sheet': 0.12, 'MaxOpacity': 0.5}),
       'MI_Crack504': ('M_CrackCard504', {}),
       'MI_Lichen504_Cap': ('M_LichenCard504', {'Coverage': 0.5, 'Yellow': 0.18}),
       'MI_Lichen504_Shade': ('M_LichenCard504', {'Coverage': 0.4, 'Yellow': 0.02, 'Dark': 0.35, 'MaxOpacity': 0.6})}
for n, (parent, vals) in MIS.items():
    mi, made = fresh(n, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not mi: continue
    MEL.set_material_instance_parent(mi, unreal.load_asset(DST + '/' + parent))
    for k, v in vals.items(): MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    SAVE(DST + '/' + n)
print('\n'.join(log))
