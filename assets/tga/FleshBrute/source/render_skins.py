# Flesh Brute skin line-up: renders Mesh_Skin_01 once per skin, then stitches the shots side by side.
#   blender -b Monster_001.blend -P render_skins.py -- <tex dir (make_skins out)> <normal OpenGL dir> <out png>
import sys, os, math
import bpy, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; TEX, NGL, OUT = a
SKINS = ['Clean', 'Bloody', 'Rotten', 'Charred', 'Drowned']
sc = bpy.context.scene
body = bpy.data.objects['Mesh_Skin_01']
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
mats = {}
for i, part in enumerate(('01', '02')):
    m = bpy.data.materials.new('FB_P' + part); nt = m.node_tree; nt.nodes.clear()
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs[0], out.inputs[0])
    bc = nt.nodes.new('ShaderNodeTexImage'); orm = nt.nodes.new('ShaderNodeTexImage'); nm = nt.nodes.new('ShaderNodeTexImage')
    nm.image = bpy.data.images.load(os.path.join(NGL, f'Monster_001_Skin_01_part_{part}_Normal_OpenGL_4K.png')); nm.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(bc.outputs[0], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs[1], bsdf.inputs['Roughness'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs[0], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], bsdf.inputs['Normal'])
    bsdf.inputs['Subsurface Weight'].default_value = 0.08; bsdf.inputs['Subsurface Radius'].default_value = (0.6, 0.2, 0.1)
    body.material_slots[i].material = m; mats[part] = (bc, orm)
bpy.ops.mesh.primitive_plane_add(size=30); g = bpy.context.active_object
gm = bpy.data.materials.new('G'); gb = gm.node_tree.nodes['Principled BSDF']; gb.inputs['Base Color'].default_value = (0.04, 0.035, 0.03, 1); gb.inputs['Roughness'].default_value = 0.9
g.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.38, 0.41, 0.46, 1); bg.inputs['Strength'].default_value = 0.6
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(55), 0, math.radians(-35))); s = bpy.context.active_object.data; s.energy = 3.0; s.angle = math.radians(5); s.color = (1, 0.88, 0.75)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(70), 0, math.radians(160))); s = bpy.context.active_object.data; s.energy = 1.6; s.color = (0.7, 0.8, 1.0)   # cold rim
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
bb = [body.matrix_world @ Vector(c) for c in ev.bound_box]
ctr = sum(bb, Vector()) / 8; ctr.z = 1.05
t = ctr; cam.location = ctr + Vector((1.9, -4.3, 0.4)); cd.lens = 45
cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 700, 1000; sc.view_settings.view_transform = 'AgX'
shots = []
for sk in SKINS:
    for part, (bc, orm) in mats.items():
        bc.image = bpy.data.images.load(os.path.join(TEX, f'T_FleshBrute_{sk}_P{part}_BC.png'))
        orm.image = bpy.data.images.load(os.path.join(TEX, f'T_FleshBrute_{sk}_P{part}_ORM.png')); orm.image.colorspace_settings.name = 'Non-Color'
    p = os.path.join(os.path.dirname(OUT), f'skin_{sk}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p); px = np.empty(700 * 1000 * 4, np.float32); im.pixels.foreach_get(px); shots.append(px.reshape(1000, 700, 4)); bpy.data.images.remove(im)
    print('SHOT', sk, flush=True)
row = np.concatenate(shots, axis=1)
im = bpy.data.images.new('lineup', row.shape[1], row.shape[0], alpha=False); im.colorspace_settings.name = 'Non-Color'
im.pixels.foreach_set(row.ravel()); im.filepath_raw = OUT; im.file_format = 'PNG'; im.save()
print('LINEUP OK', OUT, flush=True)
