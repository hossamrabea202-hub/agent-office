import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L=[]
for a in E.get_selected_level_actors():
    l=a.get_actor_location(); s=a.get_actor_scale3d()
    L.append('%s | %s | loc %d,%d,%d | scale %.3f,%.3f,%.3f'%(a.get_actor_label(),a.get_class().get_name(),l.x,l.y,l.z,s.x,s.y,s.z))
    for c in a.get_components_by_class(unreal.MeshComponent):
        mesh=''
        try: mesh=(c.static_mesh if isinstance(c,unreal.StaticMeshComponent) else c.get_editor_property('skeletal_mesh_asset')).get_name()
        except Exception: pass
        ws=c.get_world_scale()
        L.append('  %s %s mesh %s wscale %.2f,%.2f,%.2f'%(c.get_class().get_name(),c.get_name(),mesh,ws.x,ws.y,ws.z))
        for i,m in enumerate(c.get_materials()):
            if m:
                par=m.get_editor_property('parent').get_path_name() if isinstance(m,unreal.MaterialInstance) and m.get_editor_property('parent') else ''
                L.append('    slot %d %s  parent %s'%(i,m.get_path_name(),par))
open(r'C:/Users/hossa/Documents/agent-office/_sel_out.txt','w').write('\n'.join(L) or 'nothing selected')
