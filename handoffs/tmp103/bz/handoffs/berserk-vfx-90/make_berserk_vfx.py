# #90 Berserk VFX (laptop2, 2026-10-29): a rage-fire take on CGHOW's "Character Ice Aura" Niagara technique.
# Run in the editor:  py "<repo>/handoffs/berserk-vfx-90/make_berserk_vfx.py"
# Imports the 4 textures and builds 4 materials in /Game/CastleDefender/VFX/Berserk (re-running rebuilds them):
#   M_BerserkAura    overlay material for the hero meshes: fresnel rim + world-space flames boiling upward, pulse
#   M_BerserkWisp    Niagara sprite: a flame tongue that burns away (erodes) as Particle Color alpha falls
#   M_BerserkEmber   Niagara sprite: hot ember dot (stretch it with velocity alignment)
#   M_BerserkGround  Niagara sprite facing up: the cracked burning ring at the hero's feet
# All additive + unlit. Scalar 'Intensity' (0..1) on M_BerserkAura is the fade the BP drives. NS_BerserkAura itself is
# built by hand from README.md (5.3's Python can't edit Niagara modules).
import os
import unreal

REPO = r''
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.path.join(REPO, 'handoffs', 'berserk-vfx-90')
DST = '/Game/CastleDefender/VFX/Berserk'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
X = unreal

# ---- textures ----
TEX = ('T_BerserkNoise', 'T_BerserkWisp', 'T_BerserkEmber', 'T_BerserkRing')
tasks = []
for t in TEX:
    k = unreal.AssetImportTask(); k.filename = os.path.join(SRC, 'textures', t + '.png'); k.destination_path = DST
    k.automated = True; k.save = True; k.replace_existing = True; tasks.append(k)
tools.import_asset_tasks(tasks)
for t in TEX:
    a = unreal.load_asset(DST + '/' + t); a.modify()
    a.set_editor_property('srgb', False); a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    if t in ('T_BerserkWisp', 'T_BerserkEmber', 'T_BerserkRing'):
        a.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); a.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    EAL.save_loaded_asset(a)
tex = lambda n: unreal.load_asset(DST + '/' + n)

# ---- helpers ----
def new_mat(name, niagara=False, skel=False):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)
    m = tools.create_asset(name, DST, X.Material, X.MaterialFactoryNew())
    m.set_editor_property('blend_mode', X.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model', X.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided', True)
    if niagara: m.set_editor_property('used_with_niagara_sprites', True)
    if skel: m.set_editor_property('used_with_skeletal_mesh', True)
    return m
class G:
    """tiny node-graph helper: each call returns the new expression; pins are (expr, output_name)."""
    def __init__(s, m): s.m, s.x, s.y = m, -1600, 0
    def n(s, cls, **props):
        e = MEL.create_material_expression(s.m, cls, s.x, s.y); s.y += 140
        if s.y > 1400: s.y, s.x = 0, s.x + 260
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(s, src, dst, pin, out=''):
        MEL.connect_material_expressions(src, out, dst, pin)
    def sp(s, name, v):
        return s.n(X.MaterialExpressionScalarParameter, parameter_name=name, default_value=v)
    def vp(s, name, r, g, b):
        return s.n(X.MaterialExpressionVectorParameter, parameter_name=name, default_value=X.LinearColor(r, g, b, 1))
    def k(s, v): return s.n(X.MaterialExpressionConstant, r=v)
    def op(s, cls, a, b, ao='', bo=''):
        e = s.n(cls)
        if isinstance(a, (int, float)): e.set_editor_property('const_a', a)
        else: s.c(a, e, 'A', ao)
        if isinstance(b, (int, float)): e.set_editor_property('const_b', b)
        else: s.c(b, e, 'B', bo)
        return e
    def mul(s, a, b, ao='', bo=''): return s.op(X.MaterialExpressionMultiply, a, b, ao, bo)
    def add(s, a, b, ao='', bo=''): return s.op(X.MaterialExpressionAdd, a, b, ao, bo)
    def sub(s, a, b, ao='', bo=''): return s.op(X.MaterialExpressionSubtract, a, b, ao, bo)
    def lerp(s, a, b, t, to=''):
        e = s.n(X.MaterialExpressionLinearInterpolate); s.c(a, e, 'A'); s.c(b, e, 'B'); s.c(t, e, 'Alpha', to); return e
    def sat(s, a, ao=''):
        e = s.n(X.MaterialExpressionSaturate); s.c(a, e, '', ao); return e
    def mask(s, a, r=False, g=False, b=False, al=False, ao=''):
        e = s.n(X.MaterialExpressionComponentMask, r=r, g=g, b=b, a=al); s.c(a, e, '', ao); return e
    def tex(s, t, uv=None, uvo=''):
        e = s.n(X.MaterialExpressionTextureSample, texture=t, sampler_type=X.MaterialSamplerType.SAMPLERTYPE_MASKS)
        if uv is not None: s.c(uv, e, 'UVs', uvo)
        return e
    def pan(s, uv, sx, sy):
        e = s.n(X.MaterialExpressionPanner, speed_x=sx, speed_y=sy); s.c(uv, e, 'Coordinate'); return e
    def app(s, a, b):
        e = s.n(X.MaterialExpressionAppendVector); s.c(a, e, 'A'); s.c(b, e, 'B'); return e
def done(m):
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name().split('.')[0])

# ---- M_BerserkAura: overlay on the hero ----
m = new_mat('M_BerserkAura', skel=True); g = G(m)
wp = g.n(X.MaterialExpressionWorldPosition)
uv = g.app(g.add(g.mask(wp, r=True), g.mask(wp, g=True)), g.mask(wp, b=True))
uv = g.mul(uv, g.sp('FlameScale', 0.006))
n1 = g.tex(tex('T_BerserkNoise'), g.pan(uv, 0.0, -0.55))
n2 = g.tex(tex('T_BerserkNoise'), g.pan(g.mul(uv, 0.45), 0.04, -0.22))
flames = g.sat(g.mul(g.mul(g.mask(n1, r=True, ao='RGB'), g.mask(n2, g=True, ao='RGB')), 2.6))
fr = g.n(X.MaterialExpressionFresnel, exponent=2.4, base_reflect_fraction=0.02)
fexp = g.sp('FresnelExp', 2.4); g.c(fexp, fr, 'ExponentIn')
shape = g.mul(fr, g.add(0.30, g.mul(flames, 1.7)))
tm = g.n(X.MaterialExpressionTime)
sn = g.n(X.MaterialExpressionSine, period=1.0); g.c(g.mul(tm, g.sp('PulseSpeed', 0.9)), sn, '')
pulse = g.add(0.85, g.mul(sn, 0.15))
col = g.lerp(g.vp('ColorDeep', 0.85, 0.04, 0.01), g.vp('ColorHot', 1.0, 0.42, 0.05), flames)
em = g.mul(g.mul(g.mul(col, shape), pulse), g.mul(g.sp('Glow', 14.0), g.sp('Intensity', 1.0)))
MEL.connect_material_property(em, '', X.MaterialProperty.MP_EMISSIVE_COLOR)
done(m)

# ---- M_BerserkWisp: flame tongue that erodes as the particle ages ----
m = new_mat('M_BerserkWisp', niagara=True); g = G(m)
pc = g.n(X.MaterialExpressionParticleColor)
t = g.tex(tex('T_BerserkWisp'))
n = g.tex(tex('T_BerserkNoise'), g.pan(g.mul(g.n(X.MaterialExpressionTextureCoordinate), 0.6), 0.0, -0.8))
body = g.mul(g.mask(t, r=True, ao='RGB'), g.add(g.mask(t, g=True, ao='RGB'), g.mul(g.mask(n, r=True, ao='RGB'), 0.5)))
vis = g.sat(g.mul(g.sub(body, g.sub(1.0, g.mask(pc, al=True))), 5.0))
hot = g.lerp(g.vp('ColorDeep', 0.9, 0.06, 0.01), g.vp('ColorHot', 1.0, 0.55, 0.12), g.sat(g.mul(body, 1.6)))
em = g.mul(g.mul(g.mul(hot, g.mask(pc, r=True, g=True, b=True)), vis), g.sp('Glow', 6.0))
MEL.connect_material_property(em, '', X.MaterialProperty.MP_EMISSIVE_COLOR)
done(m)

# ---- M_BerserkEmber ----
m = new_mat('M_BerserkEmber', niagara=True); g = G(m)
pc = g.n(X.MaterialExpressionParticleColor)
t = g.tex(tex('T_BerserkEmber'))
em = g.mul(g.mul(g.mul(g.mask(t, r=True, ao='RGB'), g.mask(pc, r=True, g=True, b=True)), g.mask(pc, al=True)), g.sp('Glow', 18.0))
MEL.connect_material_property(em, '', X.MaterialProperty.MP_EMISSIVE_COLOR)
done(m)

# ---- M_BerserkGround: cracked burning ring, the cracks flicker with panning noise ----
m = new_mat('M_BerserkGround', niagara=True); g = G(m)
pc = g.n(X.MaterialExpressionParticleColor)
t = g.tex(tex('T_BerserkRing'))
n = g.tex(tex('T_BerserkNoise'), g.pan(g.mul(g.n(X.MaterialExpressionTextureCoordinate), 1.5), 0.05, 0.07))
flick = g.add(0.45, g.mul(g.mask(n, g=True, ao='RGB'), 1.1))
lit = g.add(g.mul(g.mask(t, r=True, ao='RGB'), flick), g.mul(g.mask(t, g=True, ao='RGB'), 0.35))
col = g.lerp(g.vp('ColorDeep', 0.85, 0.05, 0.01), g.vp('ColorHot', 1.0, 0.5, 0.1), g.mask(t, r=True, ao='RGB'))
em = g.mul(g.mul(g.mul(col, lit), g.mul(g.mask(pc, r=True, g=True, b=True), g.mask(pc, al=True))), g.sp('Glow', 8.0))
MEL.connect_material_property(em, '', X.MaterialProperty.MP_EMISSIVE_COLOR)
done(m)

unreal.log('#90 Berserk VFX materials built in ' + DST + ' (next: NS_BerserkAura by hand, README.md)')
