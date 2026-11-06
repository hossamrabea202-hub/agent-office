# zrig.py - Blender helpers for authoring zombie / colossus clips on the real SK_Zombie rig (adjustedfilm, #449 follow-up).
# UE's FBX export makes the root bone 'Hips' the ARMATURE OBJECT; Spine, the legs and the cloth chains hang parentless
# under it. In a CLIP export the armature is parentless, scale 0.01, location in METRES, bones in cm; the pelvis
# animation is the object's own location/rotation_euler (never strip it). In the MESH export the same armature sits
# under an empty 'SK_Zombie' (scale 0.01) with its location in cm. So: author on a clip armature, attach the mesh for
# previews only (zrender.py).
import bpy, math
from mathutils import Vector, Quaternion, Matrix

# the bind pose of the hips object (from SK_Zombie.fbx): A-pose, legs straight, feet on the ground
BIND_LOC = Vector((0.0, -0.009031, 1.167377)); BIND_ROT = (math.pi/2, 0.0, 0.0)

def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)

def _fcurves(act):
    try: return list(act.fcurves)
    except Exception: return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]

def load_rig(clip_fbx, rest=True):
    """import a UE CLIP fbx and use its armature as the authoring rig. rest=True clears its animation and puts the
    hips object at the bind transform (A-pose standing on the ground)."""
    reset()
    bpy.ops.import_scene.fbx(filepath=clip_fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    if rest:
        if arm.animation_data: arm.animation_data_clear()
        arm.rotation_mode = 'XYZ'; arm.location = BIND_LOC.copy(); arm.rotation_euler = BIND_ROT; arm.scale = (0.01, 0.01, 0.01)
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
        bpy.context.view_layer.update()
    return arm

def apply_anim_fbx(arm, anim_fbx):
    """import another UE clip and put its action (object + bone curves) on arm (same armature layout)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=anim_fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
    new = [o for o in bpy.data.objects if o not in before]
    src = [o for o in new if o.type == 'ARMATURE'][0]; act = src.animation_data.action
    arm.rotation_mode = src.rotation_mode; arm.location = src.location.copy(); arm.scale = src.scale.copy(); arm.rotation_euler = src.rotation_euler.copy()
    arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and getattr(src.animation_data, 'action_slot', None):
        arm.animation_data.action_slot = src.animation_data.action_slot
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    fr = act.frame_range; bpy.context.scene.frame_start, bpy.context.scene.frame_end = int(fr[0]), int(fr[1])
    return act

def key(arm, frame):
    """key every bone and the hips object."""
    arm.keyframe_insert('location', frame=frame); arm.keyframe_insert('rotation_euler', frame=frame)
    for pb in arm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=frame); pb.keyframe_insert('location', frame=frame)

def export_anim(arm, path, frame_start=None, frame_end=None):
    """export the armature (+ its object animation = Hips) + action as FBX for UE import onto SK_Zombie_Skeleton."""
    sc = bpy.context.scene
    if frame_start is not None: sc.frame_start = frame_start
    if frame_end is not None: sc.frame_end = frame_end
    for o in bpy.data.objects: o.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE'}, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
                             bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0, primary_bone_axis='Y', secondary_bone_axis='X',
                             apply_unit_scale=True, global_scale=1.0, axis_forward='-Z', axis_up='Y', armature_nodetype='NULL')
