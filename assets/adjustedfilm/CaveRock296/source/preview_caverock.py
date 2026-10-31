# #296 lookdev preview of M_CaveRock (adjustedfilm, 2026-10-31): the same height / mask / colour / roughness logic as the
# HLSL in handoffs/cave-296-297/setup_caverock296_ue.py, ported to OSL, on a box tunnel like the East Front tunnel
# (flat boxes: 3 m wide, 2.8 m high). Torch-lit (1900 K) with a 0.18 grey ball for exposure. Preview only, not the engine.
#   blender -b --factory-startup -P preview_caverock.py -- <out_dir> [natural|mine|both]
import bpy, math, os, sys

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else '.')
WHICH = argv[1] if len(argv) > 1 else 'both'
os.makedirs(OUT, exist_ok=True)

OSL = r'''
float h1(point q) { point p = q * 0.3183099 + 0.1; p = p - floor(p); p *= 17.0; float v = p[0] * p[1] * p[2] * (p[0] + p[1] + p[2]); return v - floor(v); }
float vn(point x) {
  point i = floor(x); vector f = x - i; f = f * f * (3.0 - 2.0 * f);
  float a = mix(mix(h1(i), h1(i + vector(1,0,0)), f[0]), mix(h1(i + vector(0,1,0)), h1(i + vector(1,1,0)), f[0]), f[1]);
  float b = mix(mix(h1(i + vector(0,0,1)), h1(i + vector(1,0,1)), f[0]), mix(h1(i + vector(0,1,1)), h1(i + vector(1,1,1)), f[0]), f[1]);
  return mix(a, b, f[2]);
}
float fbm(point q) { point p = q; float a = 0.5, s = 0.0; for (int o = 0; o < 4; o++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s / 0.9375; }
float ridge(point q) { point p = q; float a = 0.5, s = 0.0; for (int o = 0; o < 3; o++) { float r = 1.0 - abs(vn(p) * 2.0 - 1.0); s += a * r * r; p = p * 2.11 + 5.3; a *= 0.5; } return s / 0.875; }
float cell(point x, output float id) {
  point i = floor(x); vector f = x - i; float d1 = 8.0, d2 = 8.0; id = 0.0;
  for (int a = -1; a <= 1; a++) for (int b = -1; b <= 1; b++) for (int c = -1; c <= 1; c++) {
    vector o = vector(a, b, c); point q = i + o;
    vector r = o + vector(h1(q), h1(q + 19.19), h1(q + 47.3)) - f; float d = dot(r, r);
    if (d < d1) { d2 = d1; d1 = d; id = h1(q + 71.7); } else if (d < d2) { d2 = d; }
  }
  return sqrt(d2) - sqrt(d1);
}
float hgt(point w, float sc, float strataCm, float sharp) {
  point p = w / sc;
  float big = fbm(p);
  float lay = w[2] / max(strataCm, 1.0) + fbm(p * 0.4) * 1.6;      // limestone beds, warped
  float ledge = lay - floor(lay);                                    // sawtooth = each bed overhangs the one below
  ledge = smoothstep(0.0, 0.12, ledge) * (1.0 - ledge * 0.6);
  float bid; float e1 = cell(p * 2.2 + vn(p * 3.0) * 0.35, bid);   // angular fracture blocks
  float fid; float e2 = cell(p * 7.0 + 11.3, fid);                  // finer cracks
  float crk = ((1.0 - smoothstep(0.0, 0.035, e1)) + (1.0 - smoothstep(0.0, 0.02, e2)) * 0.3) * smoothstep(0.45, 0.62, vn(p * 1.3 + 2.2));   // broken, not closed polygons
  float block = (bid - 0.5) * 0.22 + smoothstep(0.0, 0.25, e1) * 0.1;   // each block its own plane, edges rounded
  float grain = fbm(w / 2.2);                                        // centimetre grain
  return big * 0.55 + ledge * 0.25 * sharp + block * 0.6 * sharp - crk * 0.18 * sharp + grain * 0.12;
}
shader caverock(float Scale = 140, float Strata = 38, float Sharp = 1, float Wetness = 1, float WetHeight = 0.35,
  float DripAmt = 0.6, float PuddleAmt = 0.8, float Porosity = 0.9, float Soot = 0, float Iron = 0.3, float Calcite = 0.3,
  float Moss = 0, float MossRadius = 1500, point MossOrigin = point(0, 0, 0), float ZMin = 0, float ZMax = 280,
  color RockA = color(0.075, 0.068, 0.058), color RockB = color(0.24, 0.215, 0.18),
  output color Col = 0, output float Rough = 0.5, output float Height = 0) {
  point W = P * 100.0;                                   // metres -> cm, like UE
  float H = hgt(W, Scale, Strata, Sharp);
  Height = H;
  vector Nn = normalize(Ng);
  float up = max(Nn[2], 0.0), dn = max(-Nn[2], 0.0), side = 1.0 - max(up, dn);
  float hb = clamp((W[2] - ZMin) / max(ZMax - ZMin, 1.0), 0.0, 1.0);
  float streak = smoothstep(0.58, 0.8, vn(point(W[0] / 35.0, W[1] / 35.0, W[2] / 700.0)));
  float band = clamp(1.0 - hb / max(WetHeight, 0.01), 0.0, 1.0) * side;
  band = band * band;
  float puddle = smoothstep(0.55, 0.62, vn(W / 260.0) * 0.6 + (1.0 - H) * 0.55) * up * PuddleAmt;
  float wet = clamp(max(max(band, up * 0.45), (streak * side + dn * 0.35) * DripAmt), 0.0, 1.0) * Wetness;
  wet = max(wet, puddle);
  float soot = clamp(dn * 1.2 + side * smoothstep(0.65, 1.0, hb) * 0.6, 0.0, 1.0) * Soot * (0.7 + 0.3 * vn(W / 90.0));
  float iron = smoothstep(0.72, 0.86, vn(point(W[0] / 22.0, W[1] / 22.0, W[2] / 500.0) + 3.7)) * side * Iron;
  float calcite = streak * side * Calcite * smoothstep(0.3, 0.7, vn(W / 120.0 + 9.1));
  float nearm = clamp(1.0 - distance(W, MossOrigin) / max(MossRadius, 1.0), 0.0, 1.0);
  float moss = nearm * clamp(Nn[2] + 0.35, 0.0, 1.0) * Moss * smoothstep(0.42, 0.6, vn(W / 55.0) * 0.6 + H * 0.5);
  float t = clamp(H * 1.5 - 0.25, 0.0, 1.0);
  color c = mix(RockA, RockB, t);
  c *= mix(0.82, 1.15, h1(point(floor(W[2] / max(Strata, 1.0) + fbm(W / Scale * 0.4) * 1.6), 3.1, 7.7)));   // each bed its own tone
  float bid2; float ee = cell(W / Scale * 2.2 + vn(W / Scale * 3.0) * 0.35, bid2);
  c *= mix(0.86, 1.12, bid2);                                        // blocks differ slightly in tone
  c *= mix(0.75, 1.0, smoothstep(0.0, 0.04, ee));                    // grit / dirt in the cracks
  c *= mix(0.72, 1.0, clamp(H * 2.2, 0.0, 1.0));
  c = mix(c, color(0.45, 0.43, 0.39), calcite);
  c = mix(c, color(0.16, 0.065, 0.022), iron);
  c = mix(c, color(0.035, 0.05, 0.014), moss);
  c = mix(c, color(0.014, 0.013, 0.012), soot);
  c *= mix(1.0, 0.5, clamp(Porosity * wet, 0.0, 1.0));
  Col = max(c, color(0.0127));
  float r = mix(0.9, 0.68, clamp(H, 0.0, 1.0));
  r = mix(r, 0.6, moss * 0.5);
  r = mix(r, 0.95, soot);
  r = mix(r, r * 0.42, wet);
  Rough = mix(r, 0.06, puddle);
}
'''

INST = {
    'natural': dict(Sharp=1.0, Bump=1.1, Iron=0.35, Calcite=0.35, Moss=0.6, Soot=0.0, Scale=140.0, Wetness=1.0, DripAmt=0.6),
    'mine': dict(Sharp=0.35, Bump=0.55, Scale=110.0, Soot=0.6, Iron=0.2, Calcite=0.1, Wetness=0.7, DripAmt=0.4, Moss=0.0),
}


def scene(kind):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.shading_system = True
    sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0      # locked
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    txt = bpy.data.texts.new('caverock.osl'); txt.write(OSL)
    p = INST[kind]

    def rockmat(name, floor=False):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        s = nt.nodes.new('ShaderNodeScript'); s.mode = 'INTERNAL'; s.script = txt
        vals = dict(p)
        if floor: vals.update(Sharp=0.5, Scale=90.0, PuddleAmt=1.0, Wetness=1.0, Iron=0.0, Calcite=0.0)
        for k, v in vals.items():
            if k in s.inputs: s.inputs[k].default_value = v
        if kind == 'natural' and 'MossOrigin' in s.inputs: s.inputs['MossOrigin'].default_value = (0.0, 1400.0, 0.0)   # tunnel mouth
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = 0.06 * vals.get('Bump', 1.0)
        nt.links.new(s.outputs['Height'], bump.inputs['Height'])
        nt.links.new(s.outputs['Col'], bsdf.inputs['Base Color']); nt.links.new(s.outputs['Rough'], bsdf.inputs['Roughness'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        bsdf.inputs['Specular IOR Level'].default_value = 0.5
        nt.links.new(bsdf.outputs[0], out.inputs[0]); return m

    wall, flr = rockmat('Rock'), rockmat('Floor', True)

    def box(name, loc, dims, mat):
        bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name
        o.scale = (dims[0] / 2, dims[1] / 2, dims[2] / 2); bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat); return o
    L = 14.0
    box('Floor', (0, L / 2, -0.15), (3.4, L, 0.3), flr)
    box('WallL', (-1.65, L / 2, 1.4), (0.3, L, 3.0), wall)
    box('WallR', (1.65, L / 2, 1.4), (0.3, L, 3.0), wall)
    box('Ceil', (0, L / 2, 2.95), (3.4, L, 0.3), wall)
    # grey ball (albedo 0.18) for exposure
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.7, 2.2, 0.12)); g = bpy.context.object
    gm = bpy.data.materials.new('Grey'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6; g.data.materials.append(gm)
    bpy.ops.object.shade_smooth()

    def torch(loc, wpow):
        bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.object.data
        l.energy = wpow; l.color = (1.0, 0.52, 0.22); l.shadow_soft_size = 0.06       # ~1900 K flame
    torch((-1.35, 3.0, 1.75), 90); torch((1.35, 9.5, 1.75), 90)
    if kind == 'natural':   # daylight from the mouth at the far end, cool
        bpy.ops.object.light_add(type='AREA', location=(0, L + 0.5, 1.4), rotation=(math.radians(-90), 0, 0))
        a = bpy.context.object.data; a.size = 3.0; a.energy = 40; a.color = (0.75, 0.85, 1.0)
    else:                   # a lantern down the tunnel
        torch((0.0, 12.5, 2.3), 35)
    bpy.ops.object.camera_add(location=(0.2, 0.25, 1.6), rotation=(math.radians(88), 0, math.radians(-3)))
    cam = bpy.context.object; cam.data.lens = 22; sc.camera = cam
    sc.render.filepath = os.path.join(OUT, 'caverock_%s.png' % kind)
    bpy.ops.render.render(write_still=True)
    print('wrote', sc.render.filepath)


for k_ in (['natural', 'mine'] if WHICH == 'both' else [WHICH]):
    scene(k_)
