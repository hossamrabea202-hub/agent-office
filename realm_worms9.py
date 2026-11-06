# Light worms polish (owner 00:35): AA-safe width, white core + coloured sheath, photon bokeh + motion streak,
# silky breathing (no fast flicker), fresnel weighting, near-camera fade, film lift. Same count/size/life cycle.
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
float pa = max(length(ddx(d)), length(ddy(d)));                  // angular size of one pixel
float wdE = max(Wd, pa * 1.1);                                    // never thinner than a pixel (no sparkle)
float energy = Wd / wdE;                                          // keep the same total light when widened
float fres = pow(1.0 - abs(dot(normalize(N), normalize(V))), 1.5);
float near = smoothstep(600.0, 3500.0, length(WP - Cam));
float3 em = Em; float op = Op; float liftAcc = 0.0;
const int NW = 450; const int S = 8;
for (int k = 0; k < NW; k++)
{
    float seed = k * 17.13 + 3.0;
    float life = Life * (0.6 + 0.8 * frac(sin(seed) * 43758.5453));
    float tt = T / life + frac(sin(seed * 1.7) * 91.3);
    float cyc = floor(tt), lt = frac(tt);
    float fade = smoothstep(0.0, 0.18, lt) * (1.0 - smoothstep(0.62, 1.0, lt));
    float4 r = F.R(cyc, seed);
    float head = lt * Travel;
    float LenL = Len * (0.12 + 0.88 * sin(3.14159265 * lt));
    float3 hp = F.P(head, r, Curve);
    if (dot(d, hp) < cos(LenL + wdE * 10.0 + 0.03)) continue;
    // trail: nearest point on the polyline
    float best = 1e3, ba = 1.0;
    float3 a0 = hp, dirH = hp;
    for (int i = 1; i < S; i++)
    {
        float fa = (float)i / (S - 1);
        float3 a1 = F.P(head - LenL * fa, r, Curve);
        if (i == 1) dirH = normalize(hp - a1 + 1e-6);
        float3 ab = a1 - a0; float h = saturate(dot(d - a0, ab) / max(dot(ab, ab), 1e-9));
        float dist = length(d - (a0 + ab * h));
        if (dist < best) { best = dist; ba = ((i - 1) + h) / (S - 1); }
        a0 = a1;
    }
    float xr = best / wdE;
    float coreL = exp(-xr * xr * 3.0);                             // thin white-hot core
    float sheath = exp(-xr * xr * 0.5) * 0.55;                     // coloured sheath
    float bloomL = exp(-xr * 0.35) * 0.06;                         // faint wide glow
    float tailFade = 1.0 - smoothstep(0.45, 1.0, ba);
    float pulse = 0.6 + 0.4 * pow(0.5 + 0.5 * sin(ba * 11.0 - T * PulseSpd + seed), 2.5);
    float breathe = 0.85 + 0.15 * sin(T * 1.7 + seed * 3.1);      // silky, slow
    // photon head: soft bokeh disc + a short streak along the travel direction
    float3 dh = d - hp;
    float rh = length(dh) / wdE;
    float along = dot(dh, dirH) / wdE;
    float across = length(dh - dirH * dot(dh, dirH)) / wdE;
    float bokeh = exp(-rh * rh * 0.45) * 1.2;
    float streak = exp(-across * across * 1.5) * exp(-abs(along) * 0.25) * 0.35;
    float3 hue = 0.5 + 0.5 * cos(6.2831853 * (r.z * 0.6 + ba * 0.18 + T * 0.02 + float3(0.0, 0.33, 0.67)));
    hue = lerp(hue, float3(1.0, 0.5, 0.35), Warm);
    float3 white = float3(1.0, 0.96, 0.92);
    float t = (sheath + bloomL) * tailFade * pulse;
    float c = coreL * tailFade * pulse;
    float3 col = hue * t + lerp(hue, white, 0.75) * c + lerp(hue, white, 0.6) * (bokeh + streak);
    float w = fade * breathe * energy * near * (0.55 + 0.45 * fres);
    em += col * w * Int;
    op += saturate(c * 0.5 + t * 0.25 + bokeh * 0.25) * w * OpAdd;
    liftAcc += (sheath + bokeh) * w;
}
em += Em * saturate(liftAcc) * 0.6;                               // the film around a thread glows a little
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    pulse=MEL.get_inputs_for_material_expression(m,emn)[0]          # EM pulse node
    c=MEL.get_inputs_for_material_expression(m,pulse)[0]            # its 'In' = worms node
    assert c.get_editor_property('description')=='RealmLightWorms2', c.get_editor_property('description')
    c.set_editor_property('code',CODE)
    ins=list(c.get_editor_property('inputs')); have=[str(i.get_editor_property('input_name')) for i in ins]
    newp={'N':unreal.MaterialExpressionVertexNormalWS,'V':unreal.MaterialExpressionCameraVectorWS,'Cam':unreal.MaterialExpressionCameraPositionWS}
    add=[n for n in newp if n not in have]
    for n in add:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); ins.append(ci)
    c.set_editor_property('inputs',ins)
    for i,n in enumerate(add): MEL.connect_material_expressions(MEL.create_material_expression(m,newp[n],600,2500+60*i),'',c,n)
    MEL.recompile_material(m); L.append('worms polish; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
