import unreal
MEL=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3')
L=[]
def walk(e,seen):
    if e is None or e in seen: return
    seen.add(e)
    if e.get_class().get_name()=='MaterialExpressionCustom':
        L.append('=== %s out=%s inputs=%s'%(e.get_editor_property('description'),e.get_editor_property('output_type'),[str(i.get_editor_property('input_name')) for i in e.get_editor_property('inputs')]))
        L.append(e.get_editor_property('code'))
        try: L.append('extra outputs %s'%[str(o.get_editor_property('output_name')) for o in e.get_editor_property('additional_outputs')])
        except Exception: pass
    elif e.get_class().get_name()=='MaterialExpressionComponentMask':
        L.append('mask r%s g%s b%s a%s'%(e.get_editor_property('r'),e.get_editor_property('g'),e.get_editor_property('b'),e.get_editor_property('a')))
    for i in MEL.get_inputs_for_material_expression(m,e): walk(i,seen)
for p in [unreal.MaterialProperty.MP_OPACITY, unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_NORMAL]:
    L.append('##### %s'%p); walk(MEL.get_material_property_input_node(m,p),set())
open(r'C:/Users/hossa/Documents/agent-office/_bubcode_out.txt','w').write('\n'.join(L))
