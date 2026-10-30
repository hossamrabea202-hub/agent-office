# Half-horse zombie: the rotting horse body (#155; TGA, 2026-10-30): import into UE 5.3.
# Original procedural work, all in this repo. The zombie torso on top is the existing (licensed) SK_Zombie, attached
# in the Blueprint to the 'TorsoSocket' bone (README). Run in the editor:
#   py "<repo>/assets/tga/HalfHorseZombie/import_horsebody_ue.py"
# Creates (re-running re-imports the same files):
#   /Game/CastleDefender/Characters/Enemies/HalfHorseZombie/SK_HorseBody (+ _Skeleton, _PhysicsAsset) and 5 anims:
#       A_HorseBody_Gallop / _Walk / _Idle (loops), _Rear (knock-down, impact frame 22), _Death
#   .../M_HorseBody (BaseColor / ORM / Normal + Tint, TintAmount, Wetness, HitT, the zombie skin master's names)
#   .../MI_HorseBody_Bay / _Grey, and a 'TorsoSocket' skeletal-mesh socket on the TorsoSocket bone
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/Enemies/HalfHorseZombie'
SKINS = ('Bay', 'Grey')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t

TEX = [('T_HorseBody_%s_BC' % s, True, unreal.TextureCompressionSettings.TC_DEFAULT) for s in SKINS]
TEX += [('T_HorseBody_%s_ORM' % s, False, unreal.TextureCompressionSettings.TC_MASKS) for s in SKINS]
TEX += [('T_HorseBody_N', False, unreal.TextureCompressionSettings.TC_NORMALMAP)]
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png')) for n, _, _ in TEX])
for n, srgb, comp in TEX:
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if n.endswith('_N'): t.set_editor_property('flip_green_channel', False)     # already DirectX
    EAL.save_loaded_asset(t)

f = unreal.FbxImportUI()
f.import_mesh = True; f.import_as_skeletal = True; f.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
f.import_materials = False; f.import_textures = False; f.import_animations = True; f.create_physics_asset = True
f.skeletal_mesh_import_data.import_morph_targets = False
f.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
tools.import_asset_tasks([task(os.path.join(SRC, 'SK_HorseBody.fbx'), f)])
for path in EAL.list_assets(DST, recursive=False):          # FBX takes -> A_HorseBody_<Clip>
    name = path.split('.')[-1]
    if 'A_HorseBody_' in name and not name.startswith('A_HorseBody_'):
        new = DST + '/' + name[name.index('A_HorseBody_'):]
        if EAL.does_asset_exist(new): EAL.delete_asset(new)
        EAL.rename_asset(path.split('.')[0], new)

MASTER = DST + '/M_HorseBody'
if not EAL.does_asset_exist(MASTER):
    m = tools.create_asset('M_HorseBody', DST, unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    bc = p(unreal.MaterialExpressionTextureSampleParameter2D, 'BaseColor', -1100, -250, DST + '/T_HorseBody_Bay_BC')
    orm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'ORM', -1100, 150, DST + '/T_HorseBody_Bay_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(unreal.MaterialExpressionTextureSampleParameter2D, 'Normal', -1100, 500, DST + '/T_HorseBody_N', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1100, -480); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    tamt = p(unreal.MaterialExpressionScalarParameter, 'TintAmount', -1100, -380); tamt.set_editor_property('default_value', 0.0)
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1100, 380); wet.set_editor_property('default_value', 0.0)
    hit = p(unreal.MaterialExpressionScalarParameter, 'HitT', -1100, -560); hit.set_editor_property('default_value', 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    tl = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -600, -300)
    MEL.connect_material_expressions(bc, 'RGB', tl, 'A'); MEL.connect_material_expressions(mul, '', tl, 'B'); MEL.connect_material_expressions(tamt, '', tl, 'Alpha')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, -180)
    MEL.connect_material_expressions(tl, '', half, 'A'); half.set_editor_property('const_b', 0.6)      # wet hair darkens a lot
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -280)
    MEL.connect_material_expressions(tl, '', dark, 'A'); MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 150)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    flash = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -520)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -620); col.set_editor_property('constant', unreal.LinearColor(4.0, 0.25, 0.1, 1))
    MEL.connect_material_expressions(col, '', flash, 'A'); MEL.connect_material_expressions(hit, '', flash, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(flash, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

for s in SKINS:
    name = 'MI_HorseBody_' + s; MI = DST + '/' + name
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    MEL.set_material_instance_texture_parameter_value(mi, 'BaseColor', unreal.load_asset('%s/T_HorseBody_%s_BC' % (DST, s)))
    MEL.set_material_instance_texture_parameter_value(mi, 'ORM', unreal.load_asset('%s/T_HorseBody_%s_ORM' % (DST, s)))
    MEL.set_material_instance_texture_parameter_value(mi, 'Normal', unreal.load_asset(DST + '/T_HorseBody_N'))
    EAL.save_asset(MI)

sk = unreal.load_asset(DST + '/SK_HorseBody')
mats = sk.get_editor_property('materials')
if mats: mats[0].set_editor_property('material_interface', unreal.load_asset(DST + '/MI_HorseBody_Bay')); sk.set_editor_property('materials', mats)
# socket for the zombie torso (BP attaches SK_Zombie here); the bone points up, so the socket needs no rotation
skel = sk.get_editor_property('skeleton')
try:
    if not sk.find_socket('TorsoSocket'):
        sock = unreal.SkeletalMeshSocket(sk); sock.set_editor_property('socket_name', 'TorsoSocket'); sock.set_editor_property('bone_name', 'TorsoSocket')
        sk.add_socket(sock, True)
except Exception as e:
    unreal.log_warning('TorsoSocket: add it by hand in the Skeleton editor on bone TorsoSocket (%s)' % e)
EAL.save_loaded_asset(sk)
unreal.log('Horse body imported: ' + DST + ' (2 skins, 5 anims). Next: BP_HalfHorseZombie, see README.')
