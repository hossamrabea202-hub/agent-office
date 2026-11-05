# Horde crowd material (i5 checkking for i9, 2026-11-05). UE 5.8 editor Python, safe to re-run.   [--dry-run] [--temp]
# Builds, ALL NEW, in /Game/CastleDefender/Horde (nothing existing is touched):
#   M_CD_HordeZombie      the crowd material for UCDHordeSubsystem's instanced zombies: plays the baked bone texture on the GPU
#                         (contract v1, CDHordeAnimData.h), skinned normal, melt, brute tint
#   MI_CD_Horde_A / _B    the two zombie looks (T_Zombie_A_* / T_Zombie_B_* from Characters/Enemies/Zombie/AAA)
#   M_CD_MeltPool         deferred decal: the wet dark rot a melting zombie leaves (irregular round mask, fades with the decal's lifetime)
# --temp: builds in /Game/_i5tmpHorde and never saves (i5 compile test). --dry-run: lists what it would do.
#
# CONTRACT v1 as implemented here (vertex shader):
#   custom data [0] StartFrame [1] NumFrames [2] ClipStartTime [3] FPS (<0 = hold last frame) [4] MeltStartTime (0 = none) [5] tint (1 = brute)
#   f = max(Time - C2, 0) * |C3|; loop: f = fmod(f, C1), next = fmod(floor(f) + 1, C1); hold: f = min(f, C1 - 1), next = min(floor(f) + 1, C1 - 1)
#   rows r0 = C0 + floor(f), r1 = C0 + next, a = frac(f); skin = sum_k w_k * (q_b * v * q_b^-1 + t_b), q at texel (2b, row), t at (2b+1, row)
#   bones b in UV1.xy / UV2.xy (whole numbers), weights in UV3.xy / UV4.xy (largest first, sum 1)
#   v = the vertex in mesh space (PreSkinnedPosition: reference pose, origin at the feet, Z up). WPO = LocalToWorld(skin(v) - v).
#   melt m = C4 > 0 ? smoothstep(saturate((Time - C4) / 1.6)) : 0, after skinning: the body slumps to the feet and spreads out.
#   BoneTex is only read with Load() (integer texels, no sampler, no filtering), as the contract says.
# Pixel: BaseColor x lerp(1, BruteTint, C5); melt darkens to x0.22 and roughness to 0.07 (wet); Glow emissive fades out with the melt.
# ASSUMPTION to confirm: T_Zombie_*_ORMS = R occlusion, G roughness, B metallic, A specular (the usual packing).
import sys, unreal

DRY = '--dry-run' in sys.argv
TEMP = '--temp' in sys.argv
DST = '/Game/_i5tmpHorde' if TEMP else '/Game/CastleDefender/Horde'
ZT = '/Game/CastleDefender/Characters/Enemies/Zombie/AAA/'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SAVE = (lambda p: True) if (TEMP or DRY) else (lambda p: EAL.save_asset(p, only_if_is_dirty=False))
log = ['horde material build' + (' (DRY RUN)' if DRY else '') + (' (TEMP, not saved)' if TEMP else '')]


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


def E(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e


def link(a, out, b, inp):
    if not MEL.connect_material_expressions(a, out, b, inp): log.append('LINK FAILED %s.%s -> %s.%s' % (a.get_name(), out, b.get_name(), inp))


def custom(m, code, inputs, otype, x, y, desc):
    e = E(m, unreal.MaterialExpressionCustom, x, y, code=code, output_type=otype, description=desc)
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def param(m, cls, name, x, y, **props):
    return E(m, cls, x, y, parameter_name=name, **props)


QR = '#define QR(q, v) ((v) + 2.0 * cross((q).xyz, cross((q).xyz, (v)) + (q).w * (v)))\n'
FRAME = '''float nf = max(C1, 1.0);
float f = max(T - C2, 0.0) * abs(C3);
float nx;
if (C3 >= 0.0) { f = fmod(f, nf); nx = fmod(floor(f) + 1.0, nf); }
else { f = min(f, nf - 1.0); nx = min(floor(f) + 1.0, nf - 1.0); }
int r0 = (int)(C0 + floor(f)); int r1 = (int)(C0 + nx); float a = frac(f);
float4 bi = float4(B01, B23); float4 bw = float4(W01, W23);
float3 p0 = 0, p1 = 0, n0 = 0, n1 = 0;
[unroll] for (int k = 0; k < 4; k++) {
  float w = bw[k];
  if (w > 0.0) {
    int b = (int)(bi[k] + 0.5);
    float4 q0 = BoneTex.Load(int3(2 * b, r0, 0)); float3 t0 = BoneTex.Load(int3(2 * b + 1, r0, 0)).xyz;
    float4 q1 = BoneTex.Load(int3(2 * b, r1, 0)); float3 t1 = BoneTex.Load(int3(2 * b + 1, r1, 0)).xyz;
    p0 += w * (QR(q0, P) + t0); p1 += w * (QR(q1, P) + t1);
    n0 += w * QR(q0, N); n1 += w * QR(q1, N);
  }
}
float3 pos = lerp(p0, p1, a); float3 nrm = normalize(lerp(n0, n1, a) + 1e-5);
float m = C4 > 0.0 ? smoothstep(0.0, 1.0, saturate((T - C4) / 1.6)) : 0.0;
pos.z *= 1.0 - 0.88 * m;
pos.xy *= 1.0 + 0.55 * m * saturate(1.0 - pos.z / 60.0);
nrm = normalize(lerp(nrm, float3(0, 0, 1), 0.8 * m));
'''


def build_zombie():
    m, made = fresh('M_CD_HordeZombie', unreal.Material, unreal.MaterialFactoryNew())
    if not m: return
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_SURFACE'))
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_OPAQUE'))
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_DEFAULT_LIT'))
    m.set_editor_property('tangent_space_normal', False)
    m.set_editor_property('used_with_instanced_static_meshes', True)
    for k in ('used_with_nanite',):
        try: m.set_editor_property(k, False)
        except Exception: pass
    # ---- vertex inputs
    bone = param(m, unreal.MaterialExpressionTextureObjectParameter, 'BoneTex', -2200, -400)
    P = E(m, unreal.MaterialExpressionPreSkinnedPosition, -2200, -250)
    N = E(m, unreal.MaterialExpressionPreSkinnedNormal, -2200, -170)
    uvs = [E(m, unreal.MaterialExpressionTextureCoordinate, -2200, -90 + 70 * i, coordinate_index=i + 1) for i in range(4)]
    cd = [E(m, unreal.MaterialExpressionPerInstanceCustomData, -2200, 200 + 70 * i, data_index=i) for i in range(6)]
    T = E(m, unreal.MaterialExpressionTime, -2200, 650)
    ins = ['BoneTex', 'P', 'N', 'B01', 'B23', 'W01', 'W23', 'C0', 'C1', 'C2', 'C3', 'C4', 'T']
    srcs = [bone, P, N] + uvs + cd[:5] + [T]
    offs = custom(m, QR + FRAME + 'return pos - P;', ins, unreal.CustomMaterialOutputType.CMOT_FLOAT3, -1500, -300, 'Horde skin: position offset (mesh space)')
    nrmc = custom(m, QR + FRAME + 'return nrm;', ins, unreal.CustomMaterialOutputType.CMOT_FLOAT3, -1500, 100, 'Horde skin: normal (mesh space)')
    for c in (offs, nrmc):
        for nm, s in zip(ins, srcs):
            link(s, '', c, nm)
    # mesh space -> world: the instance transform (Local space includes it for ISM)
    tw = E(m, unreal.MaterialExpressionTransform, -1100, -300, transform_source_type=enum(unreal.MaterialVectorCoordTransformSource, 'TRANSFORMSOURCE_LOCAL'),
           transform_type=enum(unreal.MaterialVectorCoordTransform, 'TRANSFORM_WORLD'))
    link(offs, '', tw, '')
    MEL.connect_material_property(tw, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    tn = E(m, unreal.MaterialExpressionTransform, -1100, 100, transform_source_type=enum(unreal.MaterialVectorCoordTransformSource, 'TRANSFORMSOURCE_LOCAL'),
           transform_type=enum(unreal.MaterialVectorCoordTransform, 'TRANSFORM_WORLD'))
    link(nrmc, '', tn, '')
    vi = E(m, unreal.MaterialExpressionVertexInterpolator, -850, 100)
    link(tn, '', vi, '')
    MEL.connect_material_property(vi, '', unreal.MaterialProperty.MP_NORMAL)
    # ---- pixel
    S = unreal.MaterialExpressionTextureSampleParameter2D
    bc = param(m, S, 'BaseColor', -1500, 500, texture=unreal.load_asset(ZT + 'T_Zombie_A_BC'))
    orms = param(m, S, 'ORMS', -1500, 800, texture=unreal.load_asset(ZT + 'T_Zombie_A_ORMS'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    glow = param(m, S, 'Glow', -1500, 1100, texture=unreal.load_asset(ZT + 'T_Zombie_Glow'))
    tint = param(m, unreal.MaterialExpressionVectorParameter, 'BruteTint', -1500, 1400, default_value=unreal.LinearColor(0.78, 0.62, 0.55, 1))
    gs = param(m, unreal.MaterialExpressionScalarParameter, 'GlowStrength', -1500, 1550, default_value=1.0)
    pc4 = E(m, unreal.MaterialExpressionPerInstanceCustomData, -1500, 1650, data_index=4)
    pc5 = E(m, unreal.MaterialExpressionPerInstanceCustomData, -1500, 1720, data_index=5)
    pt = E(m, unreal.MaterialExpressionTime, -1500, 1790)
    def pixel(code, x, y, desc):
        c = custom(m, '''float m = C4 > 0.0 ? smoothstep(0.0, 1.0, saturate((T - C4) / 1.6)) : 0.0;\n''' + code,
                   ['BC', 'ORMS', 'Glow', 'Tint', 'GlowStrength', 'C4', 'C5', 'T'], unreal.CustomMaterialOutputType.CMOT_FLOAT3, x, y, desc)
        for nm, s, o in (('BC', bc, 'RGB'), ('ORMS', orms, 'RGBA'), ('Glow', glow, 'RGB'), ('Tint', tint, 'RGB'), ('GlowStrength', gs, ''), ('C4', pc4, ''), ('C5', pc5, ''), ('T', pt, '')):
            link(s, o, c, nm)
        return c
    pc = pixel('float3 col = BC * lerp(float3(1, 1, 1), Tint, saturate(C5));\nreturn lerp(col, col * 0.22, m);', -900, 500, 'Horde base colour (brute tint, melt darkening)')
    pr = pixel('return float3(lerp(ORMS.g, 0.07, m), ORMS.b, ORMS.r);', -900, 800, 'Horde rough / metal / AO (melt = wet)')
    pe = pixel('return Glow * GlowStrength * (1.0 - m);', -900, 1100, 'Horde glow (fades with the melt)')
    MEL.connect_material_property(pc, '', unreal.MaterialProperty.MP_BASE_COLOR)
    for out, prop in (('R', 'MP_ROUGHNESS'), ('G', 'MP_METALLIC'), ('B', 'MP_AMBIENT_OCCLUSION')):
        msk = E(m, unreal.MaterialExpressionComponentMask, -650, 800, r=out == 'R', g=out == 'G', b=out == 'B', a=False)
        link(pr, '', msk, ''); MEL.connect_material_property(msk, '', getattr(unreal.MaterialProperty, prop))
    MEL.connect_material_property(pe, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); SAVE(DST + '/M_CD_HordeZombie')
    for n, look in (('MI_CD_Horde_A', 'A'), ('MI_CD_Horde_B', 'B')):
        mi, _ = fresh(n, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not mi: continue
        MEL.set_material_instance_parent(mi, m)
        MEL.set_material_instance_texture_parameter_value(mi, 'BaseColor', unreal.load_asset(ZT + 'T_Zombie_%s_BC' % look))
        MEL.set_material_instance_texture_parameter_value(mi, 'ORMS', unreal.load_asset(ZT + 'T_Zombie_%s_ORMS' % look))
        SAVE(DST + '/' + n)


def build_pool():
    m, made = fresh('M_CD_MeltPool', unreal.Material, unreal.MaterialFactoryNew())
    if not m: return
    if not made: MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_DEFERRED_DECAL'))
    m.set_editor_property('blend_mode', enum(unreal.BlendMode, 'BLEND_TRANSLUCENT'))
    try: m.set_editor_property('decal_blend_mode', enum(unreal.DecalBlendMode, 'DBM_DBUFFER_COLOR_NORMAL_ROUGHNESS', 'DBM_TRANSLUCENT'))
    except Exception as ex: log.append('decal_blend_mode not set (%s): 5.8 picks it from the outputs' % ex)
    uv = E(m, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    life = E(m, unreal.MaterialExpressionDecalLifetimeOpacity, -1100, 200)
    seed = param(m, unreal.MaterialExpressionScalarParameter, 'Seed', -1100, 300, default_value=0.0)
    # irregular round pool: radius wobbles with angle (3 lobes + noise), a thick dark core, a thinner wet rim that spread further
    mask = custom(m, '''float2 p = (UV - 0.5) * 2.0; float r = length(p); float ang = atan2(p.y, p.x);
float h = frac(sin(dot(floor((p + Seed) * 9.0), float2(127.1, 311.7))) * 43758.5453);
float edge = 0.72 + 0.10 * sin(ang * 3.0 + Seed * 6.0) + 0.07 * sin(ang * 7.0 + Seed * 2.0) + 0.04 * (h - 0.5);
return saturate((1.0 - smoothstep(edge * 0.82, edge, r)) * Life);''', ['UV', 'Life', 'Seed'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -700, 100, 'Melt pool mask x lifetime')
    for nm, s in (('UV', uv), ('Life', life), ('Seed', seed)): link(s, '', mask, nm)
    core = custom(m, '''float2 p = (UV - 0.5) * 2.0; float r = length(p);
return float3(lerp(float3(0.030, 0.028, 0.018), float3(0.060, 0.050, 0.030), smoothstep(0.2, 0.8, r)));''', ['UV'], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -700, -150, 'Melt pool colour: dark wet rot')
    link(uv, '', core, 'UV')
    rough = custom(m, 'float r = length((UV - 0.5) * 2.0); return lerp(0.04, 0.30, smoothstep(0.5, 0.9, r));', ['UV'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -700, 300, 'Melt pool roughness (wet)')
    link(uv, '', rough, 'UV')
    MEL.connect_material_property(core, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); SAVE(DST + '/M_CD_MeltPool')


if not DRY and not EAL.does_directory_exist(DST): EAL.make_directory(DST)
for t in ('T_Zombie_A_BC', 'T_Zombie_A_ORMS', 'T_Zombie_B_BC', 'T_Zombie_B_ORMS', 'T_Zombie_Glow'):
    if not EAL.does_asset_exist(ZT + t): log.append('MISSING texture ' + ZT + t)
build_zombie()
build_pool()
print('\n'.join(log))
