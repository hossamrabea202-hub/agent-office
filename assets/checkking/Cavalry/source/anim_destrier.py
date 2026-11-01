# #402 Destrier animations + FBX. checkking (Claude), 2026-11-01. Leg cycle code from TGA's #155 anim_horse.py, extended
# with neck / head / ear motion, a trot, and the 'lance' socket bone (upright when walking, couched in the gallop).
#   blender -b <work>/destrier_tack.blend -P anim_destrier.py -- <work>   -> destrier_anim.blend, out/SK_Destrier.fbx (+ anims),
#                                                                         out/SK_Destrier_Tack.fbx (same skeleton, no anims)
# Clips at 30 fps, in place (CharacterMovement moves the actor): Idle 90 (loop), Walk 36 (loop, 4-beat), Trot 20 (loop,
# 2-beat diagonal), Gallop 18 (loop, transverse; lance couched), Rear 36 (one-shot, forehooves strike on frame 22),
# Death 45 (one-shot, falls on its right side). Rotations in armature space: faces -Y, its left is +X; pitch about X
# (+ swings a hanging limb back, + tips the nose down), roll about Y, yaw about Z (+ turns -Y toward +X).
import bpy, math, os, sys
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(bpy.data.filepath))
os.makedirs(os.path.join(D, 'out'), exist_ok=True)
sc = bpy.context.scene; sc.render.fps = 30
arm = bpy.data.objects['SK_Destrier_Rig']
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
def neckhead(r, n1, n2, hd, yaw=0.0):
    r['neck_01'] = pitch(n1) @ R('Z', yaw * 0.5); r['neck_02'] = pitch(n2) @ R('Z', yaw * 0.5); r['head'] = pitch(hd)
def ears(r, l, rr):                       # + = pinned back, - = pricked forward
    r['ear_L'] = pitch(-l); r['ear_R'] = pitch(-rr)
LANCE_UP = R('X', -84) @ R('Z', 4)          # resting upright on the right thigh
LANCE_COUCHED = R('Z', 11) @ R('X', 3)      # couched: forward, across the neck to the left, a little down

def idle(f, n=90):
    r = {}; br = math.sin(2 * math.pi * f / n * 3)
    r['spine_01'] = pitch(0.8 * br)
    look = env(f, [(0, 0), (20, 0), (34, 1), (58, 1), (72, 0), (90, 0)])
    neckhead(r, -2 * br, -1.5 * br - 4 * look, 3 * look, yaw=10 * look)
    stamp = env(f, [(44, 0), (49, 1), (53, 0)])
    r['upperarm_R'] = pitch(-14 * stamp); r['forearm_R'] = pitch(-8 * stamp); r['cannon_f_R'] = pitch(55 * stamp); r['pastern_f_R'] = pitch(20 * stamp)
    rest = env(f, [(0, 0), (10, 1), (80, 1), (90, 0)])
    r['cannon_h_L'] = pitch(-6 * rest); r['pastern_h_L'] = pitch(14 * rest)
    ears(r, -10 * look + 18 * env(f, [(60, 0), (64, 1), (70, 0)]), 6 * math.sin(2 * math.pi * f / 45))
    tail(r, f, n / 2, 10); r['lance'] = LANCE_UP
    return r, {'root': (0, 0, -0.006 * br)}
def walk(f, n=36):
    r = {}; ph = f / n
    for kind, sd, off in (('hind', 'L', 0.0), ('front', 'L', 0.25), ('hind', 'R', 0.5), ('front', 'R', 0.75)):
        leg(r, kind, sd, (ph + off) % 1.0, 0.64, 17, 45)
    r['pelvis'] = R('Y', 2.5 * math.sin(2 * math.pi * ph)); r['spine_02'] = R('Y', -2 * math.sin(2 * math.pi * ph))
    nod = math.sin(4 * math.pi * ph + 0.6)                          # the head nods twice per stride in the walk
    neckhead(r, 3 * nod, 2 * nod, 2 * nod); ears(r, -6, -6 + 8 * max(0, math.sin(2 * math.pi * ph)))
    tail(r, f, n, 6); r['lance'] = LANCE_UP @ R('X', 2 * nod)
    return r, {'root': (0, 0, 0.018 * math.cos(4 * math.pi * ph))}
def trot(f, n=20):
    r = {}; ph = f / n
    for kind, sd, off in (('hind', 'L', 0.0), ('front', 'R', 0.0), ('hind', 'R', 0.5), ('front', 'L', 0.5)):
        leg(r, kind, sd, (ph + off) % 1.0, 0.45, 22, 62)
    b = math.cos(4 * math.pi * ph)                                   # two suspensions per stride
    r['pelvis'] = pitch(1.5 * b); neckhead(r, 2 * b, 1.5 * b, 1 * b); ears(r, -4, -4)
    tail(r, f, n, 5, 10); r['lance'] = LANCE_UP @ R('X', 3 * b)
    return r, {'root': (0, 0, 0.045 * max(0.0, b) - 0.01)}
def gallop(f, n=18):
    r = {}; ph = f / n
    for kind, sd, off in (('hind', 'L', 0.0), ('hind', 'R', 0.1), ('front', 'L', 0.42), ('front', 'R', 0.52)):
        leg(r, kind, sd, (ph + off) % 1.0, 0.36, 30 if kind == 'hind' else 32, 70 if kind == 'front' else 60)
    bounce = math.sin(2 * math.pi * (ph - 0.15))
    r['pelvis'] = pitch(5 * bounce); r['spine_02'] = pitch(-4 * bounce)
    neckhead(r, -7 * bounce - 6, -4 * bounce - 4, 4 * bounce + 6)    # neck stretched forward, pumping with the stride
    ears(r, 20, 20)                                                   # ears pinned back at the charge
    tail(r, f, n, 8, 28); r['lance'] = LANCE_COUCHED @ R('X', 1.5 * bounce)
    return r, {'root': (0, 0, 0.07 * math.sin(4 * math.pi * ph) + 0.02)}
def rear(f, n=36):
    r = {}
    up = env(f, [(0, 0), (12, 1), (19, 1), (22, -0.12), (28, 0.05), (36, 0)])
    paw = math.sin(2 * math.pi * f / 6) * env(f, [(8, 0), (12, 1), (18, 1), (20, 0)])
    r['pelvis'] = pitch(-36 * up)
    for sd in 'LR':
        r[f'thigh_{sd}'] = pitch(26 * up); r[f'gaskin_{sd}'] = pitch(18 * up); r[f'cannon_h_{sd}'] = pitch(-16 * up); r[f'pastern_h_{sd}'] = pitch(8 * up)
        g = 1 if sd == 'L' else -1
        r[f'upperarm_{sd}'] = pitch(-45 * max(up, 0) + 12 * paw * g); r[f'forearm_{sd}'] = pitch(-20 * max(up, 0))
        r[f'cannon_f_{sd}'] = pitch(85 * max(up, 0) - 30 * paw * g); r[f'pastern_f_{sd}'] = pitch(30 * max(up, 0))
    neckhead(r, 14 * up, 8 * up, -6 * up); ears(r, 25 * max(up, 0), 25 * max(up, 0))
    tail(r, f, 12, 6, 30 * max(up, 0)); r['lance'] = LANCE_UP
    return r, {'root': (0, 0.10 * max(up, 0), -0.08 * max(up, 0))}
def death(f, n=45):
    r = {}
    buck = env(f, [(0, 0), (10, 1)]); fall = env(f, [(8, 0), (26, 1)]); stiff = env(f, [(26, 0), (40, 1)])
    for sd in 'LR':
        r[f'upperarm_{sd}'] = pitch(-10 * buck + 30 * stiff); r[f'forearm_{sd}'] = pitch(-15 * buck * (1 - stiff))
        r[f'cannon_f_{sd}'] = pitch(85 * buck * (1 - stiff) + 5 * stiff); r[f'pastern_f_{sd}'] = pitch(30 * buck * (1 - stiff))
        r[f'thigh_{sd}'] = pitch(-12 * fall - 20 * stiff); r[f'gaskin_{sd}'] = pitch(30 * fall * (1 - stiff)); r[f'cannon_h_{sd}'] = pitch(-30 * fall * (1 - stiff))
    r['root'] = R('Y', -86 * fall)
    r['pelvis'] = pitch(-6 * buck); neckhead(r, -25 * fall, -10 * fall, 15 * fall)
    ears(r, 20 * fall, 20 * fall); tail(r, f, 10, 8 * (1 - fall)); r['lance'] = LANCE_UP
    settle = 0.04 * math.sin(math.pi * min(max((f - 26) / 6, 0), 1))
    return r, {'root': (0, 0, -0.18 * buck * (1 - fall) + 0.24 * fall + settle)}

def action(name, n, fn):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and act.slots: arm.animation_data.action_slot = act.slots[0]
    for f in range(n + 1): rot, loc = fn(f); key(f, rot, loc)
    act.use_fake_user = True; act.frame_range = (0, n); print('ACTION', name, n, flush=True); return act
acts = [action('A_Destrier_Idle', 90, idle), action('A_Destrier_Walk', 36, walk), action('A_Destrier_Trot', 20, trot),
        action('A_Destrier_Gallop', 18, gallop), action('A_Destrier_Rear', 36, rear), action('A_Destrier_Death', 45, death)]
arm.animation_data.action = acts[0]
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
body = bpy.data.objects['SK_Destrier']; body.data.materials.clear()
body.data.materials.append(bpy.data.materials.get('M_DestrierCoat') or bpy.data.materials.new('M_DestrierCoat'))
tack = bpy.data.objects['SK_Destrier_Tack']; tack.data.materials.clear()
tack.data.materials.append(bpy.data.materials.get('M_DestrierTack') or bpy.data.materials.new('M_DestrierTack'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'destrier_anim.blend'))
arm.name = 'Armature'
def export(objs, fbx, anim):
    for ob in sc.objects: ob.select_set(ob.name in objs)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=anim, bake_anim_use_all_actions=anim, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                             primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
    print('FBX OK', fbx, os.path.getsize(fbx), flush=True)
export({'Armature', 'SK_Destrier', 'SK_Destrier_Hair'}, os.path.join(D, 'out', 'SK_Destrier.fbx'), True)
export({'Armature', 'SK_Destrier_Tack'}, os.path.join(D, 'out', 'SK_Destrier_Tack.fbx'), False)
arm.name = 'SK_Destrier_Rig'
