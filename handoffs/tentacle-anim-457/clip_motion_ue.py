# #457 (i5): how far each tentacle clip really moves the tip, from the bone tracks (read-only, no Play). For each placed tentacle (clip, rate, scale from placed.txt):
# the largest tip travel in any 2 s window, in cm at its placed scale. Compare with i9's Play measure (chat 1332): more than this = the strike, not the idle.
import unreal
L = unreal.AnimationLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
by = {str(d.asset_name): d for d in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'AnimSequence')], package_paths=['/Game/CastleDefender/Environment/Tentacles'], recursive_paths=True))}
CHAIN = ['tentaclerig'] + ['seg_%02d' % i for i in range(14)]
def tip(a, t):
    x = unreal.Transform()
    for b in CHAIN:
        x = L.get_bone_pose_for_time(a, b, t, False) * x
    return x.translation
def dist(p, q): return ((p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2) ** 0.5
PLACED = [('Fog1', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway040', .85, 3.0, 247), ('05', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway040', 1.1, 2.4, 1664), ('02', 'SK_CorruptedTentacle_01_Anim_Ripple', 1.0, 2.3, 2044),
          ('04', 'SK_CorruptedTentacle_01_Anim_Ripple', .92, 2.5, 2639), ('03', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway030', .75, 2.9, 205), ('5', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway030', 1.0, 2.5, 387),
          ('4', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway000', .85, 2.5, 0), ('01', 'SK_CorruptedTentacle_01_Anim_Ripple_Sway020', .85, 2.5, 399)]
cache = {}
def clipdata(n):
    if n in cache: return cache[n]
    a = by[n].get_asset(); T = L.get_sequence_length(a); N = 80
    pts = [tip(a, T * i / N) for i in range(N + 1)]
    r = [max(abs(p.x - pts[0].x) for p in pts), max(abs(p.y - pts[0].y) for p in pts), max(abs(p.z - pts[0].z) for p in pts)]
    cache[n] = (T, pts, r); return cache[n]
print('RIG reach of the rest pose', tip(by[PLACED[0][1]].get_asset(), 0))
for name, clip, rate, sc, measured in PLACED:
    T, pts, r = clipdata(clip)
    w = max(1, int(round(2.0 * rate / T * 80)))         # samples in a 2 s window at this rate
    best = max(dist(pts[i], pts[(i + w) % 80]) for i in range(80)) * sc
    print('RIG %-5s %-14s len %.1fs rate %.2f scale %.1f | idle max 2 s tip travel %5.0f cm | i9 measured %5d cm | clip range xyz %.0f %.0f %.0f' % (name, clip.split('Anim_')[-1], T, rate, sc, best, measured, r[0], r[1], r[2]))
for n in sorted(by):
    if 'Polish' in n: T, pts, r = clipdata(n); print('RIG', n, 'len %.0f range xyz %.0f %.0f %.0f' % (T, r[0], r[1], r[2]))
