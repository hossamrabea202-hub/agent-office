import unreal
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
L=[]
def nodes(m):
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
    m=unreal.load_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'); n=nodes(m)
    # vortex: skip unless seen from inside
    v=n['RealmVortex']; c=v.get_editor_property('code')
    if 'Amt <= 0.001' not in c:
        v.set_editor_property('code','if (Amt <= 0.001 || Sgn >= 0.0 || Int <= 0.0) return float4(EmOld, OpOld);\n'+c); L.append('vortex early-out')
    # layers 4-9: each block only runs when its intensity > 0
    ly=n['RealmLayers4to9']; c=ly.get_editor_property('code')
    if 'if (L4 > 0.0) {' not in c:
        marks=['// 4 flowing','// 5 spore','// 6 wet','// 7 heart','// 8 aurora','// 9 contact']
        ok=all(k in c for k in marks)
        if ok:
            for i,k in enumerate(marks):
                c=c.replace(k, ('}\n' if i else '')+'if (L%d > 0.0) {\n'%(i+4)+k,1)
            c=c.replace('return float4(em, saturate(op));','}\nreturn float4(em, saturate(op));',1)
            ly.set_editor_property('code',c); L.append('layers guarded')
        else: L.append('layer marks missing')
    # cells: 2x2x2 search instead of 3x3x3
    ce=n['RealmMembraneCells']; c=ce.get_editor_property('code')
    if 'floor(p - 0.5)' not in c:
        c=c.replace('float3 g = floor(p), f = frac(p);','float3 g = floor(p - 0.5), f = p - g;')
        c=c.replace('for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++)','for (int z = 0; z <= 1; z++) for (int y = 0; y <= 1; y++) for (int x = 0; x <= 1; x++)')
        ce.set_editor_property('code',c); L.append('cells 2x2x2')
    MEL.recompile_material(m); L.append('save %s'%EAL.save_asset('/Game/CastleDefender/Realm/M_RealmBubble3_Dream'))
    o=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
    for k,v in [('Layer4_Marble',0.12),('WormIntensity2',24.0),('CellIntensity',0.12),('Layer7_Veins',0.0)]: MEL.set_material_instance_scalar_parameter_value(o,k,v)
    MEL.update_material_instance(o); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Dream')
    i=unreal.load_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Inner')
    for k,v in [('Layer7_Veins',0.9),('Layer5_Motes',0.0),('Layer6_Sheen',0.0),('VortexIntensity',0.0),('WormIntensity2',0.0),('PulseIntensity',0.0),('CellIntensity',0.0),('Layer4_Marble',0.0),('Layer8_Aurora',0.0),('Layer9_Seam',0.0)]:
        MEL.set_material_instance_scalar_parameter_value(i,k,v)
    MEL.update_material_instance(i); EAL.save_asset('/Game/CastleDefender/Realm/MI_RealmBubble3_Inner'); L.append('polish values set')
except Exception as ex:
    import traceback; L.append('ERR '+traceback.format_exc()[-500:])
open(r'C:/Users/hossa/Documents/agent-office/_opt_out.txt','w').write('\n'.join(L))
