import bpy, sys, math
f = sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=f, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene; act = arm.animation_data.action
print('TENT arm', arm.name, 'scale', tuple(round(x, 3) for x in arm.scale), 'fps', sc.render.fps, 'range', act.frame_range[:], 'objects', [(o.name, o.type) for o in bpy.data.objects][:6])
bones = [b for b in arm.pose.bones]; print('TENT bones', [b.name for b in bones])
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); mw = arm.matrix_world
tips = []; mids = []
for fr in range(f0, f1 + 1, 12):
    sc.frame_set(fr); tips.append(mw @ arm.pose.bones['seg_13'].head); mids.append(mw @ arm.pose.bones['seg_07'].head)
import mathutils
c = sum(tips, mathutils.Vector()) / len(tips); r = max((t - c).length for t in tips); cm = sum(mids, mathutils.Vector()) / len(mids); rm = max((t - cm).length for t in mids)
print('TENT idle tip centre %s radius %.2f m; mid radius %.2f m; tip height %.1f m' % (tuple(round(x, 2) for x in c), r, rm, c.z))
sc.frame_set(f0)
for b in ('seg_00', 'seg_06', 'seg_12'):
    pb = arm.pose.bones[b]; m = mw @ pb.matrix
    print('TENT %s local axes in world: X %s Y %s Z %s len %.2f' % (b, tuple(round(v, 2) for v in m.col[0][:3]), tuple(round(v, 2) for v in m.col[1][:3]), tuple(round(v, 2) for v in m.col[2][:3]), pb.length * arm.scale.x))
# per-bone euler at a mid frame to see the idle's bend magnitudes
sc.frame_set(f0 + 240)
print('TENT idle eulers @f240:', [(b.name, tuple(round(math.degrees(a), 1) for a in b.matrix_basis.to_euler('XYZ'))) for b in bones[1:14:3]])
