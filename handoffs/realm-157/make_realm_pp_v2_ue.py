# #157 v2 (adjustedfilm, 2026-10-31, on laptop2's v1 look): no PostProcessVolume to place any more.
#   py "<repo>/handoffs/realm-157/make_realm_pp_v2_ue.py"
# Changes from v1: (1) safe re-run: the material is rebuilt in place (v1 deleted it, which broke MI_PP_Realm);
# (2) MPC_Realm.Inside (0..1) scales everything and the result is lerped onto the untouched scene sample, so outside the
# realm the picture is exactly the original; (3) desaturate 10 % inside (card spec); (4) M_PP_Realm is added to the
# hero cameras' blendables (weight 1) and BPC_RealmFX (added to the hero as "RealmFX") drives Inside by distance to the
# realm (centre / radius of the actors tagged laptop2_realm), fading over 2 s.
# v1 header:
# Makes M_PP_Realm (+ MI_PP_Realm) in /Game/CastleDefender/Realm/: a post-process material (before tonemapping) that
# bends the picture at the edges of the screen with slow animated noise, splits the colours (chromatic), darkens and
# tints the corners purple-green, and leaves the centre of the screen clean so the player can still fight.
# Then: a PostProcessVolume covering the realm area (NOT unbound, Blend Radius 800) with MI_PP_Realm in Post Process
# Materials, weight 1. Params on the MI: Strength (0.8), EdgeStart (0.45: where the clean centre ends, 0..1 of the
# half-diagonal), Speed (0.35), Split (0.004: chromatic offset), Tint (purple), TintAmount (0.35).
import unreal
ROOT = '/Game/CastleDefender/Realm'
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(ROOT): EAL.make_directory(ROOT)

name = 'M_PP_Realm'
# MPC_Realm (Inside)
if EAL.does_asset_exist(ROOT + '/MPC_Realm'):
    mpc = unreal.load_asset(ROOT + '/MPC_Realm')
else:
    mpc = tools.create_asset('MPC_Realm', ROOT, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
if 'Inside' not in [str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')]:
    pin = unreal.CollectionScalarParameter(); pin.set_editor_property('parameter_name', 'Inside'); pin.set_editor_property('default_value', 0.0)
    mpc.set_editor_property('scalar_parameters', list(mpc.get_editor_property('scalar_parameters')) + [pin])
EAL.save_asset(ROOT + '/MPC_Realm')
if EAL.does_asset_exist(ROOT + '/' + name):
    m = unreal.load_asset(ROOT + '/' + name); MEL.delete_all_material_expressions(m)
else:
    m = tools.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property('material_domain', unreal.MaterialDomain.MD_POST_PROCESS)
m.set_editor_property('blendable_location', unreal.BlendableLocation.BL_BEFORE_TONEMAPPING)

def node(cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e
def scalar(pname, x, y, v):
    return node(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=pname, default_value=v)
def link(a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)

strength = scalar('Strength', -1800, -400, 0.8)
edge0 = scalar('EdgeStart', -1800, -300, 0.45)
speed = scalar('Speed', -1800, -200, 0.35)
split = scalar('Split', -1800, -100, 0.004)
tint = node(unreal.MaterialExpressionVectorParameter, -1800, 300, parameter_name='Tint', default_value=unreal.LinearColor(0.45, 0.12, 0.6, 1.0))
tinta = scalar('TintAmount', -1800, 450, 0.35)

# radial mask: 0 in the clean centre, 1 at the corners (uses the screen UV of the post-process input)
uv = node(unreal.MaterialExpressionScreenPosition, -1800, 0)
cen = node(unreal.MaterialExpressionSubtract, -1600, 0, const_b=0.5); link(uv, '', cen, 'A')
rad = node(unreal.MaterialExpressionDistance, -1450, 0); link(cen, '', rad, 'A')
zero = node(unreal.MaterialExpressionConstant2Vector, -1600, 100, r=0.0, g=0.0); link(zero, '', rad, 'B')
radn = node(unreal.MaterialExpressionMultiply, -1300, 0, const_b=1.414); link(rad, '', radn, 'A')          # 0..1 at the corner
edge1 = node(unreal.MaterialExpressionAdd, -1450, -250, const_b=0.5); link(edge0, '', edge1, 'A')
mask = node(unreal.MaterialExpressionSmoothStep, -1150, 0); link(radn, '', mask, 'Value'); link(edge0, '', mask, 'Min'); link(edge1, '', mask, 'Max')
maskp = node(unreal.MaterialExpressionPower, -1000, 0, const_exponent=1.6); link(mask, '', maskp, 'Base')
inside = node(unreal.MaterialExpressionCollectionParameter, -1800, -800, collection=mpc, parameter_name='Inside')
sti = node(unreal.MaterialExpressionMultiply, -1000, -250); link(strength, '', sti, 'A'); link(inside, '', sti, 'B')
amt = node(unreal.MaterialExpressionMultiply, -850, 0); link(maskp, '', amt, 'A'); link(sti, '', amt, 'B')

# slow living noise that warps the UV, driven by Time x Speed (3D noise on screen uv + time)
t = node(unreal.MaterialExpressionTime, -1800, -600)
ts = node(unreal.MaterialExpressionMultiply, -1650, -600); link(t, '', ts, 'A'); link(speed, '', ts, 'B')
uv8 = node(unreal.MaterialExpressionMultiply, -1650, -500, const_b=3.0); link(uv, '', uv8, 'A')
ap = node(unreal.MaterialExpressionAppendVector, -1500, -550); link(uv8, '', ap, 'A'); link(ts, '', ap, 'B')
nz = node(unreal.MaterialExpressionNoise, -1350, -550, scale=1.0, quality=1, noise_function=unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX, turbulence=False, levels=3, output_min=-1.0, output_max=1.0)
link(ap, '', nz, 'Position')
nz2 = node(unreal.MaterialExpressionNoise, -1350, -400, scale=1.0, quality=1, noise_function=unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX, turbulence=False, levels=3, output_min=-1.0, output_max=1.0)
ap2 = node(unreal.MaterialExpressionAdd, -1500, -400, const_b=17.3); link(ap, '', ap2, 'A'); link(ap2, '', nz2, 'Position')
warp = node(unreal.MaterialExpressionAppendVector, -1200, -500); link(nz, '', warp, 'A'); link(nz2, '', warp, 'B')
warps = node(unreal.MaterialExpressionMultiply, -1050, -500, const_b=0.06); link(warp, '', warps, 'A')
warpm = node(unreal.MaterialExpressionMultiply, -900, -500); link(warps, '', warpm, 'A'); link(amt, '', warpm, 'B')
uvw = node(unreal.MaterialExpressionAdd, -750, -500); link(uv, '', uvw, 'A'); link(warpm, '', uvw, 'B')

# chromatic split: sample the scene three times, R and B pushed outward along the radius
dirn = node(unreal.MaterialExpressionNormalize, -1300, 200); link(cen, '', dirn, 'VectorInput')
sp = node(unreal.MaterialExpressionMultiply, -1150, 200); link(dirn, '', sp, 'A'); link(split, '', sp, 'B')
spm = node(unreal.MaterialExpressionMultiply, -1000, 200); link(sp, '', spm, 'A'); link(amt, '', spm, 'B')
uvr = node(unreal.MaterialExpressionAdd, -600, -600); link(uvw, '', uvr, 'A'); link(spm, '', uvr, 'B')
uvb = node(unreal.MaterialExpressionSubtract, -600, -300); link(uvw, '', uvb, 'A'); link(spm, '', uvb, 'B')
def scene(x, y, uvn):
    s = node(unreal.MaterialExpressionSceneTexture, x, y, scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    link(uvn, '', s, 'UVs'); return s
sr, sg, sb = scene(-400, -600, uvr), scene(-400, -450, uvw), scene(-400, -300, uvb)
cr = node(unreal.MaterialExpressionComponentMask, -250, -600, r=True, g=False, b=False, a=False); link(sr, 'Color', cr, '')
cg = node(unreal.MaterialExpressionComponentMask, -250, -450, r=False, g=True, b=False, a=False); link(sg, 'Color', cg, '')
cb = node(unreal.MaterialExpressionComponentMask, -250, -300, r=False, g=False, b=True, a=False); link(sb, 'Color', cb, '')
rg = node(unreal.MaterialExpressionAppendVector, -100, -550); link(cr, '', rg, 'A'); link(cg, '', rg, 'B')
rgb = node(unreal.MaterialExpressionAppendVector, 50, -500); link(rg, '', rgb, 'A'); link(cb, '', rgb, 'B')

# the corners: tinted and darkened, slow breathing
sn = node(unreal.MaterialExpressionSine, -1500, 450, period=5.0); link(t, '', sn, '')
br = node(unreal.MaterialExpressionMultiply, -1350, 450, const_b=0.15); link(sn, '', br, 'A')
br1 = node(unreal.MaterialExpressionAdd, -1200, 450, const_b=0.85); link(br, '', br1, 'A')
tm = node(unreal.MaterialExpressionMultiply, -1000, 400); link(amt, '', tm, 'A'); link(tinta, '', tm, 'B')
tm2 = node(unreal.MaterialExpressionMultiply, -850, 400); link(tm, '', tm2, 'A'); link(br1, '', tm2, 'B')
tinted = node(unreal.MaterialExpressionMultiply, 200, -300); link(rgb, '', tinted, 'A'); link(tint, '', tinted, 'B')
lerp = node(unreal.MaterialExpressionLinearInterpolate, 400, -400); link(rgb, '', lerp, 'A'); link(tinted, '', lerp, 'B'); link(tm2, '', lerp, 'Alpha')
dark = node(unreal.MaterialExpressionMultiply, -850, 550, const_b=0.35); link(amt, '', dark, 'A')
dark1 = node(unreal.MaterialExpressionOneMinus, -700, 550); link(dark, '', dark1, '')
out = node(unreal.MaterialExpressionMultiply, 600, -400); link(lerp, '', out, 'A'); link(dark1, '', out, 'B')
# desaturate 10 % inside, then lerp onto the untouched scene (default UVs) by Inside: outside the realm = the original
des = node(unreal.MaterialExpressionDesaturation, 750, -400); link(out, '', des, '')
dk = node(unreal.MaterialExpressionMultiply, 650, -250, const_b=0.10); link(inside, '', dk, 'A'); link(dk, '', des, 'Fraction')
orig = node(unreal.MaterialExpressionSceneTexture, 600, -100, scene_texture_id=unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
origc = node(unreal.MaterialExpressionComponentMask, 750, -100, r=True, g=True, b=True, a=False); link(orig, 'Color', origc, '')
fin = node(unreal.MaterialExpressionLinearInterpolate, 950, -300); link(origc, '', fin, 'A'); link(des, '', fin, 'B'); link(inside, '', fin, 'Alpha')
MEL.connect_material_property(fin, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(m); EAL.save_asset(m.get_path_name())

mi_name = 'MI_PP_Realm'
if not EAL.does_asset_exist(ROOT + '/' + mi_name):
    mi = tools.create_asset(mi_name, ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, m); EAL.save_asset(mi.get_path_name())
# hero: cameras get the blendable, BPC_RealmFX component
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); LIB = unreal.SubobjectDataBlueprintFunctionLibrary; BEL = unreal.BlueprintEditorLibrary
hero = unreal.load_asset(HERO); log = []
objs = [LIB.get_object(SDS.k2_find_subobject_data_from_handle(h)) for h in SDS.k2_gather_subobject_data_for_blueprint(hero)]
for c in [o for o in objs if isinstance(o, unreal.CameraComponent)]:
    pps = c.get_editor_property('post_process_settings'); wb = pps.get_editor_property('weighted_blendables'); arr_ = list(wb.get_editor_property('array'))
    if any(x.get_editor_property('object') == m for x in arr_): log.append('%s already has M_PP_Realm' % c.get_name()); continue
    w = unreal.WeightedBlendable(); w.set_editor_property('weight', 1.0); w.set_editor_property('object', m)
    wb.set_editor_property('array', arr_ + [w]); pps.set_editor_property('weighted_blendables', wb); c.set_editor_property('post_process_settings', pps)
    log.append('%s + M_PP_Realm' % c.get_name())
CP = '/Game/CastleDefender/Realm/BPC_RealmFX'
if EAL.does_asset_exist(CP): comp = unreal.load_asset(CP)
else:
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.ActorComponent)
    comp = tools.create_asset('BPC_RealmFX', ROOT, unreal.Blueprint, f); BEL.compile_blueprint(comp); EAL.save_asset(CP); log.append('created ' + CP)
names = [str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) for h in SDS.k2_gather_subobject_data_for_blueprint(hero)]
if 'RealmFX' not in names:
    h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=SDS.k2_gather_subobject_data_for_blueprint(hero)[0], new_class=comp.generated_class(), blueprint_context=hero))
    SDS.rename_subobject(h, unreal.Text('RealmFX')); log.append('hero + RealmFX')
BEL.compile_blueprint(hero); EAL.save_asset(HERO)
unreal.log('M_PP_Realm v2 + MPC_Realm + MI_PP_Realm in %s; %s. Next: BPVar lines + graph on BPC_RealmFX (README). No volume to place.' % (ROOT, '; '.join(log)))
