import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
for n in ['M_BerserkAura','M_BerserkEmber','M_BerserkGround','M_BerserkWisp']:
    p='/Game/CastleDefender/VFX/Berserk/'+n; m=unreal.load_asset(p)
    before={k:m.get_editor_property(k) for k in ('used_with_niagara_sprites','used_with_niagara_mesh_particles','used_with_niagara_ribbons','used_with_skeletal_mesh','used_with_static_lighting')}
    print(n,'blend',m.get_editor_property('blend_mode'),'shading',m.get_editor_property('shading_model'),'before',before,'nexpr',MEL.get_num_material_expressions(m))
    for k in ('used_with_niagara_sprites','used_with_niagara_mesh_particles','used_with_niagara_ribbons','used_with_skeletal_mesh'):
        m.set_editor_property(k,True)
    MEL.recompile_material(m); print('  saved',EAL.save_asset(p))
