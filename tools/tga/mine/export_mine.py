# Export the mine kit (#309, TGA): one FBX per mesh (vertex colour Col kept), pivot = object origin.
#   blender -b mine.blend -P export_mine.py      env OUT (default <blend dir>/out/fbx)
import bpy, os
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.environ.get('OUT') or os.path.join(D, 'out', 'fbx'); os.makedirs(OUT, exist_ok=True)
n = 0
for o in [o for o in bpy.data.objects if o.name.startswith('SM_Mine_')]:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='LINEAR', apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
    n += 1
print('EXPORTED', n, flush=True)
