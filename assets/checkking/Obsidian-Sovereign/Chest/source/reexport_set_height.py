# Move the chest into the Codex set frame (its bottom at Z 0.970, like the Codex chest) and re-export the FBX.
import os, bpy, mathutils
D = r'C:\Users\hossam.rabea\checkking-work\chest'
ob = bpy.data.objects['SM_ObsidianSovereign_Chest']
ob.data.transform(mathutils.Matrix.Translation((0, 0, 0.970))); ob.data.update()
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=os.path.join(D, 'SM_ObsidianSovereign_Chest.fbx'), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE',
                         use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'chest_final_setframe.blend'))
zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
print('CHEST Z', round(min(zs), 3), round(max(zs), 3))
