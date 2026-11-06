# blender -b --factory-startup -P ch_limb.py -- : limb radius profile along forearms and shins on the real mesh (bind pose), to size the cuffs
import bpy, os
from mathutils import Vector
Z = os.path.dirname(os.path.abspath(__file__))
bpy.ops.import_scene.fbx(filepath=Z + '/fbx_mesh/SK_Zombie.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
ARM = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); ME = [o for o in bpy.data.objects if o.type == 'MESH']
for bone in ('LeftForeArm', 'LeftLeg'):
    pb = ARM.pose.bones[bone]; h = ARM.matrix_world @ pb.head; t = ARM.matrix_world @ pb.tail; d = (t - h); L = d.length; d.normalize()
    print('BONE', bone, 'head', [round(x, 3) for x in h], 'len', round(L, 3))
    prof = {}
    for o in ME:
        idx = o.vertex_groups.get(bone).index if o.vertex_groups.get(bone) else None
        if idx is None: continue
        hand = o.vertex_groups.get('LeftHand' if 'Arm' in bone else 'LeftFoot'); hi = hand.index if hand else -1
        mw = o.matrix_world
        for v in o.data.vertices:
            w = sum(g.weight for g in v.groups if g.group in (idx, hi))
            if w < 0.3: continue
            p = mw @ v.co; s = (p - h).dot(d)
            r = ((p - h) - d * s); k = round(s / 0.03)
            prof.setdefault(k, []).append((r.length, r))
    for k in sorted(prof):
        rs = sorted(x[0] for x in prof[k]); n = len(rs)
        if n > 3: print(' at %.2f m: n %d  r50 %.3f r90 %.3f max %.3f' % (k * 0.03, n, rs[n // 2], rs[int(n * 0.9)], rs[-1]))
print('LIMB OK')
