# #451: import SM_FirePitLogs451 (blender/out, built by blender/campfire_logs451.py) as a NEW asset and give it the project's
# firewood materials (bark on slot 0, end grain on slot 1). No existing asset is changed. Saves only the new mesh.
import unreal
SRC = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/blender/out/SM_FirePitLogs451.fbx'
DST = '/Game/CastleDefender/Props/FirePit451'
EAL = unreal.EditorAssetLibrary
t = unreal.AssetImportTask(); t.filename = SRC; t.destination_path = DST; t.automated = True; t.replace_existing = True; t.save = False
o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = False
o.static_mesh_import_data.generate_lightmap_u_vs = True; t.options = o
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
m = unreal.load_asset(DST + '/SM_FirePitLogs451')
mats = ['/Game/CastleDefender/Props/AshenGate/Materials/M_AshenGate_FirewoodBark', '/Game/CastleDefender/Props/AshenGate/Materials/M_AshenGate_FirewoodEnd']
for i, p in enumerate(mats):
    if EAL.does_asset_exist(p): m.set_material(i, unreal.load_asset(p))
b = m.get_bounding_box(); print('imported', m.get_path_name(), 'bbox', b.min, b.max, 'slots', [s.material_interface.get_name() if s.material_interface else None for s in m.static_materials])
EAL.save_asset(DST + '/SM_FirePitLogs451')
