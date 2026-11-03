# #457 (i5, 2026-11-03): polished idle for SK_CorruptedTentacle_01 (14-bone chain seg_00..seg_13).
# The old clips: base 4 bones frozen (hinge at seg_04), ONE 20 s sine of 3-6 deg per bone, no secondary motion.
# This writes a layered, loop-seamless 40 s clip on all 14 bones (octopus-arm reference: bends travel base -> tip,
# the tip is the most active part, slow reaches and curls with ease, never a pure sine):
#   1 primary sway       2 cycles / 40 s, two bend axes in quadrature (an ellipse, not a pendulum)
#   2 travelling wave    5-7 cycles / 40 s, phase lag per bone (the wave runs up the arm)
#   3 tip flick          13-17 cycles / 40 s, only the last 5 bones, small
#   4 curls              2 eased curl events / 40 s, the outer half rolls inward and unrolls
#   5 twist              slow roll along the length, small
# Amplitude envelope grows base -> tip (seg_00 0.15x, tip 1x), so the root stays planted but not dead.
# Every frequency is a whole number of cycles in 40 s, so frame 0 == frame 960 (seamless loop, checked).
#   blender -b --factory-startup -P gen_anim.py -- <src rig .fbx> <out .fbx> <seed> [amp=1.0]
import bpy, sys, math, random
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, SEED = argv[0], argv[1], int(argv[2])
AMP = float(argv[3]) if len(argv) > 3 else 1.0
rnd = random.Random(SEED)
bpy.ops.wm.read_factory_settings(use_empty=True)          # no default Cube / camera / light in the export
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FPS, SEC = 24, 40.0
N = int(FPS * SEC)                       # 960 -> frames 1..961, last == first
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth)
nb = len(bones)
TAU = 2 * math.pi
ph = lambda: rnd.uniform(0, TAU)
P = dict(sway=(2, ph(), ph()), wave=(rnd.choice([5, 6, 7]), ph()), wave2=(rnd.choice([3, 4]), ph()),
         flick=(rnd.choice([13, 15, 17]), ph()), twist=(1, ph()))
curls = sorted(rnd.uniform(0, SEC) for _ in range(2))
CURL_LEN = 5.5                                                   # seconds per curl (ease in, hold, ease out)
def curl_amt(t):
    a = 0.0
    for c in curls:
        for cc in (c - SEC, c, c + SEC):                         # wrap so the loop stays seamless
            u = (t - cc) / CURL_LEN
            if 0 <= u <= 1: a = max(a, math.sin(math.pi * u) ** 2)   # smooth 0 -> 1 -> 0
    return a
# sanity: curl must be 0 at both loop ends or equal there
act = bpy.data.actions.new('Polish457_%d' % SEED); arm.animation_data_create(); arm.animation_data.action = act
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS
    w = lambda cyc, p, lag=0.0: math.sin(TAU * cyc * t / SEC + p - lag)
    ca = curl_amt(t)
    for i, b in enumerate(bones):
        s = i / (nb - 1)                                         # 0 base .. 1 tip
        env = (0.15 + 0.85 * s ** 1.3) * AMP
        lag = 0.55 * i                                           # rad per bone: the wave climbs the arm
        x = 3.2 * w(P['sway'][0], P['sway'][1], 0.18 * i) + 2.4 * w(P['wave'][0], P['wave'][1], lag) + 1.2 * w(P['wave2'][0], P['wave2'][1], 0.8 * lag)
        z = 3.0 * w(P['sway'][0], P['sway'][2] + 1.3, 0.18 * i) + 2.0 * w(P['wave'][0], P['wave'][1] + 1.7, lag)
        if s > 0.6:                                              # tip flick, fades in over the last 40 %
            k = (s - 0.6) / 0.4
            x += 2.2 * k * w(P['flick'][0], P['flick'][1], 0.9 * i)
            z += 1.6 * k * w(P['flick'][0], P['flick'][1] + 2.1, 0.9 * i)
        x, z = x * env, z * env
        if s > 0.45: x += 9.0 * ca * ((s - 0.45) / 0.55) ** 1.5 * AMP   # curl: the outer half rolls inward
        y = 4.0 * s * w(P['twist'][0], P['twist'][1]) * AMP     # slow twist
        b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
        b.keyframe_insert('rotation_euler', frame=f + 1)
for fc in act.fcurves:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in bpy.data.objects:
    if o.type == 'MESH': o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
print('ANIM', OUT, 'seed', SEED, 'P', {k: v[0] for k, v in P.items()}, 'curls at', [round(c, 1) for c in curls])
