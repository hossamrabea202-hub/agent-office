# #472 (i5): what really costs the frame in a wave. READ-ONLY for the project: console settings in the running Play session only, all put back, nothing saved.
# Master: press Play, then:  py handoffs/aaa-472/profile/wave_sweep_ue.py        Leave the camera still at the gate. Takes about 2 minutes; editor in the foreground.
# If fewer than 60 zombies are alive it calls ForceNextWave and waits up to 90 s. Writes sweep_<time>.json + .txt next to this file (or in --out <folder>): git push them, done.
# Each step switches one feature off, measures the average frame time for 3 s, switches it back. The drop is that feature's real cost, whatever thread it is on.
import json, os, time, unreal
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = '.'
import sys
ARGS = sys.argv[1:]
OUT = ARGS[ARGS.index('--out') + 1] if '--out' in ARGS else HERE
QUICK = '--quick' in ARGS       # i5's script test: short windows
SETTLE, WINDOW = (0.3, 0.5) if QUICK else (1.5, 3.0)
STEPS = [  # name, off commands, on commands
 ('BASE again', [], []),
 ('screen 25 % (pixel cost test)', ['r.ScreenPercentage 25'], ['r.ScreenPercentage 67']),
 ('skeletal meshes off (zombies + soldiers + hero drawn)', ['ShowFlag.SkeletalMeshes 0'], ['ShowFlag.SkeletalMeshes 1']),
 ('dynamic shadows off', ['ShowFlag.DynamicShadows 0'], ['ShowFlag.DynamicShadows 1']),
 ('CSM 1 cascade', ['r.Shadow.CSM.MaxCascades 1'], ['r.Shadow.CSM.MaxCascades 4']),
 ('point / spot light shadows off', ['r.Shadow.MaxNumPointShadowCacheUpdatesPerFrame 0', 'r.AllowPointLightCubemapShadows 0'], ['r.Shadow.MaxNumPointShadowCacheUpdatesPerFrame -1', 'r.AllowPointLightCubemapShadows 1']),
 ('Lumen GI + reflections off', ['r.DynamicGlobalIlluminationMethod 0', 'r.ReflectionMethod 0'], ['r.DynamicGlobalIlluminationMethod 1', 'r.ReflectionMethod 1']),
 ('translucency off', ['ShowFlag.Translucency 0'], ['ShowFlag.Translucency 1']),
 ('particles off', ['ShowFlag.Particles 0'], ['ShowFlag.Particles 1']),
 ('decals off', ['ShowFlag.Decals 0'], ['ShowFlag.Decals 1']),
 ('grass + foliage off', ['ShowFlag.InstancedGrass 0', 'ShowFlag.InstancedFoliage 0'], ['ShowFlag.InstancedGrass 1', 'ShowFlag.InstancedFoliage 1']),
 ('volumetric fog + clouds off', ['ShowFlag.VolumetricFog 0', 'ShowFlag.Cloud 0'], ['ShowFlag.VolumetricFog 1', 'ShowFlag.Cloud 1']),
 ('post: bloom, AO, motion blur off', ['ShowFlag.Bloom 0', 'ShowFlag.AmbientOcclusion 0', 'ShowFlag.MotionBlur 0'], ['ShowFlag.Bloom 1', 'ShowFlag.AmbientOcclusion 1', 'ShowFlag.MotionBlur 1']),
 ('anim: no skeleton update while off', ['a.ParallelAnimEvaluation 0'], ['a.ParallelAnimEvaluation 1']),
 ('BASE at the end', [], []),
]
W = unreal.EditorLevelLibrary.get_game_world()
if not W: raise SystemExit('Not in Play: press Play first, then run this.')
SL, GS = unreal.SystemLibrary, unreal.GameplayStatics
def cmd(c): SL.execute_console_command(unreal.EditorLevelLibrary.get_game_world(), c)
def alive():
    w = unreal.EditorLevelLibrary.get_game_world()
    return len(GS.get_all_actors_of_class(w, unreal.load_asset('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie').generated_class())) if w else -1
S = {'i': -1, 'phase': 'wait', 't': 0.0, 'buf': [], 'res': [], 'waited': 0.0, 'n0': alive(), 'done': False, 'forced': False}
print('sweep: zombies now', S['n0'])
def stats(b):
    if not b: return None
    s = sorted(b); return {'avg_ms': round(1000 * sum(b) / len(b), 1), 'p95_ms': round(1000 * s[int(len(s) * .95) - 1], 1), 'frames': len(b)}
def finish():
    stamp = time.strftime('%m%d_%H%M%S'); out = {'zombies_start': S['n0'], 'zombies_end': alive(), 'map': W.get_name(), 'quick': QUICK, 'steps': S['res']}
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, 'sweep_%s.json' % stamp); json.dump(out, open(p, 'w'), indent=1)
    base = [r['avg_ms'] for r in S['res'] if r['name'].startswith('BASE') and r['avg_ms']]; ref = sum(base) / len(base) if base else 0
    lines = ['zombies %s -> %s; base %.0f ms (%.1f fps)' % (out['zombies_start'], out['zombies_end'], ref, 1000 / ref if ref else 0)]
    for r in S['res']: lines.append('%-58s %7.1f ms  saves %7.1f ms   (%s zombies)' % (r['name'], r['avg_ms'] or 0, ref - (r['avg_ms'] or 0), r.get('z')))
    open(p[:-5] + '.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines)); print('sweep DONE, written', p)
    cmd('ProfileGPU'); S['gpu_file'] = p[:-5] + '_gpu.txt'; S['gpu_wait'] = 4.0; S['phase'] = 'gpu'; S['done'] = False; S['t'] = 0.0
    print('sweep: ProfileGPU sent, its table goes to', S['gpu_file'])
def tick(dt):
    if S['done']: return
    if not unreal.EditorLevelLibrary.get_game_world():
        S['done'] = True; unreal.unregister_slate_post_tick_callback(HANDLE); print('sweep: Play ended, stopped. Settings live only in Play, so nothing to restore.'); return
    S['t'] += dt
    if S['phase'] == 'gpu':                                          # copy the ProfileGPU table out of the log, then stop
        if S['t'] < S['gpu_wait']: return
        S['done'] = True; unreal.unregister_slate_post_tick_callback(HANDLE)
        logf = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_log_dir()) + 'CastleDefender.log'
        rows = [l for l in open(logf, encoding='utf-8', errors='replace').read().split('\n')[-3000:] if 'LogRHI' in l and ' ms' in l]
        open(S['gpu_file'], 'w', encoding='utf-8').write('\n'.join(l.split('Display:')[-1] for l in rows)); print('sweep: ALL DONE, git push the 3 files', len(rows), 'GPU rows'); return
    if S['phase'] == 'wait':                                         # get a busy wave first
        S['waited'] += dt
        n = alive()
        if not QUICK and n < 60 and S['waited'] < 90:
            if not S['forced']:
                S['forced'] = True
                wm = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager').generated_class()
                for a in GS.get_all_actors_of_class(unreal.EditorLevelLibrary.get_game_world(), wm):
                    try: a.call_method('ForceNextWave')
                    except Exception as e: print('sweep: ForceNextWave', e)
                print('sweep: forced next wave, waiting for zombies')
            return
        S['n0'] = n; S['phase'] = 'next'
    if S['phase'] == 'next':
        S['i'] += 1
        if S['i'] >= len(STEPS): S['done'] = True; finish(); return
        for c in STEPS[S['i']][1]: cmd(c)
        S['phase'] = 'settle'; S['t'] = 0.0; return
    if S['phase'] == 'settle':
        if S['t'] >= SETTLE: S['phase'] = 'measure'; S['t'] = 0.0; S['buf'] = []
        return
    if S['phase'] == 'measure':
        S['buf'].append(dt)
        if S['t'] >= WINDOW:
            r = stats(S['buf']) or {}; r.update(name=STEPS[S['i']][0], z=alive()); r.setdefault('avg_ms', None); S['res'].append(r)
            print('sweep: %-58s %s ms' % (r['name'], r['avg_ms']))
            for c in STEPS[S['i']][2]: cmd(c)
            S['phase'] = 'restore'; S['t'] = 0.0
        return
    if S['phase'] == 'restore':
        if S['t'] >= SETTLE: S['phase'] = 'next'
HANDLE = unreal.register_slate_post_tick_callback(tick)
print('sweep: started, %d steps' % len(STEPS))
