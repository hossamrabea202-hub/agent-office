# Light worms v2 (owner 00:15): each worm is one snake following a hidden curved path over the bubble skin,
# born -> crawls (big random curves) -> pulses along its body -> fades; then reborn on a new random path.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
struct WormFn {
    float3 P(float u, float4 r)
    {
        float lon = r.x * 6.2831853 + u;
        float lat = (r.y - 0.5) * 1.5 + 0.55 * sin(u * 1.3 + r.z * 6.2831853) + 0.28 * sin(u * 2.9 + r.w * 6.2831853);
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
const int NW = 9; const int S = 9;
for (int k = 0; k < NW; k++)
{
    float seed = k * 17.13 + 3.0;
    float life = Life * (0.7 + 0.6 * frac(sin(seed) * 43758.5453));
    float tt = T / life + frac(sin(seed * 1.7) * 91.3);
    float cyc = floor(tt), lt = frac(tt);
    float fade = sin(3.14159265 * lt); fade *= fade;
    float4 r = F.R(cyc, seed);
    float head = lt * Travel;
    float3 mid = F.P(head - Len * 0.5, r);
    if (dot(d, mid) < cos(Len * 0.6 + 0.25)) continue;          // pixel far from this worm: skip
    float best = 1e3, ba = 0.0;
    float3 a0 = F.P(head, r);
    for (int i = 1; i < S; i++)
    {
        float fa = (float)i / (S - 1);
        float3 a1 = F.P(head - Len * fa, r);
        float3 ab = a1 - a0; float h = saturate(dot(d - a0, ab) / max(dot(ab, ab), 1e-8));
        float dist = length(d - (a0 + ab * h));
        if (dist < best) { best = dist; ba = ((i - 1) + h) / (S - 1); }
        a0 = a1;
    }
    float wd = Wd * (1.0 - 0.75 * ba) * (0.6 + 0.4 * fade);       // thick head, thin tail
    float core = smoothstep(wd, wd * 0.25, best);
    float halo = exp(-best / (wd * 3.5)) * 0.35;
    float pulse = pow(0.5 + 0.5 * sin(ba * 14.0 - T * PulseSpd + seed), 4.0);
    float bright = (0.45 + 1.4 * pulse + 2.0 * exp(-ba * 9.0)) * (1.0 - 0.55 * ba) * fade;
    bright *= 0.85 + 0.15 * sin(T * 31.0 + seed * 5.0 + ba * 40.0);  // electric shimmer
    float3 col = 0.5 + 0.5 * cos(6.2831853 * (r.z * 0.6 + ba * 0.25 + float3(0.0, 0.33, 0.67)));
    col = lerp(col, float3(1.0, 0.45, 0.32), Warm);
    em += col * (core + halo) * bright * Int + float3(1.0, 0.92, 0.85) * core * pulse * fade * Int * 0.4;
    op += core * fade * OpAdd;
}
return float4(em, saturate(op));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    old=MEL.get_inputs_for_material_expression(m,emn)[0]                     # the v1 worms custom
    assert old.get_editor_property('description')=='RealmLightWorms', old.get_editor_property('description')
    oins=MEL.get_inputs_for_material_expression(m,old)                      # [Em, Op, WP, T, ...]
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,900,900)
    c.set_editor_property('code',CODE); c.set_editor_property('description','RealmLightWorms2')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names=['Em','Op','WP','T','Ctr','CH','Life','Len','Travel','Wd','PulseSpd','Int','Warm','OpAdd']; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    for i,n in enumerate(['Em','Op','WP','T']): MEL.connect_material_expressions(oins[i],'',c,n)
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionObjectPositionWS,600,1700),'',c,'Ctr')
    for i,(n,pin,v) in enumerate([('WormCenterHeight','CH',2000.0),('WormLife','Life',9.0),('WormLength','Len',0.9),('WormTravel','Travel',2.6),
                                  ('WormWidth','Wd',0.006),('WormPulseSpeed','PulseSpd',5.0),('WormIntensity2','Int',16.0),('WormWarmth','Warm',0.45),('WormOpacity','OpAdd',0.6)]):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,600,1760+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    mr=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,1200,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mr.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,1200,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(c,'',mr,''); MEL.connect_material_expressions(c,'',ma,'')
    MEL.connect_material_property(mr,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); L.append('worms v2; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-700:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
