import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lay=MEL.get_inputs_for_material_expression(m,emn)[0]; assert lay.get_editor_property('description')=='RealmLayers4to9'
    lc=lay.get_editor_property('code').replace('   // deep inside the jelly','\n')
    lay.set_editor_property('code',lc)
    cel=MEL.get_inputs_for_material_expression(m,lay)[0]
    cc=cel.get_editor_property('code').replace('   // sits inside the skin','\n')
    cel.set_editor_property('code',cc)
    MEL.recompile_material(m); L.append('fixed; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
