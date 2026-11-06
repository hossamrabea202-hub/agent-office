# blender -b -P zoneshot.py -- <clip_rig.fbx> <which: smash|death|...> <out.fbx>   [env Z_LAG = overlap lag scale]
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig, zperform as F, zperf as S
a = sys.argv[sys.argv.index('--')+1:]; RIG, WHICH, OUT = a
F.LAG_SCALE = float(os.environ.get('Z_LAG', '1.6'))     # a giant's follow-through trails longer
spec = S.ALL[WHICH]
arm = zrig.load_rig(RIG)
perf = F.Performance(spec['keys'], spec['length'])
n = F.author(arm, perf, spec['name'])
zrig.export_anim(arm, OUT, 1, n)
print('AUTHOR OK', spec['name'], n, 'frames')
