import unreal
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
a=[x for x in E.get_all_level_actors() if x.get_actor_label()=='Realm_Vision'][0]
a.modify(); old=a.get_editor_property('FadeSpeed'); a.set_editor_property('FadeSpeed', 1.2)
ok=unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:/Users/hossa/Documents/agent-office/_rvfade_out.txt','w').write('FadeSpeed %s -> %s saved %s'%(old,a.get_editor_property('FadeSpeed'),ok))
