# Realm wasp animations + FBX (#156, TGA). blender -b wasp_rig.blend -P anim_wasp.py  ->  wasp_anim.blend, out/SK_RealmWasp.fbx
# Clips at 30 fps, keyed on every frame (wingbeats are too fast for curve interpolation):
#   Hover (32, loop), Fly (32, loop), Dive (24, loop), Sting (24, one-shot), Death (40, one-shot, ends belly-up on the ground)
# Rotations are written in armature space (world axes, the wasp faces -Y, its left is +X) and converted to each bone's
# rest frame, so the numbers below read directly: pitch = about X, flap = about Y, sweep = about Z.
import bpy, math, os
from mathutils import Matrix, Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene; sc.render.fps = 30
arm = bpy.data.objects['SK_RealmWasp_Rig']; Z0 = 1.30
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
def R(ax, deg): return Matrix.Rotation(math.radians(deg), 3, ax)
def flap(sd, up): return R('Y', -up if sd == 'L' else up)              # wing/leg tip up
def sweep(sd, back): return R('Z', back if sd == 'L' else -back)       # tip toward the tail
def fold(sd, inward): return R('Y', inward if sd == 'L' else -inward)   # hanging segment swings under the body
def pitch(down): return R('X', down)                                    # nose down / tail up (+), tail curls under (-)
SIDES = ('L', 'R'); LEGS = ('F', 'M', 'H')

def key(f, rot, loc=None):
    for pb in arm.pose.bones:
        B = pb.bone.matrix_local.to_3x3(); Rm = rot.get(pb.name, Matrix.Identity(3))
        pb.rotation_quaternion = (B.inverted() @ Rm @ B).to_quaternion(); pb.keyframe_insert('rotation_quaternion', frame=f)
        pb.location = B.inverted() @ Vector((loc or {}).get(pb.name, (0, 0, 0))); pb.keyframe_insert('location', frame=f)

def wingbeat(f, up=50, down=-35, period=4, amp=1.0, swp=0.0):
    ph = (f % period) / period * 2 * math.pi; a = math.cos(ph); fe = math.sin(ph)   # cos: up at 0, down at half period
    ang = (up + down) / 2 + (up - down) / 2 * a
    r = {}
    for sd in SIDES:
        r[f'wing_fore_{sd}'] = sweep(sd, swp) @ flap(sd, ang * amp) @ R('X', 22 * fe * amp)        # feathering flips each stroke
        r[f'wing_hind_{sd}'] = sweep(sd, swp * 1.1) @ flap(sd, ang * amp * 0.9) @ R('X', 18 * fe * amp)
    return r

def legs(r, femur_back, tibia_fold, sway=0.0, f=0, n=32, femur_lift=0.0):
    for i, lg in enumerate(LEGS):
        for j, sd in enumerate(SIDES):
            s = sway * math.sin(2 * math.pi * f / n + i * 1.3 + j * 0.7)
            r[f'leg_{lg}_{sd}_1'] = pitch(femur_back + s) @ flap(sd, femur_lift)
            r[f'leg_{lg}_{sd}_2'] = fold(sd, tibia_fold + 0.6 * s)
            r[f'leg_{lg}_{sd}_3'] = fold(sd, tibia_fold * 0.4)
    return r

def head_bits(r, f, n, amt=1.0):
    for sd, sg in (('L', 1), ('R', -1)):
        r[f'antenna_{sd}'] = pitch(-6 * amt * math.sin(2 * math.pi * f / n * 2 + sg)) @ sweep(sd, 4 * amt * math.sin(2 * math.pi * f / n + sg))
        r[f'mandible_{sd}'] = R('Z', sg * 9 * amt * (0.5 + 0.5 * math.sin(2 * math.pi * f / n)))
    return r

def action(name, n, fn):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    for f in range(n + 1): rot, loc = fn(f); key(f, rot, loc)
    act.use_fake_user = True; act.frame_range = (0, n); print('ACTION', name, n, flush=True); return act

def hover(f, n=32):
    r = wingbeat(f); legs(r, 18, 10, 6, f, n); head_bits(r, f, n)
    r['thorax'] = pitch(-12 + 2 * math.sin(2 * math.pi * f / n))
    r['abdomen_01'] = pitch(-8 - 4 * math.sin(4 * math.pi * f / n)); r['abdomen_02'] = pitch(-5 - 3 * math.sin(4 * math.pi * f / n + 0.8))
    return r, {'root': (0, 0, 0.04 * math.sin(2 * math.pi * f / n))}
def fly(f, n=32):
    r = wingbeat(f, 60, -45); legs(r, 48, 34, 3, f, n); head_bits(r, f, n, 0.5)
    r['thorax'] = pitch(18 + 2 * math.sin(2 * math.pi * f / n)); r['abdomen_01'] = pitch(4); r['abdomen_02'] = pitch(3)
    r['head'] = pitch(-10)
    return r, {'root': (0, 0, 0.02 * math.sin(4 * math.pi * f / n))}
def dive(f, n=24):
    r = wingbeat(f, 18, -12, 4, 1.0, 38); legs(r, -38, -6, 2, f, n); head_bits(r, f, n, 0.3)
    r['thorax'] = pitch(50); r['head'] = pitch(-22)
    r['abdomen_01'] = pitch(-30); r['abdomen_02'] = pitch(-28); r['stinger'] = pitch(-18)
    return r, {}
def sting(f, n=24):
    r, loc = hover(f % 32)
    def env(keys):          # piecewise-smooth key curve: [(frame, value)]
        for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
            if f0 <= f <= f1: t = (f - f0) / max(f1 - f0, 1); t = t * t * (3 - 2 * t); return v0 + (v1 - v0) * t
        return keys[-1][1]
    a1 = env([(0, -8), (6, 12), (11, -50), (13, -62), (18, -38), (24, -8)])
    a2 = env([(0, -5), (6, 8), (11, -40), (13, -48), (18, -28), (24, -5)])
    sg = env([(0, 0), (6, 6), (11, -22), (13, -28), (18, -10), (24, 0)])
    th = env([(0, -12), (6, -18), (12, -26), (18, -16), (24, -12)])
    lunge = env([(0, 0), (6, 0.06), (12, -0.28), (16, -0.22), (24, 0)])
    r['abdomen_01'] = pitch(a1); r['abdomen_02'] = pitch(a2); r['stinger'] = pitch(sg); r['thorax'] = pitch(th)
    loc = {'root': (0, lunge, loc['root'][2])}
    return r, loc
def death(f, n=40):
    t = f / n
    def ease(a, b, f0, f1, p=2.0): u = min(max((f - f0) / (f1 - f0), 0), 1); return a + (b - a) * u ** p
    beat = 1 - ease(0, 1, 0, 14, 1.0)
    r = wingbeat(f, 50 * beat - 10 * (1 - beat), -35 * beat - 10 * (1 - beat), 4 + int(6 * (1 - beat)), 1.0, ease(0, 70, 8, 22, 1.5))
    legs(r, ease(18, -35, 0, 26, 1.0), ease(10, 85, 0, 26, 1.0), 10 * beat, f, n, ease(0, 20, 6, 26, 1.0))
    head_bits(r, f, 8, beat)
    r['thorax'] = R('Y', ease(0, 168, 4, 30, 1.6)) @ pitch(ease(-12, 4, 0, 30, 1.0))
    r['abdomen_01'] = pitch(ease(-8, -38, 0, 20, 1.0)); r['abdomen_02'] = pitch(ease(-5, -30, 0, 20, 1.0))
    drop = -ease(0, 1.05, 2, 26, 2.2)
    if f > 26: drop = -1.05 + 0.05 * math.sin(math.pi * min((f - 26) / 8, 1)) * (1 if f < 34 else 0)
    return r, {'root': (0, 0, drop)}

acts = [action('A_RealmWasp_Hover', 32, hover), action('A_RealmWasp_Fly', 32, fly), action('A_RealmWasp_Dive', 24, dive),
        action('A_RealmWasp_Sting', 24, sting), action('A_RealmWasp_Death', 40, death)]
arm.animation_data.action = acts[0]
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
# material slots named for UE
for on, mn in (('SK_RealmWasp', 'M_RealmWasp_Body'), ('SK_RealmWasp_Wings', 'M_RealmWasp_Wings')):
    o = bpy.data.objects[on]; o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get(mn) or bpy.data.materials.new(mn))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'wasp_anim.blend'))
# FBX for UE: the armature object is named 'Armature' so UE adds no extra root bone
arm.name = 'Armature'
for o in sc.objects: o.select_set(o.name in ('Armature', 'SK_RealmWasp', 'SK_RealmWasp_Wings'))
bpy.context.view_layer.objects.active = arm
fbx = os.path.join(D, 'out', 'SK_RealmWasp.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                         primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
arm.name = 'SK_RealmWasp_Rig'
print('FBX OK', fbx, os.path.getsize(fbx), flush=True)
