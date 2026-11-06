import unreal, sys
w=unreal.EditorLevelLibrary.get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
mode=sys.argv[-1] if len(sys.argv)>1 else 'in'
E=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if mode=='in':
    m=[a for a in E.get_all_level_actors() if 'BlobMine' in a.get_actor_label()]
    l=m[len(m)//2].get_actor_location(); l.z+=250; l.x+=300
else:
    l=unreal.Vector(-11100,1750,1200)
p.set_actor_location(l, False, True)
rv=[a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_actor_label()=='Realm_Vision' or 'RealmVision' in a.get_class().get_name()]
s='tp %s to %s; vision actors %d'%(mode,l,len(rv))
for a in rv:
    try: s+=' Inside=%s W=%s'%(a.get_editor_property('Inside'),a.get_editor_property('W'))
    except Exception as e: s+=' err %s'%e
open(r'C:/Users/hossa/Documents/agent-office/_tp_out.txt','w').write(s)
