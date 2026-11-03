# #457 (i5): what does the tentacle clip do? Per-bone rotation range, main period, and the phase lag base -> tip.
#   blender -b --factory-startup -P analyze.py -- <clip.fbx>
import bpy, sys, math
import numpy as np
f = sys.argv[sys.argv.index('--') + 1]
bpy.ops.import_scene.fbx(filepath=f, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = arm.animation_data.action
fr0, fr1 = [int(x) for x in act.frame_range]
sc = bpy.context.scene; fps = sc.render.fps
bones = [b for b in arm.pose.bones]
def chain(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones.sort(key=chain)
print('bones', len(bones), 'frames', fr0, fr1, 'fps', fps, 'mesh tris', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'))
step = max(1, (fr1 - fr0) // 400)
frames = list(range(fr0, fr1 + 1, step))
data = {b.name: [] for b in bones}
for fr in frames:
    sc.frame_set(fr)
    for b in bones:
        q = b.matrix_basis.to_quaternion()
        e = q.to_euler()
        data[b.name].append((math.degrees(e.x), math.degrees(e.y), math.degrees(e.z)))
for i, b in enumerate(bones):
    a = np.array(data[b.name])
    rng = a.max(0) - a.min(0)
    ax = int(np.argmax(rng)); sig = a[:, ax] - a[:, ax].mean()
    sp = np.abs(np.fft.rfft(sig)); k = int(np.argmax(sp[1:]) + 1)
    per = (frames[-1] - frames[0]) / fps / k
    ph = math.degrees(np.angle(np.fft.rfft(sig)[k]))
    if i % max(1, len(bones) // 14) == 0 or i == len(bones) - 1:
        print('%-26s depth %2d range xyz %5.1f %5.1f %5.1f  main axis %s period %.2fs phase %6.1f' % (b.name, chain(b), *rng, 'xyz'[ax], per, ph))
# smoothness: max frame-to-frame jump at the tip (pops) and seamless loop check
tip = np.array(data[bones[-1].name]); d = np.abs(np.diff(tip, axis=0)).max(0)
print('tip max step per sample (deg)', d.round(2), ' loop seam (first-last, deg)', np.abs(tip[0] - tip[-1]).round(2))
