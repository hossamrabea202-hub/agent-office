# Card #447 (i5, 2026-11-02): baked stone stairs, one watertight mesh per flight.
#   py apply_stairs447_ue.py assets <build_dir>        import mesh + textures, build M_Castle_StairBaked + 2 MIs, save ASSETS only
#   py apply_stairs447_ue.py place --dry-run           list what would be placed / hidden (default)
#   py apply_stairs447_ue.py place --apply             place the new flights, hide the old pieces (visibility + collision off)
#   py apply_stairs447_ue.py place --revert            remove the new flights, show the old pieces again
# The map is NOT saved by this script (i9 owns map saves). Old pieces are never deleted; the list of what was hidden is
# kept in Stairs447_hidden.json next to this script, so --revert restores exactly that.
# Live materials are not edited (decal rule): M_Castle_StairBaked is a duplicate of M_Castle_StoneWall_World.
import json, os, sys, unreal

HERE = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Environment/Castle/StairsBaked'
SRC_MAT = '/Game/CastleDefender/Shared/Materials/Castle/M_Castle_StoneWall_World'
MI_SRC = {'Tread': '/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_StepCap',
          'Body': '/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_StoneWall_World'}
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# asset name -> placements (world location, scale) and the old pieces each placement replaces (UE world boxes, cm)
STAIRS = {
    'SM_Stair447_Courtyard34': [
        {'label': 'Stair447_F2', 'loc': (1250, 495, 0), 'scale': (1, 1, 1),
         'old_boxes': [(1249, 494, -1, 2339, 726, 681), (1761, 729, -1, 2339, 771, 756)],
         'merged': ('CastleStones_0_0_4', 'SM_CastleStones_0_0_4_s447')},
        {'label': 'Stair447_F3', 'loc': (1250, 3005, 0), 'scale': (1, -1, 1),
         'old_boxes': [(1249, 2774, -1, 2339, 3006, 681), (1761, 2729, -1, 2339, 2771, 756)],
         'merged': ('CastleStones_0_1_6', 'SM_CastleStones_0_1_6_s447')},
    ],
}
# merged castle-stone meshes that held the stepped side stones of the lower flight: swapped for copies without them
MERGED_COPIES = ('SM_CastleStones_0_0_4_s447', 'SM_CastleStones_0_1_6_s447')
MERGED_MAT = '/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_StoneWall_World'
OLD_MESHES = ('SM_StairTread', 'SM_StoneModule', 'Cube')       # what a stair is made of today
OLD_MATS = ('MI_Castle_StepCap', 'MI_Castle_StoneWall_World', 'MI_Castle_Trim_World')
HIDDEN_JSON = os.path.join(HERE, 'Stairs447_hidden.json')


def find_in_project(name, cls):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', cls)):
        if str(a.asset_name) == name:
            return str(a.package_name)
    return None


def import_file(path, dest, name, options=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    if options:
        t.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return unreal.load_asset(dest + '/' + name)


def build_material():
    path = DST + '/M_Castle_StairBaked'
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    mat = EAL.duplicate_asset(SRC_MAT, path)
    def inp(prop):
        node = MEL.get_material_property_input_node(mat, prop)
        try:
            out = MEL.get_material_property_input_node_output_name(mat, prop)
        except Exception:
            out = ''
        return node, out
    X = -1400
    # baked textures (UV0)
    bn = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, X, 600)
    bn.set_editor_property('parameter_name', 'BakedNormal'); bn.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    bn.set_editor_property('texture', unreal.load_asset('/Engine/EngineMaterials/FlatNormal'))
    bm = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, X, 900)
    bm.set_editor_property('parameter_name', 'BakedMasks'); bm.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    bm.set_editor_property('texture', unreal.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
    def scalar(name, val, y):
        s = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, X, y)
        s.set_editor_property('parameter_name', name); s.set_editor_property('default_value', val)
        return s
    # normal: world-aligned stone normal + baked masonry normal (angle corrected)
    n0, n0o = inp(unreal.MaterialProperty.MP_NORMAL)
    blend = MEL.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, X + 500, 600)
    blend.set_editor_property('material_function', unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/Utility/BlendAngleCorrectedNormals'))
    if n0:
        MEL.connect_material_expressions(n0, n0o, blend, 'BaseNormal')
    MEL.connect_material_expressions(bn, 'RGB', blend, 'AdditionalNormal')
    MEL.connect_material_property(blend, '', unreal.MaterialProperty.MP_NORMAL)
    # base colour: mortar joints darker, per-stone tone variation
    c0, c0o = inp(unreal.MaterialProperty.MP_BASE_COLOR)
    jd = scalar('JointDarken', 0.45, 1100); tv = scalar('StoneToneVar', 0.10, 1200)
    j = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 300, 1100)
    MEL.connect_material_expressions(bm, 'G', j, 'A'); MEL.connect_material_expressions(jd, '', j, 'B')
    one_minus_j = MEL.create_material_expression(mat, unreal.MaterialExpressionOneMinus, X + 450, 1100)
    MEL.connect_material_expressions(j, '', one_minus_j, '')
    tone = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, X + 450, 1200)
    lo = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, X + 300, 1260); lo.set_editor_property('r', 1.0)
    sub = MEL.create_material_expression(mat, unreal.MaterialExpressionSubtract, X + 300, 1200)
    MEL.connect_material_expressions(lo, '', sub, 'A'); MEL.connect_material_expressions(tv, '', sub, 'B')
    add = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, X + 300, 1300)
    MEL.connect_material_expressions(lo, '', add, 'A'); MEL.connect_material_expressions(tv, '', add, 'B')
    MEL.connect_material_expressions(sub, '', tone, 'A'); MEL.connect_material_expressions(add, '', tone, 'B'); MEL.connect_material_expressions(bm, 'A', tone, 'Alpha')
    m1 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 650, 1150)
    MEL.connect_material_expressions(one_minus_j, '', m1, 'A'); MEL.connect_material_expressions(tone, '', m1, 'B')
    if c0:
        m2 = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 800, 1150)
        MEL.connect_material_expressions(c0, c0o, m2, 'A'); MEL.connect_material_expressions(m1, '', m2, 'B')
        MEL.connect_material_property(m2, '', unreal.MaterialProperty.MP_BASE_COLOR)
    # roughness: the worn foot path is polished
    r0, r0o = inp(unreal.MaterialProperty.MP_ROUGHNESS)
    if r0:
        wp = scalar('WearPolish', 0.25, 1400)
        wm = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 300, 1400)
        MEL.connect_material_expressions(bm, 'B', wm, 'A'); MEL.connect_material_expressions(wp, '', wm, 'B')
        om = MEL.create_material_expression(mat, unreal.MaterialExpressionOneMinus, X + 450, 1400)
        MEL.connect_material_expressions(wm, '', om, '')
        rm = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 650, 1400)
        MEL.connect_material_expressions(r0, r0o, rm, 'A'); MEL.connect_material_expressions(om, '', rm, 'B')
        MEL.connect_material_property(rm, '', unreal.MaterialProperty.MP_ROUGHNESS)
    # AO: baked cavities on top of whatever the stone material had
    a0, a0o = inp(unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    if a0:
        am = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, X + 650, 1500)
        MEL.connect_material_expressions(a0, a0o, am, 'A'); MEL.connect_material_expressions(bm, 'R', am, 'B')
        MEL.connect_material_property(am, '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    else:
        MEL.connect_material_property(bm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


def make_mi(kind, parent, tex_n, tex_m):
    path = DST + '/MI_StairBaked_' + kind
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    fac = unreal.MaterialInstanceConstantFactoryNew()
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_StairBaked_' + kind, DST, unreal.MaterialInstanceConstant, fac)
    MEL.set_material_instance_parent(mi, parent)
    src = unreal.load_asset(MI_SRC[kind])
    for n in MEL.get_scalar_parameter_names(src):
        MEL.set_material_instance_scalar_parameter_value(mi, n, MEL.get_material_instance_scalar_parameter_value(src, n))
    for n in MEL.get_vector_parameter_names(src):
        MEL.set_material_instance_vector_parameter_value(mi, n, MEL.get_material_instance_vector_parameter_value(src, n))
    for n in MEL.get_texture_parameter_names(src):
        t = MEL.get_material_instance_texture_parameter_value(src, n)
        if t:
            MEL.set_material_instance_texture_parameter_value(mi, n, t)
    MEL.set_material_instance_texture_parameter_value(mi, 'BakedNormal', tex_n)
    MEL.set_material_instance_texture_parameter_value(mi, 'BakedMasks', tex_m)
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi


def do_assets(build_dir):
    for name in STAIRS:
        ui = unreal.FbxImportUI()
        ui.import_mesh = True; ui.import_materials = False; ui.import_textures = False; ui.import_as_skeletal = False
        sm = ui.static_mesh_import_data
        sm.combine_meshes = True; sm.generate_lightmap_u_vs = True; sm.auto_generate_collision = False
        sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        sm.build_nanite = False
        mesh = import_file(os.path.join(build_dir, name + '_low.fbx'), DST, name, ui)
        tn = import_file(os.path.join(build_dir, name + '_N.png'), DST, 'T_' + name[3:] + '_N')
        tn.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        tn.set_editor_property('srgb', False); tn.set_editor_property('flip_green_channel', True)
        tm = import_file(os.path.join(build_dir, name + '_M.png'), DST, 'T_' + name[3:] + '_M')
        tm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        tm.set_editor_property('srgb', False)
        mat = build_material()
        mis = [make_mi('Tread', mat, tn, tm), make_mi('Body', mat, tn, tm)]
        mesh.set_material(0, mis[0]); mesh.set_material(1, mis[1])
        body = mesh.get_editor_property('body_setup')
        body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for a in (mesh, tn, tm):
            EAL.save_loaded_asset(a)
        b = mesh.get_bounding_box()
        print('assets OK', name, 'tris', mesh.get_num_triangles(0), 'bounds', b.min, b.max, 'slots', [m.get_name() for m in mis])
    for name in MERGED_COPIES:
        ui = unreal.FbxImportUI()
        ui.import_mesh = True; ui.import_materials = False; ui.import_textures = False; ui.import_as_skeletal = False
        sm = ui.static_mesh_import_data
        sm.combine_meshes = True; sm.generate_lightmap_u_vs = False; sm.auto_generate_collision = False
        sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        mesh = import_file(os.path.join(build_dir, name + '.fbx'), DST, name, ui)
        mesh.set_material(0, unreal.load_asset(MERGED_MAT))
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        EAL.save_loaded_asset(mesh)
        b = mesh.get_bounding_box()
        print('assets OK', name, 'tris', mesh.get_num_triangles(0), 'bounds', b.min, b.max)


def old_pieces(boxes):
    out = []
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith('Stair447_'):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = c.get_editor_property('static_mesh')
            if not sm or sm.get_name() not in OLD_MESHES or c.get_num_materials() == 0:
                continue
            m = c.get_material(0)
            if not m or m.get_name() not in OLD_MATS:
                continue
            o, e = a.get_actor_bounds(False)
            lo = (o.x - e.x, o.y - e.y, o.z - e.z); hi = (o.x + e.x, o.y + e.y, o.z + e.z)
            for bx in boxes:
                if all(lo[k] >= bx[k] - 0.5 and hi[k] <= bx[k + 3] + 0.5 for k in range(3)):
                    out.append((a, c)); break
    return out


def do_place(mode):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if mode == 'revert':
        for a in EAS.get_all_level_actors():
            if a.get_actor_label().startswith('Stair447_'):
                print('remove', a.get_actor_label()); EAS.destroy_actor(a)
        hidden = json.load(open(HIDDEN_JSON)) if os.path.exists(HIDDEN_JSON) else []
        for h in [h for h in hidden if 'mesh' in h]:
            for a in EAS.get_all_level_actors():
                if a.get_actor_label() == h['actor']:
                    a.static_mesh_component.set_static_mesh(unreal.load_asset(h['mesh']))
                    print('merged mesh restored on', h['actor'])
        hidden = [h for h in hidden if 'path' in h]
        names = {h['path'] for h in hidden}
        n = 0
        for a in EAS.get_all_level_actors():
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                if c.get_path_name() in names:
                    c.set_visibility(True); c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                    a.set_folder_path(next(h['folder'] for h in hidden if h['path'] == c.get_path_name())); n += 1
        print('revert: shown again', n, 'pieces (map NOT saved)')
        return
    record = []
    for name, places in STAIRS.items():
        mesh = unreal.load_asset(DST + '/' + name)
        for p in places:
            olds = old_pieces(p['old_boxes'])
            print('%s: place %s at %s scale %s, hide %d old pieces' % (mode, p['label'], p['loc'], p['scale'], len(olds)))
            for a, c in olds[:6]:
                print('     e.g.', a.get_actor_label(), c.get_editor_property('static_mesh').get_name(), a.get_folder_path())
            if mode != 'apply':
                continue
            if mesh is None:
                print('   MISSING asset', name, '- run "assets" first'); continue
            act = EAS.spawn_actor_from_object(mesh, unreal.Vector(*p['loc']), unreal.Rotator(0, 0, 0))
            act.set_actor_scale3d(unreal.Vector(*p['scale'])); act.set_actor_label(p['label'])
            act.set_folder_path('Castle/StairsBaked')
            for a, c in olds:
                record.append({'path': c.get_path_name(), 'folder': str(a.get_folder_path())})
                c.set_visibility(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                a.set_folder_path('Stairs_Old_447')
            label, copy = p['merged']
            for a in EAS.get_all_level_actors():
                if a.get_actor_label() == label:
                    old = a.static_mesh_component.get_editor_property('static_mesh')
                    record.append({'actor': label, 'mesh': old.get_path_name()})
                    a.static_mesh_component.set_static_mesh(unreal.load_asset(DST + '/' + copy))
                    print('   merged', label, old.get_name(), '->', copy)
    if mode == 'apply':
        json.dump(record, open(HIDDEN_JSON, 'w'), indent=0)
        print('apply: placed, hid %d old pieces (list in %s). Map NOT saved.' % (len(record), HIDDEN_JSON))


args = sys.argv[1:]
if args and args[0] == 'assets':
    do_assets(args[1])
elif args and args[0] == 'place':
    do_place('apply' if '--apply' in args else 'revert' if '--revert' in args else 'dry-run')
else:
    print(__doc__ if __doc__ else 'usage: assets <dir> | place [--dry-run|--apply|--revert]')
