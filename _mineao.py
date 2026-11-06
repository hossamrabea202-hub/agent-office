import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary; BEL=unreal.BlueprintEditorLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools()
D='/Game/CastleDefender/Environment/Flora/BlobMine'
# 1) flesh too bright: the subsurface was lighting the whole body salmon -> plain lit, dark wet flesh
fm=unreal.load_asset(D+'/M_FleshSlime')
fm.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
MEL.recompile_material(fm); EAL.save_asset(D+'/M_FleshSlime')
print('flesh -> DefaultLit')
# 2) ground ambient under the mine: a dark wet contact stain decal (new asset, never touches existing decals)
P=D+'/M_BlobMineContactAO'
if not EAL.does_asset_exist(P):
    m=tools.create_asset('M_BlobMineContactAO', D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('material_domain', unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    g=MEL.create_material_expression(m, unreal.MaterialExpressionRadialGradientExponential, -600, 200)
    g.set_editor_property('radius', 0.5) if hasattr(g,'radius') else None
    k=MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 400); k.set_editor_property('parameter_name','Strength'); k.set_editor_property('default_value',0.8)
    mul=MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 300)
    MEL.connect_material_expressions(g,'',mul,'A'); MEL.connect_material_expressions(k,'',mul,'B')
    c=MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, -100); c.set_editor_property('constant', unreal.LinearColor(0.012,0.009,0.007,1))
    r=MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 100); r.set_editor_property('r', 0.35)
    MEL.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mul,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_asset(P); print('made', P)
mat=unreal.load_asset(P)
bpp=None
for a in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path('/Game',True):
    if str(a.asset_name)=='BP_BlobMine' and str(a.asset_class_path.asset_name)=='Blueprint': bpp=str(a.package_name)
bp=unreal.load_asset(bpp)
SDS=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L=unreal.SubobjectDataBlueprintFunctionLibrary
hs=SDS.k2_gather_subobject_data_for_blueprint(bp)
names=[str(L.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) for h in hs]
if 'ContactAO' not in names:
    p=unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=unreal.DecalComponent, blueprint_context=bp)
    h,fail=SDS.add_new_subobject(p); SDS.rename_subobject(h, unreal.Text('ContactAO'))
    hs=SDS.k2_gather_subobject_data_for_blueprint(bp)
for h in hs:
    d=SDS.k2_find_subobject_data_from_handle(h)
    if str(L.get_variable_name(d))=='ContactAO':
        o=L.get_object(d)
        o.set_editor_property('decal_material', mat)
        o.set_editor_property('decal_size', unreal.Vector(40,110,110))
        o.set_editor_property('relative_rotation', unreal.Rotator(0,-90,0))
        o.set_editor_property('relative_location', unreal.Vector(0,0,0))
        o.set_editor_property('sort_order', 5)
        print('ContactAO set')
BEL.compile_blueprint(bp); print('saved', EAL.save_asset(bpp))
