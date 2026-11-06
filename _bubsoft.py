# Copy of the bubble material where the skin fades out softly where it touches/cuts through cliffs (DepthFade).
# Original M_RealmBubble3 / MI_RealmBubble3 untouched. Nothing is assigned to the bubble.
import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
SRC='/Game/CastleDefender/Realm/M_RealmBubble3'; DST='/Game/CastleDefender/Realm/M_RealmBubble3_Soft'
MIS='/Game/CastleDefender/Realm/MI_RealmBubble3'; MID='/Game/CastleDefender/Realm/MI_RealmBubble3_Soft'
L=[]
for p in (DST,MID):
    if EAL.does_asset_exist(p): EAL.delete_asset(p)
EAL.duplicate_asset(SRC,DST); m=unreal.load_asset(DST)
op=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
sp=MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 500)
sp.set_editor_property('parameter_name','ContactFade'); sp.set_editor_property('default_value',600.0)
df=MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade, -400, 450)
MEL.connect_material_expressions(sp,'',df,'FadeDistance')
mul=MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 400)
MEL.connect_material_expressions(op,'',mul,'A'); MEL.connect_material_expressions(df,'',mul,'B')
MEL.connect_material_property(mul,'',unreal.MaterialProperty.MP_OPACITY)
MEL.recompile_material(m); EAL.save_asset(DST)
EAL.duplicate_asset(MIS,MID); mi=unreal.load_asset(MID)
MEL.set_material_instance_parent(mi, m); MEL.update_material_instance(mi); EAL.save_asset(MID)
L.append('made %s + %s, ContactFade 600 cm'%(DST,MID))
open(r'C:/Users/hossa/Documents/agent-office/_bubsoft_out.txt','w').write('\n'.join(L))
