# blender -b -P author_oneshot.py -- <SK.fbx> <which: roar|slam|swipe> <out.fbx>
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, bl_rig, bl_perform as F, perf_stage2 as S
a = sys.argv[sys.argv.index('--')+1:]; SK, WHICH, OUT = a
spec = S.ALL[WHICH]
arm = bl_rig.load_rig(SK, keep_mesh=False)
perf = F.Performance(spec['keys'], spec['length'])
n = F.author(arm, perf, spec['name'])
bl_rig.export_anim(arm, OUT, 1, n)
print('AUTHOR OK', spec['name'], n, 'frames')
