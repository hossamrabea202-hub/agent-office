# #169 stage 1: the realm bubble material, rebuilt. Run in the UE 5.3 editor:  py "<repo>/handoffs/realm-169/make_realm_bubble.py"
# Makes /Game/CastleDefender/Realm/M_RealmBubble2 (+ MI_RealmBubble2) for SM_RealmDome (assets/laptop2/RealmKit):
#  - translucent, unlit, two-sided, depth-tested, no shadow: a purple haze that is readable day and night
#  - fresnel rim (thicker at grazing angles, like a soap film seen edge-on) with slow wave distortion along the rim
#  - dark red tentacle silhouettes: three layers of panning stretched noise in the dome's UV (u around, v up), the
#    silhouettes drift slowly and "breathe"; they are darker than the haze, never glowing
#  - drips: the lower band (v < 0.2) has hanging streaks that sag with time (the wall-top overhang)
#  - refraction from the same noise, small (0.03) so the castle behind still reads
# Parameters on the MI: HazeColor, TentacleColor, HazeOpacity (0.10), RimPower (2.2), RimOpacity (0.45), WaveSpeed (0.05),
# TentacleScale (3), TentacleContrast (0.6), DripAmount (0.5), Refraction (0.03), Glow (1.5: the haze's emissive, unlit).
import unreal
ROOT = '/Game/CastleDefender/Realm'
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(ROOT): EAL.make_directory(ROOT)
name = 'M_RealmBubble2'
if EAL.does_asset_exist(ROOT + '/' + name): EAL.delete_asset(ROOT + '/' + name)
m = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property('two_sided', True)
m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
try: m.set_editor_property('refraction_method', unreal.RefractionMode.RM_INDEX_OF_REFRACTION)
except Exception: pass

def node(cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def scalar(pname, x, y, v): return node(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=pname, default_value=v)
def link(a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)
def noise(x, y, pos, scale=1.0, levels=4):
    n = node(unreal.MaterialExpressionNoise, x, y, scale=scale, quality=1, noise_function=unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX, turbulence=False, levels=levels, output_min=0.0, output_max=1.0)
    link(pos, '', n, 'Position'); return n

haze = node(unreal.MaterialExpressionVectorParameter, -2000, -600, parameter_name='HazeColor', default_value=unreal.LinearColor(0.34, 0.05, 0.48, 1))
tent = node(unreal.MaterialExpressionVectorParameter, -2000, -400, parameter_name='TentacleColor', default_value=unreal.LinearColor(0.12, 0.0, 0.015, 1))
hop = scalar('HazeOpacity', -2000, -200, 0.10); rimp = scalar('RimPower', -2000, -100, 2.2); rimo = scalar('RimOpacity', -2000, 0, 0.45)
spd = scalar('WaveSpeed', -2000, 100, 0.05); tsc = scalar('TentacleScale', -2000, 200, 3.0); tcon = scalar('TentacleContrast', -2000, 300, 0.6)
drip = scalar('DripAmount', -2000, 400, 0.5); refr = scalar('Refraction', -2000, 500, 0.03); glow = scalar('Glow', -2000, 600, 1.5)

uv = node(unreal.MaterialExpressionTextureCoordinate, -1800, -300)
t = node(unreal.MaterialExpressionTime, -1800, 700)
ts = node(unreal.MaterialExpressionMultiply, -1650, 700); link(t, '', ts, 'A'); link(spd, '', ts, 'B')
# tentacle silhouettes: stretched noise (tall thin shapes) in uv, panning sideways and breathing
uvs = node(unreal.MaterialExpressionMultiply, -1650, -300); link(uv, '', uvs, 'A'); link(tsc, '', uvs, 'B')
stretch = node(unreal.MaterialExpressionConstant2Vector, -1650, -200, r=1.0, g=0.22)                 # squash v: tall shapes
uvst = node(unreal.MaterialExpressionMultiply, -1500, -300); link(uvs, '', uvst, 'A'); link(stretch, '', uvst, 'B')
pan = node(unreal.MaterialExpressionAppendVector, -1500, 500); link(ts, '', pan, 'A'); link(ts, '', pan, 'B')
pan2 = node(unreal.MaterialExpressionMultiply, -1350, 500); link(pan, '', pan2, 'A'); pv = node(unreal.MaterialExpressionConstant2Vector, -1500, 600, r=0.35, g=0.08); link(pv, '', pan2, 'B')
uvp = node(unreal.MaterialExpressionAdd, -1350, -300); link(uvst, '', uvp, 'A'); link(pan2, '', uvp, 'B')
ap = node(unreal.MaterialExpressionAppendVector, -1200, -300); link(uvp, '', ap, 'A'); link(ts, '', ap, 'B')
n1 = noise(-1050, -300, ap, 1.0, 3)
uvp2 = node(unreal.MaterialExpressionMultiply, -1350, -100, const_b=1.7); link(uvp, '', uvp2, 'A')
ap2 = node(unreal.MaterialExpressionAppendVector, -1200, -100); link(uvp2, '', ap2, 'A'); link(ts, '', ap2, 'B')
n2 = noise(-1050, -100, ap2, 1.0, 3)
nmix = node(unreal.MaterialExpressionMultiply, -900, -200); link(n1, '', nmix, 'A'); link(n2, '', nmix, 'B')
# contrast: smoothstep around 0.35 so only the darkest cores read as tentacles
lo = node(unreal.MaterialExpressionSubtract, -750, -150, const_b=0.0); link(tcon, '', lo, 'A'); lo2 = node(unreal.MaterialExpressionMultiply, -750, -50, const_b=0.5); link(tcon, '', lo2, 'A')
hi = node(unreal.MaterialExpressionAdd, -600, -50); link(lo2, '', hi, 'A'); link(tcon, '', hi, 'B')
tmask = node(unreal.MaterialExpressionSmoothStep, -450, -200); link(nmix, '', tmask, 'Value'); link(lo2, '', tmask, 'Min'); link(hi, '', tmask, 'Max')
tinv = node(unreal.MaterialExpressionOneMinus, -300, -200); link(tmask, '', tinv, '')
# drips: low band of the dome, stretched vertical noise sagging with time
vmask = node(unreal.MaterialExpressionComponentMask, -1650, 900, r=False, g=True, b=False, a=False); link(uv, '', vmask, '')
dband = node(unreal.MaterialExpressionSmoothStep, -1500, 900); link(vmask, '', dband, 'Value'); c22 = node(unreal.MaterialExpressionConstant, -1650, 1000, r=0.22); c02 = node(unreal.MaterialExpressionConstant, -1650, 1050, r=0.02); link(c22, '', dband, 'Min'); link(c02, '', dband, 'Max')
dst = node(unreal.MaterialExpressionConstant2Vector, -1650, 1150, r=14.0, g=0.6); duv = node(unreal.MaterialExpressionMultiply, -1500, 1150); link(uv, '', duv, 'A'); link(dst, '', duv, 'B')
sag = node(unreal.MaterialExpressionAppendVector, -1500, 1250); z0 = node(unreal.MaterialExpressionConstant, -1650, 1250, r=0.0); link(z0, '', sag, 'A'); link(ts, '', sag, 'B')
duv2 = node(unreal.MaterialExpressionAdd, -1350, 1150); link(duv, '', duv2, 'A'); link(sag, '', duv2, 'B')
dap = node(unreal.MaterialExpressionAppendVector, -1200, 1150); link(duv2, '', dap, 'A'); link(z0, '', dap, 'B')
dn = noise(-1050, 1150, dap, 1.0, 2)
dcore = node(unreal.MaterialExpressionSmoothStep, -900, 1150); link(dn, '', dcore, 'Value'); c55 = node(unreal.MaterialExpressionConstant, -1050, 1300, r=0.55); c80 = node(unreal.MaterialExpressionConstant, -1050, 1350, r=0.8); link(c55, '', dcore, 'Min'); link(c80, '', dcore, 'Max')
dm = node(unreal.MaterialExpressionMultiply, -750, 1150); link(dcore, '', dm, 'A'); link(dband, '', dm, 'B')
dm2 = node(unreal.MaterialExpressionMultiply, -600, 1150); link(dm, '', dm2, 'A'); link(drip, '', dm2, 'B')
# fresnel rim with wave distortion
fr = node(unreal.MaterialExpressionFresnel, -1050, 400); link(rimp, '', fr, 'ExponentIn')
wave = node(unreal.MaterialExpressionMultiply, -900, 450, const_b=0.5); link(n2, '', wave, 'A'); wave1 = node(unreal.MaterialExpressionAdd, -750, 450, const_b=0.75); link(wave, '', wave1, 'A')
frw = node(unreal.MaterialExpressionMultiply, -600, 400); link(fr, '', frw, 'A'); link(wave1, '', frw, 'B')
rim = node(unreal.MaterialExpressionMultiply, -450, 400); link(frw, '', rim, 'A'); link(rimo, '', rim, 'B')
# opacity = haze + rim + tentacles + drips (clamped)
o1 = node(unreal.MaterialExpressionAdd, -300, 300); link(hop, '', o1, 'A'); link(rim, '', o1, 'B')
tm = node(unreal.MaterialExpressionMultiply, -300, 100, const_b=0.55); link(tmask, '', tm, 'A')
o2 = node(unreal.MaterialExpressionAdd, -150, 300); link(o1, '', o2, 'A'); link(tm, '', o2, 'B')
o3 = node(unreal.MaterialExpressionAdd, 0, 300); link(o2, '', o3, 'A'); link(dm2, '', o3, 'B')
oc = node(unreal.MaterialExpressionClamp, 150, 300, min_default=0.0, max_default=0.9); link(o3, '', oc, '')
MEL.connect_material_property(oc, '', unreal.MaterialProperty.MP_OPACITY)
# colour: haze lit by its own glow, tentacles dark, drips darker haze
col = node(unreal.MaterialExpressionLinearInterpolate, -150, -500); link(haze, '', col, 'A'); link(tent, '', col, 'B'); link(tmask, '', col, 'Alpha')
hg = node(unreal.MaterialExpressionMultiply, 0, -500); link(col, '', hg, 'A'); link(glow, '', hg, 'B')
dd = node(unreal.MaterialExpressionMultiply, 0, -350, const_b=0.5); link(hg, '', dd, 'A')
col2 = node(unreal.MaterialExpressionLinearInterpolate, 150, -450); link(hg, '', col2, 'A'); link(dd, '', col2, 'B'); link(dm2, '', col2, 'Alpha')
MEL.connect_material_property(col2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# refraction: 1 + noise * Refraction
rf = node(unreal.MaterialExpressionMultiply, -150, 600); link(n1, '', rf, 'A'); link(refr, '', rf, 'B')
rf1 = node(unreal.MaterialExpressionAdd, 0, 600, const_b=1.0); link(rf, '', rf1, 'A')
try: MEL.connect_material_property(rf1, '', unreal.MaterialProperty.MP_REFRACTION)
except Exception as e: unreal.log_warning('refraction not wired: %s' % e)
MEL.recompile_material(m); EAL.save_asset(m.get_path_name())
mi = ROOT + '/MI_RealmBubble2'
if not EAL.does_asset_exist(mi):
    i = tools.create_asset('MI_RealmBubble2', ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(i, m); EAL.save_asset(i.get_path_name())
unreal.log('M_RealmBubble2 + MI_RealmBubble2 ready; place_realm_ue.py puts them on SM_RealmDome.')
