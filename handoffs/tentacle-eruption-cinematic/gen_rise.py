# #545 RISE clips (adjustedfilm, 2026-11-06). blender -b --factory-startup -P gen_rise.py -- <rig clip .fbx> <out .fbx> RISE|RISE_FAST
# Spec: "driver + damped followers", coiled, uncoils with overshoot, a 2-3 frame snap at the top, a hold, a slow settle. Bones only; the actor's height comes from BP_TentacleEruption, curve in the README.
# Method: a driver pose per bone is keyed by hand; each bone follows it through its own spring, softer towards the tip, so the motion travels up the arm and overshoots by itself.
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]; SRC, OUT, WHICH = a[0], a[1], a[2].upper()
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True); arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FAST = WHICH == 'RISE_FAST'; K = 0.62 if FAST else 1.0; SEC = 4.2 if FAST else 6.5; FPS = 24; N = int(round(SEC * FPS)); SUB = 10; dt = 1.0 / (FPS * SUB)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth); nb = len(bones); ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
gauss = lambda x, c, w: math.exp(-((x - c) / w) ** 2)
def driver(t, i, s):
    t = t / K
    coil = 1.0 - ease((t - 0.15) / 1.25)                                                   # starts wound tight, unwinds as it clears the dust
    x = coil * (-9.0 * gauss(s, 0.2, 0.25) + 19.0 * gauss(s, 0.58, 0.2) - 32.0 * gauss(s, 0.92, 0.16)); y = -34.0 * coil * s; z = 10.0 * coil * math.sin(i * 0.7) * s
    if 1.45 <= t:                                                                          # the snap: 2-3 frames, whole upper arm cracks forward to its full height, then holds still
        sn = ease((t - 1.45) / (2.6 / 24.0)) * (1.0 - ease((t - 1.95) / 0.6)); x += -13.0 * sn * s ** 1.3; z += 5.0 * sn * s
    return x, y, z
state = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in bones]                                    # x, vx, y, vy, z, vz
for i, st in enumerate(state):
    d0 = driver(0.0, i, i / (nb - 1)); st[0], st[2], st[4] = d0
act = bpy.data.actions.new('Tentacle' + WHICH); arm.animation_data_create(); arm.animation_data.action = act; worst = 0.0; prev = None
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS; s_end = 1.0 - ease((t - (SEC - 0.8)) / 0.8); cur = []
    for i, b in enumerate(bones):
        s = i / (nb - 1); st = state[i]
        for _ in range(SUB):
            tt = t + _ * dt; tg = driver(tt, i, s); w = 2 * math.pi * (3.2 - 2.0 * s) / K; zeta = 0.34 - 0.14 * s         # base stiff and calm, tip loose and ringing
            for j in (0, 2, 4):
                st[j + 1] += (w * w * (tg[j // 2] - st[j]) - 2 * zeta * w * st[j + 1]) * dt; st[j] += st[j + 1] * dt
        sh = 0.9 * max(0.0, 1.0 - abs(t / K - 2.0) / 0.7) * math.sin(2 * math.pi * 11.0 * t + 0.9 * i) * (0.3 + 0.7 * s)     # a strain tremor in the hold
        x, y, z = (st[0] + sh) * s_end, st[2] * s_end, (st[4] + 0.6 * sh) * s_end; cur.append((x, y, z))
        b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z)); b.keyframe_insert('rotation_euler', frame=f + 1)
    if prev: worst = max(worst, max(max(abs(c[j] - p[j]) for j in range(3)) for c, p in zip(cur, prev)))
    prev = cur
for fc in act.fcurves:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
print('RISE %s frames %d (%.1f s) | worst %.1f deg/frame | start tip curl %.0f deg, last frame %.2f deg' % (WHICH, N + 1, SEC, worst, abs(state[-1][0]), max(abs(v) for v in cur[-1])))
