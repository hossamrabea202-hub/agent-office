import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrig
f = sys.argv[sys.argv.index('--')+1]; frames = [int(x) for x in sys.argv[sys.argv.index('--')+2].split(',')]
arm = zrig.load_rig(f, rest=False); sc = bpy.context.scene
for fr in frames:
    sc.frame_set(fr); h = arm.matrix_world.translation
    out = []
    for b in ('LeftHand', 'RightHand', 'LeftArm', 'RightArm', 'Head'):
        p = arm.matrix_world @ arm.pose.bones[b].head - h; out.append('%s(%+.2f %+.2f %+.2f)' % (b[:5], p.x, p.y, p.z))
    print('HANDS f%d hips z %.2f |' % (fr, h.z), ' '.join(out), '| x=left, -y=forward, rel. to hips')
