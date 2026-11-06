# 3rd layer (Master's choice, owner 00:37): living membrane cells - faint breathing violet cell walls + cells that light up.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 p = WP / Scale;
float3 g = floor(p), f = frac(p);
float f1 = 8.0, f2 = 8.0; float3 id1 = 0;
for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++)
{
    float3 o = float3(x, y, z);
    float3 h = frac(sin(float3(dot(g + o, float3(127.1, 311.7, 74.7)), dot(g + o, float3(269.5, 183.3, 246.1)), dot(g + o, float3(113.5, 271.9, 124.6)))) * 43758.5453);
    h = 0.5 + 0.45 * sin(T * Drift + 6.2831853 * h);                 // cells slowly drift
    float dd = length(o + h - f);
    if (dd < f1) { f2 = f1; f1 = dd; id1 = g + o; } else if (dd < f2) { f2 = dd; }
}
float edge = f2 - f1;
float pa = max(length(ddx(p)), length(ddy(p)));                    // AA: soften walls by pixel size
float wall = 1.0 - smoothstep(0.0, WallW + pa * 1.5, edge);
float rnd = frac(sin(dot(id1, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float breathe = 0.7 + 0.3 * sin(T * 0.6 + rnd * 6.2831853);
float lit = pow(saturate(sin(T * 0.35 + rnd * 40.0)), 24.0);        // now and then one cell glows from inside
float coreGlow = lit * exp(-f1 * f1 * 6.0);
float fres = pow(1.0 - abs(dot(normalize(N), normalize(V))), 1.2);
float near = smoothstep(500.0, 3000.0, length(WP - Cam));
float3 violet = lerp(float3(0.55, 0.15, 1.0), float3(1.0, 0.2, 0.7), rnd);
float3 add = violet * (wall * breathe * (0.35 + 0.65 * fres) + coreGlow * 1.5) * Int * near;
return float4(In.rgb + add, saturate(In.a + (wall * 0.12 * fres + coreGlow * 0.2) * OpAdd * near));
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    prev=MEL.get_inputs_for_material_expression(m,emn)[0]
    assert prev.get_editor_property('description')=='RealmEMPulse', prev.get_editor_property('description')
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,2100,900)
    c.set_editor_property('code',CODE); c.set_editor_property('description','RealmMembraneCells')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names=['In','WP','T','N','V','Cam','Scale','Drift','WallW','Int','OpAdd']; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    MEL.connect_material_expressions(prev,'',c,'In')
    for i,(n,cls) in enumerate([('WP',unreal.MaterialExpressionWorldPosition),('T',unreal.MaterialExpressionTime),('N',unreal.MaterialExpressionVertexNormalWS),
                                ('V',unreal.MaterialExpressionCameraVectorWS),('Cam',unreal.MaterialExpressionCameraPositionWS)]):
        MEL.connect_material_expressions(MEL.create_material_expression(m,cls,1800,1300+60*i),'',c,n)
    for i,(n,pin,v) in enumerate([('CellScale','Scale',900.0),('CellDrift','Drift',0.15),('CellWallWidth','WallW',0.06),('CellIntensity','Int',0.8),('CellOpacity','OpAdd',0.5)]):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,1800,1650+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    mr=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,2400,880)
    for k,v in (('r',True),('g',True),('b',True),('a',False)): mr.set_editor_property(k,v)
    ma=MEL.create_material_expression(m,unreal.MaterialExpressionComponentMask,2400,980)
    for k,v in (('r',False),('g',False),('b',False),('a',True)): ma.set_editor_property(k,v)
    MEL.connect_material_expressions(c,'',mr,''); MEL.connect_material_expressions(c,'',ma,'')
    MEL.connect_material_property(mr,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(ma,'',unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); L.append('cells; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_worms_out.txt','w').write('\n'.join(L))
