# Performance pass (owner 01:03): worms bucketed by longitude (~40 checks/pixel instead of 450), early-outs for layers at 0,
# caustic light function 1 octave. Same look.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
WORMS=r'''
struct WormFn {
    float3 P(float lon0, float u, float4 r, float k)
    {
        float lon = lon0 + u;
        float lat = (r.y - 0.5) * 2.4 + (0.55 * sin(u * 1.3 * k + r.z * 6.2831853) + 0.28 * sin(u * 2.9 * k + r.w * 6.2831853)) / k;
        lat = clamp(lat, -1.45, 1.45);
        return float3(cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat));
    }
    float4 R(float c, float s)
    {
        return frac(sin(float4(c + s, c * 1.37 + s * 2.1, c * 2.11 + s * 0.7, c * 0.73 + s * 3.3) * float4(12.9898, 78.233, 39.425, 93.989)) * 43758.5453);
    }
};
if (Int <= 0.0) return float4(Em, Op);
WormFn F;
float3 d = normalize(WP - (Ctr + float3(0, 0, CH)));
float pa = max(length(ddx(d)), length(ddy(d)));
float wdE = max(Wd, pa * 1.1);
float energy = Wd / wdE;
float fres = pow(1.0 - abs(dot(normalize(N), normalize(V))), 1.5);
float near = smoothstep(600.0, 3500.0, length(WP - Cam));
float3 em = Em; float op = Op; float liftAcc = 0.0;
const float NW = 450.0;
const float STEP = 6.2831853 / NW;
float lonP = atan2(d.y, d.x); if (lonP < 0.0) lonP += 6.2831853;
float reach = Travel + Len + 0.12;                                // how far behind a worm's home slice it can still be
int nb = (int)ceil(reach / STEP) + 3;
int kp = (int)floor(lonP / STEP) + 2;
const int S = 8;
for (int j = 0; j < nb; j++)
{
    float kk = fmod((float)(kp - j) + NW * 4.0, NW);
    float seed = kk * 17.13 + 3.0;
    float life = Life * (0.6 + 0.8 * frac(sin(seed) * 43758.5453));
    float tt = T / life + frac(sin(seed * 1.7) * 91.3);
    float cyc = floor(tt), lt = frac(tt);
    float fade = smoothstep(0.0, 0.18, lt) * (1.0 - smoothstep(0.62, 1.0, lt));
    if (fade <= 0.001) continue;
    float4 r = F.R(cyc, seed);
    float lon0 = (kk + r.x * 0.9) * STEP;                        // home slice (+ jitter); latitude stays random per life
    float head = lt * Travel;
    float LenL = Len * (0.12 + 0.88 * sin(3.14159265 * lt));
    float3 hp = F.P(lon0, head, r, Curve);
    if (dot(d, hp) < cos(LenL + wdE * 10.0 + 0.03)) continue;
    float best = 1e3, ba = 1.0;
    float3 a0 = hp, dirH = hp;
    for (int i = 1; i < S; i++)
    {
        float fa = (float)i / (S - 1);
        float3 a1 = F.P(lon0, head - LenL * fa, r, Curve);
        if (i == 1) dirH = normalize(hp - a1 + 1e-6);
        float3 ab = a1 - a0; float h = saturate(dot(d - a0, ab) / max(dot(ab, ab), 1e-9));
        float dist = length(d - (a0 + ab * h));
        if (dist < best) { best = dist; ba = ((i - 1) + h) / (S - 1); }
        a0 = a1;
    }
    float xr = best / wdE;
    float coreL = exp(-xr * xr * 3.0);
    float sheath = exp(-xr * xr * 0.5) * 0.55;
    float bloomL = exp(-xr * 0.35) * 0.06;
    float tailFade = 1.0 - smoothstep(0.45, 1.0, ba);
    float pulse = 0.6 + 0.4 * pow(0.5 + 0.5 * sin(ba * 11.0 - T * PulseSpd + seed), 2.5);
    float breathe = 0.85 + 0.15 * sin(T * 1.7 + seed * 3.1);
    float3 dh = d - hp;
    float rh = length(dh) / wdE;
    float along = dot(dh, dirH) / wdE;
    float across = length(dh - dirH * dot(dh, dirH)) / wdE;
    float bokeh = exp(-rh * rh * 0.45) * 1.2;
    float streak = exp(-across * across * 1.5) * exp(-abs(along) * 0.25) * 0.35;
    float3 hue = 0.5 + 0.5 * cos(6.2831853 * (r.z * 0.6 + ba * 0.18 + T * 0.02 + float3(0.0, 0.33, 0.67)));
    hue = lerp(hue, float3(1.0, 0.5, 0.35), Warm);
    float3 white = float3(1.0, 0.96, 0.92);
    float tr = (sheath + bloomL) * tailFade * pulse;
    float cr = coreL * tailFade * pulse;
    float3 col = hue * tr + lerp(hue, white, 0.75) * cr + lerp(hue, white, 0.6) * (bokeh + streak);
    float w = fade * breathe * energy * near * (0.55 + 0.45 * fres);
    em += col * w * Int;
    op += saturate(cr * 0.5 + tr * 0.25 + bokeh * 0.25) * w * OpAdd;
    liftAcc += (sheath + bokeh) * w;
}
em += Em * saturate(liftAcc) * 0.6;
return float4(em, saturate(op));
'''
CAUSTIC=r'''
float a = saturate(Amt);
if (Int <= 0.0) return 0.0;
float3 q = WP / Scale + float3(T * 0.05, -T * 0.04, T * 0.03);
float3 g = floor(q), f = frac(q); float md = 8.0;
for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++)
{
    float3 o = float3(x, y, z);
    float3 h = frac(sin(float3(dot(g + o, float3(127.1, 311.7, 74.7)), dot(g + o, float3(269.5, 183.3, 246.1)), dot(g + o, float3(113.5, 271.9, 124.6)))) * 43758.5453);
    h = 0.5 + 0.5 * sin(T * 0.6 + 6.2831853 * h);
    md = min(md, length(o + h - f));
}
return pow(saturate(1.0 - md * 1.15), 5.0) * 1.6 * Int * (0.15 + 0.85 * a);
'''
def walk(m):
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    out={}; st=[emn]; seen=set()
    while st:
        e=st.pop()
        if e is None or e in seen: continue
        seen.add(e)
        if e.get_class().get_name()=='MaterialExpressionCustom': out[e.get_editor_property('description')]=e
        st+=MEL.get_inputs_for_material_expression(m,e)
    return out
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    n=walk(m); L.append('nodes %s'%sorted(n))
    n['RealmLightWorms2'].set_editor_property('code',WORMS)
    ep=n['RealmEMPulse']; c=ep.get_editor_property('code')
    if 'if (Int <= 0.0)' not in c: ep.set_editor_property('code','if (Int <= 0.0) return In;\n'+c)
    ce=n['RealmMembraneCells']; c=ce.get_editor_property('code')
    if 'if (Int <= 0.0)' not in c: ce.set_editor_property('code','if (Int <= 0.0) return In;\n'+c)
    ly=n['RealmLayers4to9']; c=ly.get_editor_property('code')
    if 'L4 + L5' not in c: ly.set_editor_property('code','if (L4 + L5 + L6 + L7 + L8 + L9 <= 0.0) return In;\n'+c)
    MEL.recompile_material(m); L.append('bubble shader optimized; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR bubble '+traceback.format_exc()[-500:])
try:
    r=unreal.AssetRegistryHelpers.get_asset_registry()
    for x in r.get_assets_by_path('/Game/CastleDefender/Gameplay/Realm/Dream',True):
        if str(x.asset_name).startswith('M_RealmCausticLF'):
            p=str(x.package_name); cm=unreal.load_asset(p)
            node=MEL.get_material_property_input_node(cm, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            node.set_editor_property('code',CAUSTIC); MEL.recompile_material(cm); EAL.save_asset(p); L.append('caustic 1 octave: %s'%p)
except Exception as ex:
    import traceback; L.append('ERR caustic '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_opt_out.txt','w').write('\n'.join(L))
