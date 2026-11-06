import unreal
M=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/CastleDefender/VFX/JellyBubble/M_TentacleJellyShell')
out=['blend %s shading %s'%(m.get_editor_property('blend_mode'), m.get_editor_property('shading_model'))]
seen=[]; st=[]
for prop in dir(unreal.MaterialProperty):
    if not prop.startswith('MP_'): continue
    try:
        e=M.get_material_property_input_node(m,getattr(unreal.MaterialProperty,prop))
        if e: out.append('%s <- %s'%(prop,e.get_name())); st.append(e)
    except Exception: pass
while st:
    e=st.pop()
    if e in seen: continue
    seen.append(e); ins=[i for i in M.get_inputs_for_material_expression(m,e) if i]; st+=ins
    line='%s %s <- [%s]'%(e.get_class().get_name(), e.get_name(), ', '.join(i.get_name() for i in ins))
    for p in ('parameter_name','texture','default_value','input_name'):
        try: v=e.get_editor_property(p); line+=' %s=%s'%(p, v.get_name() if hasattr(v,'get_name') else v)
        except Exception: pass
    out.append(line)
    if isinstance(e, unreal.MaterialExpressionCustom):
        out.append('  inputs %s outputs %s'%([str(i.get_editor_property('input_name')) for i in e.get_editor_property('inputs')], [str(o.get_editor_property('output_name')) for o in e.get_editor_property('additional_outputs')]))
        out.append(e.get_editor_property('code'))
open(r'C:/Users/hossa/Documents/agent-office/_shell.txt','w').write('\n'.join(out))
