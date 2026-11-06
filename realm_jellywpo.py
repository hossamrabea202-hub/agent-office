# Jelly wobble via World Position Offset on M_RealmBubble3_Dream (owner 01:06). Outer + inner shell both use it.
import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
CODE=r'''
float3 rel = WP - Ctr;
float3 n = normalize(N);
float R = max(Rad, 100.0);
float br = sin(T * 6.2831853 * Hz) * Breath * R;                                         // slow breathing
float3 dirA = normalize(float3(0.6, 0.5, 0.62)), dirB = normalize(float3(-0.7, 0.3, 0.4));
float rip = Ripple * (sin((dot(WP, dirA) - T * RipSpd) * 6.2831853 / RipLen) + 0.6 * sin((dot(WP, dirB) + T * RipSpd * 0.7) * 6.2831853 / (RipLen * 0.63)));
float3 u = rel / R;
float wob = Wobble * R * (sin(u.z * 3.0 + T * 1.3) * sin(u.x * 2.5 - T * 0.9) + 0.5 * sin(u.y * 3.7 + T * 1.7));   // jelly wobble
return n * (br + rip + wob);
'''
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    c=MEL.create_material_expression(m,unreal.MaterialExpressionCustom,2400,-400)
    c.set_editor_property('code',CODE); c.set_editor_property('description','RealmJellyWPO')
    c.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    names=['WP','Ctr','N','T','Rad','Hz','Breath','Ripple','RipLen','RipSpd','Wobble']; arr=[]
    for n in names:
        ci=unreal.CustomInput(); ci.set_editor_property('input_name',n); arr.append(ci)
    c.set_editor_property('inputs',arr)
    for i,(n,cls) in enumerate([('WP',unreal.MaterialExpressionWorldPosition),('Ctr',unreal.MaterialExpressionObjectPositionWS),('N',unreal.MaterialExpressionVertexNormalWS),
                                ('T',unreal.MaterialExpressionTime),('Rad',unreal.MaterialExpressionObjectRadius)]):
        MEL.connect_material_expressions(MEL.create_material_expression(m,cls,2100,-400+60*i),'',c,n)
    for i,(n,pin,v) in enumerate([('JellyHz','Hz',0.18),('JellyBreath','Breath',0.012),('JellyRipple','Ripple',70.0),('JellyRippleLen','RipLen',1800.0),
                                  ('JellyRippleSpeed','RipSpd',260.0),('JellyWobble','Wobble',0.008)]):
        e=MEL.create_material_expression(m,unreal.MaterialExpressionScalarParameter,2100,-80+60*i); e.set_editor_property('parameter_name',n); e.set_editor_property('default_value',v)
        MEL.connect_material_expressions(e,'',c,pin)
    wired=False
    for attempt in ('enum','cast','int'):
        try:
            if attempt=='enum': prop=unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
            elif attempt=='cast': prop=unreal.MaterialProperty.cast(12)
            else: prop=unreal.MaterialProperty(12)
            MEL.connect_material_property(c,'',prop); wired=True; L.append('WPO wired via %s'%attempt); break
        except Exception as ex: L.append('wpo %s: %s'%(attempt,str(ex)[:80]))
    try: m.set_editor_property('max_world_position_offset_displacement',600.0)
    except Exception as ex: L.append('maxwpo: %s'%str(ex)[:60])
    MEL.recompile_material(m); L.append('save %s; WIRED=%s'%(EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'),wired))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_opt_out.txt','w').write('\n'.join(L))
