# Sword fire (owner 2026-10-30 "i want it now"; the fire element of #95, delivered on its own). Run in the UE 5.3 editor:
#   py "<repo>/handoffs/sword-fire/make_sword_fire_ue.py"
# Imports assets/laptop2/SwordFire/T_SwordFire_Noise.png (seamless fire noise, R body / G wisps / B break-up) and
# T_SwordFire_Ramp.png (heat ramp), and makes /Game/CastleDefender/VFX/SwordFire/M_SwordFireOverlay + MI_SwordFire.
# The material is an OVERLAY (Additive, Unlit, two-sided): the hero's Sword component gets it as its Overlay Material,
# so the sword's own material is never touched. Flames are world-aligned noise rising along world Z, shaped by a
# fresnel so they sit on the edges, coloured by the ramp; everything scales with the scalar parameter Heat (0..1),
# which the hero Blueprint drives (zombies near -> 1, clear -> 0).
# WPO (flames stand off the blade): UE 5.3 Python cannot connect World Position Offset. The chain ends in a node
# named "WPO_OUT": drag its output to the material's World Position Offset pin by hand, then Apply.
import os, unreal
ROOT = '/Game/CastleDefender/VFX/SwordFire'
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(ROOT): EAL.make_directory(ROOT)
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(REPO, 'assets', 'laptop2', 'SwordFire')
for nm, srgb, comp, ay in (('T_SwordFire_Noise', False, unreal.TextureCompressionSettings.TC_MASKS, unreal.TextureAddress.TA_WRAP),
                           ('T_SwordFire_Ramp', True, unreal.TextureCompressionSettings.TC_DEFAULT, unreal.TextureAddress.TA_CLAMP)):
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, nm + '.png'); t.destination_path = ROOT; t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t]); T = unreal.load_asset(ROOT + '/' + nm)
    T.set_editor_property('srgb', srgb); T.set_editor_property('compression_settings', comp)
    T.set_editor_property('address_x', unreal.TextureAddress.TA_WRAP if nm.endswith('Noise') else unreal.TextureAddress.TA_CLAMP); T.set_editor_property('address_y', ay)
    T.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS if nm.endswith('Ramp') else unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    EAL.save_asset(T.get_path_name())
NOISE, RAMP = unreal.load_asset(ROOT + '/T_SwordFire_Noise'), unreal.load_asset(ROOT + '/T_SwordFire_Ramp')

name = 'M_SwordFireOverlay'
if EAL.does_asset_exist(ROOT + '/' + name): EAL.delete_asset(ROOT + '/' + name)
m = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
m.set_editor_property('two_sided', True)

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
def mulc(x, y, a, ao, c):
    n = node(unreal.MaterialExpressionMultiply, x, y, const_b=c); link(a, ao, n, 'A'); return n
def addc(x, y, a, ao, c):
    n = node(unreal.MaterialExpressionAdd, x, y, const_b=c); link(a, ao, n, 'A'); return n
def sat(x, y, a, ao=''):
    n = node(unreal.MaterialExpressionSaturate, x, y); link(a, ao, n, ''); return n

heat = scalar('Heat', -2400, -600, 0.0); inten = scalar('Intensity', -2400, -500, 8.0); speed = scalar('Speed', -2400, -400, 1.4)
scale = scalar('Scale', -2400, -300, 2.5); edge = scalar('EdgePower', -2400, -200, 2.0); tint = vec('Tint', -2400, -100, (1.0, 0.85, 0.7, 1))
standoff = scalar('StandoffCm', -2400, 0, 2.0)
# world-aligned flame coordinates: u from x+y, v from z, rising with time
wp = node(unreal.MaterialExpressionWorldPosition, -2200, 300)
cm = node(unreal.MaterialExpressionComponentMask, -2050, 300, r=True, g=True, b=False, a=False); link(wp, '', cm, '')
dot = node(unreal.MaterialExpressionDotProduct, -1900, 300); c2 = node(unreal.MaterialExpressionConstant2Vector, -2050, 420, r=0.7, g=0.7); link(cm, '', dot, 'A'); link(c2, '', dot, 'B')
zc = node(unreal.MaterialExpressionComponentMask, -2050, 520, r=False, g=False, b=True, a=False); link(wp, '', zc, '')
tm = node(unreal.MaterialExpressionTime, -2050, 650); rise = mul(-1900, 650, tm, '', speed)
zr = node(unreal.MaterialExpressionSubtract, -1750, 520); link(zc, '', zr, 'A'); link(rise, '', zr, 'B')
uv = node(unreal.MaterialExpressionAppendVector, -1600, 400); link(dot, '', uv, 'A'); link(zr, '', uv, 'B')
sc = node(unreal.MaterialExpressionDivide, -1600, 250, const_b=100.0); link(scale, '', sc, 'A')
uvs = mul(-1450, 400, uv, '', sc)
tex1 = node(unreal.MaterialExpressionTextureSample, -1250, 350, texture=NOISE, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); link(uvs, '', tex1, 'UVs')
uv2 = mulc(-1450, 600, uvs, '', 1.9); off = node(unreal.MaterialExpressionConstant2Vector, -1450, 700, r=0.31, g=0.0); uv2o = add(-1300, 600, uv2, '', off)
tex2 = node(unreal.MaterialExpressionTextureSample, -1150, 600, texture=NOISE, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS); link(uv2o, '', tex2, 'UVs')
body = add(-950, 350, tex1, 'R', mulc(-1050, 450, tex2, 'B', 0.5))            # 0..1.5 soft flame body
wisp = mulc(-950, 550, tex1, 'G', 0.7)
flame = add(-800, 400, body, '', wisp)
# the edges burn first: fresnel^EdgePower, and Heat lifts the threshold so cold = nothing, hot = full blade
fr = node(unreal.MaterialExpressionFresnel, -1050, 0); link(edge, '', fr, 'ExponentIn')
gate = add(-800, 0, mulc(-950, 0, fr, '', 0.7), '', mulc(-950, 100, heat, '', 0.9))   # 0..1.6
cold = node(unreal.MaterialExpressionSubtract, -650, 200, const_b=1.1); link(flame, '', cold, 'A')
temp = sat(-350, 200, add(-500, 200, cold, '', gate))
temp2 = mul(-200, 200, temp, '', heat)
# colour from the ramp (u = temperature), scaled by Intensity * Tint * Heat
rampuv = node(unreal.MaterialExpressionAppendVector, -50, 200); half = node(unreal.MaterialExpressionConstant, -200, 320, r=0.5); link(temp2, '', rampuv, 'A'); link(half, '', rampuv, 'B')
rt = node(unreal.MaterialExpressionTextureSample, 100, 200, texture=RAMP, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); link(rampuv, '', rt, 'UVs')
col = mul(300, 200, rt, 'RGB', tint, 'RGB'); col2 = mul(450, 200, col, '', inten); col3 = mul(600, 200, col2, '', heat)
MEL.connect_material_property(col3, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# WPO: push the flaming parts out along the vertex normal and up (left unconnected - drag WPO_OUT to World Position Offset)
vn = node(unreal.MaterialExpressionVertexNormalWS, -650, 900); up = node(unreal.MaterialExpressionConstant3Vector, -650, 1000, constant=unreal.LinearColor(0, 0, 1, 1))
dirn = add(-500, 900, vn, '', up); amt = mul(-500, 1050, temp2, '', standoff)
wpo = mul(-300, 950, dirn, '', amt); wpo.set_editor_property('desc', 'WPO_OUT')
MEL.recompile_material(m); EAL.save_asset(m.get_path_name())

mi = ROOT + '/MI_SwordFire'
if EAL.does_asset_exist(mi): EAL.delete_asset(mi)
inst = tools.create_asset('MI_SwordFire', ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(inst, m); MEL.set_material_instance_scalar_parameter_value(inst, 'Heat', 0.0)
EAL.save_asset(inst.get_path_name())
unreal.log('SWORD FIRE OK: %s/M_SwordFireOverlay + MI_SwordFire (drag WPO_OUT -> World Position Offset, Apply)' % ROOT)
