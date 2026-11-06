# #530 tentacle style pass (i5, 2026-11-06). Bar: Netflix Stranger Things. Conventions of ../tentacle-anim-457/gen_cannon.py:
# the UE-exported rig FBX (clip export, no mesh), 24 fps, rotation_euler per bone: X = main bend, Y = twist, Z = sideways.
#   blender -b --factory-startup -P gen_style.py -- <src rig .fbx> <out .fbx> STRIKE|HUNT_A|HUNT_B|HUNT_C|WOUNDED [amp=1.0]
# STRIKE (7.6 s, starts and ends at rest) is timed to BPC_TentacleStrike: hit on frame 96 (4.0 s).
#   0.0-3.2 s  the arm gathers into a cobra S-coil while the head keeps searching; 3.2-3.79 s coil tightens, 14 Hz quiver
#   3.79-4.0 s the strike: 5 frames, base leads, the tip arrives last
#   4.0 s      contact: the head buckles, a shock runs DOWN the arm; the mid-arm mass keeps going (follow-through)
#   4.3-7.6 s  the head drags out late, a damped wave, a last shiver, rest
# HUNT_x (40 s seamless loops): head-led pose-to-pose search with holds, startle twitches right before a look,
#   an asymmetric breath pulse climbing the arm, a small organic residue. Variants differ in posture, looks, breath and twitches.
# WOUNDED (20 s seamless loop): sagging posture, laboured breath, tremor bursts on the hurt side.
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, WHICH = argv[0], argv[1], argv[2].upper()
AMP = float(argv[3]) if len(argv) > 3 else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FPS = 24; SEC = {'STRIKE': 7.6, 'WOUNDED': 20.0}.get(WHICH, 40.0); N = int(round(FPS * SEC))
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth); nb = len(bones)
TAU = 2 * math.pi
ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
def bump(t, a, b, p=2.0):
    if t <= a or t >= b: return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** p
def gauss(x, c, w): return math.exp(-((x - c) / w) ** 2)
def snap(u, rise=0.08, fall=0.3):
    if u <= 0: return 0.0
    return ease(u / rise) if u < rise else math.exp(-(u - rise) / fall)
def wrapd(t, c):                     # signed loop distance t - c, in [-SEC/2, SEC/2)
    return (t - c + SEC / 2) % SEC - SEC / 2

# ---------- STRIKE ----------
T_HIT = 4.0; T_REL = T_HIT - 5.0 / FPS
def strike(t, i, s):
    # the coil: base leans back, the middle folds forward, the head recoils (S shape), wound with a twist
    C = ease((t - 0.3) / 2.9) + 0.18 * ease((t - 3.2) / 0.55)
    shape = -8.0 * gauss(s, 0.18, 0.25) + 15.0 * gauss(s, 0.60, 0.17) - 24.0 * gauss(s, 0.92, 0.15)
    rel = ease((t - (T_REL + 0.009 * i)) / 0.085)            # release, base leads: the tip lets go last
    x = C * shape * (1 - rel); y = -16.0 * C * s * (1 - rel); z = 0.0
    # the head searches while it gathers, then locks on and goes still before the release
    look = (1 - ease((t - 2.9) / 0.5)) * ease(t / 0.6)
    z += 4.0 * look * math.sin(TAU * 0.42 * t - 0.25 * i) * s ** 1.5
    x += 2.2 * look * math.sin(TAU * 0.31 * t + 0.9 - 0.2 * i) * s ** 1.5
    # the tension: a quiver that grows until the release
    q = ease((t - 3.2) / 0.5) * (1 - rel)
    x += 1.5 * q * math.sin(TAU * 14.0 * t + 0.8 * i) * (0.4 + 0.6 * s); z += 1.0 * q * math.sin(TAU * 11.0 * t + 1.1 * i) * s
    # the strike pose: everything forward, the twist unwinds through. It holds, then the head drags out LAST
    out = 1.0 - ease((t - (4.35 + 0.075 * i)) / 2.1)
    P = rel * out
    x += 24.0 * P * (0.35 + 0.65 * s); y += 12.0 * P * s
    if t >= T_HIT:
        u = t - T_HIT
        # contact: the head buckles against the hit, the shock runs down the arm at 30 ms per bone
        x += -20.0 * gauss(i, 12.0, 2.0) * snap(u, 0.05, 0.22)
        sh = u - 0.030 * (nb - 1 - i)
        x += 7.0 * snap(sh, 0.05, 0.16) * (0.3 + 0.7 * s); z += -4.5 * snap(sh, 0.05, 0.20) * math.sin(i * 1.3)
        # follow-through: the middle of the arm is heavy and keeps going, drifting sideways with the unwinding twist
        ft = bump(t, T_HIT, 5.0, 1.5)
        x += 9.0 * ft * gauss(s, 0.5, 0.32); z += 7.0 * bump(t, T_HIT + 0.05, 5.4, 1.5) * s; y += 10.0 * ft * s
        # a damped wave climbing the arm, and a last shiver
        d = t - 4.7
        if d > 0:
            a = 6.5 * math.exp(-d / 0.85) * ease(d / 0.25) * math.sin(TAU * 0.95 * d - 0.42 * i) * (0.2 + 0.8 * s)
            x += a; z += 0.55 * math.exp(-d / 1.1) * 6.5 * ease(d / 0.3) * math.sin(TAU * 0.8 * d - 0.42 * i + 1.3) * s
        x += 1.1 * bump(t, 5.9, 6.9) * math.sin(TAU * 6.0 * t + 0.6 * i) * s
    k = 1.0 - ease((t - 7.1) / 0.5)
    return x * k, y * k, z * k

# ---------- HUNT ----------
# looks: (start of the move, move seconds, yaw, pitch), each held until the next; head-led
HUNT = {
 'A': dict(bias=0.0, breath=7, br=1.5, tw=[(6.2, 8.0, 1), (17.8, 6.0, -1), (31.4, 10.0, 1)], fl=13,
           looks=[(1.0, 2.6, 5.5, 0.5), (7.0, 1.3, -5.0, 2.5), (13.5, 3.4, -1.5, -2.5), (18.6, 1.1, 6.5, 3.0), (25.0, 3.0, 2.0, -1.0), (32.2, 1.2, -6.0, 1.5)]),
 'B': dict(bias=2.0, breath=6, br=1.9, tw=[(10.6, 7.0, -1), (22.1, 9.0, 1), (35.3, 5.5, -1)], fl=17,   # lurks low, curled forward, slower breath
           looks=[(3.0, 3.2, -4.0, 2.5), (11.4, 1.5, 4.5, 3.5), (17.0, 3.6, 6.0, 0.0), (22.9, 1.0, -3.0, 4.0), (29.0, 2.8, -6.0, 0.5), (36.1, 1.4, 1.0, 3.0)]),
 'C': dict(bias=-1.8, breath=8, br=1.2, tw=[(4.1, 10.0, 1), (12.9, 6.5, 1), (20.3, 5.0, -1), (33.7, 8.5, -1)], fl=19,  # tall and alert, quicker breath, jumpy
           looks=[(4.9, 1.0, -6.5, -1.0), (9.0, 2.2, -2.0, -3.0), (13.7, 0.9, 5.5, -0.5), (21.1, 1.2, 1.0, 2.0), (26.5, 3.0, 6.5, -2.5), (34.5, 1.1, -3.5, -1.5)]),
}
def look_at(t, looks):
    # cyclic pose-to-pose: move eased over its own duration, hold until the next one
    n = len(looks); tt = t % SEC; idx = n - 1
    for j, l in enumerate(looks):
        if tt >= l[0]: idx = j
    if tt < looks[0][0]: tt += SEC
    st, mv, yaw, pit = looks[idx]; py, pp = looks[idx - 1][2], looks[idx - 1][3]
    u = ease((tt - st) / mv)
    return py + (yaw - py) * u, pp + (pit - pp) * u
def hunt(t, i, s, H):
    env = 0.10 + 0.90 * s ** 1.25
    yaw, pit = look_at(t - 0.11 * (nb - 1 - i), H['looks'])                 # the head turns first, the body follows
    x = (pit + H['bias']) * env; z = yaw * env; y = 1.5 * yaw * s ** 2
    # breath: inhale quick, exhale slow, climbing the arm
    ph = (t * H['breath'] / SEC - 0.035 * i) % 1.0
    b = ease(ph / 0.36) if ph < 0.36 else (1.0 - ease((ph - 0.42) / 0.5) if ph >= 0.42 else 1.0)
    x += H['br'] * b * (gauss(s, 0.5, 0.3) - 0.55 * gauss(s, 0.95, 0.18)); z += 0.25 * H['br'] * b * math.sin(i * 0.7)
    # twitch: tip-first startle, 2 frames in, travels down the arm at 22 ms per bone
    for c, a, sg in H['tw']:
        u = wrapd(t, c) - 0.022 * (nb - 1 - i)
        k = snap(u, 0.07, 0.24) * s ** 2.2
        x += -a * k * 0.8; z += sg * a * k
        if u > 0: x += 1.2 * math.exp(-u / 0.55) * math.sin(TAU * 8.0 * u + i) * s ** 2
    # residue, whole cycles only: never quite still, never a clean sine
    w = lambda c, p: math.sin(TAU * c * t / SEC + p - 0.5 * i)
    x += (0.55 * w(5, 0.4) + 0.3 * w(H['fl'], 2.0) * s) * env; z += (0.5 * w(4, 1.9) + 0.28 * w(H['fl'] + 4, 4.0) * s) * env
    return x, y, z

# ---------- WOUNDED (20 s loop, 4 laboured breaths, 3 tremor bursts) ----------
def wounded(t, i, s):
    env = 0.15 + 0.85 * s ** 1.2
    x = 5.5 * gauss(s, 0.62, 0.3) - 2.0 * gauss(s, 0.25, 0.2); z = -2.0 * env; y = -4.0 * s    # the sag, favouring one side
    ph = (t * 4 / SEC - 0.05 * i) % 1.0
    b = ease(ph / 0.28) if ph < 0.28 else (1.0 - ease((ph - 0.4) / 0.55) if ph >= 0.4 else 1.0)
    x += -2.6 * b * gauss(s, 0.55, 0.32); z += 0.7 * b * math.sin(i * 0.6)                     # each breath lifts it, then it sinks
    for c, a in ((3.4, 2.4), (10.9, 3.4), (15.6, 2.0)):
        u = wrapd(t, c)
        e = ease((u + 0.15) / 0.25) * math.exp(-max(0.0, u) / 0.7) if u > -0.15 else 0.0
        x += a * e * math.sin(TAU * 10.0 * t + 0.9 * i) * (0.3 + 0.7 * s); z += 0.7 * a * e * math.sin(TAU * 8.0 * t + 1.2 * i) * s
    w = lambda c, p: math.sin(TAU * c * t / SEC + p - 0.45 * i)
    x += 0.8 * w(1, 0.7) * env; z += 1.0 * w(2, 2.2) * env
    return x, y, z

act = bpy.data.actions.new('Tentacle' + WHICH); arm.animation_data_create(); arm.animation_data.action = act
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS
    for i, b in enumerate(bones):
        s = i / (nb - 1)
        if WHICH == 'STRIKE': x, y, z = strike(t, i, s)
        elif WHICH == 'WOUNDED': x, y, z = wounded(t, i, s)
        else: x, y, z = hunt(t, i, s, HUNT[WHICH[-1]])
        b.rotation_euler = (math.radians(x * AMP), math.radians(y * AMP), math.radians(z * AMP))
        b.keyframe_insert('rotation_euler', frame=f + 1)
for fc in act.fcurves:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
# checks: worst turn overall and outside the strike window, tip travel, loop seam
sc.frame_set(1); mw = arm.matrix_world; tip0 = (mw @ arm.pose.bones['seg_13'].head).copy(); prev = None; worst = (0, 0); calm = (0, 0); far = 0.0
first = [b.matrix_basis.to_quaternion() for b in bones]
ang = lambda a, b: math.degrees(min(a.rotation_difference(b).angle, TAU - a.rotation_difference(b).angle))
for f in range(1, N + 2):
    sc.frame_set(f); cur = [b.matrix_basis.to_quaternion() for b in bones]
    if prev:
        m = max(ang(q, p) for q, p in zip(cur, prev)); worst = max(worst, (m, f))
        if not (WHICH == 'STRIKE' and 90 <= f <= 104): calm = max(calm, (m, f))
    prev = cur; far = max(far, (mw @ arm.pose.bones['seg_13'].head - tip0).length)
seam = max(ang(q, p) for q, p in zip(cur, first))
print('STYLE %s frames %d (%.2f s) | worst %.1f deg/frame @%d | outside the strike %.1f @%d | tip travels up to %.1f m | first-to-last frame %.3f deg' % (WHICH, N + 1, N / FPS, worst[0], worst[1], calm[0], calm[1], far, seam))
