# blender -b -P zoneshot.py -- <clip_rig.fbx> <which: smash|death|...> <out.fbx>   [env Z_LAG = overlap lag scale]
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig, zperform as F, zperf as S, zperf_walkers as SW
a = sys.argv[sys.argv.index('--')+1:]; RIG, WHICH, OUT = a
ALL = dict(S.ALL); ALL.update(SW.ALL)
F.LAG_SCALE = float(os.environ.get('Z_LAG', '1.6' if WHICH in S.ALL else '1.0'))     # a giant's follow-through trails longer
spec = ALL[WHICH]
arm = zrig.load_rig(RIG)
perf = F.Performance(spec['keys'], spec['length'])
n = F.author(arm, perf, spec['name'])
zrig.export_anim(arm, OUT, 1, n)
print('AUTHOR OK', spec['name'], n, 'frames')
