# blender -b -P zl_roundtrip.py -- <anim.fbx> <out.fbx>   (the clip's own armature is the rig; re-export as authored clips will be)
import bpy, sys, os
a = sys.argv[sys.argv.index('--')+1:]; ANIM, OUT = a
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig as R
arm = R.load_rig(ANIM, rest=False)
act = arm.animation_data.action
print('RT curves', len(R._fcurves(act)), 'range', act.frame_range[:], 'mode', arm.rotation_mode, 'scale', tuple(arm.scale))
for f in (1, 30, 60):
    bpy.context.scene.frame_set(f); print('RT frame', f, 'arm loc', tuple(round(x, 4) for x in arm.matrix_world.translation))
R.export_anim(arm, OUT, int(act.frame_range[0]), int(act.frame_range[1]))
print('ROUNDTRIP OK', OUT)
