import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
struct WormFn {
    float3 P(float u, float4 r, float k)
    {
        float lon = r.x * 6.2831853 + u;
        float lat = (r.y - 0.5) * 2.4 + (0.55 * sin(u * 1.3 * k + r.z * 6.2831853) + 0.28 * sin(u * 2.9 * k + r.w * 6.2831853)) / k;
        lat = clamp(lat, -1.45, 1.45);
        return float3(cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat));
    }
    float4 R(float c, float s)
    {
        return frac(sin(float4(c + s, c * 1.37 + s * 2.1, c * 2.11 + s * 0.7, c * 0.73 + s * 3.3) * float4(12.9898, 78.233, 39.425, 93.989)) * 43758.5453);
    }
};
WormFn F;
float3 d = normalize(WP - (Ctr + float3(0, 0, CH)));
float3 em = Em; float op = Op;
const int NW = 50; const int S = 9;
for (int k = 0; k < NW; k++)
{
    float seed = k * 17.13 + 3.0;
    float life = Life * (0.6 + 0.8 * frac(sin(seed) * 43758.5453));
    float tt = T / life + frac(sin(seed * 1.7) * 91.3);
    float cyc = floor(tt), lt = frac(tt);
    float fade = smoothstep(0.0, 0.15, lt) * (1.0 - smoothstep(0.6, 1.0, lt));   // fades in fast, dissolves slowly
    float4 r = F.R(cyc, seed);
    float head = lt * Travel;
    float3 hp = F.P(head, r, Curve);
    if (dot(d, hp) < cos(Len + Wd * 8.0 + 0.05)) continue;
    // photon: a soft glowing point at the head
    float dh = length(d - hp);
    float photon = exp(-pow(dh / (Wd * 0.9), 2.0)) * 1.1 + exp(-dh / (Wd * 2.5)) * 0.12;
    // silky trail: soft gaussian line, thinning and dimming towards the tail, pulses running along it
    float best = 1e3, ba = 1.0;
    float3 a0 = hp;
    for (int i = 1; i < S; i++)
    {
        float fa = (float)i / (S - 1);
        float3 a1 = F.P(head - Len * fa, r, Curve);
        float3 ab = a1 - a0; float h = saturate(dot(d - a0, ab) / max(dot(ab, ab), 1e-9));
        float dist = length(d - (a0 + ab * h));
        if (dist < best) { best = dist; ba = ((i - 1) + h) / (S - 1); }
        a0 = a1;
    }
    float wd = Wd;                                   // one even width: a spline, not a taper
    float trail = exp(-pow(best / wd, 2.0)) + exp(-best / (wd * 3.0)) * 0.12;
    trail *= 1.0 - 0.6 * smoothstep(0.55, 1.0, ba);   // only the very end softens
    float pulse = 0.55 + 0.45 * pow(0.5 + 0.5 * sin(ba * 18.0 - T * PulseSpd + seed), 3.0);
    float3 col = 0.5 + 0.5 * cos(6.2831853 * (r.z * 0.6 + ba * 0.2 + float3(0.0, 0.33, 0.67)));
    col = lerp(col, float3(1.0, 0.5, 0.35), Warm);
    float3 hot = lerp(col, float3(1.0, 0.95, 0.9), 0.6);
    em += (col * trail * pulse + hot * photon) * fade * Int;
    op += saturate(trail * 0.6 + photon * 0.3) * fade * OpAdd;
}
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    c=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert c.get_editor_property('description')=='RealmLightWorms2'
    c.set_editor_property('code',CODE); MEL.recompile_material(m)
    L.append('v5 count50 slower; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
    mi=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
    MEL.set_material_instance_scalar_parameter_value(mi,'WormIntensity2',18.0); MEL.set_material_instance_scalar_parameter_value(mi,'WormTravel',0.7); MEL.update_material_instance(mi); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
