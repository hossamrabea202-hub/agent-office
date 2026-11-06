import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lay=MEL.get_inputs_for_material_expression(m,emn)[0]; assert lay.get_editor_property('description')=='RealmLayers4to9'
    c=lay.get_editor_property('code')
    old='float3 marble = 0.5 + 0.5 * cos(6.2831853 * (flowv * 0.15 + float3(0.0, 0.33, 0.67)));'
    new=('float mph = 0.5 + 0.5 * sin(flowv * 0.94);\n'
         'float3 marble = lerp(lerp(float3(1.0, 0.25, 0.6), float3(1.0, 0.55, 0.22), mph), float3(0.6, 0.25, 1.0), 0.5 + 0.5 * sin(flowv * 0.53 + 1.7)) * 0.8;   // pink / orange / violet only')
    if old in c: c=c.replace(old,new); lay.set_editor_property('code',c); L.append('marble palette warm')
    else: L.append('marble line not found')
    MEL.recompile_material(m); EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    for p in ['/Game/CastleDefender/Realm/MI_RealmBubble3_Dream']:
        mi=unreal.load_asset(p); MEL.set_material_instance_scalar_parameter_value(mi,'WormWarmth',0.75); MEL.update_material_instance(mi); EAL.save_asset(p)
    L.append('saved')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_opt_out.txt','w').write('\n'.join(L))
