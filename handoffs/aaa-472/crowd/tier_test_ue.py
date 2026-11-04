# i5 #493: prove crowd tiers in Play before building BPC_CrowdTier. Play only, everything put back, nothing saved.
# BASE 8 s / TIERS 8 s / BASE 8 s, each a csvprofile capture. Tiers re-applied 4x a second like the component will.
import time, unreal
GS, SL, ELL = unreal.GameplayStatics, unreal.SystemLibrary, unreal.EditorLevelLibrary
L = lambda p: unreal.load_asset(p).generated_class()
CLS = [L('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'), L('/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute') if unreal.EditorAssetLibrary.does_asset_exist('/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute') else None]
CLS = [c for c in CLS if c]
WM = L('/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager')
NEAR, MID = 2500.0, 6000.0
RATE = {'full': (0.0, 0.0), 'mid': (0.1, 1 / 15.), 'low': (0.25, 0.5)}   # (movement, animation) tick interval
def W(): return ELL.get_game_world()
def zs():
    out = []
    for c in CLS: out += list(GS.get_all_actors_of_class(W(), c))
    return out
cnt = {}
def apply(on):
    p = GS.get_player_pawn(W(), 0); cnt.clear()
    for z in zs():
        cm = z.get_component_by_class(unreal.CharacterMovementComponent); me = z.get_component_by_class(unreal.SkeletalMeshComponent)
        wid = z.get_components_by_class(unreal.WidgetComponent)
        if on and p:
            d = z.get_distance_to(p); seen = z.was_recently_rendered(0.2)
            t = 'full' if d < NEAR or (seen and d < MID) else ('mid' if seen or d < MID else 'low')
        else: t = 'full'
        cnt[t] = cnt.get(t, 0) + 1
        mv, an = RATE[t]
        if cm: cm.set_component_tick_interval(mv)
        if me: me.set_component_tick_interval(an)
        for w in wid: w.set_component_tick_enabled(t == 'full'); w.set_visibility(t == 'full')
def con(c): SL.execute_console_command(W(), c)
S = {'last': time.perf_counter(), 'p': 'wait', 't': 0.0, 'k': 0.0, 'buf': [], 'forced': False, 'i': 0}
PH = ['BASE', 'TIERS', 'BASE']
def tick(dt):
    if not W(): unreal.unregister_slate_post_tick_callback(H); print('tier: Play ended'); return
    if GS.is_game_paused(W()): GS.set_game_paused(W(), False)
    now = time.perf_counter(); dt = now - S['last']; S['last'] = now; S['t'] += dt
    if S['p'] == 'wait':
        n = len(zs())
        if n < 100 and S['t'] < 150:
            if not S['forced']:
                S['forced'] = True
                for a in GS.get_all_actors_of_class(W(), WM):
                    try: a.call_method('ForceNextWave')
                    except Exception as e: print('tier: ForceNextWave', e)
            return
        print('tier: go, zombies', n); S.update(p='run', t=0.0, buf=[]); con('csvprofile start'); return
    ph = PH[S['i']]
    if ph == 'TIERS':
        S['k'] += dt
        if S['k'] >= 0.25: S['k'] = 0.0; apply(True)
    S['buf'].append(dt)
    if S['t'] >= 8.0:
        con('csvprofile stop'); b = S['buf']
        print('tier RESULT %-6s %6.1f ms avg, %d frames, %d zombies, tiers %s' % (ph, 1000 * sum(b) / len(b), len(b), len(zs()), dict(cnt) if ph == 'TIERS' else '-'))
        if ph == 'TIERS': apply(False)
        S['i'] += 1
        if S['i'] >= len(PH): unreal.unregister_slate_post_tick_callback(H); print('tier DONE'); return
        S.update(t=0.0, buf=[]); con('csvprofile start')
H = unreal.register_slate_post_tick_callback(tick)
print('tier: started')
