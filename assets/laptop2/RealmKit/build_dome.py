# The realm bubble mesh (#169): a closed half-ellipsoid, unit size (radius 1 in X/Y, height 1 in Z), smooth, with a
# slightly irregular rim so it does not read as a perfect sphere, UVs for the panning tentacle noise (u around, v up).
# The dome is double-sided in the material; the mesh has outward normals only.  blender -b --factory-startup -P build_dome.py
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
from shieldkit import mesh, grid_quads, PI
D = os.path.dirname(os.path.abspath(__file__))
nu, nv = 96, 40
th = np.linspace(0, 2 * PI, nu + 1); ph = np.linspace(0, PI / 2, nv + 1)
T, Ph = np.meshgrid(th, ph, indexing='ij')
# the dome bulges a little past vertical near the rim (an overhang that "hangs over the wall"), then tucks back in
rim = 1.0 + 0.08 * np.sin(Ph * 2.2) ** 3 * (1 - np.sin(Ph)) + 0.03 * np.sin(T * 5 + 1.0) * np.cos(Ph) ** 4
X, Y, Z = rim * np.cos(Ph) * np.cos(T), rim * np.cos(Ph) * np.sin(T), np.sin(Ph) * (1 + 0.02 * np.sin(T * 3))
V = np.stack([X, Y, Z], -1).reshape(-1, 3)
# weld the pole row into one vertex (the last ring is a single point)
V[-(nu + 1):] = [0, 0, 1.0]
Q = grid_quads(nu + 1, nv + 1, False)
uv = np.stack([T / (2 * PI) * 4, Ph / (PI / 2)], -1).reshape(-1, 2)
ob = mesh('SM_RealmDome', V, [Q], 'Bubble', uv=uv)
# flat skirt that goes 0.08 below the rim, to hide any gap between the dome and the terrain
sk = np.stack([np.cos(th), np.sin(th), np.full_like(th, -0.08)], -1); rm = np.stack([X[:, 0], Y[:, 0], Z[:, 0]], -1)
Vs = np.vstack([rm, sk]); Qs = grid_quads(2, nu + 1, False)
mesh('Skirt', Vs, [Qs], 'Bubble', uv=np.stack([np.tile(th / (2 * PI) * 4, 2), np.repeat([0.0, -0.08], nu + 1)], -1))
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = ob; bpy.ops.object.join(); ob.name = 'SM_RealmDome'
me = ob.data
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-5); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
bpy.ops.export_scene.fbx(filepath=os.path.join(D, 'SM_RealmDome.fbx'), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons)); print('BUILD OK')
