# #397 lookdev (TGA): one locked rig for BEFORE (checkking's kit) and AFTER (AAA), KB rule 1: judge only under the grey ball.
#   blender -b --factory-startup -P lookdev_weapon.py -- <mesh.fbx> <textures dir> <texture prefix, e.g. T_CK_ArmingSword> <out.png>
# The textures are wired like UE's MI: BaseColor (sRGB), ORM (R AO, G roughness, B metallic), Normal DirectX (G flipped).
# Rig: AgX, exposure 0 (locked), warm key, cool rim, weak fill, 18 % grey card; an 18 % grey ball and a chrome ball beside
# the weapon (sized from its length) so values and reflections can be compared between renders.
import bpy, sys, os, math
from mathutils import Vector
fbx, texd, pre, out = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = sc.collection
bpy.ops.import_scene.fbx(filepath=fbx)
obj = [o for o in sc.objects if o.type == 'MESH'][0]
m = bpy.data.materials.new('MI'); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links; b = N['Principled BSDF']
def tex(suffix, cs):
    p = os.path.join(texd, pre + suffix)
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p); t.image.colorspace_settings.name = cs; return t
bc, orm, nm = tex('_BaseColor.png', 'sRGB'), tex('_ORM.png', 'Non-Color'), tex('_Normal_DirectX.png', 'Non-Color')
sp = N.new('ShaderNodeSeparateColor'); L.new(orm.outputs['Color'], sp.inputs[0])
L.new(bc.outputs['Color'], b.inputs['Base Color']); L.new(sp.outputs[1], b.inputs['Roughness']); L.new(sp.outputs[2], b.inputs['Metallic'])
s2 = N.new('ShaderNodeSeparateColor'); L.new(nm.outputs['Color'], s2.inputs[0])
inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(s2.outputs[1], inv.inputs[1])
cc = N.new('ShaderNodeCombineColor'); L.new(s2.outputs[0], cc.inputs[0]); L.new(inv.outputs[0], cc.inputs[1]); L.new(s2.outputs[2], cc.inputs[2])
nmap = N.new('ShaderNodeNormalMap'); L.new(cc.outputs[0], nmap.inputs['Color']); L.new(nmap.outputs[0], b.inputs['Normal'])
obj.data.materials.clear(); obj.data.materials.append(m)
for p in obj.data.polygons: p.use_smooth = True
# frame: lay the weapon diagonally (edge toward the key), as checkking's previews
obj.rotation_euler = (0, math.radians(-90 + 18), math.radians(-28)); bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
xs, zs = [v.x for v in bb], [v.z for v in bb]; Lw = max(max(xs) - min(xs), max(zs) - min(zs)); cx, cz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2
def area(name, loc, energy, color, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((cx, 0, cz)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
area('Key', (cx - 1.2 * Lw, -1.6 * Lw, cz + 0.8 * Lw), 120 * Lw * Lw, (1.0, 0.88, 0.74), 0.8 * Lw)
area('Rim', (cx + 1.4 * Lw, 1.2 * Lw, cz + 0.4 * Lw), 160 * Lw * Lw, (0.72, 0.82, 1.0), 0.4 * Lw)
area('Fill', (cx + 1.4 * Lw, -1.3 * Lw, cz - 0.3 * Lw), 18 * Lw * Lw, (1, 1, 1), 1.2 * Lw)
bpy.ops.mesh.primitive_plane_add(size=8 * Lw, location=(cx, 0.6 * Lw, cz), rotation=(math.pi / 2, 0, 0))
card = bpy.context.object; cm = bpy.data.materials.new('Grey18'); cm.use_nodes = True
cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); cm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
card.data.materials.append(cm)
r = Lw * 0.045
for k, (alb, rough, met) in enumerate((((0.18, 0.18, 0.18, 1), 0.5, 0.0), ((0.95, 0.95, 0.95, 1), 0.02, 1.0))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(cx - Lw * 0.42 + k * r * 2.6, -0.1 * Lw, cz - Lw * 0.19), segments=48, ring_count=24)
    s_ = bpy.context.object; bpy.ops.object.shade_smooth(); bm = bpy.data.materials.new('Ball%d' % k); bm.use_nodes = True
    pb = bm.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value = alb; pb.inputs['Roughness'].default_value = rough; pb.inputs['Metallic'].default_value = met
    s_.data.materials.append(bm)
cam_d = bpy.data.cameras.new('Cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = Lw * 1.12
cam = bpy.data.objects.new('Cam', cam_d); col.objects.link(cam); sc.camera = cam; cam.location = (cx, -3 * Lw, cz); cam.rotation_euler = (math.pi / 2, 0, 0)
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SPP', '96')); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0          # locked
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('LOOKDEV', out)
# detail: the business end (the top quarter along the weapon: blade near the middle-top, axe / mace / polearm heads)
vs = [obj.matrix_world @ v.co for v in obj.data.vertices]; top = max(vs, key=lambda v: v.z - v.x * 0.5)
zl = sorted(v.z for v in vs); frac = float(os.environ.get('DFRAC', '0.82'))
zc = zl[int(len(zl) * frac)]; near = [v for v in vs if abs(v.z - zc) < Lw * 0.08] or vs
cam.location.x = sum(v.x for v in near) / len(near); cam.location.z = sum(v.z for v in near) / len(near); cam_d.ortho_scale = Lw * 0.22
sc.render.resolution_x, sc.render.resolution_y = 900, 900
sc.render.filepath = out.replace('.png', '_detail.png'); bpy.ops.render.render(write_still=True); print('LOOKDEV', sc.render.filepath)
