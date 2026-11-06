# Depth (owner 00:43, item 4): parallax-shift inner layers along the view ray so they sit INSIDE the skin.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
def add_param(m,node,pin,name,val,x,y):
    ins=list(node.get_editor_property('inputs'))
    if pin in [str(i.get_editor_property('input_name')) for i in ins]: return
    ci=unreal.CustomInput(); ci.set_editor_property('input_name',pin); ins.append(ci); node.set_editor_property('inputs',ins)
    e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,x,y); e.set_editor_property('parameter_name',name); e.set_editor_property('default_value',val)
    MEL.connect_material_expressions(e,'',node,pin)
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lay=MEL.get_inputs_for_material_expression(m,emn)[0]; assert lay.get_editor_property('description')=='RealmLayers4to9'
    cel=MEL.get_inputs_for_material_expression(m,lay)[0]; assert cel.get_editor_property('description')=='RealmMembraneCells'
    # cells ~1.5 m inside
    cc=cel.get_editor_property('code')
    if 'CellDepth' not in cc:
        cc=cc.replace('float3 p = WP / Scale;',
          'float ndv0 = max(abs(dot(normalize(N), normalize(V))), 0.25);\nfloat3 p = (WP - normalize(V) * CellDepth / ndv0) / Scale;   // sits inside the skin')
        cc=cc.replace('float3 add = violet *','float3 add = 0.85 * violet *')
        cel.set_editor_property('code',cc); add_param(m,cel,'CellDepth','CellDepth',150.0,1800,2100)
    # veins ~4 m inside (dimmer, redder), marbling ~0.6 m
    lc=lay.get_editor_property('code')
    if 'VeinDepth' not in lc:
        lc=lc.replace('float3 vq = WP / VeinScale;','float ndvL = max(abs(dot(nN, vV)), 0.25);\nfloat3 vq = (WP - vV * VeinDepth / ndvL) / VeinScale;   // deep inside the jelly')
        lc=lc.replace('em += float3(0.9, 0.08, 0.12) * ridge * throb * L7 * near;','em += float3(0.75, 0.05, 0.09) * ridge * throb * L7 * near * 0.8;')
        lc=lc.replace('float3 q = WP / MarbleScale;','float3 q = (WP - vV * MarbleDepth / max(abs(dot(nN, vV)), 0.25)) / MarbleScale;')
        lay.set_editor_property('code',lc)
        add_param(m,lay,'VeinDepth','VeinDepth',400.0,2400,2600); add_param(m,lay,'MarbleDepth','MarbleDepth',60.0,2400,2660)
    MEL.recompile_material(m); L.append('depth; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
