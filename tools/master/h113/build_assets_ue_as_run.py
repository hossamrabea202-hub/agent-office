"""Run ONLY by the authorized UE editor operator, outside PIE.

Creates new assets only. Refuses an existing output folder; never touches the
soldier Blueprints, character materials, maps, Lumen or post-process settings.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = '/Game/Codex/AssignmentMarkers102_v1'


def main(u):
    lib = u.MaterialEditingLibrary
    assets = u.AssetToolsHelpers.get_asset_tools()
    editor = u.EditorAssetLibrary
    required = [ROOT/'shaders'/'OrderGround.hlsl', ROOT/'shaders'/'OrderAir.hlsl',
                ROOT/'meshes'/'SM_Assignment102_AirRim.obj', ROOT/'orders.json']
    for file in required:
        if not file.is_file() or file.stat().st_size == 0:
            raise RuntimeError('Missing source file: '+str(file))
    if editor.does_directory_exist(DEST):
        raise RuntimeError('Output already exists. Use a NEW versioned DEST; do not overwrite '+DEST)
    report = {'destination': DEST, 'created': [], 'existing_assets_modified': False,
              'project_settings_modified': False, 'blueprints_modified': False,
              'compile_pass_confirmed': False, 'play_tested': False}

    def create(name, cls, factory):
        value = assets.create_asset(name, DEST, cls, factory)
        if not value:
            raise RuntimeError('Asset creation failed: '+name)
        report['created'].append(value.get_path_name())
        return value

    def node(mat, cls, x, y):
        result = lib.create_material_expression(mat, cls, x, y)
        if result is None:
            raise RuntimeError('Could not create expression '+str(cls))
        return result

    def connect(a, output, b, input_name):
        # Editor releases sometimes expose the native DepthFade pin as InOpacity.
        if isinstance(b, u.MaterialExpressionDepthFade):
            available = list(lib.get_material_expression_input_names(b))
            if input_name not in available:
                alias = {'Opacity': 'InOpacity'}.get(input_name)
                if alias in available:
                    input_name = alias
        if lib.connect_material_expressions(a, output, b, input_name):
            return
        # UE 5.3 python names some single-input pins '' (ComponentMask, DepthFade opacity): retry with the real names
        for alt in [''] + list(lib.get_material_expression_input_names(b)):
            if alt != input_name and lib.connect_material_expressions(a, output, b, alt):
                u.log('connect: used input %r instead of %r on %s' % (alt, input_name, b.get_name()))
                return
        raise RuntimeError('Connection failed: '+str(a)+' -> '+input_name)

    def property_link(a, output, prop):
        if not lib.connect_material_property(a, output, prop):
            raise RuntimeError('Material property connection failed: '+str(prop))

    collection = create('MPC_Assignment102', u.MaterialParameterCollection,
                        u.MaterialParameterCollectionFactoryNew())
    show = u.CollectionScalarParameter()
    show.set_editor_property('parameter_name', 'ShowMarkers')
    show.set_editor_property('default_value', 1.0)
    collection.set_editor_property('scalar_parameters', [show])
    editor.save_loaded_asset(collection)

    def build_material(name, code_file, is_ground):
        mat = create(name, u.Material, u.MaterialFactoryNew())
        mat.set_editor_property('material_domain', u.MaterialDomain.MD_DEFERRED_DECAL if is_ground else u.MaterialDomain.MD_SURFACE)
        mat.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('two_sided', not is_ground)
        if not is_ground:
            mat.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
            mat.set_editor_property('disable_depth_test', False)
        uv = node(mat, u.MaterialExpressionTextureCoordinate, -950, -200)
        style = node(mat, u.MaterialExpressionScalarParameter, -950, -80)
        style.set_editor_property('parameter_name', 'StyleIndex')
        style.set_editor_property('default_value', 0.0)
        tint = node(mat, u.MaterialExpressionVectorParameter, -950, 40)
        tint.set_editor_property('parameter_name', 'MarkerTint')
        tint.set_editor_property('default_value', u.LinearColor(1,1,1,1))
        strength = node(mat, u.MaterialExpressionScalarParameter, -950, 170)
        strength.set_editor_property('parameter_name', 'MarkerStrength')
        strength.set_editor_property('default_value', 0.70 if is_ground else 6.0)
        visible = node(mat, u.MaterialExpressionCollectionParameter, -950, 290)
        visible.set_editor_property('collection', collection)
        visible.set_editor_property('parameter_name', 'ShowMarkers')
        custom = node(mat, u.MaterialExpressionCustom, -500, 0)
        custom.set_editor_property('description', 'Assignment102 shared semantic order marker')
        custom.set_editor_property('code', (ROOT/'shaders'/code_file).read_text())
        custom.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT4)
        inputs=[]
        for name in ['UV','Style','Tint','Strength','Show']:
            item=u.CustomInput();item.set_editor_property('input_name',name);inputs.append(item)
        custom.set_editor_property('inputs',inputs)
        for expr,out,pin in [(uv,'','UV'),(style,'','Style'),(tint,'','Tint'),
                             (strength,'','Strength'),(visible,'','Show')]:
            connect(expr,out,custom,pin)
        rgb=node(mat,u.MaterialExpressionComponentMask,-150,-100)
        for k,v in {'r':True,'g':True,'b':True,'a':False}.items():rgb.set_editor_property(k,v)
        connect(custom,'',rgb,'Input')
        alpha=node(mat,u.MaterialExpressionComponentMask,-150,130)
        for k,v in {'r':False,'g':False,'b':False,'a':True}.items():alpha.set_editor_property(k,v)
        connect(custom,'',alpha,'Input')
        if is_ground:
            property_link(rgb,'',u.MaterialProperty.MP_BASE_COLOR)
            dim=node(mat,u.MaterialExpressionMultiply,80,-50);dim.set_editor_property('const_b',0.15)
            connect(rgb,'',dim,'A');property_link(dim,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
            property_link(alpha,'',u.MaterialProperty.MP_OPACITY)
        else:
            fade=node(mat,u.MaterialExpressionDepthFade,80,130)
            fade.set_editor_property('fade_distance_default',6.0)
            connect(alpha,'',fade,'Opacity')
            property_link(rgb,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
            property_link(fade,'',u.MaterialProperty.MP_OPACITY)
        lib.recompile_material(mat)
        editor.save_loaded_asset(mat)
        return mat

    ground=build_material('M_Assignment102_Ground','OrderGround.hlsl',True)
    air=build_material('M_Assignment102_Air','OrderAir.hlsl',False)
    # Prefer the included FBX; OBJ remains a rebuildable fallback. Inspect bounds.
    mesh_source = ROOT/'meshes'/'SM_Assignment102_AirRim.fbx'
    if not mesh_source.exists():
        mesh_source = ROOT/'meshes'/'SM_Assignment102_AirRim.obj'
    report['mesh_source'] = mesh_source.name
    task=u.AssetImportTask()
    options=u.FbxImportUI()
    for key,value in {'import_mesh':True,'import_as_skeletal':False,
                      'import_materials':False,'import_textures':False}.items():
        options.set_editor_property(key,value)
    options.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
    data=options.get_editor_property('static_mesh_import_data')
    for key,value in {'combine_meshes':True,'auto_generate_collision':False,
                      'generate_lightmap_u_vs':False,'import_uniform_scale':1.0}.items():
        data.set_editor_property(key,value)
    for key,value in {'filename':str(mesh_source),
                      'destination_path':DEST,'destination_name':'SM_Assignment102_AirRim',
                      'automated':True,'replace_existing':False,'save':True,'options':options}.items():
        task.set_editor_property(key,value)
    assets.import_asset_tasks([task])
    mesh=editor.load_asset(DEST+'/SM_Assignment102_AirRim')
    if mesh is None:
        raise RuntimeError('Mesh import failed; inspect editor log. Do not continue with an empty component.')
    mesh.set_material(0,air);editor.save_loaded_asset(mesh)
    report['created'].append(mesh.get_path_name())
    # Native dimensions must be verified in the editor; OBJ axis conversion can vary.
    try:
        box=mesh.get_bounding_box()
        report['mesh_bounds']=str(box)
    except Exception as exc:
        report['mesh_bounds_query_error']=str(exc)
    styles=json.loads((ROOT/'orders.json').read_text())['styles']
    for entry in styles:
        for label,parent in [('Ground',ground),('Air',air)]:
            mi=create('MI_Assignment102_'+label+'_'+str(entry['id']),u.MaterialInstanceConstant,
                      u.MaterialInstanceConstantFactoryNew())
            lib.set_material_instance_parent(mi,parent)
            if not lib.set_material_instance_scalar_parameter_value(mi,'StyleIndex',float(entry['id'])):
                u.log_warning('StyleIndex not settable yet on '+mi.get_path_name()+' (parent still compiling); the marker uses MIDs, so this preview MI is optional')
            lib.update_material_instance(mi);editor.save_loaded_asset(mi)
    report['recompile_requested']=True
    report['next_checks']=['Inspect shader errors and both domains in UE5.3',
        'Confirm imported bounds approx 135 x 135 x 16 cm with Z vertical',
        'Build BP_AssignmentMarker102 per BLUEPRINT_SETUP.md, paste graphs, compile',
        'Apply fresh raw order mapping; do not treat semantic StyleIndex as raw Order',
        'Play-test uneven terrain, death, Settings toggle and 60/120-unit crowd']
    report_path=ROOT/'reports'/'ue-build-result.json'
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('ASSIGNMENT102_ASSETS_CREATED '+str(report_path))
    return report


if __name__=='__main__':
    import unreal
    main(unreal)
