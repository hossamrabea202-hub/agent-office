# #169 stage 1 v2: the realm membrane material, per the owner's concept (a huge glassy soap-bubble dome: mostly clear, a
# fine cell network, bright branching veins, a bright rim, colour only inside). Run in the UE 5.3 editor:
#   py "<repo>/handoffs/realm-169/make_realm_membrane.py"
# Imports assets/laptop2/RealmKit/T_RealmMembrane_Veins.png (R cell walls, G veins, B cell shading) and makes
# /Game/CastleDefender/Realm/M_RealmMembrane + MI_RealmMembrane: translucent, unlit, two-sided, depth-tested.
#   opacity  = Clear (0.04) + rim (fresnel^RimPower * RimOpacity) + walls * WallOpacity + veins * VeinOpacity
#   emissive = rim and veins glow in VeinColor / RimColor; the cells tint a faint MembraneColor; everything * Glow
#   the cell texture pans slowly in u (WaveSpeed) and a second copy at 1.7x drifts the other way (breathing)
#   refraction = 1 + walls * 0.02 (the membrane bends the view a little, not the whole sky)
# WOBBLE (vertex wave): UE 5.3 Python cannot connect World Position Offset. The chain is built and left unconnected:
#   node "WPO_OUT" (a Multiply) -> drag its output to the material's World Position Offset pin by hand, then Apply.
import os, unreal
ROOT = '/Game/CastleDefender/Realm'
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(ROOT): EAL.make_directory(ROOT)
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
tex_path = os.path.join(REPO, 'assets', 'laptop2', 'RealmKit', 'T_RealmMembrane_Veins.png')
t = unreal.AssetImportTask(); t.filename = tex_path; t.destination_path = ROOT; t.automated = True; t.replace_existing = True; t.save = True
tools.import_asset_tasks([t]); VT = unreal.load_asset(ROOT + '/T_RealmMembrane_Veins')
VT.set_editor_property('srgb', False); VT.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
VT.set_editor_property('address_x', unreal.TextureAddress.TA_WRAP); VT.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP); EAL.save_asset(VT.get_path_name())

name = 'M_RealmMembrane'
if EAL.does_asset_exist(ROOT + '/' + name): EAL.delete_asset(ROOT + '/' + name)
m = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property('two_sided', True)
try: m.set_editor_property('refraction_method', unreal.RefractionMode.RM_INDEX_OF_REFRACTION)
except Exception: pass

def node(cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def scalar(pname, x, y, v): return node(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=pname, default_value=v)
def vec(pname, x, y, c): return node(unreal.MaterialExpressionVectorParameter, x, y, parameter_name=pname, default_value=unreal.LinearColor(*c))
def link(a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)
def mul(x, y, a, ao, b, bo=''):
    n = node(unreal.MaterialExpressionMultiply, x, y); link(a, ao, n, 'A'); link(b, bo, n, 'B'); return n
def add(x, y, a, ao, b, bo=''):
    n = node(unreal.MaterialExpressionAdd, x, y); link(a, ao, n, 'A'); link(b, bo, n, 'B'); return n

memb = vec('MembraneColor', -2200, -700, (0.75, 0.25, 0.45, 1)); veinc = vec('VeinColor', -2200, -550, (1.0, 0.18, 0.42, 1)); rimc = vec('RimColor', -2200, -400, (1.0, 0.45, 0.7, 1))
clear = scalar('ClearOpacity', -2200, -250, 0.04); wallo = scalar('WallOpacity', -2200, -150, 0.18); veino = scalar('VeinOpacity', -2200, -50, 0.55)
rimp = scalar('RimPower', -2200, 50, 3.0); rimo = scalar('RimOpacity', -2200, 150, 0.5); spd = scalar('WaveSpeed', -2200, 250, 0.015)
glow = scalar('Glow', -2200, 350, 2.0); refr = scalar('Refraction', -2200, 450, 0.02); wob = scalar('WobbleCm', -2200, 550, 60.0)

uv = node(unreal.MaterialExpressionTextureCoordinate, -2000, -300)
tm = node(unreal.MaterialExpressionTime, -2000, 700); ts = mul(-1850, 700, tm, '', spd)
pan = node(unreal.MaterialExpressionAppendVector, -1700, 700); link(ts, '', pan, 'A'); z0 = node(unreal.MaterialExpressionConstant, -1850, 800, r=0.0); link(z0, '', pan, 'B')
uv1 = add(-1700, -300, uv, '', pan)
tex1 = node(unreal.MaterialExpressionTextureSample, -1500, -300, texture=VT, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); link(uv1, '', tex1, 'UVs')
uv2s = node(unreal.MaterialExpressionMultiply, -1700, -100, const_b=1.7); link(uv, '', uv2s, 'A')
pan2 = node(unreal.MaterialExpressionMultiply, -1700, 850, const_b=-0.6); link(pan, '', pan2, 'A')
uv2 = add(-1550, -100, uv2s, '', pan2)
tex2 = node(unreal.MaterialExpressionTextureSample, -1400, -100, texture=VT, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); link(uv2, '', tex2, 'UVs')
walls = node(unreal.MaterialExpressionMax, -1200, -300); link(tex1, 'R', walls, 'A'); w2 = node(unreal.MaterialExpressionMultiply, -1300, -200, const_b=0.5); link(tex2, 'R', w2, 'A'); link(w2, '', walls, 'B')
veins = node(unreal.MaterialExpressionMax, -1200, -100); link(tex1, 'G', veins, 'A'); v2 = node(unreal.MaterialExpressionMultiply, -1300, 0, const_b=0.6); link(tex2, 'G', v2, 'A'); link(v2, '', veins, 'B')
# breathing: veins pulse 0.75..1
sn = node(unreal.MaterialExpressionSine, -1500, 900, period=6.0); link(tm, '', sn, ''); br = node(unreal.MaterialExpressionMultiply, -1350, 900, const_b=0.125); link(sn, '', br, 'A')
br1 = node(unreal.MaterialExpressionAdd, -1200, 900, const_b=0.875); link(br, '', br1, 'A')
veinsb = mul(-1050, -100, veins, '', br1)
# rim
fr = node(unreal.MaterialExpressionFresnel, -1200, 300); link(rimp, '', fr, 'ExponentIn')
rim = mul(-1050, 300, fr, '', rimo)
# opacity
o1 = add(-900, 200, clear, '', rim); o2 = add(-750, 200, o1, '', mul(-900, 0, walls, '', wallo)); o3 = add(-600, 200, o2, '', mul(-900, 100, veinsb, '', veino))
oc = node(unreal.MaterialExpressionClamp, -450, 200, min_default=0.0, max_default=0.85); link(o3, '', oc, '')
MEL.connect_material_property(oc, '', unreal.MaterialProperty.MP_OPACITY)
# emissive colour: membrane tint * cell shading, veins in VeinColor, rim in RimColor; all * Glow
shade = node(unreal.MaterialExpressionAdd, -1200, -500, const_b=0.4); link(tex1, 'B', shade, 'A')
cm = mul(-1000, -600, memb, '', shade)
vc = mul(-1000, -450, veinc, '', veinsb); rc = mul(-1000, -350, rimc, '', rim)
c1 = node(unreal.MaterialExpressionLinearInterpolate, -800, -550); link(cm, '', c1, 'A'); link(veinc, '', c1, 'B'); link(veinsb, '', c1, 'Alpha')
c2 = add(-650, -500, c1, '', rc); c3 = mul(-500, -500, c2, '', glow)
MEL.connect_material_property(c3, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# refraction
rf = mul(-900, 500, walls, '', refr); rf1 = node(unreal.MaterialExpressionAdd, -750, 500, const_b=1.0); link(rf, '', rf1, 'A')
try: MEL.connect_material_property(rf1, '', unreal.MaterialProperty.MP_REFRACTION)
except Exception as e: unreal.log_warning('refraction not wired: %s' % e)
# wobble chain (connect WPO_OUT -> World Position Offset by hand): normal * sin(time*0.7 + v*6) * WobbleCm
vn = node(unreal.MaterialExpressionVertexNormalWS, -1200, 1100)
vmask = node(unreal.MaterialExpressionComponentMask, -1500, 1200, r=False, g=True, b=False, a=False); link(uv, '', vmask, '')
v6 = node(unreal.MaterialExpressionMultiply, -1350, 1200, const_b=6.0); link(vmask, '', v6, 'A')
t07 = node(unreal.MaterialExpressionMultiply, -1350, 1300, const_b=0.7); link(tm, '', t07, 'A')
ph = add(-1200, 1250, v6, '', t07); sw = node(unreal.MaterialExpressionSine, -1050, 1250, period=6.2832); link(ph, '', sw, '')
amp = mul(-900, 1250, sw, '', wob); wpo = mul(-750, 1150, vn, '', amp); wpo.set_editor_property('desc', 'WPO_OUT: drag to World Position Offset')
MEL.recompile_material(m); EAL.save_asset(m.get_path_name())
mi = ROOT + '/MI_RealmMembrane'
if not EAL.does_asset_exist(mi):
    i = tools.create_asset('MI_RealmMembrane', ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(i, m); EAL.save_asset(i.get_path_name())
unreal.log('M_RealmMembrane ready. Open it, drag the Multiply named WPO_OUT into World Position Offset, Apply. place_realm_ue.py uses MI_RealmMembrane.')
