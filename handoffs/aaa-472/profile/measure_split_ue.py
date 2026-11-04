# i5 #487: no-wave vs wave frame split. Read-only: console commands in Play only, nothing saved.
import time, unreal
from collections import Counter
GS, SL, ELL = unreal.GameplayStatics, unreal.SystemLibrary, unreal.EditorLevelLibrary
ZC = unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie').generated_class()
WM = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager').generated_class()
def W(): return ELL.get_game_world()
def cmd(c): SL.execute_console_command(W(), c); print('cmd', c)
def alive(): return len(GS.get_all_actors_of_class(W(), ZC)) if W() else -1
WIN = 8.0
S = {'p': 'settle0', 't': 0.0, 'buf': [], 'res': {}, 'w': 0.0}
def rec(name):
    b = sorted(S['buf']); n = len(b)
    S['res'][name] = r = {'avg_ms': round(1000*sum(b)/n, 1), 'p95_ms': round(1000*b[int(n*.95)-1], 1), 'frames': n, 'zombies': alive()}
    print('measure', name, r)
def tick(dt):
    if not W(): unreal.unregister_slate_post_tick_callback(H); print('measure: Play ended'); return
    S['t'] += dt; p = S['p']
    if p == 'settle0' and S['t'] > 3: cmd('csvprofile start'); S.update(p='nowave', t=0.0, buf=[])
    elif p == 'nowave':
        S['buf'].append(dt)
        if S['t'] >= WIN:
            cmd('csvprofile stop'); rec('nowave')
            for a in GS.get_all_actors_of_class(W(), WM):
                try: a.call_method('ForceNextWave'); print('measure: ForceNextWave on', a.get_name())
                except Exception as e: print('measure: ForceNextWave failed', e)
            S.update(p='waitwave', t=0.0)
    elif p == 'waitwave':
        n = alive()
        if n >= 60 or S['t'] > 120:
            print('measure: zombies', n, 'after', round(S['t']), 's'); cmd('dumpticks')
            S.update(p='settle1', t=0.0)
    elif p == 'settle1' and S['t'] > 2: cmd('csvprofile start'); S.update(p='wave', t=0.0, buf=[])
    elif p == 'wave':
        S['buf'].append(dt)
        if S['t'] >= WIN:
            cmd('csvprofile stop'); rec('wave')
            c = Counter(a.get_class().get_name() for a in GS.get_all_actors_of_class(W(), unreal.Pawn))
            print('measure pawns', c.most_common(15))
            unreal.unregister_slate_post_tick_callback(H); print('measure DONE')
H = unreal.register_slate_post_tick_callback(tick)
print('measure: started, zombies', alive())
