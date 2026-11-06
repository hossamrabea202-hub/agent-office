import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); w=unreal.EditorLevelLibrary.get_editor_world()
out=[]
for a in E.get_all_level_actors():
    if a.get_class().get_name()!='BP_BlobMine_C': continue
    p=a.get_actor_location(); ign=[a]; z=None
    for _ in range(25):
        h=unreal.SystemLibrary.line_trace_single(w, unreal.Vector(p.x,p.y,40000), unreal.Vector(p.x,p.y,-40000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ign, unreal.DrawDebugTrace.NONE, True)
        t=h.to_tuple() if h else None
        if not t or not t[0] or not t[9]: break
        if 'Landscape' in t[9].get_class().get_name(): z=t[4].z; break
        ign.append(t[9])
    if z is not None and abs(p.z-z)>30:
        a.modify(); a.set_actor_location(unreal.Vector(p.x,p.y,z), False, False); out.append('%s %.0f -> %.0f'%(a.get_actor_label(),p.z,z))
out.append('save %s'%unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
open(r'C:/Users/hossa/Documents/agent-office/_ms.txt','w').write('\n'.join(out))
