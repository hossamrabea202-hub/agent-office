# Export the stair kit (#279, TGA): one FBX per flight with its UCX_ ramp, pivot at the first riser's bottom-left corner.
#   blender -b stairs.blend -P export_stairs.py      env OUT (default <blend dir>/out/fbx)
import bpy, os
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.environ.get('OUT') or os.path.join(D, 'out', 'fbx'); os.makedirs(OUT, exist_ok=True)
n = 0
for o in [o for o in bpy.data.objects if o.name.startswith('SM_Stair_')]:
    ucx = bpy.data.objects['UCX_' + o.name]; keep = o.location.copy(); o.location = (0, 0, 0)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); ucx.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
    o.location = keep; n += 1
print('EXPORTED', n, flush=True)
