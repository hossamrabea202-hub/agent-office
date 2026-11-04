# i5 #487: Insights trace with named events + CSV, 6 s of game time. Read-only, Play only.
import unreal
SL, GS, ELL = unreal.SystemLibrary, unreal.GameplayStatics, unreal.EditorLevelLibrary
ZC = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie').generated_class()
def W(): return ELL.get_game_world()
def cmd(c): SL.execute_console_command(W(), c); print('cmd', c)
GS.set_game_paused(W(), False)
S = {'t': 0.0, 'p': 0}
def tick(dt):
    if not W(): unreal.unregister_slate_post_tick_callback(H); print('trace: Play ended'); return
    S['t'] += dt
    if GS.is_game_paused(W()): GS.set_game_paused(W(), False)
    if S['p'] == 0: cmd('stat namedevents'); cmd('Trace.File cpu,frame,bookmark'); cmd('csvprofile start'); S.update(p=1, t=0.0)
    elif S['p'] == 1 and S['t'] >= 6.0:
        cmd('csvprofile stop'); cmd('Trace.Stop'); cmd('stat namedevents')
        print('trace DONE zombies', len(GS.get_all_actors_of_class(W(), ZC))); unreal.unregister_slate_post_tick_callback(H)
H = unreal.register_slate_post_tick_callback(tick)
print('trace: started')
