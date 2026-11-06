import unreal
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
def exprs(m):
    # 5.3: iterate via the material's expressions collection
    try: return list(m.get_editor_property('expressions'))
    except Exception: pass
    return []
for n in ['M_BerserkAura','M_BerserkEmber','M_BerserkGround','M_BerserkWisp']:
    p='/Game/CastleDefender/VFX/Berserk/'+n; m=unreal.load_asset(p)
    ex=exprs(m)
    if not ex:
        # fallback: walk from outputs
        seen=[];st=[]
        for prop in ('MP_EMISSIVE_COLOR','MP_OPACITY','MP_BASE_COLOR','MP_WORLD_POSITION_OFFSET','MP_OPACITY_MASK'):
            e=MEL.get_material_property_input_node(m,getattr(unreal.MaterialProperty,prop))
            if e: st.append(e)
        while st:
            e=st.pop()
            if e in seen: continue
            seen.append(e); st+= [i for i in MEL.get_inputs_for_material_expression(m,e) if i]
        ex=seen
    fixed=0
    for e in ex:
        if isinstance(e,unreal.MaterialExpressionComponentMask):
            ins=[i for i in MEL.get_inputs_for_material_expression(m,e) if i]
            if ins and isinstance(ins[0],unreal.MaterialExpressionParticleColor):
                f=[e.get_editor_property(k) for k in 'rgba']
                print(n,'mask',e.get_name(),'rgba',f)
                if f==[False,False,False,True]:
                    MEL.connect_material_expressions(ins[0],'A',e,'')
                    for k in 'rgb': e.set_editor_property(k, k=='r')
                    e.set_editor_property('a',False); fixed+=1
    MEL.recompile_material(m); EAL.save_asset(p)
    print(n,'exprs',len(ex),'fixed',fixed)
