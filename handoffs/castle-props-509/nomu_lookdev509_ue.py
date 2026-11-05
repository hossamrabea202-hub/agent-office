# #509 i5 lookdev on i5's copy of ThirdPersonMap (no Multi-User session; everything temporary, nothing saved into the project
# except the throwaway /Game/_i5tmpWS509 folder, which 'clear' deletes).
#   py nomu_lookdev509_ue.py import     the 10 new meshes into /Game/_i5tmpWS509 (+ #504 and foot card materials, temp)
#   py nomu_lookdev509_ue.py views      picks the shot cameras from the real geometry -> views509.txt
#   py nomu_lookdev509_ue.py before     locked-exposure shots -> shots/ws509_<view>_before.png   (lookdev daylight on)
#   py nomu_lookdev509_ue.py place      all four placers with --apply --temp
#   py nomu_lookdev509_ue.py after      same shots -> _after.png (a separate run, so the new shaders have compiled)
#   py nomu_lookdev509_ue.py clear      removes WS509 / FX509 / FW509 / LD504 actors and deletes /Game/_i5tmpWS509
import math, os, sys, unreal
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-props-509'
REPO = 'C:/Users/hossam.rabea/agent-office'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
step = [a for a in sys.argv[1:] if not a.startswith('--')][0]
# --real (i9 preview on the live castle): the real asset paths (import / build done by the README steps first), 'after' removes
# everything again, nothing is saved. Without it: i5's temp folder.
REAL = '--real' in sys.argv
TMP = [] if REAL else ['--temp']


def run(path, argv):
    old = sys.argv; sys.argv = [path] + argv
    try: exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), {'__name__': '__main__', '__file__': path})
    except SystemExit: pass
    finally: sys.argv = old


if step == 'import':
    run(REPO + '/assets/laptop2/CampKit/import_kit_ue.py', ['ArrowSheaf', 'SpearStook', 'DropStones', 'FireBucket', 'HoardingBay', 'HoardingEnd', 'TieRing', 'WallBracket', 'AnchorPlate', 'DrainSpout', '--temp'])
    run(REPO + '/handoffs/castle-weather-504/build_weather504_ue.py', ['--temp'])
    run(HERE + '/build_foot509_ue.py', ['--temp'])
elif step == 'views':
    import random
    ST = {'__name__': 'v'}; code = open(HERE + '/place_stores509_ue.py', encoding='utf-8').read(); old = sys.argv; sys.argv = ['x']
    exec(compile(code[:code.rindex("if '--remove' in args:")], 'st', 'exec'), ST); sys.argv = old
    sites, clusters, gate = ST['plan']()
    trace = ST['trace']

    def clear_cam(cam, tgt, need=220.0):
        """pull the camera toward the target until it sees it; None if it ends up closer than need."""
        h = trace(tgt, cam)
        if h:
            dv = cam - tgt; L = dv.length(); cam = tgt + dv * ((h['dist'] - 40.0) / L)
        return cam if (cam - tgt).length() >= need else None
    views = {}
    gp = gate[1]; views['gate'] = (V(gp.x - 2200, gp.y - 900, 700), V(gp.x - 150, gp.y, 900))
    n_walk = 0
    for kind, P, d, dp, ng, free in clusters:
        if n_walk >= 3: break
        r = V(-d.y, d.x, 0)
        for side in (1, -1):
            tgt = P + d * (dp * 0.8) + V(0, 0, 45)
            cam = clear_cam(P - d * min(free * 0.6, 150.0) + r * (380.0 * side) + V(0, 0, 160), tgt, 260.0)   # along the walk, eye height
            if cam: views['walk%d_%s' % (n_walk, kind)] = (cam, tgt); n_walk += 1; break
    FX = {'__name__': 'v'}; code = open(HERE + '/place_fittings509_ue.py', encoding='utf-8').read(); old2 = sys.argv; sys.argv = ['x', '--only', 'spouts']
    exec(compile(code[:code.rindex("if '--remove' in args:")], 'fx', 'exec'), FX); sys.argv = old2
    put, streaks, _g = FX['plan']()
    for loc, n, w, h in streaks[:4]:
        tgt = loc + V(0, 0, -60); cam = clear_cam(loc + n * 900.0 + V(0, 0, -250), tgt, 400.0)
        if cam: views['spout'] = (cam, tgt); break
    FT = {'__name__': 'v'}; code = open(HERE + '/place_foot509_ue.py', encoding='utf-8').read(); sys.argv = ['x']
    exec(compile(code[:code.rindex("if '--remove' in args:")], 'ft', 'exec'), FT); sys.argv = old
    feet, cards, weeds = FT['plan']()
    n_foot = 0
    for k in cards:
        if n_foot >= 2: break
        n = k[2]; r = V(-n.y, n.x, 0); F = k[1]
        if trace(F + n * 150.0 + V(0, 0, 50), F + n * 150.0 + V(0, 0, 3000)): continue            # under a roof / arch: too dark to judge
        if n.x * 0.604 + n.y * 0.507 < 0.3: continue                                    # lit by the lookdev sun (nomu_ldlight504: pitch -38, yaw -140)
        cam = clear_cam(F + n * 450.0 + r * 200.0 + V(0, 0, 110), F + V(0, 0, -10), 300.0)
        if cam: views['foot%d_%s' % (n_foot, k[0][10:].lower())] = (cam, F + V(0, 0, -10)); n_foot += 1
    open(HERE + '/views509.txt', 'w').write('\n'.join('%s %s' % (k, ' '.join('%.0f' % x for x in (c.x, c.y, c.z, t.x, t.y, t.z))) for k, (c, t) in views.items()) + '\n')
    print('views', list(views))
elif step in ('before', 'after'):
    run(REPO + '/handoffs/castle-weather-504/nomu_ldlight504_ue.py', ['on'])
    sys.path.insert(0, REPO + '/handoffs/contact-decals-425'); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
    os.makedirs(HERE + '/shots', exist_ok=True)
    for line in open(HERE + '/views509.txt'):
        k, *c = line.split(); c = [float(x) for x in c]
        lookdev_cap.shot('%s/shots/ws509_%s%s_%s.png' % (HERE, 'i9_' if REAL else '', k, step), V(*c[:3]), V(*c[3:]), 1.5, 50.0)
    if step == 'after' and REAL:          # i9 preview: take it all out again, nothing saved
        gone = [x for x in EAS.get_all_level_actors() if set(str(t) for t in x.tags) & {'WS509', 'FX509', 'FW509', 'LD504'}]
        for x in gone: EAS.destroy_actor(x)
        print('preview removed', len(gone), 'actors: do NOT save the level')
    elif step == 'before':
        for x in [x for x in EAS.get_all_level_actors() if 'LD504' in [str(t) for t in x.tags]]: EAS.destroy_actor(x)
elif step == 'place':
    run(HERE + '/place_stores509_ue.py', ['--apply'] + TMP)
    run(HERE + '/place_fittings509_ue.py', ['--apply'] + TMP)
    run(HERE + '/place_foot509_ue.py', ['--apply'] + TMP)
elif step == 'clear':
    gone = [x for x in EAS.get_all_level_actors() if set(str(t) for t in x.tags) & {'WS509', 'FX509', 'FW509', 'LD504'}]
    for x in gone: EAS.destroy_actor(x)
    print('cleared', len(gone))
    if '--keep-assets' not in sys.argv:
        unreal.SystemLibrary.collect_garbage()
        print('deleted temp folder', unreal.EditorAssetLibrary.delete_directory('/Game/_i5tmpWS509'))
