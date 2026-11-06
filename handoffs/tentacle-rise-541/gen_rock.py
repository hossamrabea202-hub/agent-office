# #541 a thrown rock for the eruption: blender -b --factory-startup -P gen_rock.py -- <out.fbx>. 1 m nominal; vertex colour albedo/roughness and UV0 as the spore base, so it shares M_TentacleSporeBase.
import bpy, sys, math, numpy as np, bmesh
OUT = sys.argv[sys.argv.index('--') + 1]; rng = np.random.default_rng(41)
bpy.ops.wm.read_factory_settings(use_empty=True); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=50.0)
for _ in range(9):
    n = rng.normal(size=3); n /= np.linalg.norm(n); d = 20 + rng.random() * 22
    for v in bm.verts:
        o = v.co.x * n[0] + v.co.y * n[1] + v.co.z * n[2] - d
        if o > 0: v.co.x -= o * n[0]; v.co.y -= o * n[1]; v.co.z -= o * n[2]
me = bpy.data.meshes.new('SM_EruptRock'); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new('SM_EruptRock', me); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
c = np.array([0.135, 0.115, 0.095]) * (1 + 0.5 * np.sin(P[:, 2] * 0.3 + 2 * np.sin(P[:, 0] * 0.09)))[:, None]; col = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); col.data.foreach_set('color', np.column_stack([c, np.full(len(c), 0.88)]).astype(np.float32).ravel())
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv); uv = me.uv_layers.new(name='UV0'); uv.data.foreach_set('uv', (P[lv][:, [0, 1]] / 500.0).astype(np.float32).ravel())
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', bake_anim=False, add_leaf_bones=False, colors_type='SRGB')
print('ROCK tris', len(me.polygons))
