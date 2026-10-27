# Memory-safe 4K bake in stages, one Blender process per stage:
#   STAGE=prep   blender -b chest_build_r1.blend -P bake_staged.py   -> bake_ready.blend (LP with UVs + joined HP + materials)
#   STAGE=BC|RG|MT|AO|Normal   blender -b bake_ready.blend -P bake_staged.py   -> tex/raw_<ch>.png (16-bit)
#   STAGE=finish blender -b bake_ready.blend -P bake_staged.py   -> game textures, final material, FBX, chest_final.blend
import sys, os, math
import bpy, numpy as np
D = r'C:\Users\hossam.rabea\checkking-work\chest'
sys.path.insert(0, D)
import materials

STAGE = os.environ['STAGE']
SIZE = int(os.environ.get('BAKE_SIZE', '4096'))
NAME = 'SM_ObsidianSovereign_Chest'
TEX = os.path.join(D, 'tex'); os.makedirs(TEX, exist_ok=True)
sc = bpy.context.scene

def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    # consistent outward normals (ribbons/straps can come out flipped, which makes bake rays miss)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

if STAGE == 'prep':
    import bmesh
    BAKE_ONLY = ('Inlay', 'Laurel', 'Etch', 'Rivet', 'StrapRivet', 'ShoulderRivet')
    low = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in low: apply_mods(o)
    for o in [o for o in low if o.name.startswith(BAKE_ONLY)]: bpy.data.objects.remove(o)
    LP = join([o for o in bpy.data.objects if o.type == 'MESH'], NAME)
    LP.data.materials.clear()
    mat_lp = bpy.data.materials.new('M_ObsidianSovereign_Chest'); mat_lp.use_nodes = True; LP.data.materials.append(mat_lp)
    bm = bmesh.new(); bm.from_mesh(LP.data); uvl = bm.loops.layers.uv.active
    for f in bm.faces:
        c = f.calc_center_median(); rad = c.copy(); rad.z = 0
        if f.normal.dot(rad.normalized()) < -0.25:
            for lp in f.loops: lp[uvl].uv *= 0.35
    bm.to_mesh(LP.data); bm.free()
    bpy.context.view_layer.objects.active = LP
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    sc.tool_settings.use_uv_select_sync = True; bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', margin=0.003, rotate=True, shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    with bpy.data.libraries.load(os.path.join(D, 'chest_build_r3.blend')) as (src, dst):
        dst.objects = list(src.objects)
    hp = []
    for o in dst.objects:
        if o is None or o.type != 'MESH': continue
        sc.collection.objects.link(o); hp.append(o)
    tex = bpy.data.textures.new('Hammer', 'VORONOI'); tex.noise_scale = 0.006; tex.distance_metric = 'DISTANCE'
    for o in hp:
        if o.name.split('.')[0].startswith(('Backplate', 'Breastplate', 'Plackart', 'Fauld', 'Culet')):
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
    QUAD = os.environ.get('QUAD')   # '0'..'3': bake one quarter of the 4K sheet as a 2K image (memory-safe)
    BS = SIZE
    if QUAD is not None:
        q = int(QUAD); qx, qy = q % 2, q // 2; BS = SIZE // 2
        uvd = LP.data.uv_layers.active.data
        a = np.empty(len(uvd) * 2, np.float32); uvd.foreach_get('uv', a); a = a.reshape(-1, 2)
        a = a * 2 - np.array([qx, qy], np.float32); uvd.foreach_set('uv', a.ravel())
    nt = LP.data.materials[0].node_tree
    node = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new('raw_' + STAGE, BS, BS, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'   # raw linear data; base colour is sRGB-encoded once in 'finish'
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
        for q in range(4):   # pixel rows run bottom-up, same as UV v
            qx, qy = q % 2, q // 2
            out[qy * h:(qy + 1) * h, qx * h:(qx + 1) * h] = load(os.path.join(TEX, f'raw_{ch}_q{q}.exr'), h)[..., k]
        return out
    def save(arr, name, cs='Non-Color', depth='8'):
        # values are written as given (already encoded where needed): byte image, Non-Color, plain save()
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
        im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    def srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
    one = np.ones((SIZE, SIZE), np.float32)
    bc = [srgb(chan('BC', k)) for k in range(3)]   # EXR holds linear; PNG base colour is sRGB-encoded
    save(np.stack(bc + [one], -1), 'T_ObsidianSovereign_Chest_BaseColor', 'Non-Color'); del bc
    orm = [chan('AO', 0), chan('RG', 0), chan('MT', 0)]
    save(np.stack(orm + [one], -1), 'T_ObsidianSovereign_Chest_ORM', 'Non-Color'); del orm
    n = [chan('Normal', k) for k in range(3)]
    save(np.stack(n + [one], -1), 'T_ObsidianSovereign_Chest_Normal_OpenGL', 'Non-Color', '16')
    n[1] = 1.0 - n[1]
    save(np.stack(n + [one], -1), 'T_ObsidianSovereign_Chest_Normal_DirectX', 'Non-Color', '16'); del n
    nt = LP.data.materials[0].node_tree; nt.nodes.clear()
    def teximg(name, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, name + '.png')); t.image.colorspace_settings.name = cs; return t
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs[0], out.inputs[0])
    nt.links.new(teximg('T_ObsidianSovereign_Chest_BaseColor', 'sRGB').outputs[0], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(teximg('T_ObsidianSovereign_Chest_ORM', 'Non-Color').outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs['Roughness']); nt.links.new(sep.outputs[2], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(teximg('T_ObsidianSovereign_Chest_Normal_OpenGL', 'Non-Color').outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    bpy.ops.object.select_all(action='DESELECT'); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    bpy.ops.export_scene.fbx(filepath=os.path.join(D, NAME + '.fbx'), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE',
                             use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'chest_final.blend'))
    print('STAGE finish OK', flush=True)




