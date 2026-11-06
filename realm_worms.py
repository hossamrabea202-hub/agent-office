# Light worms on the bubble skin (owner 00:12): "splines of lights floating all over the bubble skin with relative colors,
# feels like electricity yet looks like worms". Added to the Master's copy M_RealmBubble3_Dream (owner's mesh/original untouched).
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
WORMS=r'''
float3 p = WP / Scale;
float t = T * Speed;
// two smooth, slowly flowing 3D fields; their zero lines are the worms (curvy splines over the skin)
float f1 = sin(p.x * 1.3 + sin(p.y * 1.7 + t * 0.9) * 1.6) * sin(p.y * 1.1 + sin(p.z * 1.9 - t * 0.7) * 1.6) * sin(p.z * 1.5 + sin(p.x * 1.2 + t * 0.8) * 1.6);
float3 p2 = p * 1.9 + float3(3.1, 7.7, 1.3);
float f2 = sin(p2.x * 1.1 + sin(p2.z * 1.5 - t * 1.1) * 1.4) * sin(p2.y * 1.4 + sin(p2.x * 1.3 + t * 0.6) * 1.4) * sin(p2.z * 1.2 + sin(p2.y * 1.6 - t * 0.9) * 1.4);
// constant on-screen thickness (thin like a filament at any distance)
float w1 = abs(f1) / max(length(float2(ddx(f1), ddy(f1))), 1e-5);
float w2 = abs(f2) / max(length(float2(ddx(f2), ddy(f2))), 1e-5);
float core = saturate(1.0 - w1 / Thick) + 0.7 * saturate(1.0 - w2 / (Thick * 0.8));
float halo = pow(saturate(1.0 - w1 / (Thick * 7.0)), 2.0) + 0.6 * pow(saturate(1.0 - w2 / (Thick * 6.0)), 2.0);
// worms, not endless lines: travelling segments that crawl along
float seg1 = smoothstep(Density, Density + 0.25, sin(dot(p, float3(0.9, 1.3, 0.7)) * 2.3 + t * 2.0 + f2 * 2.0) * 0.5 + 0.5);
float seg2 = smoothstep(Density, Density + 0.25, sin(dot(p2, float3(1.2, 0.6, 1.1)) * 2.0 - t * 1.7 + f1 * 2.0) * 0.5 + 0.5);
float m = max(seg1 * saturate(1.0 - w1 / (Thick * 7.0)), seg2 * saturate(1.0 - w2 / (Thick * 6.0)));
// electric life: a fast shimmer and bright pulses running along the worm
float flick = 0.75 + 0.25 * sin(T * 37.0 + p.x * 13.0 + p.y * 7.0) * sin(T * 23.0 + p.z * 11.0);
float pulse = pow(0.5 + 0.5 * sin(dot(p, float3(2.1, 1.7, 2.6)) * 3.0 - T * 4.0), 6.0);
// relative colours: the bubble's own film palette, pushed warm (pink / orange / gold)
float h = f2 * 0.35 + dot(p, float3(0.11, 0.07, 0.09)) + t * 0.05;
float3 col = 0.5 + 0.5 * cos(6.2831853 * (h + float3(0.0, 0.33, 0.67)));
col = lerp(col, float3(1.0, 0.45, 0.35), Warm);
float e = (core * (1.0 + 2.5 * pulse) + halo * 0.35) * m * flick;
float3 em = Em + col * e * Int + float3(1.0, 0.9, 0.85) * core * m * pulse * Int * 0.5;
return float4(em, saturate(Op + core * m * OpAdd + halo * m * OpAdd * 0.15));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    em=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,300,900)
    c.set_editor_property('code',WORMS); c.set_editor_property('description','RealmLightWorms')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names=['Em','Op','WP','T','Scale','Speed','Thick','Density','Int','Warm','OpAdd']; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    MEL.connect_material_expressions(em,'',c,'Em'); MEL.connect_material_expressions(op,'',c,'Op')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionWorldPosition,0,1300),'',c,'WP')
    MEL.connect_material_expressions(MEL.create_material_expression(m,unreal.MaterialExpressionTime,0,1350),'',c,'T')
    for i,(n,pin,v) in enumerate([('WormScale','Scale',2200.0),('WormSpeed','Speed',0.35),('WormThick','Thick',1.6),('WormDensity','Density',0.55),
                                  ('WormIntensity','Int',14.0),('WormWarmth','Warm',0.45),('WormOpacity','OpAdd',0.6)]):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,0,1400+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    mr=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,600,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mr.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,600,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(c,'',mr,''); MEL.connect_material_expressions(c,'',ma,'')
    MEL.connect_material_property(mr,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); L.append('worms added; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-700:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
