# Memory-safe staged bake for the vambraces (forearms), TGA 2026-10-31: checkking's greave pipeline, paths from the work dir.
#   STAGE=prep   blender -b forearm_build_r1.blend -P bake_staged.py   -> bake_ready.blend
#   STAGE=BC|RG|MT|AO|Normal (+ QUAD=0..3)  blender -b bake_ready.blend -P bake_staged.py   -> tex/raw_<ch>_q<n>.exr
#   STAGE=finish blender -b bake_ready.blend -P bake_staged.py   -> textures, material, L + R FBX, forearm_final.blend
import sys, os, math
import bpy, numpy as np
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath)
sys.path.insert(0, D)
import materials
materials.LEATHER_TONE = 0.7

STAGE = os.environ['STAGE']
SIZE = int(os.environ.get('BAKE_SIZE', '2048'))   # hero armour budget (#262)
BASE = 'SM_ObsidianSovereign_Forearms'
NAME = BASE + '_L'
TN = 'T_ObsidianSovereign_Forearms'
TEX = os.path.join(D, 'tex'); os.makedirs(TEX, exist_ok=True)
sc = bpy.context.scene

def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

if STAGE == 'prep':
    import bmesh, mathutils
    BAKE_ONLY = ('Inlay', 'Laurel', 'Etch', 'Rivet', 'Stitch')
    low = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in low: apply_mods(o)
    for o in [o for o in low if o.name.startswith(BAKE_ONLY)]: bpy.data.objects.remove(o)
    LP = join([o for o in bpy.data.objects if o.type == 'MESH'], NAME)
    LP.data.materials.clear()
    mat_lp = bpy.data.materials.new('M_ObsidianSovereign_Forearms'); mat_lp.use_nodes = True; LP.data.materials.append(mat_lp)
    # inner shells of the plates (Solidify wrote them to the 'inner' group) get less texel space
    gi = LP.vertex_groups['inner'].index
    inner = np.zeros(len(LP.data.vertices), bool)
    for v in LP.data.vertices:
        inner[v.index] = any(g.group == gi for g in v.groups)
    bm = bmesh.new(); bm.from_mesh(LP.data); uvl = bm.loops.layers.uv.active
    for f in bm.faces:
        if all(inner[v.index] for v in f.verts):
            # shrink and move away: the inner shell becomes its own island instead of sitting on top of the outer one
            for lp in f.loops: lp[uvl].uv = lp[uvl].uv * 0.35 + mathutils.Vector((8.0, 0.0))
    bm.to_mesh(LP.data); bm.free()
    bpy.context.view_layer.objects.active = LP
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    sc.tool_settings.use_uv_select_sync = True; bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', margin=0.003, rotate=True, shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    with bpy.data.libraries.load(os.path.join(D, 'forearm_build_r3.blend')) as (src, dst):
        dst.objects = list(src.objects)
    hp = []
    for o in dst.objects:
        if o is None or o.type != 'MESH': continue
        sc.collection.objects.link(o); hp.append(o)
    tex = bpy.data.textures.new('Hammer', 'VORONOI'); tex.noise_scale = 0.006; tex.distance_metric = 'DISTANCE'
    for o in hp:
        if o.name.split('.')[0].startswith(('VambOuter', 'VambInner')):
            dm = o.modifiers.new('Hammer', 'DISPLACE'); dm.texture = tex; dm.texture_coords = 'GLOBAL'; dm.strength = 0.00018; dm.mid_level = 0.6
        apply_mods(o)
    join(hp, 'HP')
    materials.build_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'bake_ready.blend'))
    print('STAGE prep OK', flush=True)

elif STAGE in ('BC', 'RG', 'MT', 'AO', 'Normal'):
    LP, HP = bpy.data.objects[NAME], bpy.data.objects['HP']
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = int(os.environ.get('BAKE_SAMPLES', '24'))
    sc.cycles.use_auto_tile = True; sc.cycles.tile_size = 1024
    b = sc.render.bake; b.use_selected_to_active = True; b.cage_extrusion = 0.0045; b.max_ray_distance = 0.012; b.margin = 16
    QUAD = os.environ.get('QUAD')
    BS = SIZE
    if QUAD is not None:
        q = int(QUAD); qx, qy = q % 2, q // 2; BS = SIZE // 2
        uvd = LP.data.uv_layers.active.data
        a = np.empty(len(uvd) * 2, np.float32); uvd.foreach_get('uv', a); a = a.reshape(-1, 2)
        a = a * 2 - np.array([qx, qy], np.float32); uvd.foreach_set('uv', a.ravel())
    nt = LP.data.materials[0].node_tree
    node = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new('raw_' + STAGE, BS, BS, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    node.image = img; nt.nodes.active = node
    for s in HP.material_slots:
        if s.material: materials.set_output(s.material, 'BSDF' if STAGE == 'Normal' else STAGE)
    bpy.ops.object.select_all(action='DESELECT'); HP.select_set(True); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    if STAGE == 'Normal':
        b.normal_space = 'TANGENT'; bpy.ops.object.bake(type='NORMAL')
    else:
        bpy.ops.object.bake(type='EMIT')
    img.filepath_raw = os.path.join(TEX, f'raw_{STAGE}' + (f'_q{QUAD}' if QUAD is not None else '') + '.exr'); img.file_format = 'OPEN_EXR'; img.save()
    print('STAGE', STAGE, 'OK', flush=True)

elif STAGE == 'finish':
    LP = bpy.data.objects[NAME]
    bpy.data.objects.remove(bpy.data.objects['HP'])
    def load(path, n):
        im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
        a = np.empty(n * n * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
        return a.reshape(n, n, 4)
    def chan(ch, k):
        full = os.path.join(TEX, f'raw_{ch}.exr')
        if os.path.exists(full): return load(full, SIZE)[..., k].copy()
        h = SIZE // 2; out = np.zeros((SIZE, SIZE), np.float32)
        for q in range(4):
            qx, qy = q % 2, q // 2
            out[qy * h:(qy + 1) * h, qx * h:(qx + 1) * h] = load(os.path.join(TEX, f'raw_{ch}_q{q}.exr'), h)[..., k]
        return out
    def save(arr, name, depth='8'):
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
        im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    def srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
    one = np.ones((SIZE, SIZE), np.float32)
    bc = [srgb(chan('BC', k)) for k in range(3)]
    save(np.stack(bc + [one], -1), TN + '_BaseColor'); del bc
    orm = [chan('AO', 0), chan('RG', 0), chan('MT', 0)]
    save(np.stack(orm + [one], -1), TN + '_ORM'); del orm
    n = [chan('Normal', k) for k in range(3)]
    save(np.stack(n + [one], -1), TN + '_Normal_OpenGL', '16')
    n[1] = 1.0 - n[1]
    save(np.stack(n + [one], -1), TN + '_Normal_DirectX', '16'); del n
    nt = LP.data.materials[0].node_tree; nt.nodes.clear()
    def teximg(name, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, name + '.png')); t.image.colorspace_settings.name = cs; return t
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs[0], out.inputs[0])
    nt.links.new(teximg(TN + '_BaseColor', 'sRGB').outputs[0], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(teximg(TN + '_ORM', 'Non-Color').outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs['Roughness']); nt.links.new(sep.outputs[2], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(teximg(TN + '_Normal_OpenGL', 'Non-Color').outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    # right vambrace: exact mirror across X, same UVs/material, outward winding restored
    R = LP.copy(); R.data = LP.data.copy(); sc.collection.objects.link(R); R.name = R.data.name = BASE + '_R'
    R.data.transform(__import__('mathutils').Matrix.Scale(-1, 4, (1, 0, 0))); R.data.flip_normals(); R.data.update()
    def export(ob):
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath=os.path.join(D, ob.name + '.fbx'), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE',
                                 use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
    export(LP); export(R)
    print('TRIS', sum(len(p.vertices) - 2 for p in LP.data.polygons))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'forearm_final.blend'))
    print('STAGE finish OK', flush=True)
