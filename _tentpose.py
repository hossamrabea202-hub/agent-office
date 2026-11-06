import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L=[]
for a in E.get_all_level_actors():
    if not (isinstance(a, unreal.SkeletalMeshActor) and 'CorruptedTentacle' in a.get_actor_label()): continue
    c=a.skeletal_mesh_component
    try: mode=c.get_editor_property('animation_mode'); anim=c.get_editor_property('animation_data').get_editor_property('anim_to_play')
    except Exception as ex: mode='?'; anim=ex
    names=[str(n) for n in c.get_all_socket_names()] if hasattr(c,'get_all_socket_names') else []
    segs=[n for n in names if n.lower().startswith('seg')]; segs.sort()
    pos=[c.get_socket_location(n) for n in segs]
    d=[round((pos[i+1]-pos[i]).length(),0) for i in range(len(pos)-1)]
    L.append('%s mode %s anim %s\n   seg spacing (world) %s'%(a.get_actor_label(),mode,anim.get_name() if hasattr(anim,'get_name') else anim,d))
open(r'C:/Users/hossa/Documents/agent-office/_tent_out.txt','w').write('\n'.join(L))
