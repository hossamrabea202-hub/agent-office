import unreal
MEL=unreal.MaterialEditingLibrary
r=unreal.AssetRegistryHelpers.get_asset_registry()
L=[]
mats=[x for x in r.get_assets_by_path('/Game',True) if 'jellyblob' in str(x.asset_name).lower() or 'jelly_blob' in str(x.asset_name).lower()]
for x in mats: L.append('%s %s'%(x.package_name, x.asset_class_path.asset_name))
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
seen={}
for a in E.get_all_level_actors():
    for c in a.get_components_by_class(unreal.MeshComponent):
        for i in range(c.get_num_materials()):
            m=c.get_material(i)
            if m and 'jelly' in m.get_name().lower() and 'mine' not in m.get_name().lower():
                k=(a.get_class().get_name(), c.get_name(), m.get_path_name()); seen[k]=seen.get(k,0)+1
for k,v in seen.items(): L.append('used %s x%d'%(k,v))
def dump(path):
    m=unreal.load_asset(path)
    if not isinstance(m, unreal.Material): return
    L.append('== %s blend %s shading %s twosided %s'%(path, m.get_editor_property('blend_mode'), m.get_editor_property('shading_model'), m.get_editor_property('two_sided')))
    seen2=set()
    def walk(e,d):
        if e is None or e in seen2 or d>25: return
        seen2.add(e); n=e.get_class().get_name(); ex=''
        if n=='MaterialExpressionCustom': ex=' CODE:'+e.get_editor_property('code')[:2500].replace('\n',' ')
        if 'Parameter' in n:
            try: ex=' %s=%s'%(e.get_editor_property('parameter_name'), e.get_editor_property('default_value'))
            except Exception: pass
        if 'Constant' in n:
            try: ex=' %s'%(e.get_editor_property('constant') if n=='MaterialExpressionConstant' else '')
            except Exception: pass
        L.append('  '*min(d,8)+n+ex)
        for i in MEL.get_inputs_for_material_expression(m,e): walk(i,d+1)
    for p in ['MP_BASE_COLOR','MP_EMISSIVE_COLOR','MP_OPACITY','MP_ROUGHNESS','MP_METALLIC','MP_SPECULAR','MP_NORMAL','MP_SUBSURFACE_COLOR','MP_REFRACTION']:
        pr=getattr(unreal.MaterialProperty,p,None)
        if pr is None: continue
        n=MEL.get_material_property_input_node(m,pr)
        if n: L.append('# '+p); walk(n,1)
for x in mats:
    if str(x.asset_class_path.asset_name)=='Material': dump(str(x.package_name))
open(r'C:/Users/hossa/Documents/agent-office/_blobmat_out.txt','w').write('\n'.join(L))
