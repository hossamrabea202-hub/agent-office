"""WinterKeep #390: Blender lookdev of the generated terrain (not the game; a fast check of land, layers and light).

blender -b --factory-startup -P render_winterkeep.py -- --preset lowsun|overcast|blizzard|night --shot aerial|gate|top|lake
        [--res 1600] [--samples 48] [--step 2] [--out <png>]

Values follow the knowledge base: snow albedo 0.80-0.85 linear (never 1.0), scoured rock 0.07, wet realm ground 0.03,
clear lake ice dark (you see the deep water through it) with white cracks and frosted edges, castle limewashed (0.42).
Exposure is LOCKED per preset (a fixed number, never auto), so presets can be compared.
"""
import bpy, json, math, os, sys
import numpy as np

A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d): return A[A.index(k) + 1] if k in A else d
PRESET, SHOT = arg('--preset', 'lowsun'), arg('--shot', 'aerial')
RES, SAMPLES, STEP = int(arg('--res', '1600')), int(arg('--samples', '48')), int(arg('--step', '2'))
HERE = os.path.dirname(os.path.abspath(__file__))
TER = os.path.join(HERE, '..', 'terrain', 'out')
OUTP = arg('--out', os.path.join(HERE, 'shots', '%s_%s.png' % (SHOT, PRESET)))
os.makedirs(os.path.dirname(OUTP), exist_ok=True)
L = json.load(open(os.path.join(TER, 'layout.json')))
H = np.load(os.path.join(TER, 'height_m.npy')); N = H.shape[0]; HALF = (N - 1) / 2
LAY = np.load(os.path.join(TER, 'layers.npz'))
rng = np.random.default_rng(390)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def to_b(x, y, z):            # image metres -> Blender (X east, Y north, Z up)
    return (x - HALF, HALF - y, z)
def ue_to_img(p):             # UE cm (X east, Y south) -> image metres
    return (p[0] / 100 + HALF, p[1] / 100 + HALF, p[2] / 100)
def hz(x, y): return float(H[int(np.clip(y, 0, N - 1)), int(np.clip(x, 0, N - 1))])

# ------------------------------------------------------------------ terrain mesh with layer attributes
def terrain():
    s = STEP; hs = H[::s, ::s]; n = hs.shape[0]
    ys, xs = np.mgrid[0:n, 0:n]
    co = np.stack([xs * s - HALF, HALF - ys * s, hs], -1).reshape(-1, 3).astype(np.float32)
    me = bpy.data.meshes.new('Terrain'); me.vertices.add(n * n); me.vertices.foreach_set('co', co.ravel())
    q = (ys[:-1, :-1] * n + xs[:-1, :-1]).ravel()
    loops = np.stack([q, q + n, q + n + 1, q + 1], -1).ravel()
    nf = len(q); me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', loops.astype(np.int32))
    me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, nf * 4, 4, dtype=np.int32))
    me.update(calc_edges=True); me.validate()
    me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
    for k in ['Snow_Fresh', 'Snow_Packed', 'Rock_Scoured', 'Ice', 'FrozenMud', 'ForestFloor', 'Road', 'RealmMelt', 'M_WindExposure', 'M_Drift']:
        a = me.attributes.new(k, 'FLOAT', 'POINT'); a.data.foreach_set('value', (LAY[k][::s, ::s].astype(np.float32) / 255).ravel())
    ob = bpy.data.objects.new('Terrain', me); sc.collection.objects.link(ob); return ob

# ------------------------------------------------------------------ materials
def nodes(mat):
    mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear(); return nt, nt.nodes, nt.links
def principled(nd, col, rough, **kw):
    p = nd.new('ShaderNodeBsdfPrincipled'); p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    for k, v in kw.items(): p.inputs[k].default_value = v
    return p
def attr(nd, name):
    a = nd.new('ShaderNodeAttribute'); a.attribute_name = name; return a.outputs['Fac']

def snow_bsdf(nd, ln, tint=(0.80, 0.82, 0.85), rough=0.62):
    """Snow: albedo ~0.82 (not white), strong forward scatter -> subsurface, tiny grazing sparkle via a 2nd lobe."""
    p = principled(nd, tint, rough, **{'Subsurface Weight': 0.25, 'Subsurface Scale': 0.02})
    p.inputs['Subsurface Radius'].default_value = (0.9, 1.0, 1.25)          # blue goes deepest in real snow
    # sparkle: sharp coat lobe masked by fine noise, weak (rule: only at grazing angles, subtle)
    nz = nd.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 0
    mr = nd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.72; mr.inputs['From Max'].default_value = 0.78
    mr.inputs['To Max'].default_value = 0.35
    ln.new(nz.outputs['Fac'], mr.inputs['Value']); ln.new(mr.outputs['Result'], p.inputs['Coat Weight'])
    p.inputs['Coat Roughness'].default_value = 0.03
    return p

def mat_terrain():
    m = bpy.data.materials.new('M_WinterLandscape_Lookdev'); nt, nd, ln = nodes(m)
    out = nd.new('ShaderNodeOutputMaterial')
    # macro variation: wind-packed snow is slightly greyer and smoother; fresh drift brighter and rougher
    macro = nd.new('ShaderNodeTexNoise'); macro.inputs['Scale'].default_value = 0.02; macro.inputs['Detail'].default_value = 4
    tc = nd.new('ShaderNodeTexCoord'); ln.new(tc.outputs['Object'], macro.inputs['Vector'])
    fresh = snow_bsdf(nd, ln, (0.80, 0.82, 0.86), 0.68)
    packed = snow_bsdf(nd, ln, (0.66, 0.68, 0.72), 0.50)
    rock = principled(nd, (0.065, 0.068, 0.072), 0.82)
    # rock: rime and snow caught in cracks, top-mask snow on flat ledges
    rnz = nd.new('ShaderNodeTexNoise'); rnz.inputs['Scale'].default_value = 0.6; rnz.inputs['Detail'].default_value = 8
    rmr = nd.new('ShaderNodeMapRange'); rmr.inputs['From Min'].default_value = 0.5; rmr.inputs['From Max'].default_value = 0.7
    rmr.inputs['To Min'].default_value = 0.05; rmr.inputs['To Max'].default_value = 0.45
    ln.new(rnz.outputs['Fac'], rmr.inputs['Value'])
    rockmix = nd.new('ShaderNodeMixRGB'); rockmix.inputs['Color1'].default_value = (0.055, 0.058, 0.062, 1); rockmix.inputs['Color2'].default_value = (0.55, 0.58, 0.62, 1)
    ln.new(rmr.outputs['Result'], rockmix.inputs['Fac']); ln.new(rockmix.outputs['Color'], rock.inputs['Base Color'])
    # lake / river ice: dark (clear ice over deep water), glossy, white cracks + bubbles scatter light
    ice = principled(nd, (0.012, 0.018, 0.024), 0.06, **{'IOR': 1.31})
    vor = nd.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 0.08
    cr = nd.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.0; cr.inputs['From Max'].default_value = 0.025
    cr.inputs['To Min'].default_value = 1; cr.inputs['To Max'].default_value = 0
    ln.new(vor.outputs['Distance'], cr.inputs['Value'])
    icecol = nd.new('ShaderNodeMixRGB'); icecol.inputs['Color1'].default_value = (0.012, 0.018, 0.024, 1); icecol.inputs['Color2'].default_value = (0.45, 0.5, 0.55, 1)
    ln.new(cr.outputs['Result'], icecol.inputs['Fac']); ln.new(icecol.outputs['Color'], ice.inputs['Base Color'])
    ln.new(cr.outputs['Result'], ice.inputs['Roughness'])
    mud = principled(nd, (0.075, 0.062, 0.05), 0.55)              # frozen mud ruts, slush gloss near the gate
    road = principled(nd, (0.36, 0.34, 0.32), 0.55)                # packed, dirty, rutted snow track
    floor = principled(nd, (0.56, 0.58, 0.60), 0.7)                # forest floor: thinner snow with needle litter
    realm = principled(nd, (0.022, 0.02, 0.02), 0.12)              # wet black ground (wet = darker + glossy)
    order = [(packed, 'Snow_Packed'), (rock, 'Rock_Scoured'), (ice, 'Ice'), (mud, 'FrozenMud'), (floor, 'ForestFloor'), (road, 'Road'), (realm, 'RealmMelt')]
    cur = fresh.outputs['BSDF']
    for sh, name in order:
        mx = nd.new('ShaderNodeMixShader'); ln.new(attr(nd, name), mx.inputs['Fac']); ln.new(cur, mx.inputs[1]); ln.new(sh.outputs['BSDF'], mx.inputs[2]); cur = mx.outputs['Shader']
    ln.new(cur, out.inputs['Surface'])
    # fine snow surface normal (wind ripples run across the wind)
    bump = nd.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.15
    wav = nd.new('ShaderNodeTexWave'); wav.inputs['Scale'].default_value = 0.6; wav.inputs['Distortion'].default_value = 6
    wav.bands_direction = 'DIAGONAL'; ln.new(wav.outputs['Fac'], bump.inputs['Height'])
    for sh in (fresh, packed): ln.new(bump.outputs['Normal'], sh.inputs['Normal'])
    return m

def mat_topsnow(name, base, rough, thresh=0.55):
    """Prop material + world-aligned top mask: snow only on up-facing surfaces (the MF_SnowCover idea)."""
    m = bpy.data.materials.new(name); nt, nd, ln = nodes(m); out = nd.new('ShaderNodeOutputMaterial')
    b = principled(nd, base, rough); s = snow_bsdf(nd, ln)
    geo = nd.new('ShaderNodeNewGeometry'); sep = nd.new('ShaderNodeSeparateXYZ'); ln.new(geo.outputs['Normal'], sep.inputs['Vector'])
    nz = nd.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3
    add = nd.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'; ln.new(nz.outputs['Fac'], add.inputs[0]); add.inputs[1].default_value = 0.3; ln.new(sep.outputs['Z'], add.inputs[2])
    mr = nd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = thresh; mr.inputs['From Max'].default_value = thresh + 0.12
    ln.new(add.outputs['Value'], mr.inputs['Value'])
    mx = nd.new('ShaderNodeMixShader'); ln.new(mr.outputs['Result'], mx.inputs['Fac']); ln.new(b.outputs['BSDF'], mx.inputs[1]); ln.new(s.outputs['BSDF'], mx.inputs[2])
    ln.new(mx.outputs['Shader'], out.inputs['Surface']); return m

# ------------------------------------------------------------------ trees (snow-loaded spruce, bare birch) via geometry nodes
def spruce_mesh():
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.022, radius2=0.015, depth=0.3, matrix=__import__('mathutils').Matrix.Translation((0, 0, 0.15)))
    tiers = 7
    for i in range(tiers):
        t = i / tiers; r = 0.19 * (1 - t) ** 1.05 + 0.02; z0 = 0.12 + 0.82 * t
        bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=r, radius2=0.01, depth=0.20 * (1 - 0.4 * t) + 0.05,
                              matrix=__import__('mathutils').Matrix.Translation((0, 0, z0 + 0.12)))
    me = bpy.data.meshes.new('Spruce'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('Spruce', me); sc.collection.objects.link(ob); ob.hide_render = True; ob.hide_viewport = True
    me.materials.append(mat_topsnow('M_Spruce_TopSnow', (0.018, 0.032, 0.024), 0.8, thresh=0.82)); return ob
def birch_mesh():
    import bmesh, mathutils
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.004, depth=1.0, matrix=mathutils.Matrix.Translation((0, 0, 0.5)))
    for i in range(9):
        a = i * 2.4; z = 0.35 + i * 0.07; m = mathutils.Matrix.Translation((0, 0, z)) @ mathutils.Matrix.Rotation(a, 4, 'Z') @ mathutils.Matrix.Rotation(0.75, 4, 'X') @ mathutils.Matrix.Translation((0, 0, 0.14))
        bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.006, radius2=0.001, depth=0.3 * (1 - i / 12), matrix=m)
    me = bpy.data.meshes.new('Birch'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('Birch', me); sc.collection.objects.link(ob); ob.hide_render = True; ob.hide_viewport = True
    me.materials.append(mat_topsnow('M_Birch', (0.42, 0.40, 0.37), 0.75, thresh=0.7)); return ob

def scatter(name, mask, density, proto, hmin, hmax, sink):
    """Points from a 0..255 mask (clumped by the mask itself), instanced with geometry nodes."""
    m = LAY['M_' + mask].astype(np.float32) / 255.0
    cell = 5
    ys, xs = np.mgrid[0:N - 1:cell, 0:N - 1:cell]
    xs = xs + rng.uniform(0, cell, xs.shape); ys = ys + rng.uniform(0, cell, ys.shape)
    xs = np.clip(xs, 0, N - 1.01); ys = np.clip(ys, 0, N - 1.01)
    p = m[ys.astype(int), xs.astype(int)] * density
    keep = rng.uniform(0, 1, p.shape) < p
    xs, ys = xs[keep], ys[keep]
    z = H[ys.astype(int), xs.astype(int)] - sink
    co = np.stack([xs - HALF, HALF - ys, z], -1).astype(np.float32)
    me = bpy.data.meshes.new(name + '_pts'); me.vertices.add(len(co)); me.vertices.foreach_set('co', co.ravel())
    sca = rng.uniform(hmin, hmax, len(co)).astype(np.float32); rot = rng.uniform(0, 6.283, len(co)).astype(np.float32)
    me.attributes.new('scale', 'FLOAT', 'POINT').data.foreach_set('value', sca)
    me.attributes.new('rot', 'FLOAT', 'POINT').data.foreach_set('value', rot)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    gn = bpy.data.node_groups.new(name + '_GN', 'GeometryNodeTree')
    gn.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    gn.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nd, ln = gn.nodes, gn.links
    gi = nd.new('NodeGroupInput'); go = nd.new('NodeGroupOutput')
    iop = nd.new('GeometryNodeInstanceOnPoints'); oi = nd.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = proto
    s_at = nd.new('GeometryNodeInputNamedAttribute'); s_at.data_type = 'FLOAT'; s_at.inputs['Name'].default_value = 'scale'
    r_at = nd.new('GeometryNodeInputNamedAttribute'); r_at.data_type = 'FLOAT'; r_at.inputs['Name'].default_value = 'rot'
    cx = nd.new('ShaderNodeCombineXYZ'); e2r = nd.new('FunctionNodeEulerToRotation')
    ln.new(gi.outputs[0], iop.inputs['Points']); ln.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    ln.new(s_at.outputs['Attribute'], iop.inputs['Scale']); ln.new(r_at.outputs['Attribute'], cx.inputs['Z'])
    ln.new(cx.outputs['Vector'], e2r.inputs['Euler']); ln.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    ln.new(iop.outputs['Instances'], go.inputs[0])
    mod = ob.modifiers.new('scatter', 'NODES'); mod.node_group = gn
    print('scatter', name, len(co)); return len(co)

# ------------------------------------------------------------------ castle stand-in (46 x 34.5 m box from #41), farms, bridge
def box(name, c, size, mat, rotz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.active_object; o.name = name
    o.scale = size; o.rotation_euler[2] = rotz; o.data.materials.append(mat); return o
def cyl(name, c, r, hgt, mat, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=hgt, location=c); o = bpy.context.active_object; o.name = name
    o.data.materials.append(mat); return o
def castle():
    lime = mat_topsnow('M_Limewash_TopSnow', (0.40, 0.39, 0.36), 0.85)    # castles were whitewashed; 0.40, never white
    roof = mat_topsnow('M_Roof_TopSnow', (0.08, 0.07, 0.065), 0.7, thresh=0.3)
    cx, cy, cz = ue_to_img(L['castle_centre']); bx, by, _ = to_b(cx, cy, cz)
    W, D, Hh = 46, 34.5, 11
    for (dx, dy, sx, sy) in ((0, D / 2, W, 3.2), (0, -D / 2, W, 3.2), (W / 2, 0, 3.2, D), (-W / 2, 0, 3.2, D)):
        box('Wall', (bx + dx, by + dy, cz + Hh / 2 - 2), (sx, sy, Hh + 4), lime)
    for (dx, dy) in ((W / 2, D / 2), (-W / 2, D / 2), (W / 2, -D / 2), (-W / 2, -D / 2)):
        cyl('Tower', (bx + dx, by + dy, cz + 8 - 2), 4.5, 20, lime)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=5.2, depth=6, location=(bx + dx, by + dy, cz + 21)); o = bpy.context.active_object; o.data.materials.append(roof)
    box('Keep', (bx - 6, by + 3, cz + 11 - 2), (16, 14, 26), lime)
    box('KeepRoof', (bx - 6, by + 3, cz + 25), (17, 15, 2), roof)
    gx, gy, gz = ue_to_img(L['gate']); g = to_b(gx, gy, cz)
    box('Gatehouse', (g[0] - 4, g[1] + 4, cz + 7), (10, 9, 16), lime)        # behind the camera on the wall-walk
    for name, p in L['farms'].items():
        fx, fy, fz = ue_to_img(p); f = to_b(fx, fy, fz)
        wood = mat_topsnow('M_FarmWood', (0.13, 0.11, 0.09), 0.85)
        o = box(name, (f[0], f[1], fz + 1.2), (12, 7, 4.5), wood, rotz=0.4)
        r = box(name + '_roof', (f[0], f[1], fz + 4.2), (13, 8.5, 0.6), roof, rotz=0.4); r.rotation_euler[0] = 0.0
        # drift: buried to the eaves on the lee (SE) side
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(f[0] + 5, f[1] - 5, fz)); d = bpy.context.active_object
        d.scale = (9, 5, 2.6); d.rotation_euler[2] = -0.7; d.data.materials.append(bpy.data.materials['M_WinterLandscape_Lookdev'] if False else mat_topsnow('M_Drift', (0.8, 0.82, 0.85), 0.7, thresh=-2))
    bx_, by_, bz_ = ue_to_img(L['bridge']); b = to_b(bx_, by_, bz_)
    stone = mat_topsnow('M_BridgeStone', (0.22, 0.21, 0.2), 0.85)
    rs = np.array(L['road_spline_cm']) / 100.0; k = int(np.argmin(np.hypot(rs[:, 0] - L['bridge'][0] / 100, rs[:, 1] - L['bridge'][1] / 100)))
    d = rs[min(k + 1, len(rs) - 1)] - rs[max(k - 1, 0)]                  # road direction at the bridge (UE: x east, y south)
    yaw = math.atan2(-d[1], d[0])                                        # Blender: y north
    br = box('Bridge', (b[0], b[1], bz_ - 0.6), (52, 6.5, 1.6), stone, rotz=yaw)        # deck along the road, spans the banks
    for side in (-1, 1):
        pr = box('BridgeParapet', (b[0] - math.sin(yaw) * side * 3.0, b[1] + math.cos(yaw) * side * 3.0, bz_ + 0.6), (52, 0.5, 1.0), stone, rotz=yaw)
    pier = box('BridgePier', (b[0], b[1], bz_ - 14), (4, 5.5, 26), stone, rotz=yaw)
    # frozen waterfall: an icy curtain on the rock step
    fx, fy, fz = ue_to_img(L['frozen_falls']); f = to_b(fx, fy + 4, fz - 6)
    icem = bpy.data.materials.new('M_FallsIce'); nt, nd, ln = nodes(icem); o = nd.new('ShaderNodeOutputMaterial')
    p = principled(nd, (0.5, 0.6, 0.66), 0.25, **{'Subsurface Weight': 0.6, 'Subsurface Scale': 0.5}); ln.new(p.outputs['BSDF'], o.inputs['Surface'])
    box('FrozenFalls', f, (16, 3, 14), icem)

def realm_steam():
    rx, ry, rz = ue_to_img(L['realm_melt']['centre']); c = to_b(rx, ry, rz + 20); r = L['realm_melt']['radius_m']
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=c); s = bpy.context.active_object; s.name = 'RealmSteam'; s.scale = (r * 0.8, r * 0.8, 35)
    m = bpy.data.materials.new('M_Steam'); nt, nd, ln = nodes(m); o = nd.new('ShaderNodeOutputMaterial')
    v = nd.new('ShaderNodeVolumePrincipled'); v.inputs['Color'].default_value = (0.75, 0.78, 0.8, 1)
    nz = nd.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 6
    grad = nd.new('ShaderNodeTexGradient'); grad.gradient_type = 'SPHERICAL'
    mul = nd.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; ln.new(nz.outputs['Fac'], mul.inputs[0]); ln.new(grad.outputs['Fac'], mul.inputs[1])
    mr = nd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.15; mr.inputs['To Max'].default_value = 0.035
    ln.new(mul.outputs['Value'], mr.inputs['Value']); ln.new(mr.outputs['Result'], v.inputs['Density'])
    ln.new(v.outputs['Volume'], o.inputs['Volume']); s.data.materials.append(m)
    # the tentacle realm stand-in: a low dark wet mound with ribs (the game has the real one)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=to_b(rx, ry, rz - 4)); d = bpy.context.active_object; d.scale = (26, 26, 12)
    dm = bpy.data.materials.new('M_RealmStandIn'); nt, nd, ln = nodes(dm); o = nd.new('ShaderNodeOutputMaterial')
    p = principled(nd, (0.03, 0.012, 0.02), 0.15, **{'Subsurface Weight': 0.3, 'Subsurface Scale': 0.4}); ln.new(p.outputs['BSDF'], o.inputs['Surface']); d.data.materials.append(dm)

# ------------------------------------------------------------------ light presets (locked exposure per preset)
def world(preset):
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; nt = w.node_tree; nd, ln = nt.nodes, nt.links; nd.clear()
    out = nd.new('ShaderNodeOutputWorld'); bg = nd.new('ShaderNodeBackground'); ln.new(bg.outputs['Background'], out.inputs['Surface'])
    sun = None
    if preset == 'lowsun':
        sky = nd.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(9); sky.sun_rotation = math.radians(215)
        sky.altitude = 900; sky.air_density = 1.0; sky.dust_density = 1.6; sky.sun_disc = True
        ln.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
        sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 0.0                                    # the sky's own sun disc lights the scene
        exposure = -3.6
    elif preset in ('overcast', 'blizzard'):
        bg.inputs['Color'].default_value = (0.62, 0.66, 0.72, 1); bg.inputs['Strength'].default_value = 1.0 if preset == 'overcast' else 0.8
        sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 0.35; sun.angle = math.radians(25); sun.color = (0.95, 0.97, 1.0)   # 2:1 overcast ratio
        exposure = -0.35 if preset == 'overcast' else 0.9   # blizzard: bright white-out (snow scatters, it doesn't absorb)
    else:  # night: grey-blue, moon on snow (blue is a stylistic choice, made on purpose: Purkinje)
        bg.inputs['Color'].default_value = (0.010, 0.014, 0.024, 1); bg.inputs['Strength'].default_value = 1.0
        sun = bpy.data.lights.new('Moon', 'SUN'); sun.energy = 0.05; sun.angle = math.radians(0.57); sun.color = (0.72, 0.82, 1.0)
        exposure = 3.4
    if sun:
        so = bpy.data.objects.new(sun.name, sun); sc.collection.objects.link(so)
        so.rotation_euler = (math.radians(90 - (9 if preset == 'lowsun' else 35 if preset == 'night' else 50)), 0, math.radians(215 - 90 if preset != 'night' else 160))
    # fog lives in a bounded box (a world volume blocks the infinitely far sky in Cycles: the frame goes black)
    dens = {'blizzard': 0.0042, 'overcast': 0.00035, 'lowsun': 0.00022, 'night': 0.0004}[preset]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 300)); fb = bpy.context.active_object; fb.name = 'FogBox'; fb.scale = (5000, 5000, 1000)
    fm = bpy.data.materials.new('M_Fog'); fnt = fm.node_tree if fm.use_nodes else None; fm.use_nodes = True; fnd, fln = fm.node_tree.nodes, fm.node_tree.links; fnd.clear()
    fo = fnd.new('ShaderNodeOutputMaterial'); vol = fnd.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = dens
    vol.inputs['Color'].default_value = (0.97, 0.98, 1.0, 1) if preset == 'blizzard' else (0.85, 0.88, 0.93, 1); vol.inputs['Anisotropy'].default_value = 0.3 if preset == 'blizzard' else 0.7
    # height falloff: fog thicker in the valley (low), thinner over the ridges
    tc = fnd.new('ShaderNodeTexCoord'); sep = fnd.new('ShaderNodeSeparateXYZ'); fln.new(tc.outputs['Object'], sep.inputs['Vector'])
    mr = fnd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.3; mr.inputs['From Max'].default_value = 0.1
    mr.inputs['To Min'].default_value = dens * (1.0 if preset == 'blizzard' else 2.5); mr.inputs['To Max'].default_value = dens * 0.3
    fln.new(sep.outputs['Z'], mr.inputs['Value']); fln.new(mr.outputs['Result'], vol.inputs['Density'])
    fln.new(vol.outputs['Volume'], fo.inputs['Volume']); fb.data.materials.append(fm)
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = exposure                       # LOCKED: one number per preset, written in the README
    return exposure

def falling_snow(cam, count, preset):
    """Falling snow streaks in front of the camera (blizzard / overcast)."""
    import mathutils
    me = bpy.data.meshes.new('flakes'); co = []
    for _ in range(count):
        d = rng.uniform(3, 70); a = rng.uniform(-0.7, 0.7); b = rng.uniform(-0.45, 0.45)
        v = cam.matrix_world @ mathutils.Vector((a * d, b * d, -d)); co.append(v)
    me.vertices.add(len(co)); me.vertices.foreach_set('co', np.array(co, np.float32).ravel())
    ob = bpy.data.objects.new('Flakes', me); sc.collection.objects.link(ob)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=0.012 if preset == 'blizzard' else 0.009); fl = bpy.context.active_object
    fl.scale = (1, 1, 6 if preset == 'blizzard' else 2.5); fl.rotation_euler = (0.5, 0.6, 0) if preset == 'blizzard' else (0.1, 0, 0)
    m = bpy.data.materials.new('M_Flake'); nt, nd, ln = nodes(m); o = nd.new('ShaderNodeOutputMaterial'); p = principled(nd, (0.85, 0.87, 0.9), 0.9)
    ln.new(p.outputs['BSDF'], o.inputs['Surface']); fl.data.materials.append(m)
    ob.instance_type = 'VERTS'; fl.parent = ob; fl.location = (0, 0, 0)

# ------------------------------------------------------------------ cameras
def camera(shot):
    cam = bpy.data.cameras.new('Cam'); co = bpy.data.objects.new('Cam', cam); sc.collection.objects.link(co); sc.camera = co
    cam.clip_end = 6000
    import mathutils
    if shot == 'top':
        cam.type = 'ORTHO'; cam.ortho_scale = N - 1; co.location = (0, 0, 2500); co.rotation_euler = (0, 0, 0); return co
    if shot == 'aerial':
        cx, cy, cz = ue_to_img(L['castle_centre'])
        eye = to_b(cx + 700, cy + 900, 420); tgt = to_b(cx - 80, cy - 40, 40); cam.lens = 32
    elif shot == 'gate':                                            # the player's first view: gatehouse top, down the road to the bridge
        f = L['first_view']; ex, ey, ez = ue_to_img(f['from']); tx, ty, tz = ue_to_img(f['look_at'])
        eye = to_b(ex, ey, ez); tgt = to_b(tx, ty, tz); cam.lens = 30
    elif shot == 'lake':                                            # from the lake shore toward the castle
        lx, ly, lz = ue_to_img(L['lake']['centre']); cx, cy, cz = ue_to_img(L['castle_centre'])
        eye = to_b(lx - 120, ly + 90, lz + 6); tgt = to_b(cx, cy, cz + 15); cam.lens = 40
    co.location = eye
    d = mathutils.Vector(tgt) - mathutils.Vector(eye); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return co

# ------------------------------------------------------------------ build + render
ter = terrain(); ter.data.materials.append(mat_terrain())
castle(); realm_steam()
sp = spruce_mesh(); bi = birch_mesh()
n_sp = scatter('Spruces', 'Forest', 0.85, sp, 16, 27, 0.6)
n_bi = scatter('Birches', 'Birch', 0.25, bi, 9, 15, 0.3)
exp = world(PRESET); cam = camera(SHOT)
if SHOT != 'top' and PRESET in ('blizzard', 'overcast'): falling_snow(cam, 9000 if PRESET == 'blizzard' else 2500, PRESET)
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
if '--gpu' in A:
  try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
        try:
            prefs.compute_device_type = t; prefs.get_devices()
            if any(d.type == t for d in prefs.devices):
                for d in prefs.devices: d.use = True
                sc.cycles.device = 'GPU'; break
        except Exception: pass
  except Exception: pass
sc.cycles.volume_step_rate = 4; sc.cycles.max_bounces = 6
sc.render.resolution_x = RES; sc.render.resolution_y = RES if SHOT == 'top' else int(RES * 9 / 16)
sc.render.filepath = OUTP; sc.render.image_settings.file_format = 'PNG'
print('render', SHOT, PRESET, 'exposure', exp, 'spruces', n_sp, 'birches', n_bi, 'device', sc.cycles.device)
exec(open(r'C:/Users/HOSSAM~1.RAB/AppData/Local/Temp/dbg.py').read()) if '--dbg' in A else None
if '--dbg' not in A: bpy.ops.render.render(write_still=True)
print('wrote', OUTP)
