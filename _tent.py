import unreal
M=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/CastleDefender/Environment/Tentacles/M_CorruptedTentacle_Ripple2')
print(type(m).__name__, M.get_scalar_parameter_names(m), M.get_vector_parameter_names(m), M.get_texture_parameter_names(m))
print('shading', m.get_editor_property('shading_model'), 'blend', m.get_editor_property('blend_mode'), 'n', M.get_num_material_expressions(m))
seen=[]; st=[]
for prop in ('MP_BASE_COLOR','MP_EMISSIVE_COLOR','MP_NORMAL','MP_ROUGHNESS','MP_OPACITY','MP_SUBSURFACE_COLOR','MP_SPECULAR','MP_METALLIC','MP_AMBIENT_OCCLUSION'):
    try:
        e=M.get_material_property_input_node(m,getattr(unreal.MaterialProperty,prop))
        print(prop,'<-',e.get_name() if e else None)
        if e: st.append(e)
    except Exception as ex: pass
while st:
    e=st.pop()
    if e in seen: continue
    seen.append(e)
    ins=[i for i in M.get_inputs_for_material_expression(m,e) if i]
    line='%s %s'%(e.get_class().get_name(), e.get_name())
    for p in ('parameter_name','texture','coordinate_index','u_tiling','v_tiling','r','constant','default_value','const_a','const_b'):
        try:
            v=e.get_editor_property(p); line+=' %s=%s'%(p, v.get_name() if hasattr(v,'get_name') else v)
        except Exception: pass
    line+=' <- [%s]'%', '.join(i.get_name() for i in ins)
    print(line); st+=ins
