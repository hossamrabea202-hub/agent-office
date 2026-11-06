import unreal
w=unreal.EditorLevelLibrary.get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
cam=unreal.GameplayStatics.get_player_camera_manager(w,0)
s='pawn %s cam %s\n'%(p.get_actor_location(), cam.get_camera_location() if cam else None)
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    if 'RealmVision' in a.get_class().get_name():
        for v in ['Bubble','BubbleMesh','Inside','W','Dist','TwoSided','CrossT0','CrossDir','PullDist','DeepDist','PullMax','EnterTime','ExitTime','FadeSpeed']:
            try: s+='%s=%s; '%(v,a.get_editor_property(v))
            except Exception as e: s+='%s=ERR; '%v
        pp=a.get_component_by_class(unreal.PostProcessComponent)
        if pp:
            st=pp.get_editor_property('settings')
            s+='\npp weight %s unbound %s enabled %s blendables %s'%(pp.get_editor_property('blend_weight'),pp.get_editor_property('unbound'),pp.get_editor_property('enabled') if True else '', [ (b.get_editor_property('object').get_name() if b.get_editor_property('object') else None, b.get_editor_property('weight')) for b in st.get_editor_property('weighted_blendables').get_editor_property('array')])
mpc=unreal.load_asset('/Game/CastleDefender/Gameplay/Realm/MPC_RealmDream')
if mpc:
    for n in ['Amount','Cross','CrossDir','BreathHz']:
        s+='\nMPC %s=%s'%(n,unreal.KismetMaterialLibrary.get_scalar_parameter_value(w,mpc,n) if hasattr(unreal,'KismetMaterialLibrary') else unreal.MaterialLibrary.get_scalar_parameter_value(w,mpc,n))
open(r'C:/Users/hossa/Documents/agent-office/_tp_out.txt','w').write(s)
