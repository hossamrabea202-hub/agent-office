import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 d = normalize(WP - (Ctr + float3(0, 0, CH)));
float3 em = In.rgb; float op = In.a;
const int NP = 6;
for (int k = 0; k < NP; k++)
{
    float seed = k * 31.7 + 11.0;
    float life = Life * (0.7 + 0.6 * frac(sin(seed * 1.3) * 43758.5453));
    float tt = T / life + frac(sin(seed * 2.9) * 71.7);
    float cyc = floor(tt), lt = frac(tt);
    if (lt > Active) continue;
    float p = lt / Active;
    float4 r = frac(sin(float4(cyc + seed, cyc * 1.7 + seed, cyc * 2.3 + seed * 0.5, cyc * 0.9 + seed * 1.9) * float4(12.9898, 78.233, 39.425, 93.989)) * 43758.5453);
    float lon = r.x * 6.2831853, lat = (r.y - 0.5) * 2.4;
    float3 c = float3(cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat));
    float dist = length(d - c);
    float rad = MaxR * p;                                         // slow, even sweep
    float x = (dist - rad) / RingW;
    // a soft wavefront with faint interference bands trailing behind it
    float front = exp(-x * x);
    float bands = (x < 0.0) ? (0.5 + 0.5 * cos(x * 2.4)) * exp(x * 0.35) * 0.35 : 0.0;
    float shimmer = 0.75 + 0.25 * sin(dot(d, float3(37.0, 51.0, 43.0)) + T * 6.0);
    float env = sin(3.14159265 * p); env *= env;                  // fades in and out, no burst
    float w = (front + bands) * shimmer * env;
    float3 col = lerp(float3(0.2, 0.8, 1.0), float3(0.35, 0.5, 1.0), r.w);
    em += col * w * Int;
    op += saturate(w * 0.25) * OpAdd;
}
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    c=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert c.get_editor_property('description')=='RealmEMPulse'
    c.set_editor_property('code',CODE); MEL.recompile_material(m)
    L.append('EM waves; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
    mi=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
    for n,v in [('PulseLife',10.0),('PulseActive',0.5),('PulseMaxRadius',1.1),('PulseRingWidth',0.03),('PulseIntensity',3.0),('PulseOpacity',0.35)]:
        MEL.set_material_instance_scalar_parameter_value(mi,n,v)
    MEL.update_material_instance(mi); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
