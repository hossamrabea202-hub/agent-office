# EM waves, film-quality pass (owner 00:32).
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 d = normalize(WP - (Ctr + float3(0, 0, CH)));
float3 em = In.rgb; float op = In.a;
float fres = pow(1.0 - abs(dot(normalize(N), normalize(V))), 2.0);          // energy shows most where the skin turns away
float near = smoothstep(800.0, 4000.0, length(WP - Cam));                    // never flare in the player's face
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
    if (dist > MaxR * 1.15) continue;
    // organic front: low-frequency noise bends the circle
    float3 q = d * 5.0 + r.xyz * 9.0;
    float wob = sin(q.x * 1.7 + sin(q.y * 2.3 + T * 0.4)) * sin(q.y * 1.9 + sin(q.z * 1.4 - T * 0.3)) * sin(q.z * 2.1 + sin(q.x * 1.6 + T * 0.35));
    float ease = 1.0 - pow(1.0 - p, 2.4);                                    // fast start, long glide
    float rad = MaxR * ease + wob * RingW * 2.5;
    float x = (dist - rad) / RingW;
    // spectral dispersion: R/G/B fronts slightly apart, thin bright line + soft glow ahead + afterglow behind
    float3 xs = x + float3(-0.35, 0.0, 0.35) * Disp;
    float3 line = exp(-xs * xs * 6.0);
    float3 glow = exp(-xs * xs * 0.6) * 0.35;
    float3 after = (xs < 0.0) ? exp(xs * 0.25) * (0.5 + 0.5 * cos(xs * 1.8 + T * 2.0)) * 0.18 : 0.0;
    float env = smoothstep(0.0, 0.12, p) * (1.0 - smoothstep(0.55, 1.0, p));
    float spread = 1.0 / (1.0 + 2.5 * ease);                                 // energy thins as it travels
    float3 w = (line + glow + after) * env * spread;
    // light the existing film toward cyan rather than painting over it
    float3 tint = lerp(float3(0.25, 0.85, 1.0), float3(0.45, 0.55, 1.0), r.w);
    float3 lift = In.rgb * tint * 2.0 + tint * 0.35;
    em += lift * w * Int * (0.35 + 0.65 * fres) * near;
    op += saturate(dot(w, float3(0.33, 0.34, 0.33)) * 0.3) * OpAdd * near;
}
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    c=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert c.get_editor_property('description')=='RealmEMPulse'
    c.set_editor_property('code',CODE)
    ins=list(c.get_editor_property('inputs')); have=[str(i.get_editor_property('input_name')) for i in ins]
    newp={'N':unreal.MaterialExpressionVertexNormalWS,'V':unreal.MaterialExpressionCameraVectorWS,'Cam':unreal.MaterialExpressionCameraPositionWS}
    add=[n for n in ['N','V','Cam','Disp'] if n not in have]
    for n in add:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); ins.append(ci)
    c.set_editor_property('inputs',ins)
    for i,n in enumerate(add):
        if n in newp: MEL.connect_material_expressions(MEL.create_material_expression(m,newp[n],1200,1900+60*i),'',c,n)
        else:
            e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,1200,1900+60*i); e.set_editor_property('parameter_name','PulseDispersion'); e.set_editor_property('default_value',1.0)
            MEL.connect_material_expressions(e,'',c,n)
    MEL.recompile_material(m); L.append('EM film pass; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
    mi=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
    for n,v in [('PulseIntensity',1.4),('PulseRingWidth',0.02),('PulseMaxRadius',1.0),('PulseOpacity',0.15)]:
        MEL.set_material_instance_scalar_parameter_value(mi,n,v)
    MEL.update_material_instance(mi); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
