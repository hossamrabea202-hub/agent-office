# #337 blood splat decals, editor import (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run. NEW assets only:
# no live decal material, no DBuffer / project setting is touched (owner rule).
#   py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py" --dry-run
#   py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py"
# Makes in /Game/CastleDefender/VFX/Blood337:
#   T_BloodSplat_337_BC (sRGB, alpha = opacity), _N (normal), _M (masks, linear: R thickness, G opacity, B dry rim)
#   M_BloodDecal_337   deferred decal, Translucent blend (GBuffer, works with or without DBuffer). 8 splats in a 4 x 2
#                      atlas picked by Index (0-7). It dries by itself from SpawnT (set to the game time at spawn): over
#                      DryTime (30 s) fresh wet (rough 0.08, dark maroon) -> dried (rough 0.7, brown 45,30,20, flatter), then
#                      fades out over FadeTime (3 s). Specular 0.28 (blood IOR 1.35). No emissive.
#   MI_BloodDecal_337  the instance the gore Blueprint will spawn (Index / Dry / Fade set per decal at runtime)
import os, sys, unreal

DRY = '--dry-run' in sys.argv
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\assets\adjustedfilm\Blood337'
DST = '/Game/CastleDefender/VFX/Blood337'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
log = ['#337 blood decals import' + (' (DRY RUN, nothing written)' if DRY else '')]
TEX = [('T_BloodSplat_337_BC', True, unreal.TextureCompressionSettings.TC_DEFAULT),
       ('T_BloodSplat_337_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP),
       ('T_BloodSplat_337_M', False, unreal.TextureCompressionSettings.TC_MASKS)]
for n, srgb, comp in TEX:
    f = os.path.join(HERE, n + '.png'); log.append('import %s (%s)' % (n, 'ok' if os.path.exists(f) else 'MISSING ' + f))
    if DRY or not os.path.exists(f): continue
    t = unreal.AssetImportTask()
    for k, v in (('filename', f), ('destination_path', DST), ('automated', True), ('save', True), ('replace_existing', True)): t.set_editor_property(k, v)
    AT.import_asset_tasks([t])
    tx = unreal.load_asset(DST + '/' + n); tx.set_editor_property('srgb', srgb); tx.set_editor_property('compression_settings', comp)
    tx.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD); tx.set_editor_property('max_texture_size', 2048)
    EAL.save_asset(DST + '/' + n)

M = DST + '/M_BloodDecal_337'
log.append(('rebuild ' if EAL.does_asset_exist(M) else 'create ') + M)
if not DRY:
    m = unreal.load_asset(M) if EAL.does_asset_exist(M) else AT.create_asset('M_BloodDecal_337', DST, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    m.set_editor_property('material_domain', unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    def P(name, v, x, y):
        e = E(unreal.MaterialExpressionScalarParameter, x, y); e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', v); return e
    def C(v, x, y): e = E(unreal.MaterialExpressionConstant, x, y); e.set_editor_property('r', v); return e
    def C3(rgb, x, y): e = E(unreal.MaterialExpressionConstant3Vector, x, y); e.set_editor_property('constant', unreal.LinearColor(*rgb, 1)); return e
    def op(cls, a, b_, x, y, ai='', bi=''):
        e = E(cls, x, y); MEL.connect_material_expressions(a, ai, e, 'A'); MEL.connect_material_expressions(b_, bi, e, 'B'); return e
    def lerp(a, b_, al, x, y, ali=''):
        e = E(unreal.MaterialExpressionLinearInterpolate, x, y)
        MEL.connect_material_expressions(a, '', e, 'A'); MEL.connect_material_expressions(b_, '', e, 'B'); MEL.connect_material_expressions(al, ali, e, 'Alpha'); return e
    # atlas UV: (uv + (Index mod 4, floor(Index / 4))) / (4, 2)
    idx = P('Index', 0.0, -1800, 0)
    col = op(unreal.MaterialExpressionFmod, idx, C(4.0, -1800, 100), -1600, 0)
    row = E(unreal.MaterialExpressionFloor, -1450, 150); MEL.connect_material_expressions(op(unreal.MaterialExpressionDivide, idx, C(4.0, -1800, 200), -1600, 150), '', row, '')
    cell = op(unreal.MaterialExpressionAppendVector, col, row, -1300, 50)
    uv = op(unreal.MaterialExpressionAdd, E(unreal.MaterialExpressionTextureCoordinate, -1300, -100), cell, -1150, 0)
    k42 = E(unreal.MaterialExpressionConstant2Vector, -1150, 150); k42.set_editor_property('r', 4.0); k42.set_editor_property('g', 2.0)
    auv = op(unreal.MaterialExpressionDivide, uv, k42, -1000, 0)
    def tex(name, st, x, y):
        e = E(unreal.MaterialExpressionTextureSample, x, y); e.set_editor_property('texture', unreal.load_asset(DST + '/' + name))
        e.set_editor_property('sampler_type', st); MEL.connect_material_expressions(auv, '', e, 'UVs'); return e
    bc = tex('T_BloodSplat_337_BC', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -800, -300)
    nm = tex('T_BloodSplat_337_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -800, 300)
    mk = tex('T_BloodSplat_337_M', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -800, 0)
    # drying runs by itself from the spawn time: Dry = (Time - SpawnT) / DryTime, Fade = (Time - SpawnT - DryTime) / FadeTime
    age = op(unreal.MaterialExpressionSubtract, E(unreal.MaterialExpressionTime, -1300, 600), P('SpawnT', 0.0, -1300, 700), -1150, 650)
    dry = E(unreal.MaterialExpressionSaturate, -850, 600)
    dryt = P('DryTime', 30.0, -1150, 750)
    MEL.connect_material_expressions(op(unreal.MaterialExpressionDivide, age, dryt, -1000, 600), '', dry, '')
    fade = E(unreal.MaterialExpressionSaturate, -850, 750)
    MEL.connect_material_expressions(op(unreal.MaterialExpressionDivide, op(unreal.MaterialExpressionSubtract, age, dryt, -1000, 800),
                                        P('FadeTime', 3.0, -1150, 950), -900, 850), '', fade, '')
    # colour: wet maroon -> dried brown (45,30,20 sRGB = 0.026, 0.013, 0.007 linear)
    dcol = lerp(bc, C3((0.026, 0.013, 0.007), -500, -200), op(unreal.MaterialExpressionMultiply, dry, C(0.75, -600, -100), -450, -100), -300, -300)
    MEL.connect_material_property(dcol, '', unreal.MaterialProperty.MP_BASE_COLOR)
    # roughness: thin film 0.16 / thick 0.08 when wet -> 0.7 dried
    wet_r = lerp(C(0.16, -500, 50), C(0.08, -500, 100), mk, -300, 50, ali='R')
    MEL.connect_material_property(lerp(wet_r, C(0.7, -300, 150), dry, -150, 50), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(C(0.28, -150, 200), '', unreal.MaterialProperty.MP_SPECULAR)
    MEL.connect_material_property(C(0.0, -150, 250), '', unreal.MaterialProperty.MP_METALLIC)
    flat = C3((0.0, 0.0, 1.0), -500, 400)
    MEL.connect_material_property(lerp(nm, flat, op(unreal.MaterialExpressionMultiply, dry, C(0.6, -600, 500), -450, 500), -150, 350), '', unreal.MaterialProperty.MP_NORMAL)
    oneminus = E(unreal.MaterialExpressionOneMinus, -500, 700); MEL.connect_material_expressions(fade, '', oneminus, '')
    MEL.connect_material_property(op(unreal.MaterialExpressionMultiply, bc, oneminus, -150, 650, ai='A'), '', unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(M)
    MI = DST + '/MI_BloodDecal_337'
    if not EAL.does_asset_exist(MI):
        f = unreal.MaterialInstanceConstantFactoryNew(); mi = AT.create_asset('MI_BloodDecal_337', DST, unreal.MaterialInstanceConstant, f)
        MEL.set_material_instance_parent(mi, m); EAL.save_asset(MI)
    log.append('made M_BloodDecal_337 + MI_BloodDecal_337')

# ---- wound caps (caps/): SM_WoundCap_<Part>_337 + T_WoundCap_<Part>_337_BC/ORM/N, one master M_WoundCap_337 + an MI per cap.
# Cap faces +X, pivot in the cut centre (attach to the cut bone, no rotation). No collision (it rides on the limb / stump).
CAPS = ('Forearm', 'UpperArm', 'Calf', 'Neck')
CD = DST + '/WoundCaps'
CM = CD + '/M_WoundCap_337'
for part in CAPS:
    log.append('cap ' + part + ('' if os.path.exists(os.path.join(HERE, 'caps', 'SM_WoundCap_%s_337.fbx' % part)) else ' (MISSING fbx)'))
if not DRY:
    for part in CAPS:
        for suf, srgb, comp in (('BC', True, unreal.TextureCompressionSettings.TC_DEFAULT), ('ORM', False, unreal.TextureCompressionSettings.TC_MASKS),
                                ('N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)):
            n = 'T_WoundCap_%s_337_%s' % (part, suf); t = unreal.AssetImportTask()
            for k, v in (('filename', os.path.join(HERE, 'caps', n + '.png')), ('destination_path', CD), ('automated', True), ('save', True), ('replace_existing', True)):
                t.set_editor_property(k, v)
            AT.import_asset_tasks([t])
            tx = unreal.load_asset(CD + '/' + n); tx.set_editor_property('srgb', srgb); tx.set_editor_property('compression_settings', comp)
            tx.set_editor_property('max_texture_size', 512); EAL.save_asset(CD + '/' + n)
    m = unreal.load_asset(CM) if EAL.does_asset_exist(CM) else AT.create_asset('M_WoundCap_337', CD, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    def tp(name, st, x, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property('parameter_name', name); e.set_editor_property('sampler_type', st)
        e.set_editor_property('texture', unreal.load_asset(CD + '/T_WoundCap_Forearm_337_' + name[:-3])); return e
    bc = tp('BCTex', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -600, -200)
    orm = tp('ORMTex', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -600, 100)
    nm = tp('NTex', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -600, 400)
    MEL.connect_material_property(bc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(nm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(CM)
    for part in CAPS:
        mi_p = CD + '/MI_WoundCap_%s_337' % part
        mi = unreal.load_asset(mi_p) if EAL.does_asset_exist(mi_p) else AT.create_asset('MI_WoundCap_%s_337' % part, CD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, m)
        for pn, suf in (('BCTex', 'BC'), ('ORMTex', 'ORM'), ('NTex', 'N')):
            MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset(CD + '/T_WoundCap_%s_337_%s' % (part, suf)))
        EAL.save_asset(mi_p)
        t = unreal.AssetImportTask()
        for k, v in (('filename', os.path.join(HERE, 'caps', 'SM_WoundCap_%s_337.fbx' % part)), ('destination_path', CD), ('automated', True), ('save', True), ('replace_existing', True)):
            t.set_editor_property(k, v)
        o = unreal.FbxImportUI(); o.set_editor_property('import_mesh', True); o.set_editor_property('import_as_skeletal', False)
        o.set_editor_property('import_materials', False); o.set_editor_property('import_textures', False)
        o.static_mesh_import_data.set_editor_property('auto_generate_collision', False)
        t.set_editor_property('options', o); AT.import_asset_tasks([t])
        sm = unreal.load_asset(CD + '/SM_WoundCap_%s_337' % part)
        if sm: sm.set_material(0, mi); EAL.save_asset(CD + '/SM_WoundCap_%s_337' % part)
    log.append('made 4 wound caps + M_WoundCap_337 + 4 MIs in ' + CD)

# ---- particle materials for the Niagara blood (RESEARCH §3.1): lit, never emissive
#   M_BloodParticle_337  droplets / strands: Masked, Default Lit, a fake sphere normal from the sprite UV so each droplet
#                        gets one sharp highlight; colour from Particle Color (Niagara sets 50,16,10 wet); rough 0.08,
#                        specular 0.28; dithered fade with Particle Color alpha (last 20 % of life)
#   M_BloodMist_337      mist: Translucent, Volumetric Non-Directional lighting (cheap), soft disc x Particle Color alpha x
#                        MistOpacity (0.15), depth fade 20 cm
PM, MM = DST + '/M_BloodParticle_337', DST + '/M_BloodMist_337'
log.append('particle materials: M_BloodParticle_337, M_BloodMist_337')
if not DRY:
    for path, name in ((PM, 'M_BloodParticle_337'), (MM, 'M_BloodMist_337')):
        m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew())
        MEL.delete_all_material_expressions(m)
        m.set_editor_property('used_with_niagara_sprites', True); m.set_editor_property('used_with_niagara_ribbons', True)
        E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
        pc = E(unreal.MaterialExpressionParticleColor, -900, -200)
        uv = E(unreal.MaterialExpressionTextureCoordinate, -1300, 100)
        two = E(unreal.MaterialExpressionConstant, -1300, 250); two.set_editor_property('r', 2.0)
        one = E(unreal.MaterialExpressionConstant, -1300, 320); one.set_editor_property('r', 1.0)
        mul = E(unreal.MaterialExpressionMultiply, -1150, 100); MEL.connect_material_expressions(uv, '', mul, 'A'); MEL.connect_material_expressions(two, '', mul, 'B')
        xy = E(unreal.MaterialExpressionSubtract, -1000, 100); MEL.connect_material_expressions(mul, '', xy, 'A'); MEL.connect_material_expressions(one, '', xy, 'B')
        ln = E(unreal.MaterialExpressionLength, -850, 100); MEL.connect_material_expressions(xy, '', ln, '')
        disc = E(unreal.MaterialExpressionOneMinus, -700, 100); MEL.connect_material_expressions(ln, '', disc, '')     # 1 centre -> 0 rim
        if name == 'M_BloodParticle_337':
            m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
            dot = E(unreal.MaterialExpressionDotProduct, -850, 300); MEL.connect_material_expressions(xy, '', dot, 'A'); MEL.connect_material_expressions(xy, '', dot, 'B')
            om = E(unreal.MaterialExpressionOneMinus, -700, 300); MEL.connect_material_expressions(dot, '', om, '')
            sat = E(unreal.MaterialExpressionSaturate, -600, 300); MEL.connect_material_expressions(om, '', sat, '')
            zz = E(unreal.MaterialExpressionSquareRoot, -500, 300); MEL.connect_material_expressions(sat, '', zz, '')
            nrm = E(unreal.MaterialExpressionAppendVector, -350, 250); MEL.connect_material_expressions(xy, '', nrm, 'A'); MEL.connect_material_expressions(zz, '', nrm, 'B')
            MEL.connect_material_property(nrm, '', unreal.MaterialProperty.MP_NORMAL)
            MEL.connect_material_property(pc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
            r_ = E(unreal.MaterialExpressionConstant, -350, 450); r_.set_editor_property('r', 0.08); MEL.connect_material_property(r_, '', unreal.MaterialProperty.MP_ROUGHNESS)
            s_ = E(unreal.MaterialExpressionConstant, -350, 520); s_.set_editor_property('r', 0.28); MEL.connect_material_property(s_, '', unreal.MaterialProperty.MP_SPECULAR)
            dith = E(unreal.MaterialExpressionDitherTemporalAA, -500, 0); MEL.connect_material_expressions(pc, 'A', dith, '')
            mk = E(unreal.MaterialExpressionMultiply, -350, 0)
            st = E(unreal.MaterialExpressionStep, -500, 100); MEL.connect_material_expressions(disc, '', st, 'X')   # inside the disc
            MEL.connect_material_expressions(st, '', mk, 'A'); MEL.connect_material_expressions(dith, '', mk, 'B')
            MEL.connect_material_property(mk, '', unreal.MaterialProperty.MP_OPACITY_MASK)
        else:
            m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
            m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_VOLUMETRIC_NON_DIRECTIONAL)
            MEL.connect_material_property(pc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
            soft = E(unreal.MaterialExpressionSaturate, -550, 100); MEL.connect_material_expressions(disc, '', soft, '')
            po = E(unreal.MaterialExpressionScalarParameter, -550, 200); po.set_editor_property('parameter_name', 'MistOpacity'); po.set_editor_property('default_value', 0.15)
            a1 = E(unreal.MaterialExpressionMultiply, -400, 100); MEL.connect_material_expressions(soft, '', a1, 'A'); MEL.connect_material_expressions(pc, 'A', a1, 'B')
            a2 = E(unreal.MaterialExpressionMultiply, -300, 150); MEL.connect_material_expressions(a1, '', a2, 'A'); MEL.connect_material_expressions(po, '', a2, 'B')
            df = E(unreal.MaterialExpressionDepthFade, -200, 150); df.set_editor_property('fade_distance_default', 20.0); MEL.connect_material_expressions(a2, '', df, '')
            MEL.connect_material_property(df, '', unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(m); EAL.save_asset(path)

out ='\n'.join(log)
if not DRY: open(os.path.join(HERE, 'import_blood337.txt'), 'w').write(out)
unreal.log(out); print(out)
