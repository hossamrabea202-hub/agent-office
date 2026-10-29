# Staged 4K bake for the shields (SHIELD=Heater|Round, default Heater) (same stages as the siege kit's bake_kit.py, plus a Metallic channel).
#   STAGE=prep   blender -b Heater_low.blend -P bake_heater.py   -> Heater_bake.blend (LP joined + packed, HP joined, materials)
#   STAGE=BC|RG|MT|AO|Normal (+ QUAD=0..3)  blender -b Heater_bake.blend -P bake_heater.py  -> tex/raw_<ch>_q<n>.exr
#   STAGE=finish blender -b Heater_bake.blend -P bake_heater.py   -> textures, preview material, FBX (+ _NoArrow when built with ARROW=1), Heater_final.blend
import sys, os, json
import bpy, numpy as np
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import shieldmat, swordmat, potionmat
from matlib import set_output

STAGE = os.environ['STAGE']
SIZE = int(os.environ.get('BAKE_SIZE', '4096'))
SH = os.environ.get('SHIELD', 'Heater')
NAME = 'SM_%sShield' % SH; TN = 'T_%sShield' % SH
if SH == 'Sword': NAME, TN = 'SM_Emberoath', 'T_Emberoath'
POT = SH.startswith('Potion')
if POT: NAME, TN = 'SM_Potion_' + SH[6:], 'T_Potion_' + SH[6:]
MATS = swordmat if SH == 'Sword' else potionmat if POT else shieldmat
UNBAKED = ('Glass', 'Liquid')     # potions: these keep translucent UE materials and are not baked
TEX = os.path.join(D, 'tex'); os.makedirs(TEX, exist_ok=True)
sc = bpy.context.scene

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

if STAGE == 'prep':
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name in UNBAKED]: bpy.data.objects.remove(o)
    LP = join([o for o in bpy.data.objects if o.type == 'MESH'], NAME)
    LP.data.materials.clear()
    m = bpy.data.materials.new('M_' + NAME); m.use_nodes = True; LP.data.materials.append(m)
    bpy.context.view_layer.objects.active = LP
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    sc.tool_settings.use_uv_select_sync = True; bpy.ops.uv.select_all(action='SELECT')
    if SH == 'Sword': bpy.ops.uv.average_islands_scale()          # equal texel density for every part
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', margin=0.003, rotate=True, shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    with bpy.data.libraries.load(os.path.join(D, SH + '_high.blend')) as (src, dst):
        dst.objects = list(src.objects)
    hp = [o for o in dst.objects if o is not None and o.type == 'MESH' and o.name not in UNBAKED]
    for o in hp: sc.collection.objects.link(o)
    join(hp, 'HP')
    MATS.build_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, SH + '_bake.blend'))
    print('TRIS', sum(len(p.vertices) - 2 for p in LP.data.polygons))
    print('STAGE prep OK', flush=True)

elif STAGE in ('BC', 'RG', 'MT', 'AO', 'Normal', 'EM'):
    LP, HP = bpy.data.objects[NAME], bpy.data.objects['HP']
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = int(os.environ.get('BAKE_SAMPLES', '24'))
    sc.cycles.use_auto_tile = True; sc.cycles.tile_size = 1024
    # thin parts (14 mm board, 4 mm straps): a short cage so a face never picks up what sits in front of it
    b = sc.render.bake; b.use_selected_to_active = True; b.cage_extrusion = 0.006; b.max_ray_distance = 0.012; b.margin = 16
    QUAD = os.environ.get('QUAD'); BS = SIZE
    if QUAD is not None:
        q = int(QUAD); qx, qy = q % 2, q // 2; BS = SIZE // 2
        uvd = LP.data.uv_layers.active.data
        a = np.empty(len(uvd) * 2, np.float32); uvd.foreach_get('uv', a); a = a.reshape(-1, 2)
        a = a * 2 - np.array([qx, qy], np.float32); uvd.foreach_set('uv', a.ravel())
    nt = LP.data.materials[0].node_tree
    node = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new('raw_' + STAGE, BS, BS, alpha=False, float_buffer=True); img.colorspace_settings.name = 'Non-Color'
    node.image = img; nt.nodes.active = node
    for s in HP.material_slots:
        if s.material: set_output(s.material, 'BSDF' if STAGE == 'Normal' else STAGE)
    bpy.ops.object.select_all(action='DESELECT'); HP.select_set(True); LP.select_set(True); bpy.context.view_layer.objects.active = LP
    if STAGE == 'Normal':
        b.normal_space = 'TANGENT'; bpy.ops.object.bake(type='NORMAL')
    else:
        bpy.ops.object.bake(type='EMIT')
    img.filepath_raw = os.path.join(TEX, f'{SH}_raw_{STAGE}' + (f'_q{QUAD}' if QUAD is not None else '') + '.exr'); img.file_format = 'OPEN_EXR'; img.save()
    print('STAGE', STAGE, 'OK', flush=True)

elif STAGE == 'finish':
    LP = bpy.data.objects[NAME]
    bpy.data.objects.remove(bpy.data.objects['HP'])
    def load(path, n):
        im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
        a = np.empty(n * n * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
        return a.reshape(n, n, 4)
    def chan(ch, k):
        h = SIZE // 2; out = np.zeros((SIZE, SIZE), np.float32)
        for q in range(4):
            qx, qy = q % 2, q // 2
            out[qy * h:(qy + 1) * h, qx * h:(qx + 1) * h] = load(os.path.join(TEX, f'{SH}_raw_{ch}_q{q}.exr'), h)[..., k]
        return out
    def save(arr, name, depth='8'):
        im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
        im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    def srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
    one = np.ones((SIZE, SIZE), np.float32)
    save(np.stack([srgb(chan('BC', k)) for k in range(3)] + [one], -1), TN + '_BaseColor')
    save(np.stack([chan('AO', 0), chan('RG', 0), chan('MT', 0)] + [one], -1), TN + '_ORM')
    if SH == 'Sword': save(np.stack([srgb(np.clip(chan('EM', k), 0, 1)) for k in range(3)] + [one], -1), TN + '_Emissive')
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
    if POT:   # put the glass and the liquid back, each with its own material slot for UE's translucent materials
        with bpy.data.libraries.load(os.path.join(D, SH + '_low.blend')) as (src, dst):
            dst.objects = [n for n in src.objects if n in UNBAKED]
        for o in dst.objects:
            sc.collection.objects.link(o); o.data.materials.clear()
            o.data.materials.append(bpy.data.materials.new('M_Potion' + o.name))
        bpy.ops.object.select_all(action='DESELECT')
        for o in dst.objects: o.select_set(True)
        LP.select_set(True); bpy.context.view_layer.objects.active = LP; bpy.ops.object.join()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, SH + '_final.blend'))     # world space, for renders
    # pivot at the hand grip centre (the hand socket goes here), then the two FBX: with and without the arrow
    g = json.load(open(os.path.join(D, SH.lower() + '_meta.json')))['grip']
    me = LP.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
    me.vertices.foreach_set('co', (co.reshape(-1, 3) - np.array(g, np.float32)).ravel()); me.update()
    def export(fn):
        bpy.ops.object.select_all(action='DESELECT'); LP.select_set(True); bpy.context.view_layer.objects.active = LP
        bpy.ops.export_scene.fbx(filepath=os.path.join(D, fn), use_selection=True, apply_unit_scale=True, mesh_smooth_type='FACE',
                                 use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')
    export(NAME + '.fbx')
    print('TRIS', sum(len(p.vertices) - 2 for p in me.polygons))
    vg = LP.vertex_groups.get('arrow')
    if vg is None:
        print('STAGE finish OK', flush=True); raise SystemExit
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
    LP.vertex_groups.active_index = vg.index; bpy.ops.object.vertex_group_select(); bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    export(NAME + '_NoArrow.fbx')
    print('TRIS_NOARROW', sum(len(p.vertices) - 2 for p in me.polygons))
    print('STAGE finish OK', flush=True)
