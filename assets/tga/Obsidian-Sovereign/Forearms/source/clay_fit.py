# Clay fit check: the vambrace build + checkking's gauntlet + Codex's upper arm.  blender -b forearm_build_r1.blend -P clay_fit.py -- <name>
import bpy, os, sys, math
from mathutils import Vector
D = os.path.dirname(bpy.data.filepath); NAME = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'clay'
sc = bpy.context.scene
for p, tint in ((r'R:\assets\checkking\Obsidian-Sovereign\Gauntlets\SM_ObsidianSovereign_Gauntlets_L.fbx', (0.25, 0.22, 0.2)),
                (r'R:\assets\Codex\Obsidian-Sovereign\UpperArms\SM_ObsidianSovereign_UpperArms_L.fbx', (0.2, 0.22, 0.26))):
    before = set(sc.objects); bpy.ops.import_scene.fbx(filepath=p)
    m = bpy.data.materials.new('ctx'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*tint, 1)
    for o in set(sc.objects) - before:
        if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(m)
clay = bpy.data.materials.new('clay'); clay.use_nodes = True; clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.42, 0.40, 0.37, 1)
gold = bpy.data.materials.new('g'); gold.use_nodes = True; gold.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.8, 0.55, 0.2, 1)
for o in sc.objects:
    if o.type == 'MESH' and o.name.startswith(('Vamb', 'Rim', 'Ridge', 'Lining', 'Hinge', 'Rivet', 'Strap', 'Buckle', 'Inlay', 'Laurel', 'Etch')):
        o.data.materials.clear(); o.data.materials.append(gold if o.name.startswith(('Inlay', 'Laurel')) else clay)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(55), 0, math.radians(-35))); bpy.context.active_object.data.energy = 3.5
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.render.resolution_x, sc.render.resolution_y = 900, 1100
tgt = Vector((0.32, 0.0, 0.98))
for tag, loc in (('front', (0.55, -0.75, 1.05)), ('back', (0.10, 0.75, 1.05)), ('side', (1.0, 0.0, 1.0))):
    cam.location = loc; cd.lens = 70; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(D, 'out', '%s_%s.png' % (NAME, tag)); bpy.ops.render.render(write_still=True)
print('CLAY OK', flush=True)
