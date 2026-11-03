# #440 (i5): read-only: the materials on the grass meshes, their parent and every parameter value. Aborts in PIE.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
MEL = unreal.MaterialEditingLibrary
seen = set()
for p in ('/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vczndjqja/Raw/SM_vczndjqja_VarA',
          '/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vlkhcbxia/Raw/SM_vlkhcbxia_VarA',
          '/Game/CastleDefender/Environment/Landscape/Meshes/Plants/SM_MWAM_GrassA'):
    m = unreal.load_asset(p)
    for s in m.static_materials:
        mi = s.material_interface
        if not mi or mi.get_path_name() in seen: continue
        seen.add(mi.get_path_name())
        par = mi.get_editor_property('parent') if isinstance(mi, unreal.MaterialInstance) else None
        print('MESH', m.get_name(), 'MAT', mi.get_path_name(), 'PARENT', par.get_path_name() if par else None)
        if isinstance(mi, unreal.MaterialInstance):
            for n in MEL.get_scalar_parameter_names(mi): print('   S', n, round(MEL.get_material_instance_scalar_parameter_value(mi, n), 3))
            for n in MEL.get_vector_parameter_names(mi): print('   V', n, MEL.get_material_instance_vector_parameter_value(mi, n))
            for n in MEL.get_texture_parameter_names(mi):
                t = MEL.get_material_instance_texture_parameter_value(mi, n); print('   T', n, t.get_name() if t else None)
