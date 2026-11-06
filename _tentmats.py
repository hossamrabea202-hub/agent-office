import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); M=unreal.MaterialEditingLibrary
L=[]
for a in E.get_all_level_actors():
    if not (isinstance(a, unreal.SkeletalMeshActor) and 'CorruptedTentacle' in a.get_actor_label()): continue
    l=a.get_actor_location(); L.append('%s at %d,%d,%d'%(a.get_actor_label(),l.x,l.y,l.z))
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        L.append('  comp %s mesh %s'%(c.get_name(), c.get_editor_property('skeletal_mesh_asset').get_name() if c.get_editor_property('skeletal_mesh_asset') else None))
        for i,m in enumerate(c.get_materials()):
            if not m: continue
            par=m.get_editor_property('parent').get_name() if isinstance(m,unreal.MaterialInstance) and m.get_editor_property('parent') else ''
            extra=''
            for p in ['HideLenBase','HideLenTip','TentScale']:
                try: extra+=' %s=%.0f'%(p,M.get_material_instance_scalar_parameter_value(m,p))
                except Exception: pass
            L.append('    slot %d %s (parent %s)%s'%(i,m.get_name(),par,extra))
open(r'C:/Users/hossa/Documents/agent-office/_tent_out.txt','w').write('\n'.join(L))
