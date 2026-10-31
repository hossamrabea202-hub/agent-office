# Export the 5 siege meshes as FBX (one file each, pivot = object origin): blender -b siege.blend -P export_siege.py
import bpy, os
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.path.join(D, 'out'); os.makedirs(OUT, exist_ok=True)
for n in ('SM_Siege_Ram', 'SM_Siege_RamWreck', 'SM_Siege_Tower', 'SM_Siege_TowerBridge', 'SM_Siege_TowerWreck'):
    bpy.ops.object.select_all(action='DESELECT'); o = bpy.data.objects[n]; o.select_set(True); bpy.context.view_layer.objects.active = o
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get('M_Siege') or bpy.data.materials.new('M_Siege'))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, n + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
    print('EXPORTED', n, flush=True)
