import unreal
w=unreal.EditorLevelLibrary.get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
t=[a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.TargetPoint) if a.get_actor_label()=='Realm_Spawn_Zombie_00']
l=t[0].get_actor_location() if t else unreal.Vector(-13808,4140,-618)
l=unreal.Vector(l.x,l.y,l.z+250)
r=p.set_actor_location(l, False, True)
open(r'C:/Users/hossa/Documents/agent-office/_tp2_out.txt','w').write('tp to %s ok %s now %s'%(l,r,p.get_actor_location()))
