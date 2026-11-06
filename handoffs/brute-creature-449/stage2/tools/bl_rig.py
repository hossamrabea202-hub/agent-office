# bl_rig.py - Blender helpers for authoring Flesh Brute clips on the real rig (adjustedfilm, #449 stage 2).
# The rig comes from UE's own FBX export of SK_FleshBrute (armature object 'Monster_001', scale 0.01, bones in cm).
import bpy, math
from mathutils import Vector, Quaternion, Matrix, Euler

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def load_rig(sk_fbx, keep_mesh=True):
    reset()
    bpy.ops.import_scene.fbx(filepath=sk_fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    if not keep_mesh:
        for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    return arm

def _fcurves(act):
    try: return list(act.fcurves)
    except Exception: return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]

def apply_anim_fbx(arm, anim_fbx):
    """import a UE anim FBX and put its action on arm (object-level transform keys stripped)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=anim_fbx, automatic_bone_orientation=False, ignore_leaf_bones=False)
    new = [o for o in bpy.data.objects if o not in before]
    src = [o for o in new if o.type == 'ARMATURE'][0]; act = src.animation_data.action
    for fc in _fcurves(act):
        if fc.data_path in ('location', 'rotation_euler', 'rotation_quaternion', 'scale'):
            try: act.fcurves.remove(fc)
            except Exception: pass
    arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and getattr(src.animation_data, 'action_slot', None):
        arm.animation_data.action_slot = src.animation_data.action_slot
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    fr = act.frame_range; bpy.context.scene.frame_start, bpy.context.scene.frame_end = int(fr[0]), int(fr[1])
    return act

def export_anim(arm, path, frame_start=None, frame_end=None):
    """export armature + action as FBX for UE import onto SK_FleshBrute_Skeleton (no mesh)."""
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
