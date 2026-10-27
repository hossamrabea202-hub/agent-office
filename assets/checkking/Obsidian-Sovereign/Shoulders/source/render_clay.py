# Clay/preview renders of the open shoulder .blend, with the checkking chest placed in the set frame for fit.
# blender -b shoulder_build_r1.blend -P render_clay.py -- out_prefix [samples] [res] [nochest]
import sys, os, math
import bpy, mathutils
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
prefix = argv[0]
samples = int(argv[1]) if len(argv) > 1 else 48
res = int(argv[2]) if len(argv) > 2 else 900
CHEST = r'C:\Users\hossam.rabea\checkking-work\chest\SM_ObsidianSovereign_Chest.fbx'
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('W') if not sc.world else sc.world
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.20, 0.21, 0.23, 1); bg.inputs[1].default_value = 0.35
TGT = mathutils.Vector((0.20, 0.0, 1.30))
if not (len(argv) > 3 and argv[3] == 'nochest') and os.path.exists(CHEST):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=CHEST)
    # give the chest its baked textures (the FBX carries none); the committed normal is DirectX, so flip green back
    T = r'C:\Users\hossam.rabea\agent-office\assets\checkking\Obsidian-Sovereign\Chest\textures\T_ObsidianSovereign_Chest_'
    cm = bpy.data.materials.new('ChestTex'); cm.use_nodes = True; nt = cm.node_tree; bs = nt.nodes['Principled BSDF']
    def ti(n, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(T + n + '.png'); t.image.colorspace_settings.name = cs; return t
    nt.links.new(ti('BaseColor', 'sRGB').outputs[0], bs.inputs['Base Color'])
    sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(ti('ORM', 'Non-Color').outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], bs.inputs['Roughness']); nt.links.new(sp.outputs[2], bs.inputs['Metallic'])
    sn = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(ti('Normal_DirectX', 'Non-Color').outputs[0], sn.inputs[0])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(sn.outputs[1], inv.inputs[1])
    cc = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(sn.outputs[0], cc.inputs[0]); nt.links.new(inv.outputs[0], cc.inputs[1]); nt.links.new(sn.outputs[2], cc.inputs[2])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(cc.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
    for o in set(bpy.data.objects) - before:
        if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(cm)
    TGT = mathutils.Vector((0.10, 0.0, 1.26))
def light(name, loc, energy, size, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = TGT + mathutils.Vector(loc)
    o.rotation_euler = (TGT - o.location).to_track_quat('-Z', 'Y').to_euler()
light('Key', (-0.9, -1.1, 0.7), 220, 0.9, (1.0, 0.95, 0.88))
light('Fill', (1.1, -0.6, 0.2), 60, 1.2, (0.8, 0.88, 1.0))
light('Rim', (0.4, 1.2, 0.8), 180, 0.6, (0.85, 0.9, 1.0))
light('Top', (0, 0, 1.2), 60, 1.0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 70
views = {'front34': (-40, 10, 1.25), 'side': (90, 6, 1.1), 'front': (0, 4, 1.4), 'back34': (140, 12, 1.25)}
for name, (az, el, d) in views.items():
    a, e = math.radians(az - 90), math.radians(el)
    cam.location = (TGT.x + d * math.cos(e) * math.cos(a), TGT.y + d * math.cos(e) * math.sin(a), TGT.z + d * math.sin(e))
    cam.rotation_euler = (TGT - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)
