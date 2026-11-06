# EM pulse layer (owner 00:29): complementary hue (cyan/blue vs the warm worms), pulses here and there on the bubble skin.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 d = normalize(WP - (Ctr + float3(0, 0, CH)));
float3 em = In.rgb; float op = In.a;
const int NP = 14;
for (int k = 0; k < NP; k++)
{
    float seed = k * 31.7 + 11.0;
    float life = Life * (0.6 + 0.8 * frac(sin(seed * 1.3) * 43758.5453));
    float tt = T / life + frac(sin(seed * 2.9) * 71.7);
    float cyc = floor(tt), lt = frac(tt);
    if (lt > Active) continue;                                  // most of the time this emitter rests
    float p = lt / Active;                                      // 0..1 over the pulse
    float4 r = frac(sin(float4(cyc + seed, cyc * 1.7 + seed, cyc * 2.3 + seed * 0.5, cyc * 0.9 + seed * 1.9) * float4(12.9898, 78.233, 39.425, 93.989)) * 43758.5453);
    float lon = r.x * 6.2831853, lat = (r.y - 0.5) * 2.6;
    float3 c = float3(cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat));
    float dist = length(d - c);
    if (dist > MaxR * 1.3) continue;
    // tangent frame around the centre, for the crackle along the ring
    float3 t1 = normalize(cross(c, abs(c.z) < 0.9 ? float3(0, 0, 1) : float3(1, 0, 0)));
    float3 t2 = cross(c, t1);
    float ang = atan2(dot(d, t2), dot(d, t1));
    float rad = MaxR * (1.0 - pow(1.0 - p, 2.2));               // fast burst, slowing down
    float rw = RingW * (1.0 + 2.0 * p);
    float crack = 0.55 + 0.45 * sin(ang * 23.0 + T * 40.0 + r.z * 20.0) * sin(ang * 9.0 - T * 25.0);
    float ring = exp(-pow((dist - rad) / rw, 2.0)) * crack;
    float ring2 = exp(-pow((dist - rad * 0.6) / (rw * 0.7), 2.0)) * 0.45 * crack;   // an echo ring inside
    float flash = exp(-dist / (RingW * 3.0)) * exp(-p * 10.0) * 3.0;               // the spark at birth
    float fade = pow(1.0 - p, 1.5);
    float3 col = lerp(float3(0.15, 0.85, 1.0), float3(0.35, 0.45, 1.0), r.w);       // cyan .. electric blue
    em += col * ((ring + ring2) * fade + flash) * Int;
    op += saturate((ring + ring2) * fade * 0.5 + flash * 0.2) * OpAdd;
}
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    w=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert w.get_editor_property('description')=='RealmLightWorms2', w.get_editor_property('description')
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,1500,900)
    c.set_editor_property('code',CODE); c.set_editor_property('description','RealmEMPulse')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names=['In','WP','T','Ctr','CH','Life','Active','MaxR','RingW','Int','OpAdd']; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    MEL.connect_material_expressions(w,'',c,'In')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionWorldPosition,1200,1300),'',c,'WP')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionTime,1200,1350),'',c,'T')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionObjectPositionWS,1200,1400),'',c,'Ctr')
    for i,(n,pin,v) in enumerate([('PulseCenterHeight','CH',2000.0),('PulseLife','Life',6.0),('PulseActive','Active',0.3),('PulseMaxRadius','MaxR',0.22),
                                  ('PulseRingWidth','RingW',0.004),('PulseIntensity','Int',14.0),('PulseOpacity','OpAdd',0.5)]):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,1200,1460+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    mr=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,1800,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mr.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,1800,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(c,'',mr,''); MEL.connect_material_expressions(c,'',ma,'')
    MEL.connect_material_property(mr,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); L.append('EM pulses; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-600:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
