# v2 zombie FBX export + the crawler's 2 clips (#199, TGA). blender -b zombie_<VARIANT>.blend -P anim_zombie.py
#   -> zombie_<VARIANT>_anim.blend, out/SK_ZombieV2_<VARIANT>.fbx
# Walkers use the existing SK_Zombie anims (same bone names, Compatible Skeletons), so only the Crawler gets clips:
#   A_ZombieV2_Crawl (32 f @ 30 fps, loop, in place: arms pull alternately, legs' stumps drag) and
#   A_ZombieV2_CrawlDeath (40 f, one-shot: head drops, arms slide out, body settles).
# Rotations are in armature space like the horse (faces -Y, its left is +X): pitch about X, + swings a hanging limb back
# and tips the body forward. Prone = Hips pitched +78; an arm's world pitch = 78 + its own (forward reach is about -70).
import bpy, math, os
from mathutils import Matrix, Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath))
VAR = os.environ.get('VARIANT', 'Crawler')
sc = bpy.context.scene; sc.render.fps = 30
arm = bpy.data.objects['SK_ZombieV2_Rig']; body = bpy.data.objects['SK_ZombieV2_' + VAR]
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
def R(ax, deg): return Matrix.Rotation(math.radians(deg), 3, ax)
def key(f, rot, loc=None):
    for pb in arm.pose.bones:
        B = pb.bone.matrix_local.to_3x3(); Rm = rot.get(pb.name, Matrix.Identity(3))
        pb.rotation_quaternion = (B.inverted() @ Rm @ B).to_quaternion(); pb.keyframe_insert('rotation_quaternion', frame=f)
        pb.location = B.inverted() @ Vector((loc or {}).get(pb.name, (0, 0, 0))); pb.keyframe_insert('location', frame=f)
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

def arm_pose(ph):
    """one arm through a pull. ph 0..1: 0-0.6 the planted hand pulls the body (upper arm world -70 -> 0, forearm flat
    forward), 0.6-1 it lifts and reaches forward again with the elbow folded high."""
    if ph < 0.6:
        t = smooth(ph / 0.6); up = lerp(-70, 0, t); el = lerp(-20, -90, t)
    else:
        t = (ph - 0.6) / 0.4; up = lerp(0, -70, smooth(t)); el = lerp(-90, -20, smooth(t)) - 50 * math.sin(math.pi * t)
    return up - 78, el

def crawl(f, n=32):
    ph = f / n; rot, loc = {}, {}
    surge = math.sin(2 * math.pi * ph * 2)                                     # two pulls per cycle
    rot['Hips'] = R('X', 78 + 2 * surge) @ R('Z', 6 * math.sin(2 * math.pi * ph))
    loc['Hips'] = (0, -0.02 * surge, -0.69 + 0.015 * abs(surge))
    rot['Spine2'] = R('X', -10); rot['Neck'] = R('X', -38 + 3 * surge); rot['Head'] = R('X', -22) @ R('Z', -8 * math.sin(2 * math.pi * ph))
    for side, off in (('Left', 0.0), ('Right', 0.5)):
        up, el = arm_pose((ph + off) % 1.0)
        rot[side + 'Arm'] = R('X', up); rot[side + 'ForeArm'] = R('X', el); rot[side + 'Hand'] = R('X', 20)
        rot[side + 'Shoulder'] = R('X', -8 * math.sin(2 * math.pi * ((ph + off) % 1.0)))
        rot[side + 'UpLeg'] = R('X', -8) @ R('Y', (6 if side == 'Left' else -6) * math.sin(2 * math.pi * ph))   # stumps drag
    return rot, loc

def death(f, n=40):
    rot, loc = crawl(0)
    t = smooth(f / 18); s = smooth((f - 10) / 30)
    rot['Neck'] = R('X', lerp(-38, 8, t)); rot['Head'] = R('X', lerp(-22, 18, t)) @ R('Z', lerp(0, 25, s))
    rot['Hips'] = R('X', 78) @ R('Y', lerp(0, 12, s)); loc['Hips'] = (0, 0, lerp(-0.69, -0.74, s))
    for side, k in (('Left', 1), ('Right', -1)):
        rot[side + 'Arm'] = R('X', lerp(-148, -120, t)) @ R('Y', k * lerp(0, -35, s)); rot[side + 'ForeArm'] = R('X', lerp(-20, -5, t))
        rot[side + 'Hand'] = R('X', lerp(20, 0, t))
    if f > 30: rot['Hips'] = R('X', 78 + 1.2 * math.sin((f - 30) * 1.2) * math.exp(-(f - 30) * 0.4)) @ R('Y', 12)   # last twitch
    return rot, loc

def action(name, n, fn):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    for f in range(n + 1): rot, loc = fn(f); key(f, rot, loc)
    act.use_fake_user = True; act.frame_range = (0, n); print('ACTION', name, n, flush=True); return act

if VAR == 'Crawler':
    acts = [action('A_ZombieV2_Crawl', 32, crawl), action('A_ZombieV2_CrawlDeath', 40, death)]
    arm.animation_data.action = acts[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'zombie_%s_anim.blend' % VAR))
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
arm.name = 'Armature'
for ob in sc.objects: ob.select_set(ob in (arm, body))
bpy.context.view_layer.objects.active = arm
os.makedirs(os.path.join(D, 'out'), exist_ok=True); fbx = os.path.join(D, 'out', 'SK_ZombieV2_%s.fbx' % VAR)
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=(VAR == 'Crawler'), bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                         primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
arm.name = 'SK_ZombieV2_Rig'
print('FBX OK', fbx, os.path.getsize(fbx), flush=True)
