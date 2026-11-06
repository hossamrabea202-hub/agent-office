import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lay=MEL.get_inputs_for_material_expression(m,emn)[0]
    cel=MEL.get_inputs_for_material_expression(m,lay)[0]; assert cel.get_editor_property('description')=='RealmMembraneCells'
    cc=cel.get_editor_property('code')
    cc=cc.replace('wall * breathe * (0.35 + 0.65 * fres)','wall * breathe * (1.0 - fres)')          # fade at the silhouette: no outline
    cc=cc.replace('(wall * 0.12 * fres + coreGlow * 0.2)','(coreGlow * 0.2)')                       # walls add no opacity
    cel.set_editor_property('code',cc)
    lc=lay.get_editor_property('code')
    lc=lc.replace('op += ridge * 0.08 * L7 * near;','')                                              # veins add light only
    lc=lc.replace('em += float3(0.75, 0.05, 0.09) * ridge * throb * L7 * near * 0.8;','em += float3(0.75, 0.05, 0.09) * ridge * throb * L7 * near * 0.8 * (1.0 - fres);')
    lay.set_editor_property('code',lc)
    MEL.recompile_material(m); EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    mi=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Inner')
    for n,v in [('Layer4_Marble',0.0),('Layer8_Aurora',0.0),('CellOpacity',0.0),('OpacityHead',0.0),('OpacityRim',0.0),('FilmGlow',0.0)]:
        MEL.set_material_instance_scalar_parameter_value(mi,n,v)
    MEL.update_material_instance(mi); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Inner'); L.append('inner invisible ok')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
