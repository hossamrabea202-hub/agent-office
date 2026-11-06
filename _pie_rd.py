import unreal
w=unreal.EditorLevelLibrary.get_game_world()
rv=[a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if 'RealmVision' in a.get_class().get_name()]
p=unreal.GameplayStatics.get_player_pawn(w,0)
s='pawn %s; '%p.get_actor_location()
for a in rv: s+='Inside=%s W=%s TwoSided=%s'%(a.get_editor_property('Inside'),a.get_editor_property('W'),a.get_editor_property('TwoSided'))
open(r'C:/Users/hossa/Documents/agent-office/_tp_out.txt','w').write(s)
