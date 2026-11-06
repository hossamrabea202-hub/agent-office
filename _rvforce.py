import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
mpc=unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
hero=unreal.GameplayStatics.get_player_character(w,0)
fx=hero.get_component_by_class(unreal.load_class(None,'/Game/CastleDefender/Gameplay/Castle/BPC_MotionFX.BPC_MotionFX_C'))
fx.set_editor_property('BookOpened', False)
st={'n':0,'log':[]}
def tick(dt):
    st['n']+=1
    try:
        if st['n']<=40: unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, 'BookAge', 0.1+0.02*st['n'])
        if st['n'] in (2,10,40,120):
            st['log'].append('tick %d RvKind %s RvT0 %s BookOpened %s Blur %s'%(st['n'], fx.get_editor_property('RvKind'), fx.get_editor_property('RvT0'), fx.get_editor_property('BookOpened'), unreal.MaterialLibrary.get_scalar_parameter_value(w, unreal.load_asset('/Game/CastleDefender/UI/Reveal/MPC_Reveal'), 'Blur')))
        if st['n']>=120:
            unreal.unregister_slate_post_tick_callback(st['h']); open(r'C:/Users/hossa/Documents/agent-office/_rvf.txt','w').write('\n'.join(st['log']))
    except Exception as e:
        st['log'].append(str(e)); unreal.unregister_slate_post_tick_callback(st['h']); open(r'C:/Users/hossa/Documents/agent-office/_rvf.txt','w').write('\n'.join(st['log']))
st['h']=unreal.register_slate_post_tick_callback(tick)
