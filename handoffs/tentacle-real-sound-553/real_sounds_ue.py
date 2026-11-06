# Real recorded tentacle sounds (adjustedfilm, 2026-11-06). Replaces the 6 synthesised waves in place, so every notify and blueprint keeps working. Editor idle, not in Play.
#   py real_sounds_ue.py --dry-run | --apply | --revert        (--revert puts back tentacle-rise-541/sound/*.wav)
# Built only from recordings already in the project (MonsterRoarsAndGrowls, Free_Sounds_Pack, FreeModularMagicSFX). They are mixed on the Master's PC at run time: no pack audio goes into this repo.
# A recipe = name, length s, [(wave, start s, speed, gain, reverse, fade in s)]. Speed under 1 lowers the pitch and makes the source sound bigger. Every stem is normalised first; the mix peaks at 0.85.
import os, sys, wave, array, math, tempfile
MR, FS, MG = '/Game/MonsterRoarsAndGrowls/wav/', '/Game/Free_Sounds_Pack/wav/', '/Game/FreeModularMagicSFX/C_Cast/Mono/SW_MagicCast_'
RECIPES = [
 ('SW_TentacleRoar', 4.4, [(MR + '07_Behemoth_Roar', 0.0, 0.80, 1.0, False, 0.0), (MR + '08_Titan_Roar', 0.3, 0.60, 0.5, False, 0.0)]),
 ('SW_TentacleGroan', 3.4, [(MR + '18_Rumbling_Growl', 0.0, 0.85, 1.0, False, 0.0), (MR + '21_Lurking_Growl', 0.4, 0.70, 0.45, False, 0.0)]),
 ('SW_TentacleRumble', 3.6, [(MR + '18_Rumbling_Growl', 0.0, 0.40, 1.0, False, 2.8), (FS + 'Rock_Large_Debris_1-3', 0.0, 0.60, 0.8, False, 2.5), (MG + 'GroundStrike_1', 2.3, 0.50, 0.6, False, 0.3)]),
 ('SW_TentacleBurst', 4.0, [(FS + 'Explosion_Large_1-1', 0.0, 0.80, 1.0, False, 0.0), (FS + 'Rock_Impact_37', 0.0, 0.70, 0.6, False, 0.0), (FS + 'Rock_Large_Debris_1-3', 0.1, 1.0, 0.5, False, 0.0), (MG + 'Liquid_Gore_2', 0.02, 0.70, 0.7, False, 0.0)]),
 ('SW_TentacleSpit', 1.9, [(MG + 'Liquid_Gore_2', 0.41, 1.10, 1.0, False, 0.0), (MG + 'Liquid_Gore_6', 0.45, 0.90, 0.5, False, 0.0)]),
 ('SW_BlobSplat', 1.2, [(MG + 'Liquid_Gore_3', -0.08, 0.85, 1.0, False, 0.0), (FS + 'Punch_2-1', 0.0, 0.70, 0.5, False, 0.0)]),
]
RATE = 44100
def read_mono(fn):
    w = wave.open(fn); c, r, n, sw = w.getnchannels(), w.getframerate(), w.getnframes(), w.getsampwidth()
    if sw != 2: raise SystemExit('REAL553 not 16 bit: ' + fn)
    a = array.array('h'); a.frombytes(w.readframes(n)); w.close()
    if sys.byteorder == 'big': a.byteswap()
    return [sum(a[i:i + c]) / (32768.0 * c) for i in range(0, len(a), c)], r
def stem(fn, speed, rev):
    x, r = read_mono(fn); pk = max(max(abs(v) for v in x), 1e-5); step = speed * r / RATE; out = []; p = 0.0; last = len(x) - 1
    while p < last: i = int(p); f = p - i; out.append((x[i] * (1 - f) + x[i + 1] * f) / pk); p += step
    return out[::-1] if rev else out
def mix(recipe, path_of):
    name, L, stems = recipe; N = int(L * RATE); m = [0.0] * N
    for (src, start, speed, gain, rev, fade) in stems:
        s = stem(path_of(src), speed, rev); o = int(start * RATE); fi = int(fade * RATE)
        for i, v in enumerate(s):
            j = i + o
            if j < 0: continue
            if j >= N: break
            m[j] += gain * v * (min(1.0, (j + 1) / fi) if fi else 1.0)
    pk = max(max(abs(v) for v in m), 1e-5); g = 0.85 / pk; ft = int(0.12 * RATE)
    for i in range(N): m[i] = m[i] * g * (min(1.0, (N - 1 - i) / ft))
    for i in range(min(60, N)): m[i] *= i / 60.0
    return m
def write(fn, m):
    w = wave.open(fn, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); a = array.array('h', [int(max(-1.0, min(1.0, v)) * 32767) for v in m])
    if sys.byteorder == 'big': a.byteswap()
    w.writeframes(a.tobytes()); w.close()
if __name__ == '__main__':
    import unreal
    HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); E = unreal.EditorAssetLibrary
    S_ = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530/Sound/'; ATT = S_ + 'ATT_Tentacle541'; TMP = os.path.join(tempfile.gettempdir(), 'real553'); os.makedirs(TMP, exist_ok=True)
    def say(*a): print('REAL553', ' '.join(str(x) for x in a))
    miss = [r[0] for r in RECIPES if not E.does_asset_exist(S_ + r[0])] + sorted({s[0] for r in RECIPES for s in r[2] if not E.does_asset_exist(s[0])})
    if miss and '--revert' not in A: raise SystemExit('REAL553 missing %s; nothing changed. Run sfx541_ue.py first, or tell i5 which pack is gone' % miss)
    def imp(fn, name):
        t = unreal.AssetImportTask(); t.filename = fn; t.destination_path = S_.rstrip('/'); t.destination_name = name; t.automated = True; t.replace_existing = True; t.save = True; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        w = unreal.load_asset(S_ + name)
        if E.does_asset_exist(ATT): w.set_editor_property('attenuation_settings', unreal.load_asset(ATT))
        E.save_loaded_asset(w); say(name, 'len', round(w.get_editor_property('duration'), 2))
    if '--revert' in A:
        for r in RECIPES: imp(os.path.normpath(os.path.join(HERE, '..', 'tentacle-rise-541', 'sound', r[0] + '.wav')), r[0])
        say('DONE revert'); raise SystemExit(0)
    if '--apply' not in A: say('WOULD mix and replace', [r[0] for r in RECIPES], 'all sources found'); raise SystemExit(0)
    done = {}
    def path_of(src):
        if src not in done:
            t = unreal.AssetExportTask(); t.object = unreal.load_asset(src); t.filename = os.path.join(TMP, src.rsplit('/', 1)[1] + '.wav'); t.automated = True; t.prompt = False; t.replace_identical = True
            if not unreal.Exporter.run_asset_export_task(t): raise SystemExit('REAL553 export failed ' + src)
            done[src] = t.filename
        return done[src]
    for r in RECIPES:
        fn = os.path.join(TMP, r[0] + '.wav'); write(fn, mix(r, path_of)); imp(fn, r[0])
    say('DONE')
