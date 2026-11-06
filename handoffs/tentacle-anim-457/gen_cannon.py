# #450 tentacle CANNON reactions (i5, 2026-11-06). Owner: the tentacle reaction is "very subtle and boring"; bar = Stranger Things.
# Today a cannonball only spawns a plasma burst and takes HP: the 76 m arm does not move. These are whole-arm performances:
#   A  HEAD HIT   (hit at seg_11): the head snaps away in 2 frames, the shock runs down the arm, the tip whips; the arm rears
#                 back (anticipation), then THRASHES forward and sideways twice with a twist; a 9 Hz tremor decays; 4.0 s.
#   B  BODY HIT   (hit at seg_06): the arm buckles at the hit (a kink), the top folds over the kink and whips; rears, thrashes; 4.0 s.
#   C  DEATH      three convulsions with twist, growing; a rigid tremor; then the arm folds over and collapses; holds; 6.0 s.
# Same conventions as gen_react.py (the clip that works in the game): the UE-exported rig FBX, 24 fps, rotation_euler per
# bone: X = the main bend, Y = twist, Z = sideways. Starts at rest; A and B end at rest (blend back to the idle), C holds.
#   blender -b --factory-startup -P gen_cannon.py -- <src rig .fbx> <out .fbx> <A|B|C> [amp=1.0]
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, WHICH = argv[0], argv[1], argv[2].upper()
AMP = float(argv[3]) if len(argv) > 3 else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
FPS = 24; SEC = 6.0 if WHICH == 'C' else 4.0; N = int(FPS * SEC)
sc = bpy.context.scene; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, N + 1
def depth(b):
    d = 0
    while b.parent: b = b.parent; d += 1
    return d
bones = sorted(arm.pose.bones, key=depth); nb = len(bones)
ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
def bump(t, a, b, p=2.0):                            # smooth 0 -> 1 -> 0 over [a, b]
    if t <= a or t >= b: return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** p
def snap(t, a, rise=0.08, fall=0.35):                # fast in, exponential out
    if t <= a: return 0.0
    u = t - a
    return ease(u / rise) if u < rise else math.exp(-(u - rise) / fall)
def gauss(i, h, w): return math.exp(-((i - h) / w) ** 2)
H = {'A': 11, 'B': 6, 'C': 8}[WHICH]
act = bpy.data.actions.new('TentacleCannon' + WHICH); arm.animation_data_create(); arm.animation_data.action = act
for b in bones: b.rotation_mode = 'XYZ'
for f in range(N + 1):
    t = f / FPS
    for i, b in enumerate(bones):
        s = i / (nb - 1); up = max(0.0, (i - H) / max(1, nb - 1 - H))      # 0 at the hit, 1 at the tip
        tl = t - 0.025 * abs(i - H)                                        # the shock spreads from the hit, 25 ms per bone
        x = y = z = 0.0
        if WHICH in 'AB':
            # IMPACT: the hit bones kick sideways and bend back, hard
            kick = gauss(i, H, 2.2) * snap(tl, 0.0, 0.06, 0.30)
            z += -40.0 * kick; x += -26.0 * kick                                  # (the impact is kept sharp: 1.6x of the broad phases)
            if WHICH == 'A' and i >= 11: x += -44.0 * snap(t, 0.0, 0.06, 0.25)          # the head snaps away
            if WHICH == 'B': x += 46.0 * gauss(i, 6.5, 1.6) * bump(t, 0.04, 0.90, 1.5)    # the body buckles: a kink at the hit
            # WHIP: the part above the hit folds over, then whips through
            x += 24.0 * bump(t - 0.03 * (i - H), 0.10, 0.70) * up ** 1.3
            # REAR back (anticipation) then THRASH forward with a wave to the tip, with a twist
            x += -14.0 * bump(tl, 0.60, 1.40) * (0.35 + 0.65 * s)
            x += 30.0 * bump(tl - 0.02 * i, 1.25, 2.00) * (0.25 + 0.75 * s)
            y += 16.0 * bump(t, 1.20, 2.20) * s
            # second thrash: sideways, the other way, wave to the tip
            z += 24.0 * bump(tl - 0.02 * i, 1.95, 2.75) * (0.2 + 0.8 * s)
            x += -10.0 * bump(tl, 2.30, 3.10) * s
            # tremor: a 9 Hz spasm from the first thrash, decaying
            tr = 4.5 * math.exp(-max(0.0, t - 1.2) / 0.55) * (1.0 if t > 1.2 else 0.0) * math.sin(2 * math.pi * 9.0 * t + i * 0.8) * (0.3 + 0.7 * s)
            x += tr; z += 0.5 * tr
            # the last shiver during the recovery
            x += 2.0 * bump(t, 3.0, 3.8) * math.sin(2 * math.pi * 6.0 * t + i * 0.5) * s
            k = 1.0 - ease((t - 3.55) / 0.45)                                   # everything to rest by 4.0 s
            x *= k; y *= k; z *= k
        else:
            # DEATH: the killing hit, then three convulsions that grow, a rigid tremor, the collapse
            kick = gauss(i, H, 2.5) * snap(tl, 0.0, 0.06, 0.30); z += -30.0 * kick; x += -20.0 * kick
            x += 22.0 * bump(t - 0.03 * (i - H), 0.10, 0.70) * up ** 1.3
            for n_, (a0, a1, amp) in enumerate(((0.9, 1.6, 26.0), (1.6, 2.3, 34.0), (2.3, 3.1, 42.0))):
                sgn = 1.0 if n_ % 2 == 0 else -1.0
                x += sgn * amp * bump(tl - 0.02 * i, a0, a1) * (0.25 + 0.75 * s)
                z += -sgn * 0.6 * amp * bump(tl - 0.03 * i, a0 + 0.15, a1 + 0.15) * s
                y += sgn * 18.0 * bump(t, a0, a1) * s
            tr = 6.0 * (ease((t - 2.9) / 0.3) if t > 2.9 else 0.0) * math.exp(-max(0.0, t - 3.4) / 0.9) * math.sin(2 * math.pi * 11.0 * t + i * 0.9) * (0.4 + 0.6 * s)
            x += tr; z += 0.4 * tr
            # the collapse: the arm folds forward from the base up, the tip comes down, and it stays there
            fold = ease((t - 3.4) / 1.9)
            x += 13.0 * fold * (0.55 + 0.45 * s) * (1.0 + 0.6 * math.sin(math.pi * s))
            z += 5.0 * fold * s
        b.rotation_euler = (math.radians(x * AMP), math.radians(y * AMP), math.radians(z * AMP))
        b.keyframe_insert('rotation_euler', frame=f + 1)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
for o in bpy.data.objects:
    if o.type == 'MESH': o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                         bake_anim_simplify_factor=0.0, add_leaf_bones=False, armature_nodetype='NULL')
# checks: worst per-frame bone turn, tip travel
sc.frame_set(1); mw = arm.matrix_world; prev = None; worst = (0, 0); tip0 = mw @ arm.pose.bones['seg_13'].head; far = 0.0
for f in range(1, N + 2):
    sc.frame_set(f); cur = [b.matrix_basis.to_quaternion() for b in bones]
    if prev: worst = max(worst, (max(math.degrees(min(q.rotation_difference(p).angle, 2 * math.pi - q.rotation_difference(p).angle)) for q, p in zip(cur, prev)), f))
    prev = cur; far = max(far, (mw @ arm.pose.bones['seg_13'].head - tip0).length)
print('CANNON %s %s frames %d | worst bone turn %.1f deg/frame @%d | tip travels up to %.1f m from rest' % (WHICH, OUT, N + 1, worst[0], worst[1], far))
