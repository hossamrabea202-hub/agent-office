# Blood VFX fix, step 2b (i5 core, 2026-11-01): M_BloodDroplet_Mesh_337, a plain lit mesh material for the BloodBurst
# chunks (M_BloodParticle_337 reads Particle Color, so on a static mesh it renders white). Values: gore-337/RESEARCH.md
# + Blood337 README: wet core 60,18,12 sRGB (KB floor), thin-film edge 110,20,14 via fresnel, roughness 0.08, specular
# 0.28 (blood IOR 1.35), no emissive. Then puts it on BP_BloodBurst_337's chunks.
#   py "<repo>/handoffs/gore-337/blood_droplet_mat_ue.py"
import unreal
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
P, COPY = '/Game/CastleDefender/VFX/Blood337/M_BloodDroplet_Mesh_337', '/Game/CastleDefender/VFX/BP_BloodBurst_337'
lin = lambda s: ((s / 255.0) / 12.92) if s / 255.0 <= 0.04045 else (((s / 255.0) + 0.055) / 1.055) ** 2.4
m = unreal.load_asset(P)
if not m:
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_BloodDroplet_Mesh_337', P.rsplit('/', 1)[0], unreal.Material, unreal.MaterialFactoryNew())
MEL.delete_all_material_expressions(m)
core = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -600, 0)
core.set_editor_property('constant', unreal.LinearColor(lin(60), lin(18), lin(12), 1))
edge = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -600, 150)
edge.set_editor_property('constant', unreal.LinearColor(lin(110), lin(20), lin(14), 1))
fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -600, 300)
lp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 100)
MEL.connect_material_expressions(core, '', lp, 'A'); MEL.connect_material_expressions(edge, '', lp, 'B'); MEL.connect_material_expressions(fr, '', lp, 'Alpha')
MEL.connect_material_property(lp, '', unreal.MaterialProperty.MP_BASE_COLOR)
for val, prop, y in ((0.08, unreal.MaterialProperty.MP_ROUGHNESS, 450), (0.28, unreal.MaterialProperty.MP_SPECULAR, 550)):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, y); c.set_editor_property('r', val)
    MEL.connect_material_property(c, '', prop)
MEL.recompile_material(m); EAL.save_asset(P)
bp = unreal.load_asset(COPY); seen, n = set(), 0
for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
    c = LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))
    if isinstance(c, unreal.StaticMeshComponent) and c.get_name() not in seen:
        seen.add(c.get_name()); c.set_editor_property('override_materials', [m]); n += 1
BEL.compile_blueprint(bp); EAL.save_asset(COPY)
unreal.log('I5CHK droplet mat built, %d chunks on BP_BloodBurst_337' % n)
