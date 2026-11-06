import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
try:
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream')
    emn=MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    st=[emn]; seen=set(); w=None
    while st:
        e=st.pop()
        if e is None or e in seen: continue
        seen.add(e)
        if e.get_class().get_name()=='MaterialExpressionCustom' and e.get_editor_property('description')=='RealmLightWorms2': w=e
        st+=MEL.get_inputs_for_material_expression(m,e)
    c=w.get_editor_property('code')
    old_hue_a='float3 hue = 0.5 + 0.5 * cos(6.2831853 * (r.z * 0.6 + ba * 0.18 + T * 0.02 + float3(0.0, 0.33, 0.67)));'
    old_hue_b='hue = lerp(hue, float3(1.0, 0.5, 0.35), Warm);'
    new_hue=('float3 cHead = float3(1.0, 0.82, 0.55), cBody = float3(1.0, 0.38, 0.45), cTail = float3(0.62, 0.3, 1.0);\n'
             '    float3 hue = (ba < 0.5) ? lerp(cHead, cBody, ba * 2.0) : lerp(cBody, cTail, ba * 2.0 - 1.0);   // gold head, rose body, violet tail\n'
             '    hue *= 1.0 + 0.12 * (r.w - 0.5) * float3(1.0, -0.6, 0.8);                                     // a slight per-worm tint')
    assert old_hue_a in c and old_hue_b in c
    c=c.replace(old_hue_a,new_hue).replace(old_hue_b,'')
    old_tail='float tailFade = 1.0 - smoothstep(0.45, 1.0, ba);'
    new_tail=('float dust = frac(sin(dot(floor(d * 900.0), float3(12.9898, 78.233, 37.719))) * 43758.5453);\n'
              '    float tailFade = (1.0 - smoothstep(0.45, 1.0, ba)) * lerp(1.0, step(ba * 0.9, dust), smoothstep(0.55, 0.95, ba));   // tail breaks into dust')
    assert old_tail in c; c=c.replace(old_tail,new_tail)
    old_col='float3 col = hue * tr + lerp(hue, white, 0.75) * cr + lerp(hue, white, 0.6) * (bokeh + streak);'
    new_col=('float spark = pow(saturate(sin(ba * 47.0 - T * 6.0 + seed * 7.0) * sin(ba * 23.0 + T * 3.1 + seed)), 18.0) * coreL * 2.5;   // stardust\n'
             '    float3 col = hue * tr + lerp(hue, white, 0.75) * cr + lerp(hue, white, 0.6) * (bokeh + streak) + white * spark;')
    assert old_col in c; c=c.replace(old_col,new_col)
    w.set_editor_property('code',c)
    MEL.recompile_material(m); L.append('worms polished; save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-400:])
open(r'C:/Users/hossa/Documents/agent-office/_opt_out.txt','w').write('\n'.join(L))
