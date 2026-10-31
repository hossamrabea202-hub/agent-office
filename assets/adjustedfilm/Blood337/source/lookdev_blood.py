# lookdev for #337 splats: ground + decal atlas, 0.18 grey ball, warm torch key, cool moon rim, locked exposure
import bpy, sys, math
a = sys.argv[sys.argv.index('--')+1:]
D, OUT, DRY = a[0], a[1], float(a[2])          # DRY 0 = fresh wet, 1 = dried (30 s)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.025, 0.035, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.4
bpy.ops.mesh.primitive_plane_add(size=1); g = bpy.context.active_object; g.scale = (1.6, 0.8, 1)
m = bpy.data.materials.new('ground'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
bs = N['Principled BSDF']
img = lambda f, cs: (lambda i: (setattr(i.colorspace_settings, 'name', cs), i)[1])(bpy.data.images.load(D + '/' + f))
tbc, tn, tm = N.new('ShaderNodeTexImage'), N.new('ShaderNodeTexImage'), N.new('ShaderNodeTexImage')
tbc.image, tn.image, tm.image = img('T_BloodSplat_337_BC.png', 'sRGB'), img('T_BloodSplat_337_N.png', 'Non-Color'), img('T_BloodSplat_337_M.png', 'Non-Color')
# ground: packed earth / worn stone, albedo ~ 0.16 linear with noise, rough 0.85
nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 18; nz.inputs['Detail'].default_value = 8
gr = N.new('ShaderNodeMapRange'); L.new(nz.outputs[0], gr.inputs[0]); gr.inputs[3].default_value = 0.10; gr.inputs[4].default_value = 0.22
gcol = N.new('ShaderNodeCombineColor'); [L.new(gr.outputs[0], gcol.inputs[i]) for i in range(3)]
gtint = N.new('ShaderNodeMix'); gtint.data_type = 'RGBA'; gtint.blend_type = 'MULTIPLY'; gtint.inputs[0].default_value = 1
L.new(gcol.outputs[0], gtint.inputs[6]); gtint.inputs[7].default_value = (1.0, 0.9, 0.78, 1)
sep = N.new('ShaderNodeSeparateColor'); L.new(tm.outputs[0], sep.inputs[0])
op = tbc.outputs['Alpha']
# blood colour: dried shifts to brown 45,30,20 and darkens the rim
dried = (0.026, 0.013, 0.007, 1)
bcol = N.new('ShaderNodeMix'); bcol.data_type = 'RGBA'; bcol.inputs[0].default_value = DRY * 0.75
L.new(tbc.outputs['Color'], bcol.inputs[6]); bcol.inputs[7].default_value = dried
mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; L.new(op, mix.inputs[0]); L.new(gtint.outputs[2], mix.inputs[6]); L.new(bcol.outputs[2], mix.inputs[7])
L.new(mix.outputs[2], bs.inputs['Base Color'])
# roughness: wet 0.08 (thin film edges 0.15) -> dried 0.7; ground 0.85
br = N.new('ShaderNodeMapRange'); L.new(sep.outputs[0], br.inputs[0]); br.inputs[3].default_value = 0.16 + DRY * 0.55; br.inputs[4].default_value = 0.08 + DRY * 0.55
rmix = N.new('ShaderNodeMix'); L.new(op, rmix.inputs[0]); rmix.inputs[2].default_value = 0.85; L.new(br.outputs[0], rmix.inputs[3])
L.new(rmix.outputs[0], bs.inputs['Roughness'])
imix = N.new('ShaderNodeMix'); L.new(op, imix.inputs[0]); imix.inputs[2].default_value = 1.5; imix.inputs[3].default_value = 1.35
L.new(imix.outputs[0], bs.inputs['IOR'])
nm = N.new('ShaderNodeNormalMap'); L.new(tn.outputs[0], nm.inputs['Color']); nm.inputs['Strength'].default_value = 1.0 - DRY * 0.6
bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.3; L.new(nz.outputs[0], bump.inputs['Height'])
nmix = N.new('ShaderNodeMix'); nmix.data_type = 'VECTOR'; L.new(op, nmix.inputs[0]); L.new(bump.outputs[0], nmix.inputs[4]); L.new(nm.outputs[0], nmix.inputs[5])
L.new(nmix.outputs[1], bs.inputs['Normal'])
g.data.materials.append(m)
# 0.18 grey ball (KB lookdev) and a 20 cm ruler reference cube
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0.62, 0.48, 0.08)); bpy.ops.object.shade_smooth()
gm = bpy.data.materials.new('grey'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.5; bpy.context.active_object.data.materials.append(gm)
# torch key ~1800 K, cool moon rim
bpy.ops.object.light_add(type='POINT', location=(-0.9, -0.6, 0.9)); t = bpy.context.active_object; t.data.energy = 90; t.data.color = (1.0, 0.52, 0.22); t.data.shadow_soft_size = 0.05
bpy.ops.object.light_add(type='SUN', location=(0, 0, 3), rotation=(math.radians(60), 0, math.radians(160))); s = bpy.context.active_object; s.data.energy = 0.25; s.data.color = (0.6, 0.72, 1.0)
bpy.ops.object.camera_add(location=(0.0, -1.35, 1.05), rotation=(math.radians(52), 0, 0)); sc.camera = bpy.context.active_object; sc.camera.data.lens = 32
sc.render.filepath = OUT; sc.render.image_settings.file_format = 'JPEG'; bpy.ops.render.render(write_still=True)
