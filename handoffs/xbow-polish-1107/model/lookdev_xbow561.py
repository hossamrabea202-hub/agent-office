# Lookdev for #561 (KB rule 2): locked exposure, HDRI + 5600 K sun, grey 18 % ball + chrome ball beside the crossbow.
#   blender -b <xbow561.blend> -P lookdev_xbow561.py -- <out.png> [view=three|side|close|top] [samples=64] [textured=0|1]
# textured=1 swaps the procedural shaders for the baked texture set (what UE will see).
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
OUT = a[0]; VIEW = a[1] if len(a) > 1 else 'three'; SMP = int(a[2]) if len(a) > 2 else 64; TEX = len(a) > 3 and a[3] == '1'
sc = bpy.context.scene; ob = bpy.data.objects['SM_Crossbow561']
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SMP; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0   # locked
w = bpy.data.worlds.new('LD'); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(os.path.join(os.path.dirname(bpy.app.binary_path), '4.5', 'datafiles', 'studiolights', 'world', 'courtyard.exr'))
bg = nt.nodes['Background']; bg.inputs[1].default_value = 0.8; nt.links.new(env.outputs[0], bg.inputs[0])
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sun.data.angle = math.radians(0.6)
sun.data.color = (1.0, 0.96, 0.92); sun.rotation_euler = (math.radians(48), 0, math.radians(-35)); sc.collection.objects.link(sun)
# ground: neutral mid-grey card so the crossbow has a contact shadow
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.075)); g = bpy.context.object
gm = bpy.data.materials.new('Ground'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']
gb.inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1); gb.inputs['Roughness'].default_value = 0.8; g.data.materials.append(gm)
for x, col, met, r in ((-0.30, (0.18, 0.18, 0.18), 0, 0.6), (-0.20, (0.95, 0.95, 0.95), 1, 0.03)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(x, 0.30, -0.035), segments=48, ring_count=24); s = bpy.context.object
    bpy.ops.object.shade_smooth(); m = bpy.data.materials.new('ball'); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Metallic'].default_value = met; bs.inputs['Roughness'].default_value = r; s.data.materials.append(m)
if TEX:
    d = os.path.dirname(bpy.data.filepath); m = bpy.data.materials.new('Baked'); m.use_nodes = True; n = m.node_tree; bs = n.nodes['Principled BSDF']
    def t(name, cs):
        x = n.nodes.new('ShaderNodeTexImage'); x.image = bpy.data.images.load(os.path.join(d, name)); x.image.colorspace_settings.name = cs; return x
    bc, orm, nm = t('T_Crossbow561M_BaseColor.png', 'sRGB'), t('T_Crossbow561M_ORM.png', 'Non-Color'), t('T_Crossbow561M_Normal.png', 'Non-Color')
    n.links.new(bc.outputs[0], bs.inputs['Base Color']); sp = n.nodes.new('ShaderNodeSeparateColor'); n.links.new(orm.outputs[0], sp.inputs[0])
    n.links.new(sp.outputs[1], bs.inputs['Roughness']); n.links.new(sp.outputs[2], bs.inputs['Metallic'])
    nmn = n.nodes.new('ShaderNodeNormalMap'); n.links.new(nm.outputs[0], nmn.inputs['Color']); n.links.new(nmn.outputs[0], bs.inputs['Normal'])
    ob.data.materials.clear(); ob.data.materials.append(m)
    for p in ob.data.polygons: p.material_index = 0
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {'three': ((0.55, -0.95, 0.42), (0.0, 0.0, 0.0), 40), 'side': ((0.0, -1.35, 0.06), (0.0, 0.0, -0.01), 45),
         'close': ((0.20, -0.30, 0.16), (0.05, 0.0, 0.0), 50), 'top': ((0.05, -0.25, 0.75), (0.05, 0.0, 0.0), 35), 'inlay': ((-0.17, -0.22, 0.06), (-0.21, 0.0, -0.022), 50), 'head': ((0.36, -0.20, 0.12), (0.27, 0.0, 0.0), 45)}
loc, tgt, lens = VIEWS[VIEW]; cam.location = loc; cam.data.lens = lens
cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
