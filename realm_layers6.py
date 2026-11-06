# 6 more skin layers (owner 00:39, Master's choice): 4 marbling, 5 spore motes, 6 wet sheen, 7 heart veins, 8 aurora, 9 contact seam.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 em = In.rgb; float op = In.a;
float3 nN = normalize(N), vV = normalize(V);
float fres = pow(1.0 - abs(dot(nN, vV)), 1.5);
float near = smoothstep(500.0, 3000.0, length(WP - Cam));
float3 dC = normalize(WP - (Ctr + float3(0, 0, CH)));
// 4 flowing marbling (soap film draining under gravity)
float3 q = WP / MarbleScale;
float m1 = sin(q.x * 1.3 + sin(q.y * 0.9 + T * 0.05) * 2.0 + q.z * 0.7 + T * 0.03);
float m2 = sin(q.y * 1.1 + sin(q.z * 1.4 - T * 0.04) * 2.0 - q.x * 0.5);
float flowv = q.z * 1.5 + m1 * 1.2 + m2 * 0.8 + T * MarbleSpeed;
float3 marble = 0.5 + 0.5 * cos(6.2831853 * (flowv * 0.15 + float3(0.0, 0.33, 0.67)));
em += marble * (0.4 + 0.6 * fres) * L4 * near;
// 5 spore motes drifting down the skin
float3 sp = WP / MoteScale; sp.z += T * MoteSpeed;
float3 sg = floor(sp), sf = frac(sp);
float3 sh = frac(sin(float3(dot(sg, float3(127.1, 311.7, 74.7)), dot(sg, float3(269.5, 183.3, 246.1)), dot(sg, float3(113.5, 271.9, 124.6)))) * 43758.5453);
float sd = length(sf - (0.2 + 0.6 * sh));
float twinkle = 0.5 + 0.5 * sin(T * 3.0 + sh.x * 30.0);
float mote = exp(-sd * sd * 700.0) * step(0.65, sh.y) * twinkle;
em += float3(1.0, 0.85, 0.6) * mote * L5 * near;
// 6 wet sheen: a soft glint from a light slowly circling the bubble
float3 Ld = normalize(float3(cos(T * 0.07), sin(T * 0.07), 0.6));
float3 Hh = normalize(Ld + vV);
float glint = pow(saturate(dot(nN, Hh)), 60.0) + pow(saturate(dot(-nN, Hh)), 60.0);
em += float3(1.0, 0.95, 0.9) * glint * L6 * near;
// 7 heart veins: faint ridged network that throbs
float3 vq = WP / VeinScale; float vn = 0.0, va = 0.5;
for (int i = 0; i < 4; i++)
{
    float s1 = sin(vq.x * 1.7 + sin(vq.y * 1.3) * 1.5) * sin(vq.y * 1.9 + sin(vq.z * 1.1) * 1.5) * sin(vq.z * 1.5 + sin(vq.x * 1.6) * 1.5);
    vn += va * (1.0 - abs(s1)); vq = vq * 2.07 + 3.1; va *= 0.5;
}
float ridge = pow(saturate(vn * 1.1 - 0.35), 6.0);
float throb = 0.55 + 0.45 * pow(0.5 + 0.5 * sin(T * 5.0), 8.0);
em += float3(0.9, 0.08, 0.12) * ridge * throb * L7 * near;
op += ridge * 0.08 * L7 * near;
// 8 aurora curtains on the upper dome
float ang = atan2(dC.y, dC.x);
float curt = pow(0.5 + 0.5 * sin(ang * 7.0 + sin(ang * 3.0 + T * 0.2) * 2.0 + T * 0.1), 3.0);
float band = exp(-pow((dC.z - 0.55) / 0.18, 2.0));
float3 aur = lerp(float3(0.1, 1.0, 0.6), float3(1.0, 0.75, 0.2), 0.5 + 0.5 * sin(ang * 2.0 + T * 0.15));
em += aur * curt * band * L8 * near;
// 9 contact seam: warm glow where the membrane meets ground and rock
float seam = pow(1.0 - saturate(DF), 3.0);
float sz = 0.7 + 0.3 * sin(T * 9.0 + WP.x * 0.02 + WP.y * 0.03);
em += float3(1.0, 0.4, 0.25) * seam * sz * L9;
op += seam * 0.2 * L9;
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    prev=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert prev.get_editor_property('description')=='RealmMembraneCells', prev.get_editor_property('description')
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,2700,900)
    c.set_editor_property('code',CODE); c.set_editor_property('description','RealmLayers4to9')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    P=[('Layer4_Marble','L4',0.25),('Layer5_Motes','L5',3.0),('Layer6_Sheen','L6',1.5),('Layer7_Veins','L7',0.6),('Layer8_Aurora','L8',0.6),('Layer9_Seam','L9',2.0),
       ('MarbleScale','MarbleScale',6000.0),('MarbleSpeed','MarbleSpeed',0.05),('MoteScale','MoteScale',300.0),('MoteSpeed','MoteSpeed',0.15),('VeinScale','VeinScale',3500.0),('AuroraCenterHeight','CH',2000.0)]
    names=['In','WP','T','N','V','Cam','Ctr','DF']+[p[1] for p in P]; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    MEL.connect_material_expressions(prev,'',c,'In')
    for i,(n,cls) in enumerate([('WP',unreal.MaterialExpressionWorldPosition),('T',unreal.MaterialExpressionTime),('N',unreal.MaterialExpressionVertexNormalWS),
                                ('V',unreal.MaterialExpressionCameraVectorWS),('Cam',unreal.MaterialExpressionCameraPositionWS),('Ctr',unreal.MaterialExpressionObjectPositionWS)]):
        MEL.connect_material_expressions(MEL.create_material_expression(m,cls,2400,1300+60*i),'',c,n)
    df=MEL.create_material_expression(m,unreal.MaterialExpressionDepthFade,2400,1700)
    fd=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,2200,1700); fd.set_editor_property('parameter_name','SeamWidth'); fd.set_editor_property('default_value',150.0)
    MEL.connect_material_expressions(fd,'',df,'FadeDistance'); MEL.connect_material_expressions(df,'',c,'DF')
    for i,(n,pin,v) in enumerate(P):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,2400,1800+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    mr=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,3000,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mr.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,3000,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(c,'',mr,''); MEL.connect_material_expressions(c,'',ma,'')
    MEL.connect_material_property(mr,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); L.append('layers 4-9; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
