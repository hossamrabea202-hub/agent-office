# Export the #543 meshes (TGA PC): one FBX per SM_*, same settings as the #309 kit (tools/tga/mine/export_mine.py), so UE
# needs the kit's import_uniform_scale = 100 too and the FBX mirrors Blender +Y to UE -Y.
#   blender -b work/mine543.blend -P export543.py      env OUT (default <WORK>/out/fbx)
import bpy, os
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.environ.get('OUT') or os.path.join(D, 'out', 'fbx'); os.makedirs(OUT, exist_ok=True)
n = 0
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('SM_')]:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, colors_type='LINEAR', apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
    n += 1
print('EXPORTED', n, flush=True)
