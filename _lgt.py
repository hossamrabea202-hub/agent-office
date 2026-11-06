import unreal, math
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cam,_=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info()
ds=[]
for a in E.get_all_level_actors():
    if 'Landscape' not in a.get_class().get_name(): continue
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        n=c.get_instance_count()
        if n: 
            o,e,_r=unreal.SystemLibrary.get_component_bounds(c)
            ds.append(math.hypot(o.x-cam.x,o.y-cam.y))
ds.sort(); print('cam',cam,'comps',len(ds),'max dist',ds[-1] if ds else None, 'p50', ds[len(ds)//2] if ds else None)
