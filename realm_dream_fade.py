import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
# near-wall fade for the vortex: the bubble wall right next to the camera stays a thin film (no striped edge)
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    em=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    cu=MEL.get_inputs_for_material_expression(m,em)[0]
    if cu.get_class().get_name()=='MaterialExpressionCustom' and 'NearFade' not in cu.get_editor_property('code'):
        code=cu.get_editor_property('code').replace('float inside = (Sgn < 0.0) ? saturate(Amt) : 0.0;',
            'float NearFade = smoothstep(1500.0, 7000.0, length(WP - Cam));\nfloat inside = (Sgn < 0.0) ? saturate(Amt) * NearFade : 0.0;')
        cu.set_editor_property('code',code)
        ins=list(cu.get_editor_property('inputs')); ci=unreal.CustomInput(); ci.set_editor_property('input_name','Cam'); ins.append(ci); cu.set_editor_property('inputs',ins)
        MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionCameraPositionWS,-700,1500),'',cu,'Cam')
        MEL.recompile_material(m); EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'); L.append('vortex near-wall fade added')
    else: L.append('vortex node %s / already faded'%cu.get_class().get_name())
except Exception as ex:
    import traceback; L.append('fade ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_dream_out.txt','w').write('\n'.join(L))
