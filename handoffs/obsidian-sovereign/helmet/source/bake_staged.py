# Staged bake for the helm (#485), same pipeline as the shield / boots / chest bake_staged.py.
#   STAGE=prep   blender -b helm_build_r1.blend -P bake_staged.py   -> bake_ready.blend (UVs, triangulated low poly, high poly + materials)
#   STAGE=BC|RG|MT|AO|Normal  blender -b bake_ready.blend -P bake_staged.py   -> tex/raw_<ch>.exr
#   STAGE=finish blender -b bake_ready.blend -P bake_staged.py   -> textures, FBX, helm_final.blend
# Intermediates live in WORK (outside the repo); textures + FBX are written to OUT (the hand-off folder).
import sys, os, math
import bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else ''
D = os.environ['WORK']; OUT = os.environ['OUT']; sys.path.insert(0, os.environ['SRC'])
import materials

STAGE = os.environ['STAGE']
SIZE = int(os.environ.get('BAKE_SIZE', '2048'))
NAME = 'SM_ObsidianSovereign_Helmet'
TN = 'T_ObsidianSovereign_Helmet'
TEX = os.path.join(OUT, 'textures'); RAW = os.path.join(D, 'tex'); os.makedirs(TEX, exist_ok=True); os.makedirs(RAW, exist_ok=True)
sc = bpy.context.scene
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(os.environ.get('RENDER_THREADS', '8'))   # keep the laptop usable

def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

if STAGE == 'prep':
    BAKE_ONLY = ('Inlay', 'Laurel', 'Etch', 'Rivet', 'Breath')
    low = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in low:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); apply_mods(o)
    for o in [o for o in low if o.name.startswith(BAKE_ONLY)]: bpy.data.objects.remove(o)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    # plates: low-stretch unwrap with the seams the builder marked; tubes and bosses keep their true-length UVs
    sc.tool_settings.use_uv_select_sync = True
    for o in objs:
        if not o.get('unwrap'): continue
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.0)
        bpy.ops.object.mode_set(mode='OBJECT')
    small = {o.name for o in objs if o.name.startswith(('Liner', 'SlitWall', 'RondelBack'))}
    # mark the texels of the inside so they can be shrunk after the scale pass
    for o in objs:
        lay = o.data.attributes.new('uv_small', 'BOOLEAN', 'FACE') if o.name in small else None
        if lay:
            for d in lay.data: d.value = True
    LP = join(objs, NAME)
    LP.data.materials.clear()
    mat_lp = bpy.data.materials.new('M_ObsidianSovereign_Helmet'); mat_lp.use_nodes = True; LP.data.materials.append(mat_lp)
    # triangulate now: the bake and the engine must share one triangulation or the normals don't line up
    bm = bmesh.new(); bm.from_mesh(LP.data)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='SHORT_EDGE', ngon_method='BEAUTY')
    bm.to_mesh(LP.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT'); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    # the inside gets a quarter of the texel density
    bm = bmesh.new(); bm.from_mesh(LP.data); uvl = bm.loops.layers.uv.active
    sm = bm.faces.layers.bool.get('uv_small') if hasattr(bm.faces.layers, 'bool') else None
    if sm is None: sm = bm.faces.layers.int.get('uv_small')
    if sm is not None:
        for f in bm.faces:
            if f[sm]:
                for lp in f.loops: lp[uvl].uv = lp[uvl].uv * 0.3
    bm.to_mesh(LP.data); bm.free()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', margin=0.004, rotate=True, shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    if 'uv_small' in LP.data.attributes: LP.data.attributes.remove(LP.data.attributes['uv_small'])
    with bpy.data.libraries.load(os.path.join(D, 'helm_build_r3.blend')) as (src, dst):
        dst.objects = list(src.objects)
    hp = []
    for o in dst.objects:
        if o is None or o.type != 'MESH': continue
        sc.collection.objects.link(o); hp.append(o)
    hammer = bpy.data.textures.new('Hammer', 'VORONOI'); hammer.noise_scale = 0.006; hammer.distance_metric = 'DISTANCE'
    dents = bpy.data.textures.new('Dents', 'CLOUDS'); dents.noise_scale = 0.030; dents.noise_depth = 2
    for o in hp:
        base = o.name.split('.')[0]
        if base.startswith(('Bowl', 'Visor', 'Cheek', 'Brow', 'LameA', 'LameB')) and not base.startswith('Rim'):
            ss = o.modifiers.new('Dense', 'SUBSURF'); ss.subdivision_type = 'SIMPLE'; ss.levels = ss.render_levels = 1
            d2 = o.modifiers.new('Dents', 'DISPLACE'); d2.texture = dents; d2.texture_coords = 'GLOBAL'; d2.strength = 0.0009; d2.mid_level = 0.5
            d1 = o.modifiers.new('Hammer', 'DISPLACE'); d1.texture = hammer; d1.texture_coords = 'GLOBAL'; d1.strength = 0.00016; d1.mid_level = 0.6
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); apply_mods(o)
    join(hp, 'HP')
    materials.build_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'bake_ready.blend'))
    print('TRIS', sum(len(p.vertices) - 2 for p in LP.data.polygons), 'HP faces', len(bpy.data.objects['HP'].data.polygons))
    print('STAGE prep OK', flush=True)

elif STAGE in ('BC', 'RG', 'MT', 'AO', 'Normal'):
    LP, HP = bpy.data.objects[NAME], bpy.data.objects['HP']
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = int(os.environ.get('BAKE_SAMPLES', '24'))
    sc.cycles.use_auto_tile = True; sc.cycles.tile_size = 1024
    b = sc.render.bake; b.use_selected_to_active = True; b.cage_extrusion = 0.0045; b.max_ray_distance = 0.012; b.margin = 8
    nt = LP.data.materials[0].node_tree
    node = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new('raw_' + STAGE, SIZE, SIZE, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    node.image = img; nt.nodes.active = node
    for s in HP.material_slots:
        if s.material: materials.set_output(s.material, 'BSDF' if STAGE == 'Normal' else STAGE)
    bpy.ops.object.select_all(action='DESELECT'); HP.select_set(True); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    if STAGE == 'Normal':
        b.normal_space = 'TANGENT'; bpy.ops.object.bake(type='NORMAL')
    else:
        bpy.ops.object.bake(type='EMIT')
    img.filepath_raw = os.path.join(RAW, f'raw_{STAGE}.exr'); img.file_format = 'OPEN_EXR'; img.save()
    print('STAGE', STAGE, 'OK', flush=True)

elif STAGE == 'finish':
    LP = bpy.data.objects[NAME]
    bpy.data.objects.remove(bpy.data.objects['HP'])
    def load(path, n):
        im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
        a = np.empty(n * n * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
        return a.reshape(n, n, 4)
    def chan(ch, k): return load(os.path.join(RAW, f'raw_{ch}.exr'), SIZE)[..., k].copy()
    def save(arr, name, depth='8', folder=TEX):
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
        im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        im.filepath_raw = os.path.join(folder, name + '.png'); im.file_format = 'PNG'
        im.save(); bpy.data.images.remove(im)
    def srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
    one = np.ones((SIZE, SIZE), np.float32)
    # calibration pass (knowledge README rule 1): metallic is 0 or 1, and no non-metal texel falls under 30 sRGB
    mt = (chan('MT', 0) > 0.5).astype(np.float32)
    bc = np.stack([chan('BC', k) for k in range(3)], -1)
    Y = bc @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    used = Y > 1e-5; floor = 0.0137                          # 30.5 sRGB, linear
    gain = np.where(used & (mt < 0.5) & (Y < floor), floor / np.maximum(Y, 1e-5), 1.0)
    save(np.stack([srgb(bc[..., k] * gain) for k in range(3)] + [one], -1), TN + '_BaseColor')
    save(np.stack([chan('AO', 0), chan('RG', 0), mt, one], -1), TN + '_ORM')
    n = [chan('Normal', k) for k in range(3)]
    n[1] = 1.0 - n[1]
    save(np.stack(n + [one], -1), TN + '_Normal_DirectX', '16')
    n[1] = 1.0 - n[1]
    save(np.stack(n + [one], -1), TN + '_Normal_OpenGL_preview', '16', RAW)   # Blender previews only: stays in WORK, not part of the hand-off
    nt = LP.data.materials[0].node_tree; nt.nodes.clear()
    def teximg(name, cs, folder=TEX):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(folder, name + '.png')); t.image.colorspace_settings.name = cs; return t
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs[0], out.inputs[0])
    nt.links.new(teximg(TN + '_BaseColor', 'sRGB').outputs[0], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(teximg(TN + '_ORM', 'Non-Color').outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs['Roughness']); nt.links.new(sep.outputs[2], bsdf.inputs['Metallic'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(teximg(TN + '_Normal_OpenGL_preview', 'Non-Color', RAW).outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
    bpy.ops.object.select_all(action='DESELECT'); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, NAME + '.fbx'), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE',
                             use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
    print('TRIS', sum(len(p.vertices) - 2 for p in LP.data.polygons))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'helm_final.blend'))
    print('STAGE finish OK', flush=True)
