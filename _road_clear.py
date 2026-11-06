import unreal
# remove meadow plants from the gate road (Env_WornGround_Decal path running west from the gate along y~1750)
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
act=[a for a in E.get_all_level_actors() if a.get_actor_label()=='Meadow351'][0]
Y0, HALF, XMIN, XMAX = 1750.0, 450.0, -7000.0, 300.0
tot=rem=0
for c in act.get_components_by_class(unreal.InstancedStaticMeshComponent):
    n=c.get_instance_count(); keep=[]
    for i in range(n):
        t=c.get_instance_transform(i, True); p=t.translation
        if XMIN < p.x < XMAX and abs(p.y-Y0) < HALF: rem+=1; continue
        keep.append(t)
    tot+=n
    if len(keep)!=n:
        c.clear_instances(); c.add_instances(keep, False, True)
print('instances %d removed %d'%(tot,rem))
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
