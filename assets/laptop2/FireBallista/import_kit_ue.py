# laptop2 kit importer (2026-10-30): static props with the shared master M_LP2Weapon (BaseColor/ORM/Normal, Tint,
# Wetness, EmissiveBoost + EmberPulse). Import into UE 5.3.
#   py "<repo>/assets/laptop2/<Kit>/import_kit_ue.py"            imports every item of the kit the script sits in
#   py "<repo>/assets/laptop2/<Kit>/import_kit_ue.py" Crate      just one item
# Kits: BarracksProps (Crate, Barrel, Sack, WeaponRack), SiegeGate (5 pieces, one texture), FireBallista (4 pieces,
# emissive coals). Each item: SM_* (3 LODs, box collision, 'Grip' socket at the pivot), T_*, MI_*.
import os, sys
import unreal
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.getcwd()
KIT = os.path.basename(SRC)
KITS = {  # kit: (UE folder, {item: (mesh names, texture prefix, emissive, collision)})
    'BarracksProps': ('/Game/CastleDefender/Environment/Barracks', {v: (['SM_Barracks_' + v], 'T_Barracks_' + v, False, True) for v in ('Crate', 'Barrel', 'Sack', 'WeaponRack')}),
    'SiegeGate': ('/Game/CastleDefender/Environment/Boundaries/SiegeGate', {'Gate': (['SM_SiegeGate_' + p for p in ('Frame', 'LeafL', 'LeafR', 'Bar', 'Lever')], 'T_SiegeGate', False, True)}),
    'CampKit': ('/Game/CastleDefender/Environment/Camp', {v: (['SM_Camp_' + v], 'T_Camp_' + v, v in ('TorchPost', 'Campfire'), v != 'Campfire') for v in ('TorchPost', 'Campfire', 'HayBale', 'Well', 'HandCart', 'MarketStall', 'Anvil')}),
    'FireBallista': ('/Game/CastleDefender/Weapons/FireBallista', {'Ballista': (['SM_FireBallista_' + p for p in ('Base', 'Frame', 'Slider', 'Spear')], 'T_FireBallista', True, True)}),
}
if KIT not in KITS: raise RuntimeError('run this from inside one of the kit folders: ' + ', '.join(KITS))
ROOT, ITEMS = KITS[KIT]
pick = [a for a in sys.argv[1:] if a in ITEMS] or list(ITEMS)
EAL, MEL, SML = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.EditorStaticMeshLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
MASTER = '/Game/CastleDefender/Weapons/M_LP2Weapon'

def task(path, dst, opts=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def fbx_ui():
    f = unreal.FbxImportUI(); f.import_mesh = True; f.import_as_skeletal = False; f.import_materials = False; f.import_textures = False
    f.static_mesh_import_data.combine_meshes = True; f.static_mesh_import_data.generate_lightmap_u_vs = False
    f.static_mesh_import_data.auto_generate_collision = False
    f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f
def make_master(T0, emis_tex):
    m = tools.create_asset('M_LP2Weapon', '/Game/CastleDefender/Weapons', unreal.Material, unreal.MaterialFactoryNew())
    def p(cls, name, x, y, tex=None, sampler=None):
        e = MEL.create_material_expression(m, cls, x, y); e.set_editor_property('parameter_name', name)
        if tex: e.set_editor_property('texture', unreal.load_asset(tex))
        if sampler: e.set_editor_property('sampler_type', sampler)
        return e
    T = unreal.MaterialExpressionTextureSampleParameter2D
    bc = p(T, 'BaseColor', -1000, -300, T0 + '_BaseColor')
    orm = p(T, 'ORM', -1000, 50, T0 + '_ORM', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    nrm = p(T, 'Normal', -1000, 400, T0 + '_Normal_DirectX', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    emt = p(T, 'Emissive', -1000, 750, emis_tex)
    tint = p(unreal.MaterialExpressionVectorParameter, 'Tint', -1000, -520); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    wet = p(unreal.MaterialExpressionScalarParameter, 'Wetness', -1000, 250); wet.set_editor_property('default_value', 0.0)
    boost = p(unreal.MaterialExpressionScalarParameter, 'EmissiveBoost', -1000, 1000); boost.set_editor_property('default_value', 8.0)
    pulse = p(unreal.MaterialExpressionScalarParameter, 'EmberPulse', -1000, 1120); pulse.set_editor_property('default_value', 0.25)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, -350); MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -450, -350); MEL.connect_material_expressions(mul, '', dark, 'A')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -200); MEL.connect_material_expressions(mul, '', half, 'A'); half.set_editor_property('const_b', 0.6)
    MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -450, 100); MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3); MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 1250); sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -750, 1250); sn.set_editor_property('period', 2.85); MEL.connect_material_expressions(tm, '', sn, '')
    sh = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 1250); sh.set_editor_property('const_b', 0.5); MEL.connect_material_expressions(sn, '', sh, 'A')
    sh2 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -480, 1250); sh2.set_editor_property('const_b', 0.5); MEL.connect_material_expressions(sh, '', sh2, 'A')
    lp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -350, 1150); lp.set_editor_property('const_a', 1.0); MEL.connect_material_expressions(sh2, '', lp, 'B'); MEL.connect_material_expressions(pulse, '', lp, 'Alpha')
    e1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 800); MEL.connect_material_expressions(emt, 'RGB', e1, 'A'); MEL.connect_material_expressions(boost, '', e1, 'B')
    e2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 900); MEL.connect_material_expressions(e1, '', e2, 'A'); MEL.connect_material_expressions(lp, '', e2, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR); MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC); MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL); MEL.connect_material_property(e2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

for item in pick:
    meshes, tn, emis, coll = ITEMS[item]; DST = ROOT if len(ITEMS) == 1 else ROOT + '/' + item
    SETTINGS = {'_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT), '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS), '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
    if emis: SETTINGS['_Emissive'] = (True, unreal.TextureCompressionSettings.TC_DEFAULT)
    tools.import_asset_tasks([task(os.path.join(SRC, item, 'textures', tn + s + '.png'), DST) for s in SETTINGS])
    for s, (srgb, comp) in SETTINGS.items():
        t = unreal.load_asset('%s/%s%s' % (DST, tn, s)); t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if 'Normal' in s: t.set_editor_property('flip_green_channel', False)
        EAL.save_loaded_asset(t)
    if not EAL.does_asset_exist(MASTER): make_master(DST + '/' + tn, (DST + '/' + tn + '_Emissive') if emis else '/Engine/EngineResources/Black')
    tools.import_asset_tasks([task(os.path.join(SRC, item, mname + '.fbx'), DST, fbx_ui()) for mname in meshes])
    MI = '%s/MI_%s' % (DST, tn[2:])
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_' + tn[2:], DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for pn, s in (('BaseColor', '_BaseColor'), ('ORM', '_ORM'), ('Normal', '_Normal_DirectX')) + ((('Emissive', '_Emissive'),) if emis else ()):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s%s' % (DST, tn, s)))
    if not emis: MEL.set_material_instance_scalar_parameter_value(mi, 'EmissiveBoost', 0.0)
    EAL.save_asset(MI)
    for mname in meshes:
        sm = unreal.load_asset('%s/%s' % (DST, mname)); sm.set_material(0, mi)
        opts = unreal.EditorScriptingMeshReductionOptions()
        opts.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, 0.3), unreal.EditorScriptingMeshReductionSettings(0.25, 0.12)]
        opts.auto_compute_lod_screen_size = False; SML.set_lods(sm, opts)
        SML.remove_collisions(sm)
        if coll: SML.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
        try:
            if not sm.find_socket('Grip'):
                sk = unreal.StaticMeshSocket(sm); sk.set_editor_property('socket_name', 'Grip'); sm.add_socket(sk)
        except Exception: pass
        EAL.save_loaded_asset(sm)
    unreal.log('%s: %s imported to %s' % (KIT, item, DST))
