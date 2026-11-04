# #472 (i5, read-only): what one crowd unit costs to draw: triangles and sections per LOD, LOD settings, material domains and shading, components on the actor.
import unreal
SM = unreal.SkeletalMeshEditorSubsystem() if hasattr(unreal, 'SkeletalMeshEditorSubsystem') else None
BP = {'Zombie': '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', 'Soldier': '/Game/CastleDefender/Characters/Knight/BP_SoldierSword', 'Brute': '/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute'}
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); LIB = unreal.SubobjectDataBlueprintFunctionLibrary
def mesh_report(tag, sk):
    n = sk.get_lod_num() if hasattr(sk, 'get_lod_num') else -1
    tris = []
    for i in range(n if n > 0 else 1):
        try: tris.append(unreal.SkeletalMeshEditorSubsystem.get_num_verts(sk, i) if False else (SM.get_lod_count(sk) if False else None))
        except Exception: tris.append(None)
    info = sk.get_editor_property('lod_info') if False else None
    print('RIG %s mesh %s LODs %s bounds %s' % (tag, sk.get_name(), n, round(sk.get_bounds().sphere_radius)))
    try:
        for i in range(n):
            print('RIG   LOD%d verts %s' % (i, SM.get_num_verts(sk, i)))
    except Exception as e: print('RIG   verts err', e)
    for m in sk.get_editor_property('materials'):
        mi = m.get_editor_property('material_interface')
        if not mi: continue
        base = mi.get_base_material()
        print('RIG   slot %-24s %-34s blend %s shading %s twoSided %s' % (m.get_editor_property('material_slot_name'), mi.get_name(), base.get_editor_property('blend_mode').name, base.get_editor_property('shading_model').name, base.get_editor_property('two_sided')))
for tag, p in BP.items():
    bp = unreal.load_asset(p); rows = []
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        d = SDS.k2_find_subobject_data_from_handle(h); c = LIB.get_object(d)
        if isinstance(c, unreal.PrimitiveComponent):
            extra = ''
            if isinstance(c, unreal.SkinnedMeshComponent):
                sk = c.get_skinned_asset()
                extra = 'sk=%s shadow=%s urotick=%s lodbias=%s' % (sk.get_name() if sk else None, c.get_editor_property('cast_shadow'), c.get_editor_property('visibility_based_anim_tick_option').name, c.get_editor_property('forced_lod_model'))
                if sk: mesh_report(tag + '.' + str(LIB.get_variable_name(d)), sk)
            elif isinstance(c, unreal.StaticMeshComponent):
                sm = c.get_editor_property('static_mesh'); extra = 'sm=%s shadow=%s' % (sm.get_name() if sm else None, c.get_editor_property('cast_shadow'))
            rows.append('%s(%s) %s' % (LIB.get_variable_name(d), c.get_class().get_name(), extra))
    print('RIG %s prims: %s' % (tag, ' | '.join(rows)))
    print('RIG %s comps total: %d' % (tag, len(SDS.k2_gather_subobject_data_for_blueprint(bp))))
