# blender -b -P zmeasure.py -- <clip.fbx> [...]: per-clip ground / hips / hand summary from UE-exported clips (world metres)
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig as R
from mathutils import Vector
for f in sys.argv[sys.argv.index('--')+1:]:
    arm = R.load_rig(f, rest=False); sc = bpy.context.scene; act = arm.animation_data.action
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); mw = lambda b: arm.matrix_world @ arm.pose.bones[b].head
    rows = []
    for fr in range(f0, f1+1):
        sc.frame_set(fr)
        rows.append(dict(f=fr, hips=arm.matrix_world.translation.copy(), lt=mw('LeftToeBase'), rt=mw('RightToeBase'), lte=mw('LeftToe_End'), rte=mw('RightToe_End'),
                         la=mw('LeftFoot'), ra=mw('RightFoot'), lh=mw('LeftHand'), rh=mw('RightHand'), hd=mw('Head'), lk=mw('LeftLeg'), rk=mw('RightLeg')))
    name = os.path.basename(f)
    toe = [min(r['lte'].z, r['rte'].z) for r in rows]; ank = [min(r['la'].z, r['ra'].z) for r in rows]
    print('MEAS %s frames %d-%d | hips z %.3f..%.3f y %.3f..%.3f | lowest toe z %.3f (max %.3f) | ankle z min %.3f | head z %.3f..%.3f' % (
        name, f0, f1, min(r['hips'].z for r in rows), max(r['hips'].z for r in rows), min(r['hips'].y for r in rows), max(r['hips'].y for r in rows),
        min(toe), max(toe), min(ank), min(r['hd'].z for r in rows), max(r['hd'].z for r in rows)))
    # hands: height per frame and the fastest frame (the blow)
    sp = [((rows[i]['lh']-rows[i-1]['lh']).length + (rows[i]['rh']-rows[i-1]['rh']).length)*30/2 for i in range(1, len(rows))]
    im = max(range(len(sp)), key=lambda i: sp[i])
    print('  hands: fastest at frame %d (%.2f m/s); hand z per 5 frames:' % (rows[im+1]['f'], sp[im]), ' '.join('%d:%.2f/%.2f' % (r['f'], r['lh'].z, r['rh'].z) for r in rows[::5]))
    # feet forward position (y, forward = -y) per 5 frames: for walks, shows the stride
    print('  toes y per 4 frames:', ' '.join('%d:%.2f/%.2f' % (r['f'], r['lt'].y, r['rt'].y) for r in rows[::4]))
    print('  frame1 ankle L', tuple(round(x, 3) for x in rows[0]['la']), 'R', tuple(round(x, 3) for x in rows[0]['ra']), 'knee L', tuple(round(x, 3) for x in rows[0]['lk']), 'hips', tuple(round(x, 3) for x in rows[0]['hips']))
print('MEASURE OK')
