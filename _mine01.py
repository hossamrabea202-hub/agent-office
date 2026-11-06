import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
a=[x for x in E.get_all_level_actors() if x.get_actor_label()=='Mine_01'][0]
out=[a.get_class().get_name()]
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    sm=c.static_mesh
    out.append('%s mesh=%s mats=%s slots=%s'%(c.get_name(), sm.get_path_name() if sm else None, [m.get_path_name() if m else None for m in c.get_materials()], [str(s.get_editor_property('material_slot_name')) + ':' + (s.get_editor_property('material_interface').get_path_name() if s.get_editor_property('material_interface') else 'None') for s in sm.get_editor_property('static_materials')] if sm else None))
txt=open(r'C:/Users/hossa/Documents/agent-office/_latest/handoffs/cave-296-297/caverock296_meshswaps.txt').read() if True else ''
out.append('swaps log: '+txt)
open(r'C:/Users/hossa/Documents/agent-office/_mine01.txt','w').write('\n'.join(out))
