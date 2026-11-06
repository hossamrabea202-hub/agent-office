import unreal
MEL=unreal.MaterialEditingLibrary
mi=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3')
L=[]
p=mi
while isinstance(p, unreal.MaterialInstance):
    L.append('MI %s'%p.get_path_name()); p=p.get_editor_property('parent')
m=p; L.append('base %s blend %s shading %s twosided %s'%(m.get_path_name(),m.get_editor_property('blend_mode'),m.get_editor_property('shading_model'),m.get_editor_property('two_sided')))
for prop in ['translucency_lighting_mode','disable_depth_test','output_translucent_velocity','used_with_static_lighting']:
    try: L.append('%s=%s'%(prop,m.get_editor_property(prop)))
    except Exception: pass
for p in MEL.get_scalar_parameter_names(m): L.append('scalar %s=%s'%(p,MEL.get_material_default_scalar_parameter_value(m,p)))
seen=set()
def walk(e,d=0):
    if e is None or e in seen or d>40: return
    seen.add(e); n=e.get_class().get_name()
    extra=''
    if n=='MaterialExpressionCustom': extra=' CODE:'+e.get_editor_property('code')[:1500].replace('\n',' ')
    if n in('MaterialExpressionScalarParameter',): extra=' '+str(e.get_editor_property('parameter_name'))
    L.append('  '*min(d,10)+n+extra)
    for i in MEL.get_inputs_for_material_expression(m,e): walk(i,d+1)
for prop in [unreal.MaterialProperty.MP_OPACITY, unreal.MaterialProperty.MP_EMISSIVE_COLOR]:
    L.append('== '+str(prop)); walk(MEL.get_material_property_input_node(m,prop))
open(r'C:/Users/hossa/Documents/agent-office/_bubmat_out.txt','w').write('\n'.join(L))
