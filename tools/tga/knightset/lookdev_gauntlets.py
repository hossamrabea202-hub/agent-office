# Owner render of a Yellow Eagle piece (#367, TGA): blender -b <piece>_tex.blend -P lookdev_gauntlets.py  (env WORK, PIECE)
# Four views like the sheet's orthos on a neutral grey, studio key + rim, AgX. VIEW per piece: rotations, spacing, ortho scale, camera z.
import bpy, os, math
PIECE = os.environ.get('PIECE', 'Gauntlets')
VIEW = {'Gauntlets': ((0, 180, 90, -40), 0.165, 0.7, -0.045), 'Greaves': ((0, 180, -90, 90), 0.215, 1.0, 0.185)}[PIECE]
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '96')); sc.render.resolution_x, sc.render.resolution_y = 1800, 900
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
g = bpy.data.objects['SM_Eagle%s_L' % PIECE]
for o in sc.objects:
    if o.type == 'MESH': o.hide_render = True
wd = bpy.data.worlds.new('W'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[0].default_value = (0.2, 0.2, 0.21, 1); wd.node_tree.nodes['Background'].inputs[1].default_value = 0.35
bpy.ops.object.light_add(type='AREA', location=(-0.4, -0.7, 0.4)); k = bpy.context.active_object; k.data.energy = 40; k.data.size = 0.6; k.rotation_euler = (math.radians(60), 0, math.radians(-30))
bpy.ops.object.light_add(type='AREA', location=(0.6, 0.6, 0.3)); r = bpy.context.active_object; r.data.energy = 40; r.data.size = 0.4; r.rotation_euler = (math.radians(-60), 0, math.radians(140))
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0.4, 0), rotation=(math.radians(90), 0, 0)); bg = bpy.context.active_object
bm = bpy.data.materials.new('BG'); bm.use_nodes = True; bm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.09, 0.095, 1); bg.data.materials.append(bm)
for i, rz in enumerate(VIEW[0]):
    o = g.copy(); sc.collection.objects.link(o); o.hide_render = False; o.location = ((i - 1.5) * VIEW[1] * 1.0 + (0.0 if PIECE != 'Gauntlets' else -0.0025), 0, 0); o.rotation_euler = (0, 0, math.radians(rz))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = VIEW[2]; cam.location = (0, -1, VIEW[3]); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.filepath = os.path.join(D, 'out', PIECE.lower() + '_views.png'); bpy.ops.render.render(write_still=True); print('RENDERED views', flush=True)
