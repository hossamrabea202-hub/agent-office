# #337 blood splat decals, editor import (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run. NEW assets only:
# no live decal material, no DBuffer / project setting is touched (owner rule).
#   py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py" --dry-run
#   py "<repo>/assets/adjustedfilm/Blood337/import_blood337_ue.py"
# Makes in /Game/CastleDefender/VFX/Blood337:
#   T_BloodSplat_337_BC (sRGB, alpha = opacity), _N (normal), _M (masks, linear: R thickness, G opacity, B dry rim)
#   M_BloodDecal_337   deferred decal, Translucent blend (GBuffer, works with or without DBuffer). 8 splats in a 4 x 2
#                      atlas picked by Index (0-7). Dry 0 -> 1 = fresh wet (rough 0.08, dark maroon) -> dried (rough 0.7,
#                      brown 45,30,20, flatter); Fade 0 -> 1 = gone. Specular 0.28 (blood IOR 1.35). No emissive.
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
    dry = P('Dry', 0.0, -800, 600); fade = P('Fade', 0.0, -800, 700)
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

out ='\n'.join(log)
if not DRY: open(os.path.join(HERE, 'import_blood337.txt'), 'w').write(out)
unreal.log(out); print(out)
