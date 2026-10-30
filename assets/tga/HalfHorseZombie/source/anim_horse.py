# Half-horse zombie body animations + FBX (#155, TGA). blender -b horse_rig.blend -P anim_horse.py
#   -> horse_anim.blend, out/SK_HorseBody.fbx
# Clips at 30 fps, keyed every frame: Gallop (18, loop, transverse gallop), Walk (36, loop, 4-beat), Idle (60, loop),
# Rear (36, one-shot knock-down attack, impact frame 22), Death (45, one-shot, falls on its right side, wound up).
# Rotations are in armature space (faces -Y, its left is +X): pitch about X (+ swings a hanging limb back, + tips the
# nose down), roll about Y. The TorsoSocket rides the neck stump, so the attached zombie torso follows every move.
import bpy, math, os
from mathutils import Matrix, Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene; sc.render.fps = 30
arm = bpy.data.objects['SK_HorseBody_Rig']
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
def R(ax, deg): return Matrix.Rotation(math.radians(deg), 3, ax)
pitch = lambda d: R('X', d)
SEG = {'front': ('upperarm', 'forearm', 'cannon_f', 'pastern_f'), 'hind': ('thigh', 'gaskin', 'cannon_h', 'pastern_h')}
def key(f, rot, loc=None):
    for pb in arm.pose.bones:
        B = pb.bone.matrix_local.to_3x3(); Rm = rot.get(pb.name, Matrix.Identity(3))
        pb.rotation_quaternion = (B.inverted() @ Rm @ B).to_quaternion(); pb.keyframe_insert('rotation_quaternion', frame=f)
        pb.location = B.inverted() @ Vector((loc or {}).get(pb.name, (0, 0, 0))); pb.keyframe_insert('location', frame=f)
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def env(f, keys):
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= f <= f1: return v0 + (v1 - v0) * smooth((f - f0) / max(f1 - f0, 1))
    return keys[-1][1] if f > keys[-1][0] else keys[0][1]

def leg(r, kind, sd, ph, stance, A, lift):
    """one leg through a stride. ph 0..1; stance: hoof planted, the leg sweeps forward -> back; swing: it folds and
    comes forward. A = sweep half-angle, lift = joint flex at mid-swing."""
    s = SEG[kind]
    if ph < stance: a = -A + 2 * A * (ph / stance); flex = 0.0
    else:
        u = (ph - stance) / (1 - stance); a = A - 2 * A * smooth(u); flex = math.sin(math.pi * u)
    if kind == 'front':
        r[f'{s[0]}_{sd}'] = pitch(a); r[f'{s[1]}_{sd}'] = pitch(-0.25 * lift * flex)
        r[f'{s[2]}_{sd}'] = pitch(1.25 * lift * flex); r[f'{s[3]}_{sd}'] = pitch(0.6 * lift * flex - 6 * (ph < stance))
    else:
        r[f'{s[0]}_{sd}'] = pitch(a - 0.25 * lift * flex); r[f'{s[1]}_{sd}'] = pitch(0.55 * lift * flex)
        r[f'{s[2]}_{sd}'] = pitch(-0.9 * lift * flex); r[f'{s[3]}_{sd}'] = pitch(0.7 * lift * flex - 6 * (ph < stance))

def tail(r, f, n, amp, lift=0.0):
    for k, b in enumerate(('tail_01', 'tail_02', 'tail_03')):
        r[b] = R('Z', amp * (k + 1) * 0.6 * math.sin(2 * math.pi * f / n - k * 0.8)) @ pitch(-lift * (1 - 0.3 * k))

def gallop(f, n=18):
    r = {}; ph = f / n
    for kind, sd, off in (('hind', 'L', 0.0), ('hind', 'R', 0.1), ('front', 'L', 0.42), ('front', 'R', 0.52)):
        leg(r, kind, sd, (ph + off) % 1.0, 0.36, 30 if kind == 'hind' else 32, 70 if kind == 'front' else 60)
    bounce = math.sin(2 * math.pi * (ph - 0.15))
    r['pelvis'] = pitch(5 * bounce); r['spine_02'] = pitch(-4 * bounce); r['neck_stump'] = pitch(-5 * bounce)
    tail(r, f, n, 8, 25)
    return r, {'root': (0, 0, 0.07 * math.sin(4 * math.pi * ph) + 0.02)}
def walk(f, n=36):
    r = {}; ph = f / n
    for kind, sd, off in (('hind', 'L', 0.0), ('front', 'L', 0.25), ('hind', 'R', 0.5), ('front', 'R', 0.75)):
        leg(r, kind, sd, (ph + off) % 1.0, 0.64, 17, 45)
    r['pelvis'] = R('Y', 2.5 * math.sin(2 * math.pi * ph)); r['spine_02'] = R('Y', -2 * math.sin(2 * math.pi * ph))
    r['neck_stump'] = pitch(3 * math.sin(4 * math.pi * ph)); tail(r, f, n, 6)
    return r, {'root': (0, 0, 0.018 * math.cos(4 * math.pi * ph))}
def idle(f, n=60):
    r = {}; br = math.sin(2 * math.pi * f / n * 2)
    r['spine_01'] = pitch(0.8 * br); r['neck_stump'] = pitch(-2 * br) @ R('Z', 3 * math.sin(2 * math.pi * f / n))
    stamp = env(f, [(28, 0), (33, 1), (37, 0)])                       # paws the ground once, impatient
    r['upperarm_R'] = pitch(-14 * stamp); r['forearm_R'] = pitch(-8 * stamp); r['cannon_f_R'] = pitch(55 * stamp); r['pastern_f_R'] = pitch(20 * stamp)
    r['cannon_h_L'] = pitch(-6 * env(f, [(0, 0), (8, 1), (50, 1), (60, 0)])); r['pastern_h_L'] = pitch(14 * env(f, [(0, 0), (8, 1), (50, 1), (60, 0)]))   # resting hind hoof
    tail(r, f, n, 10)
    return r, {'root': (0, 0, -0.006 * br)}
def rear(f, n=36):
    r = {}
    up = env(f, [(0, 0), (12, 1), (19, 1), (22, -0.12), (28, 0.05), (36, 0)])
    paw = math.sin(2 * math.pi * f / 6) * env(f, [(8, 0), (12, 1), (18, 1), (20, 0)])
    r['pelvis'] = pitch(-36 * up)
    for sd in 'LR':                                                    # hind legs stay planted: counter the body pitch
        r[f'thigh_{sd}'] = pitch(36 * up - 10 * up); r[f'gaskin_{sd}'] = pitch(18 * up); r[f'cannon_h_{sd}'] = pitch(-16 * up); r[f'pastern_h_{sd}'] = pitch(8 * up)
        g = 1 if sd == 'L' else -1
        r[f'upperarm_{sd}'] = pitch(-45 * max(up, 0) + 12 * paw * g); r[f'forearm_{sd}'] = pitch(-20 * max(up, 0))
        r[f'cannon_f_{sd}'] = pitch(85 * max(up, 0) - 30 * paw * g); r[f'pastern_f_{sd}'] = pitch(30 * max(up, 0))
    r['neck_stump'] = pitch(10 * up); tail(r, f, 12, 6, 30 * max(up, 0))
    return r, {'root': (0, 0.10 * max(up, 0), -0.08 * max(up, 0))}
def death(f, n=45):
    r = {}
    buck = env(f, [(0, 0), (10, 1)]); fall = env(f, [(8, 0), (26, 1)]); stiff = env(f, [(26, 0), (40, 1)])
    for sd in 'LR':
        r[f'upperarm_{sd}'] = pitch(-10 * buck + 30 * stiff); r[f'forearm_{sd}'] = pitch(-15 * buck * (1 - stiff))
        r[f'cannon_f_{sd}'] = pitch(85 * buck * (1 - stiff) + 5 * stiff); r[f'pastern_f_{sd}'] = pitch(30 * buck * (1 - stiff))
        r[f'thigh_{sd}'] = pitch(-12 * fall - 20 * stiff); r[f'gaskin_{sd}'] = pitch(30 * fall * (1 - stiff)); r[f'cannon_h_{sd}'] = pitch(-30 * fall * (1 - stiff))
    r['root'] = R('Y', -86 * fall)                                     # tips over its right hooves; the rib wound faces up
    r['pelvis'] = pitch(-6 * buck); r['neck_stump'] = pitch(-25 * fall) @ R('Y', 10 * stiff)
    tail(r, f, 10, 8 * (1 - fall))
    settle = 0.04 * math.sin(math.pi * min(max((f - 26) / 6, 0), 1))
    return r, {'root': (0, 0, -0.18 * buck * (1 - fall) + 0.24 * fall + settle)}

def action(name, n, fn):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    for f in range(n + 1): rot, loc = fn(f); key(f, rot, loc)
    act.use_fake_user = True; act.frame_range = (0, n); print('ACTION', name, n, flush=True); return act
acts = [action('A_HorseBody_Gallop', 18, gallop), action('A_HorseBody_Walk', 36, walk), action('A_HorseBody_Idle', 60, idle),
        action('A_HorseBody_Rear', 36, rear), action('A_HorseBody_Death', 45, death)]
arm.animation_data.action = acts[2]
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
o = bpy.data.objects['SK_HorseBody']; o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get('M_HorseBody') or bpy.data.materials.new('M_HorseBody'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'horse_anim.blend'))
arm.name = 'Armature'
for ob in sc.objects: ob.select_set(ob.name in ('Armature', 'SK_HorseBody'))
bpy.context.view_layer.objects.active = arm
fbx = os.path.join(D, 'out', 'SK_HorseBody.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                         primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
arm.name = 'SK_HorseBody_Rig'
print('FBX OK', fbx, os.path.getsize(fbx), flush=True)
