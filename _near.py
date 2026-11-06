import unreal
UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
loc,rot=UES.get_level_viewport_camera_info()
fwd=rot.get_forward_vector()
print('cam',loc,rot)
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    p=a.get_actor_location(); d=(p-loc).length()
    if d<6000 and (p-loc).dot(fwd)>0:
        out.append((d,a.get_actor_label(),a.get_class().get_name(),[str(t) for t in a.tags],a.get_level().get_outermost().get_name().split('/')[-1]))
for o in sorted(out)[:60]: print('%6.0f %-40s %-30s %s %s'%o)
