# Tentacle death clip (adjustedfilm, 2026-11-06). blender -b --factory-startup -P gen_death.py -- <rig clip .fbx> <out .fbx>
# 6.0 s, same length as AS_Tentacle_CannonC, which it replaces in place. Three convulsions, a rigid tremor, the arm goes slack and topples under its own weight, the tip whips into the ground, last twitches, holds.
# Method as RISE: a driver pose per bone, each bone follows through its own spring, so the fall starts at the base and the tip arrives late and overshoots.
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]; SRC, OUT = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True); arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FPS = 24; SEC = 6.0; N = int(SEC * FPS); SUB = 10; dt = 1.0 / (FPS * SUB); sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth); nb = len(bones); ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u); gauss = lambda x, c, w: math.exp(-((x - c) / w) ** 2)
def bump(t, a_, b_): return 0.0 if t <= a_ or t >= b_ else math.sin(math.pi * (t - a_) / (b_ - a_)) ** 2
def driver(t, i, s):
    x = y = z = 0.0
    for k, (a_, b_, amp) in enumerate(((0.0, 0.55, 20.0), (0.55, 1.05, 27.0), (1.05, 1.6, 34.0))):       # convulsions that grow
        sg = 1.0 if k % 2 == 0 else -1.0; x += sg * amp * bump(t, a_, b_) * (0.25 + 0.75 * s); z += -sg * 0.55 * amp * bump(t, a_ + 0.06, b_ + 0.06) * s; y += sg * 14.0 * bump(t, a_, b_) * s
    rigid = ease((t - 1.5) / 0.2) * (1 - ease((t - 2.35) / 0.12)); x += -9.0 * rigid * s                  # goes rigid, rears: the last breath
    fall = ease((t - 2.4) / 1.55); x += 21.0 * fall * (0.42 + 0.58 * s) * (1.0 + 0.5 * math.sin(math.pi * s)); z += 6.0 * fall * s; y += 8.0 * fall * s
    return x, y, z
state = [[0.0] * 6 for _ in bones]; act = bpy.data.actions.new('TentacleDeathFall'); arm.animation_data_create(); arm.animation_data.action = act; prev = None; worst = 0.0
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS; cur = []
    for i, b in enumerate(bones):
        s = i / (nb - 1); st = state[i]
        for k_ in range(SUB):
            tg = driver(t + k_ * dt, i, s); w = 2 * math.pi * (3.4 - 2.3 * s); zeta = 0.36 - 0.16 * s
            for j in (0, 2, 4): st[j + 1] += (w * w * (tg[j // 2] - st[j]) - 2 * zeta * w * st[j + 1]) * dt; st[j] += st[j + 1] * dt
        tr = 2.6 * ease((t - 1.5) / 0.25) * (1 - ease((t - 2.35) / 0.15)) * math.sin(2 * math.pi * 11.0 * t + 0.9 * i) * (0.4 + 0.6 * s)        # rigid tremor
        tw = 1.5 * math.exp(-max(0.0, t - 4.3) / 0.5) * (t > 4.3) * math.sin(2 * math.pi * 6.0 * t + 0.7 * i) * s ** 1.5                       # dying twitches after the tip lands
        x, y, z = st[0] + tr + tw, st[2], st[4] + 0.5 * tr; cur.append((x, y, z)); b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z)); b.keyframe_insert('rotation_euler', frame=f + 1)
    if prev: worst = max(worst, max(max(abs(c[j] - p[j]) for j in range(3)) for c, p in zip(cur, prev)))
    prev = cur
for fc in act.fcurves:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
sc.frame_set(N + 1); tip = arm.matrix_world @ arm.pose.bones['seg_13'].head; print('DEATH frames %d | worst %.1f deg/frame | tip ends at z %.0f rig m' % (N + 1, worst, tip.z))
