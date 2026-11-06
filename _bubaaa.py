# AAA membrane fix on a COPY (M_RealmBubble3_Soft / MI_RealmBubble3_Soft), rebuilt from the original each run:
#  1 grazing fade: opacity + emissive go thin when the skin is seen edge-on (no solid rainbow patches)
#  2 soft contact: DepthFade on opacity near any surface (ContactFade cm)
#  3 rock seam: a thin warm glow line where the membrane enters rock (SeamWidth cm, SeamGlow)
import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
SRC='/Game/CastleDefender/Realm/M_RealmBubble3'; DST='/Game/CastleDefender/Realm/M_RealmBubble3_Soft'
MIS='/Game/CastleDefender/Realm/MI_RealmBubble3'; MID='/Game/CastleDefender/Realm/MI_RealmBubble3_Soft'
L=[]
for p in (MID,DST):
    if EAL.does_asset_exist(p): EAL.delete_asset(p)
EAL.duplicate_asset(SRC,DST); m=unreal.load_asset(DST)
op=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
em=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
def sp(n,v,x,y):
    e=MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v); return e
def cust(code,ins,x,y,otype):
    c=MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property('code',code); c.set_editor_property('output_type',otype)
    arr=[]
    for n in ins:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr); return c
F1=unreal.CustomMaterialOutputType.CMOT_FLOAT1; F3=unreal.CustomMaterialOutputType.CMOT_FLOAT3
# grazing factor
g=cust('float d=abs(dot(normalize(N),normalize(V))); return saturate((d-Lo)/max(Hi-Lo,1e-3));',['N','V','Lo','Hi'],-700,700,F1)
MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS,-1000,650),'',g,'N')
MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS,-1000,720),'',g,'V')
MEL.connect_material_expressions(sp('GrazeLo',0.03,-1000,790),'',g,'Lo')
MEL.connect_material_expressions(sp('GrazeHi',0.30,-1000,860),'',g,'Hi')
# soft contact + seam
df=MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade,-700,950)
MEL.connect_material_expressions(sp('ContactFade',1500.0,-1000,950),'',df,'FadeDistance')
ds=MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade,-700,1100)
MEL.connect_material_expressions(sp('SeamWidth',120.0,-1000,1100),'',ds,'FadeDistance')
# opacity = op * graze * contact  + seam*SeamOpacity
oc=cust('float s=(1-Ds)*Ds2; return saturate(Op*G*Df + s*SeamOp);',['Op','G','Df','Ds','Ds2','SeamOp'],-300,600,F1)
MEL.connect_material_expressions(op,'',oc,'Op'); MEL.connect_material_expressions(g,'',oc,'G'); MEL.connect_material_expressions(df,'',oc,'Df')
MEL.connect_material_expressions(ds,'',oc,'Ds')
ds2=MEL.create_material_expression(m, unreal.MaterialExpressionDepthFade,-700,1250)
MEL.connect_material_expressions(sp('SeamInner',20.0,-1000,1250),'',ds2,'FadeDistance')
MEL.connect_material_expressions(ds2,'',oc,'Ds2')
MEL.connect_material_expressions(sp('SeamOpacity',0.35,-1000,1320),'',oc,'SeamOp')
# emissive = em * graze + seam * SeamColor * SeamGlow
ec=cust('float s=(1-Ds)*Ds2; return Em*G + s*Col*Glow;',['Em','G','Ds','Ds2','Col','Glow'],-300,800,F3)
MEL.connect_material_expressions(em,'',ec,'Em'); MEL.connect_material_expressions(g,'',ec,'G')
MEL.connect_material_expressions(ds,'',ec,'Ds'); MEL.connect_material_expressions(ds2,'',ec,'Ds2')
vc=MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter,-1000,1400); vc.set_editor_property('parameter_name','SeamColor'); vc.set_editor_property('default_value',unreal.LinearColor(1.0,0.45,0.35,1))
MEL.connect_material_expressions(vc,'',ec,'Col'); MEL.connect_material_expressions(sp('SeamGlow',2.0,-1000,1500),'',ec,'Glow')
MEL.connect_material_property(oc,'',unreal.MaterialProperty.MP_OPACITY)
MEL.connect_material_property(ec,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(m); EAL.save_asset(DST)
EAL.duplicate_asset(MIS,MID); mi=unreal.load_asset(MID); MEL.set_material_instance_parent(mi,m); MEL.update_material_instance(mi); EAL.save_asset(MID)
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in E.get_all_level_actors():
    if a.get_actor_label()=='Realm_Bubble_Owner': a.static_mesh_component.set_material(0, mi)   # PREVIEW ONLY: no modify(), not saved
L.append('built %s (graze fade, contact fade, rock seam); preview on bubble (unsaved)'%MID)
open(r'C:/Users/hossa/Documents/agent-office/_bubaaa_out.txt','w').write('\n'.join(L))
