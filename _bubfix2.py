# Real fix for the solid rainbow patches: the Fresnel rim is 1.0 on BACK faces (two-sided), so the inside of the far
# skin (seen where the near skin is buried in rock) glows at full rim. Copy: F = two-sided Fresnel (abs facing).
import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
SRC='/Game/CastleDefender/Realm/M_RealmBubble3'; DST='/Game/CastleDefender/Realm/M_RealmBubble3_Soft'
MIS='/Game/CastleDefender/Realm/MI_RealmBubble3'; MID='/Game/CastleDefender/Realm/MI_RealmBubble3_Soft'
L=[]
for p in (MID,DST):
    if EAL.does_asset_exist(p): EAL.delete_asset(p)
EAL.duplicate_asset(SRC,DST); m=unreal.load_asset(DST)
mask=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
cu=MEL.get_inputs_for_material_expression(m,mask)[0]
names=[str(i.get_editor_property('input_name')) for i in cu.get_editor_property('inputs')]
ins=MEL.get_inputs_for_material_expression(m,cu)
fr=ins[names.index('F')]
ex=5.0; br=0.04
try: ex=fr.get_editor_property('exponent'); br=fr.get_editor_property('base_reflect_fraction')
except Exception as e: L.append('fresnel props? %s'%e)
L.append('old F node %s exp %s base %s'%(fr.get_class().get_name(),ex,br))
c=MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -900, 300)
c.set_editor_property('description','Fresnel2Sided')
c.set_editor_property('code','float d=abs(dot(normalize(N),normalize(V))); return Br+(1-Br)*pow(saturate(1-d),Ex);')
c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
arr=[]
for n in ['N','V','Ex','Br']:
    ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
c.set_editor_property('inputs',arr)
MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS,-1200,250),'',c,'N')
MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS,-1200,320),'',c,'V')
def sp(n,v,y):
    e=MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter,-1200,y); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v); return e
MEL.connect_material_expressions(sp('RimExponent',float(ex),390),'',c,'Ex')
MEL.connect_material_expressions(sp('RimBase',float(br),460),'',c,'Br')
MEL.connect_material_expressions(c,'',cu,'F')
MEL.recompile_material(m); EAL.save_asset(DST)
EAL.duplicate_asset(MIS,MID); mi=unreal.load_asset(MID); MEL.set_material_instance_parent(mi,m); MEL.update_material_instance(mi); EAL.save_asset(MID)
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in E.get_all_level_actors():
    if a.get_actor_label()=='Realm_Bubble_Owner':
        a.set_is_temporarily_hidden_in_editor(False); a.static_mesh_component.set_material(0, mi)   # preview only, unsaved
L.append('built %s, F -> Fresnel2Sided; preview on bubble'%MID)
open(r'C:/Users/hossa/Documents/agent-office/_bubfix2_out.txt','w').write('\n'.join(L))
