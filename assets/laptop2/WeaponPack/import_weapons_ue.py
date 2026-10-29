# laptop2's weapon pack (2026-10-29): Heater Shield, Round Shield, Emberoath (legendary short sword), Health Potion,
# Antidote. Import into UE 5.3.
# Run in the editor:  py "<repo>/assets/laptop2/WeaponPack/import_weapons_ue.py"            (all three)
#                     py "<repo>/assets/laptop2/WeaponPack/import_weapons_ue.py" Emberoath  (just one)
# For each item it creates, in /Game/CastleDefender/Weapons/<Item>/ (re-running re-imports):
#   SM_<mesh> (3 LODs 100/50/25 %, one box collision, a 'Grip' socket at the pivot = the hand grip centre)
#   T_<tex>_BaseColor / _ORM (R AO, G roughness, B metallic) / _Normal_DirectX (+ _Emissive for the sword)
#   MI_<mesh> of the shared master M_LP2Weapon (Tint, Wetness, and EmissiveBoost + EmberPulse for glowing items)
import os, sys
import unreal

REPO = r''
try:
    SRC = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SRC = os.path.join(REPO, 'assets', 'laptop2', 'WeaponPack')
ROOT = '/Game/CastleDefender/Weapons'
ITEMS = {   # item: (folder, mesh, texture prefix, has emissive)
    'HeaterShield': ('HeaterShield', 'SM_HeaterShield', 'T_HeaterShield', False),
    'RoundShield': ('RoundShield', 'SM_RoundShield', 'T_RoundShield', False),
    'Emberoath': ('Emberoath', 'SM_Emberoath', 'T_Emberoath', True),
    'PotionHealth': ('Potions', 'SM_Potion_Health', 'T_Potion_Health', False),
    'PotionAntidote': ('Potions', 'SM_Potion_Antidote', 'T_Potion_Antidote', False),
}
LIQUID = {'PotionHealth': (0.75, 0.03, 0.02), 'PotionAntidote': (0.10, 0.62, 0.06)}   # liquid colours
pick = [a for a in sys.argv[1:] if a in ITEMS] or list(ITEMS)
EAL, MEL, SML = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.EditorStaticMeshLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, dst, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dst; t.automated = True; t.save = True; t.replace_existing = True
    if opts: t.options = opts
    return t
def fbx_ui():
    f = unreal.FbxImportUI()
    f.import_mesh = True; f.import_as_skeletal = False; f.import_materials = False; f.import_textures = False
    f.static_mesh_import_data.combine_meshes = True
    f.static_mesh_import_data.generate_lightmap_u_vs = False
    f.static_mesh_import_data.auto_generate_collision = False
    f.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    return f

# ---- shared master material ----
MASTER = ROOT + '/M_LP2Weapon'
def make_master(T0, emis_tex):
    """built once, from the first imported item's textures (the defaults must match each sampler type)."""
    m = tools.create_asset('M_LP2Weapon', ROOT, unreal.Material, unreal.MaterialFactoryNew())
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
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, -350)
    MEL.connect_material_expressions(bc, 'RGB', mul, 'A'); MEL.connect_material_expressions(tint, '', mul, 'B')
    dark = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -450, -350)
    MEL.connect_material_expressions(mul, '', dark, 'A')
    half = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -200)
    MEL.connect_material_expressions(mul, '', half, 'A'); half.set_editor_property('const_b', 0.6)
    MEL.connect_material_expressions(half, '', dark, 'B'); MEL.connect_material_expressions(wet, '', dark, 'Alpha')
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -450, 100)
    MEL.connect_material_expressions(orm, 'G', rg, 'A'); rg.set_editor_property('const_b', 0.3)
    MEL.connect_material_expressions(wet, '', rg, 'Alpha')
    # ember pulse: emissive x boost x (1 - pulse + pulse * (0.5 + 0.5 sin(time * 2.2)))
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 1250)
    sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -750, 1250); sn.set_editor_property('period', 2.85)
    MEL.connect_material_expressions(tm, '', sn, '')
    sh = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 1250); sh.set_editor_property('const_b', 0.5)
    MEL.connect_material_expressions(sn, '', sh, 'A')
    sh2 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -480, 1250); sh2.set_editor_property('const_b', 0.5)
    MEL.connect_material_expressions(sh, '', sh2, 'A')
    lp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -350, 1150); lp.set_editor_property('const_a', 1.0)
    MEL.connect_material_expressions(sh2, '', lp, 'B'); MEL.connect_material_expressions(pulse, '', lp, 'Alpha')
    e1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 800)
    MEL.connect_material_expressions(emt, 'RGB', e1, 'A'); MEL.connect_material_expressions(boost, '', e1, 'B')
    e2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 900)
    MEL.connect_material_expressions(e1, '', e2, 'A'); MEL.connect_material_expressions(lp, '', e2, 'B')
    MEL.connect_material_property(dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rg, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(e2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(MASTER)

def make_glass_liquid():
    """translucent potion glass (fresnel opacity, refraction) and a glowing liquid with a Color parameter."""
    out = {}
    for name in ('M_LP2Glass', 'M_LP2Liquid'):
        path = ROOT + '/Potions/' + name
        if EAL.does_asset_exist(path): out[name] = unreal.load_asset(path); continue
        m = tools.create_asset(name, ROOT + '/Potions', unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property('two_sided', True)
        try: m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        except Exception: pass
        fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -700, 200)
        rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 100); rough.set_editor_property('r', 0.05 if 'Glass' in name else 0.12)
        MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        if 'Glass' in name:
            col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, -100); col.set_editor_property('constant', unreal.LinearColor(0.9, 0.95, 0.9, 1))
            op = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, 250)
            op.set_editor_property('const_a', 0.10); op.set_editor_property('const_b', 0.65); MEL.connect_material_expressions(fr, '', op, 'Alpha')
            ior = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 400); ior.set_editor_property('r', 1.45)
            MEL.connect_material_property(ior, '', unreal.MaterialProperty.MP_REFRACTION)
        else:
            col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -700, -100); col.set_editor_property('parameter_name', 'Color')
            col.set_editor_property('default_value', unreal.LinearColor(0.75, 0.03, 0.02, 1))
            glow = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 50); glow.set_editor_property('parameter_name', 'Glow')
            glow.set_editor_property('default_value', 1.5)
            em = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -400, 0)
            MEL.connect_material_expressions(col, '', em, 'A'); MEL.connect_material_expressions(glow, '', em, 'B')
            MEL.connect_material_property(em, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            op = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, 250)
            op.set_editor_property('const_a', 0.72); op.set_editor_property('const_b', 0.95); MEL.connect_material_expressions(fr, '', op, 'Alpha')
        MEL.connect_material_property(col, '', unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(op, '', unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(m); EAL.save_asset(path); out[name] = m
    return out

for item in pick:
    folder, mesh, tn, emis = ITEMS[item]
    DST = ROOT + '/' + folder
    SETTINGS = {'_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
                '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
                '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
    if emis: SETTINGS['_Emissive'] = (True, unreal.TextureCompressionSettings.TC_DEFAULT)
    tools.import_asset_tasks([task(os.path.join(SRC, item, 'textures', tn + s + '.png'), DST) for s in SETTINGS])
    for s, (srgb, comp) in SETTINGS.items():
        t = unreal.load_asset('%s/%s%s' % (DST, tn, s))
        t.modify(); t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
        if 'Normal' in s: t.set_editor_property('flip_green_channel', False)
        EAL.save_loaded_asset(t)
    if not EAL.does_asset_exist(MASTER):
        make_master(DST + '/' + tn, (DST + '/' + tn + '_Emissive') if emis else '/Engine/EngineResources/Black')
    tools.import_asset_tasks([task(os.path.join(SRC, item, mesh + '.fbx'), DST, fbx_ui())])
    MI = '%s/MI_%s' % (DST, mesh[3:])
    mi = unreal.load_asset(MI) if EAL.does_asset_exist(MI) else tools.create_asset('MI_' + mesh[3:], DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
    for pn, s in (('BaseColor', '_BaseColor'), ('ORM', '_ORM'), ('Normal', '_Normal_DirectX')) + ((('Emissive', '_Emissive'),) if emis else ()):
        MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s%s' % (DST, tn, s)))
    if not emis: MEL.set_material_instance_scalar_parameter_value(mi, 'EmissiveBoost', 0.0)
    EAL.save_asset(MI)
    sm = unreal.load_asset('%s/%s' % (DST, mesh))
    sm.set_material(0, mi)
    if item in LIQUID:   # slots 1 and 2: the glass and the liquid
        gl = make_glass_liquid()
        LMI = '%s/MI_%s_Liquid' % (DST, mesh[3:])
        lmi = unreal.load_asset(LMI) if EAL.does_asset_exist(LMI) else tools.create_asset('MI_%s_Liquid' % mesh[3:], DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(lmi, gl['M_LP2Liquid'])
        MEL.set_material_instance_vector_parameter_value(lmi, 'Color', unreal.LinearColor(*LIQUID[item], 1)); EAL.save_asset(LMI)
        for i, sl in enumerate(sm.static_materials):
            nm = str(sl.material_slot_name)
            if 'Glass' in nm: sm.set_material(i, gl['M_LP2Glass'])
            elif 'Liquid' in nm: sm.set_material(i, lmi)
            else: sm.set_material(i, mi)
    opts = unreal.EditorScriptingMeshReductionOptions()
    opts.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0), unreal.EditorScriptingMeshReductionSettings(0.5, 0.3),
                               unreal.EditorScriptingMeshReductionSettings(0.25, 0.12)]
    opts.auto_compute_lod_screen_size = False
    SML.set_lods(sm, opts)
    SML.remove_collisions(sm)
    SML.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
    try:
        if not sm.find_socket('Grip'):
            sk = unreal.StaticMeshSocket(sm); sk.set_editor_property('socket_name', 'Grip'); sm.add_socket(sk)
    except Exception as e:
        unreal.log_warning('%s: Grip socket not added (%s); the pivot is the grip anyway' % (mesh, e))
    EAL.save_loaded_asset(sm)
    unreal.log('laptop2 weapon pack: %s imported to %s' % (item, DST))
