# #293 part 2 lookdev of M_FleshSlime on the real SM_Flora_BlobMine (adjustedfilm, 2026-10-31). Rules from
# handoffs/blob-realism-293/RESEARCH.md: dark organics (albedo 0.03-0.15), wet 0.05-0.15 / tacky 0.35-0.5 roughness
# patches, life through subsurface (not emission), one faint danger cue (veins pulse). Same logic as the UE HLSL.
#   blender -b --factory-startup -P preview_flesh.py -- <fbx> <out.png> [pulse 0..1]
import bpy, math, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
FBX, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
PULSE = float(argv[2]) if len(argv) > 2 else 0.5

OSL = r'''
float h1(point q) { point p = q * 0.3183099 + 0.1; p = p - floor(p); p *= 17.0; float v = p[0] * p[1] * p[2] * (p[0] + p[1] + p[2]); return v - floor(v); }
float vn(point x) {
  point i = floor(x); vector f = x - i; f = f * f * (3.0 - 2.0 * f);
  float a = mix(mix(h1(i), h1(i + vector(1,0,0)), f[0]), mix(h1(i + vector(0,1,0)), h1(i + vector(1,1,0)), f[0]), f[1]);
  float b = mix(mix(h1(i + vector(0,0,1)), h1(i + vector(1,0,1)), f[0]), mix(h1(i + vector(0,1,1)), h1(i + vector(1,1,1)), f[0]), f[1]);
  return mix(a, b, f[2]);
}
float fbm(point q) { point p = q; float a = 0.5, s = 0.0; for (int o = 0; o < 4; o++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s / 0.9375; }
float veins(point w, float vs) {
  point p = w / vs;
  point q = p + vector(fbm(p * 0.7), fbm(p * 0.7 + 5.2), fbm(p * 0.7 + 9.4)) * 1.8;   // domain warp
  float v = 1.0 - abs(vn(q) * 2.0 - 1.0);
  float v2 = 1.0 - abs(vn(q * 2.3 + 3.3) * 2.0 - 1.0);
  return pow(v, 9.0) + pow(v2, 12.0) * 0.6;
}
shader flesh(float LumpCm = 3.5, float VeinCm = 4, float Rot = 0.7, float WetAmt = 0.6, float Pulse = 0.5,
  color FleshA = color(0.055, 0.02, 0.02), color FleshB = color(0.11, 0.05, 0.042), color RotCol = color(0.055, 0.06, 0.03),
  color VeinCol = color(0.03, 0.008, 0.02),
  output color Col = 0, output float Rough = 0.4, output float Height = 0, output color SSS = 0, output float VeinM = 0) {
  point W = P * 100.0;
  float lump = fbm(W / LumpCm);
  float vm = clamp(veins(W, VeinCm), 0.0, 1.0);
  float pores = fbm(W / 0.7);
  Height = lump * 0.45 + vm * 0.55 + pores * 0.1 + fbm(W / 12.0) * 0.4;
  VeinM = vm;
  color c = mix(FleshA, FleshB, smoothstep(0.3, 0.75, lump));
  float rot = smoothstep(0.55, 0.75, fbm(W / 25.0 + 4.4)) * Rot;
  c = mix(c, RotCol, rot);
  c = mix(c, VeinCol, vm * 0.7);
  float wet = smoothstep(0.55, 0.68, fbm(W / 14.0 + 1.3)) * WetAmt;
  c *= mix(1.0, 0.8, wet);
  Col = max(c, color(0.012));
  Rough = mix(mix(0.42, 0.48, pores), mix(0.07, 0.12, pores), wet);      // tacky vs wet patches
  SSS = color(0.55, 0.05, 0.035) * (0.55 + 0.45 * Pulse) * mix(1.0, 1.6, vm);
}
'''

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.shading_system = True
sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 1280
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.02
bpy.ops.import_scene.fbx(filepath=FBX)
objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
txt = bpy.data.texts.new('flesh.osl'); txt.write(OSL)
m = bpy.data.materials.new('Flesh'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
s = nt.nodes.new('ShaderNodeScript'); s.mode = 'INTERNAL'; s.script = txt
s.inputs['Pulse'].default_value = PULSE
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = 0.02
nt.links.new(s.outputs['Height'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
nt.links.new(s.outputs['Col'], bsdf.inputs['Base Color']); nt.links.new(s.outputs['Rough'], bsdf.inputs['Roughness'])
bsdf.inputs['Subsurface Weight'].default_value = 0.35
bsdf.inputs['Subsurface Radius'].default_value = (1.2, 0.25, 0.15)
bsdf.inputs['Subsurface Scale'].default_value = 0.012
nt.links.new(s.outputs['SSS'], bsdf.inputs['Emission Color'])            # faint danger cue in the veins only
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.02 * PULSE
nt.links.new(s.outputs['VeinM'], mul.inputs[0]); nt.links.new(mul.outputs[0], bsdf.inputs['Emission Strength'])
bsdf.inputs['Specular IOR Level'].default_value = 0.4
nt.links.new(bsdf.outputs[0], out.inputs[0])
for o in objs:
    o.data.materials.clear(); o.data.materials.append(m)
# frame: bounds of the mesh
import mathutils
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
ctr, R = (lo + hi) / 2, (hi - lo).length / 2
R = R if R > 0 else 1
bpy.ops.mesh.primitive_plane_add(size=R * 10, location=(ctr.x, ctr.y, lo.z))
g = bpy.context.object; gm = bpy.data.materials.new('Ground'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.075, 0.06, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85; g.data.materials.append(gm)
bpy.ops.mesh.primitive_uv_sphere_add(radius=R * 0.12, location=(ctr.x + R * 1.1, ctr.y - R * 0.6, lo.z + R * 0.12)); gb = bpy.context.object
gr = bpy.data.materials.new('Grey'); gr.use_nodes = True; gr.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1)
gb.data.materials.append(gr); bpy.ops.object.shade_smooth()


def light(kind, loc, energy, col, size):
    bpy.ops.object.light_add(type=kind, location=loc); l = bpy.context.object
    l.data.energy = energy; l.data.color = col
    if kind == 'AREA': l.data.size = size
    d = ctr - l.location; l.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
light('AREA', ctr + mathutils.Vector((R * 2.5, -R * 2.5, R * 2.2)), 150 * R * R, (1.0, 0.85, 0.7), R * 1.5)     # warm key
light('AREA', ctr + mathutils.Vector((-R * 2.0, R * 2.8, R * 1.2)), 260 * R * R, (0.7, 0.8, 1.0), R * 1.0)     # cool rim
light('AREA', ctr + mathutils.Vector((-R * 3.0, -R * 2.0, R * 0.5)), 30 * R * R, (0.9, 0.92, 1.0), R * 2.0)    # weak fill
bpy.ops.object.camera_add(location=ctr + mathutils.Vector((R * 1.6, -R * 2.6, R * 1.3)))
cam = bpy.context.object; cam.location = ctr + mathutils.Vector((R * 1.0, -R * 1.6, R * 0.9)); cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50; sc.camera = cam
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('wrote', OUT)
