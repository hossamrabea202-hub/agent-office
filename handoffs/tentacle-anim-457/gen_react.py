# #450 tentacle HIT REACTION (i5, 2026-11-03). Owner: "very subtle and boring. not really breath taking or surprise".
# Today a hit only plays BPC_TentacleSpit's 0.8 s uniform squash/stretch of the root. A creature reacts with its whole body:
#   0.00-0.15 s  FLINCH   the arm bends away from the blow; the shock travels up the arm (20 ms per bone), the tip lags and whips
#   0.15-0.80 s  CURL     the outer half rolls in hard (pain), twisting a little
#   0.00-1.00 s  SHUDDER  11 Hz tremor, decays (muscle spasm)
#   0.80-1.80 s  REAR + LASH  it straightens, rears back, then lashes forward (anger), the wave runs to the tip
#   1.80-3.00 s  RECOVER  eases out to the rest pose (starts and ends at rest so the game can blend it in / out)
#   blender -b --factory-startup -P gen_react.py -- <src rig .fbx> <out .fbx> [amp=1.0]
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
AMP = float(argv[2]) if len(argv) > 2 else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FPS, SEC = 24, 3.0
N = int(FPS * SEC)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth); nb = len(bones)
ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
def bump(t, a, b):                                   # smooth 0 -> 1 -> 0 over [a, b]
    if t <= a or t >= b: return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2
act = bpy.data.actions.new('TentacleHitReact450'); arm.animation_data_create(); arm.animation_data.action = act
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS
    for i, b in enumerate(bones):
        s = i / (nb - 1)
        tl = t - 0.020 * i                               # the shock reaches bone i 20 ms later
        flinch = -14.0 * bump(tl, 0.0, 0.55) * (0.4 + 0.6 * s)               # bend away from the blow
        whip = 18.0 * bump(tl, 0.10, 0.45) * max(0.0, s - 0.5) * 2.0          # the tip lags, then whips through
        curl = 16.0 * bump(t, 0.15, 1.10) * max(0.0, (s - 0.4) / 0.6) ** 1.4  # outer half rolls in
        shud = 3.0 * math.exp(-t / 0.35) * math.sin(2 * math.pi * 11.0 * t + i * 0.9) * (0.3 + 0.7 * s)
        rear = -9.0 * bump(tl, 0.80, 1.45) * (0.5 + 0.5 * s)                 # rears back...
        lash = 14.0 * bump(tl - 0.03 * i, 1.25, 1.95) * s                    # ...then lashes forward, wave to the tip
        x = (flinch + whip + curl + rear + lash + shud) * AMP
        z = (6.0 * bump(tl, 0.0, 0.6) * s + 0.6 * shud) * AMP                # a sideways jolt
        y = 10.0 * bump(t, 0.2, 1.2) * s * AMP                               # twist in pain
        k = 1.0 - ease((t - 2.4) / 0.6) * 0.0                                # (shapes already decay to rest by 3 s)
        b.rotation_euler = (math.radians(x * k), math.radians(y * k), math.radians(z * k))
        b.keyframe_insert('rotation_euler', frame=f + 1)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in bpy.data.objects:
    if o.type == 'MESH': o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
print('REACT', OUT, 'frames', N + 1)
