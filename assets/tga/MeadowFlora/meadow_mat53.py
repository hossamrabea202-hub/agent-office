# Shared material builder for the meadow flora (#352 / #356 fix, TGA 2026-10-31). Used by import_flora_meadow_ue.py and
# fix_wind_53.py. UE 5.3-safe: shading model enum MSM_TWO_SIDED_FOLIAGE, used_with_instanced_static_meshes, and the wind
# reaches World Position Offset by whichever route this editor's Python exposes:
#   A) MaterialProperty.MP_WORLD_POSITION_OFFSET (any enum name containing WORLD_POSITION), else
#   B) use_material_attributes + MakeMaterialAttributes -> MP_MATERIAL_ATTRIBUTES, else
#   C) everything is built and a node comment 'CONNECT ME -> World Position Offset' marks the one drag left (logged loudly).
import unreal

EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
C = MEL.connect_material_expressions
MP = unreal.MaterialProperty
def _prop(*keys):
    for n in dir(MP):
        if n.startswith('MP_') and all(k in n for k in keys): return getattr(MP, n)
    return None
def _shading():
    for n in ('MSM_TWO_SIDED_FOLIAGE', 'MSM_TWOSIDED_FOLIAGE'):
        if hasattr(unreal.MaterialShadingModel, n): return getattr(unreal.MaterialShadingModel, n)
    raise RuntimeError('no two-sided foliage shading model enum in this build')
def build(dst, name, atlas, masked, log):
    """creates dst/name (opaque or masked two-sided foliage with wind); returns (material, route letter)"""
    tools = unreal.AssetToolsHelpers.get_asset_tools(); path = '%s/%s' % (dst, name)
    if EAL.does_asset_exist(path): return unreal.load_asset(path), 'existing'
    m = tools.create_asset(name, dst, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', _shading()); m.set_editor_property('two_sided', True)
    m.set_editor_property('used_with_instanced_static_meshes', True)
    if masked:
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED); m.set_editor_property('opacity_mask_clip_value', 0.4)
    def P(cls, pname, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', pname)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    def E(cls, x, y): return MEL.create_material_expression(m, cls, x, y)
    def S(pname, v, x, y): e = P(unreal.MaterialExpressionScalarParameter, pname, x, y); e.set_editor_property('default_value', v); return e
    bc = P(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColorTex', -1100, -300, '%s/%s_BC' % (dst, atlas))
    orm = P(unreal.MaterialExpressionTextureSampleParameter2D, 'ORMTex', -1100, 50, '%s/%s_ORM' % (dst, atlas), unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = P(unreal.MaterialExpressionTextureSampleParameter2D, 'NormalTex', -1100, 380, '%s/%s_N' % (dst, atlas), unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = P(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -520); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    col = E(unreal.MaterialExpressionMultiply, -800, -380); C(bc, 'RGB', col, 'A'); C(tint, '', col, 'B')
    ssa = S('SubsurfaceAmount', 0.6, -800, -200); ssc = E(unreal.MaterialExpressionMultiply, -550, -250); C(col, '', ssc, 'A'); C(ssa, '', ssc, 'B')
    # wind: SimpleGrassWind, weight = (1 - R)^2, + flutter = normal * sin(time * speed + G) * B * amount
    vc = E(unreal.MaterialExpressionVertexColor, -1100, 800)
    om = E(unreal.MaterialExpressionOneMinus, -850, 760); C(vc, 'R', om, '')
    wt = E(unreal.MaterialExpressionMultiply, -650, 760); C(om, '', wt, 'A'); C(om, '', wt, 'B')
    tm = E(unreal.MaterialExpressionTime, -1100, 1000); fs = S('FlutterSpeed', 2.5, -1100, 1080)
    ts = E(unreal.MaterialExpressionMultiply, -850, 1000); C(tm, '', ts, 'A'); C(fs, '', ts, 'B')
    ph = E(unreal.MaterialExpressionAdd, -650, 1000); C(ts, '', ph, 'A'); C(vc, 'G', ph, 'B')
    sn = E(unreal.MaterialExpressionSine, -500, 1000); C(ph, '', sn, '')
    fa = S('FlutterAmount', 0.8, -500, 1120)
    f1 = E(unreal.MaterialExpressionMultiply, -350, 1000); C(sn, '', f1, 'A'); C(vc, 'B', f1, 'B')
    f2 = E(unreal.MaterialExpressionMultiply, -220, 1060); C(f1, '', f2, 'A'); C(fa, '', f2, 'B')
    vn = E(unreal.MaterialExpressionVertexNormalWS, -350, 1200)
    f3 = E(unreal.MaterialExpressionMultiply, -100, 1100); C(f2, '', f3, 'A'); C(vn, '', f3, 'B')
    wind = E(unreal.MaterialExpressionMaterialFunctionCall, -100, 800)
    wind.set_editor_property('material_function', unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind'))
    wi = S('WindIntensity', 0.25, -500, 640); ws = S('WindSpeed', 0.15, -500, 700)
    C(wi, '', wind, 'WindIntensity'); C(wt, '', wind, 'WindWeight'); C(ws, '', wind, 'WindSpeed'); C(f3, '', wind, 'AdditionalWPO')
    outs = [('BaseColor', col, '', 'BASE_COLOR'), ('SubsurfaceColor', ssc, '', 'SUBSURFACE_COLOR'), ('Roughness', orm, 'G', 'ROUGHNESS'),
            ('AmbientOcclusion', orm, 'R', 'AMBIENT_OCCLUSION'), ('Normal', nrm, 'RGB', 'NORMAL')] + ([('OpacityMask', bc, 'A', 'OPACITY_MASK')] if masked else [])
    wpo, attrs = _prop('WORLD', 'POSITION'), _prop('MATERIAL', 'ATTRIBUTES')
    if wpo is not None:                                                         # route A
        route = 'A'
        for _, e, pin, key in outs: MEL.connect_material_property(e, pin, _prop(*key.split('_')))
        MEL.connect_material_property(wind, '', wpo)
    elif attrs is not None:                                                     # route B
        route = 'B'; m.set_editor_property('use_material_attributes', True)
        mma = E(unreal.MaterialExpressionMakeMaterialAttributes, 250, 300)
        for pin_in, e, pin, _ in outs + [('WorldPositionOffset', wind, '', '')]:
            if not (C(e, pin, mma, pin_in) or C(e, pin, mma, ' '.join(_split(pin_in)))): log('WARNING could not wire %s into MakeMaterialAttributes' % pin_in)
        MEL.connect_material_property(mma, '', attrs)
    else:                                                                       # route C
        route = 'C'
        for _, e, pin, key in outs: MEL.connect_material_property(e, pin, _prop(*key.split('_')))
        cm = E(unreal.MaterialExpressionComment, -120, 760); cm.set_editor_property('text', 'CONNECT ME -> World Position Offset (SimpleGrassWind output)')
        log('MANUAL STEP %s: drag the SimpleGrassWind output to World Position Offset (one wire), then Apply' % name)
    MEL.recompile_material(m); EAL.save_asset(path); return m, route
def _split(s):
    out, w = [], ''
    for ch in s:
        if ch.isupper() and w: out.append(w); w = ch
        else: w += ch
    return out + [w]
