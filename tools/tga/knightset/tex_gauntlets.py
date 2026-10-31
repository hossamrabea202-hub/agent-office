# Yellow Eagle gauntlets (#367, TGA): UVs + procedural material bake -> 2K BC / ORM / N (DirectX), LODs, R mirror, FBX.
#   blender -b gauntlets.blend -P tex_gauntlets.py      (env WORK) -> WORK/out/{tex,fbx}, saves gauntlets_tex.blend
# Materials from sheet 08's swatches, calibrated to the KB: bare steel 180-200 sRGB metallic 1 (aged by darker oxide and
# grime that are NON-metal in seams / cavities), brass rivets ~#C8A24D metal with tarnish in recesses, glove leather
# #4B3526, strap #2A1B12 (lifted to >= 40 sRGB). Wear by cause: AO (cavities, under lames) -> oxide + grime, bevel edge
# mask -> polished bright edges and scratches on high points (knuckles, cuff rim), mud low on the fingers.
import bpy, os, math, numpy as np
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath); OUT = os.path.join(D, 'out'); TEX = os.path.join(OUT, 'tex'); FBX = os.path.join(OUT, 'fbx')
for p in (TEX, FBX): os.makedirs(p, exist_ok=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
g = bpy.data.objects['SM_EagleGauntlets_L']; bpy.context.view_layer.objects.active = g; g.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')
R = 2048
IM = {k: bpy.data.images.new('T_EagleGauntlets_' + k, R, R, alpha=False, float_buffer=(k == 'N')) for k in ('BC', 'ORM', 'N')}
for k, im in IM.items(): im.colorspace_settings.name = 'sRGB' if k == 'BC' else 'Non-Color'
def lin(*c): return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 for x in c) + (1,)
def build(mat, kind):
    mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N('ShaderNodeOutputMaterial'); bs = N('ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord'); geo = N('ShaderNodeNewGeometry')
    def noise(scale, detail=4, rough=0.55, src='Object', dist=0.0):
        n = N('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        if dist: n.inputs['Distortion'].default_value = dist
        L(tc.outputs[src], n.inputs['Vector']); return n.outputs['Fac']
    def ramp(x, a, b):                                                          # smoothstep a..b
        m = N('ShaderNodeMapRange'); m.interpolation_type = 'SMOOTHSTEP'; L(x, m.inputs['Value']); m.inputs['From Min'].default_value = a; m.inputs['From Max'].default_value = b; return m.outputs['Result']
    def math_(op, a, b=None, v=None):
        m = N('ShaderNodeMath'); m.operation = op
        if isinstance(a, float): m.inputs[0].default_value = a
        else: L(a, m.inputs[0])
        if b is not None:
            if isinstance(b, float): m.inputs[1].default_value = b
            else: L(b, m.inputs[1])
        if v is not None: m.use_clamp = v
        return m.outputs[0]
    def mixc(f, a, b):
        m = N('ShaderNodeMix'); m.data_type = 'RGBA'
        if isinstance(f, float): m.inputs[0].default_value = f
        else: L(f, m.inputs[0])
        for i, c in ((6, a), (7, b)):
            if isinstance(c, tuple): m.inputs[i].default_value = c
            else: L(c, m.inputs[i])
        return m.outputs[2]
    ao = N('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.012; ao.samples = 16
    bev = N('ShaderNodeBevel'); bev.inputs['Radius'].default_value = 0.0012
    dp = N('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'; L(bev.outputs[0], dp.inputs[0]); L(geo.outputs['Normal'], dp.inputs[1])
    edge = ramp(math_('SUBTRACT', 1.0, dp.outputs['Value']), 0.004, 0.06)       # 1 on rolled edges / lame borders
    cav = ramp(math_('SUBTRACT', 1.0, ao.outputs['AO']), 0.25, 0.75)            # 1 deep in seams, under lames
    sep = N('ShaderNodeSeparateXYZ'); L(tc.outputs['Object'], sep.inputs[0])
    mud = math_('MULTIPLY', ramp(sep.outputs['Z'], -0.12, -0.16), ramp(noise(55, 3), 0.45, 0.7))   # fingertips (object -Z)
    n1, n2 = noise(14, 5), noise(260, 2, 0.6)
    bump = N('ShaderNodeBump'); bump.inputs['Distance'].default_value = 0.0004
    if kind == 'steel':
        pit = ramp(noise(420, 2, 0.7), 0.56, 0.72)                              # pitted / etched speckle of the sheet
        scr = ramp(noise(900, 1, 0.5, dist=12.0), 0.7, 0.74)   # fine scratches
        n3 = noise(38, 5, 0.6, dist=1.5)
        oxide = math_('MAXIMUM', ramp(math_('ADD', math_('ADD', cav, math_('MULTIPLY', n1, 0.45)), math_('MULTIPLY', n3, 0.35)), 0.5, 0.68), math_('MULTIPLY', mud, 0.9))
        # v2 (sheet: dark blued plate, mottled): a fire-scale patina film over about half the plate, rust-gold speckle;
        # bright metal only where edges / high spots rub it off. Patina and speckle are non-metal (KB: metal is 0 or 1).
        patina = math_('MULTIPLY', ramp(math_('ADD', noise(170, 6, 0.6, dist=0.5), math_('MULTIPLY', n1, 0.5)), 0.6, 0.66), math_('SUBTRACT', 1.0, edge))
        speck = math_('MULTIPLY', ramp(noise(320, 3, 0.65), 0.63, 0.69), 0.85)
        oxide = math_('MAXIMUM', math_('MAXIMUM', oxide, patina), speck)
        base = mixc(n3, lin(162, 164, 170), lin(184, 184, 188)); base = mixc(math_('MULTIPLY', pit, 0.5), base, lin(156, 156, 160))   # blued, hammered
        base = mixc(math_('MAXIMUM', edge, math_('MULTIPLY', scr, 0.6)), base, lin(206, 204, 200))
        film = mixc(n3, lin(44, 46, 52), lin(60, 60, 64))                         # fire scale, blue-black
        rust = mixc(n2, lin(118, 78, 40), lin(150, 108, 56))                      # rust-gold speckle
        dirt = mixc(n2, lin(66, 54, 42), lin(92, 70, 48))
        col = mixc(math_('GREATER_THAN', oxide, 0.4999), base, mixc(speck, mixc(patina, dirt, film), rust))   # hard switch with the binary metal mask
        metal = math_('LESS_THAN', oxide, 0.5)                                 # binary metal mask (KB: 0 or 1)
        rgh = math_('ADD', math_('ADD', math_('MULTIPLY', n1, 0.14), math_('MULTIPLY', n3, 0.22)), 0.4); rgh = math_('SUBTRACT', rgh, math_('MULTIPLY', edge, 0.12))
        rgh = math_('ADD', rgh, math_('MULTIPLY', pit, 0.15)); rgh = math_('ADD', rgh, math_('ADD', math_('MULTIPLY', oxide, 0.12), math_('MULTIPLY', speck, 0.3)), v=True)   # v2: the film keeps a satin sheen
        L(math_('ADD', math_('MULTIPLY', pit, -0.6), math_('MULTIPLY', scr, -0.3)), bump.inputs['Height'])
    elif kind == 'brass':
        tar = ramp(math_('ADD', cav, math_('MULTIPLY', n1, 0.4)), 0.5, 0.8)
        col = mixc(math_('GREATER_THAN', tar, 0.4999), mixc(edge, lin(214, 174, 90), lin(228, 194, 110)), lin(92, 74, 44)); metal = math_('LESS_THAN', tar, 0.5)
        rgh = math_('ADD', math_('MULTIPLY', tar, 0.45), math_('ADD', math_('MULTIPLY', n2, 0.12), 0.26), v=True)
        L(math_('MULTIPLY', n2, 0.2), bump.inputs['Height'])
    else:                                                                       # leather glove + strap
        crease = ramp(noise(90, 6, 0.65, dist=2.5), 0.55, 0.75); grain = noise(700, 2, 0.7)
        quilt = N('ShaderNodeTexWave'); quilt.wave_type = 'RINGS'; quilt.inputs['Scale'].default_value = 9.0; quilt.inputs['Distortion'].default_value = 7.0; quilt.inputs['Detail'].default_value = 3.0; L(tc.outputs['Object'], quilt.inputs['Vector'])
        seam = ramp(quilt.outputs['Fac'], 0.03, 0.08)                           # v2: quilted / stitched palm (dark seam lines)
        col = mixc(n1, lin(72, 48, 31), lin(58, 39, 27)); col = mixc(math_('MULTIPLY', cav, 0.7), col, lin(42, 31, 24))
        col = mixc(math_('MULTIPLY', math_('SUBTRACT', 1.0, seam), 0.7), col, lin(44, 31, 22))
        col = mixc(math_('MULTIPLY', crease, 0.35), col, lin(58, 42, 31)); col = mixc(math_('MULTIPLY', mud, 0.8), col, lin(70, 60, 48))
        metal = math_('MULTIPLY', n1, 0.0)
        rgh = math_('ADD', math_('ADD', math_('MULTIPLY', grain, 0.18), 0.55), math_('MULTIPLY', crease, -0.12), v=True)
        L(math_('ADD', math_('ADD', math_('MULTIPLY', crease, -0.8), math_('MULTIPLY', grain, 0.25)), math_('MULTIPLY', seam, 0.9)), bump.inputs['Height'])
    L(geo.outputs['Normal'], bump.inputs['Normal'])
    L(col, bs.inputs['Base Color']); L(metal, bs.inputs['Metallic']); L(rgh, bs.inputs['Roughness']); L(bump.outputs[0], bs.inputs['Normal'])
    L(bs.outputs[0], out.inputs['Surface'])
    # bake emitters
    e_bc = N('ShaderNodeEmission'); e_bc.name = 'E_BC'; L(col, e_bc.inputs[0])
    cmb = N('ShaderNodeCombineColor'); L(ao.outputs['AO'], cmb.inputs[0]); L(rgh, cmb.inputs[1]); L(metal, cmb.inputs[2])
    e_orm = N('ShaderNodeEmission'); e_orm.name = 'E_ORM'; L(cmb.outputs[0], e_orm.inputs[0])
    tgt = N('ShaderNodeTexImage'); tgt.name = 'TARGET'; nt.nodes.active = tgt
    mat['kind'] = kind
for m in g.data.materials: build(m, {'M_EagleSteel': 'steel', 'M_EagleBrass': 'brass', 'M_EagleLeather': 'leather'}[m.name])
def bake(key, btype, emitter=None):
    for m in g.data.materials:
        nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); nt.nodes['TARGET'].image = IM[key]; nt.nodes.active = nt.nodes['TARGET']
        src = nt.nodes[emitter].outputs[0] if emitter else next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED').outputs[0]
        nt.links.new(src, out.inputs['Surface'])
    sc.render.bake.margin = 8
    bpy.ops.object.bake(type=btype, normal_space='TANGENT') if btype == 'NORMAL' else bpy.ops.object.bake(type=btype)
    print('BAKED', key, flush=True)
bake('BC', 'EMIT', 'E_BC'); bake('ORM', 'EMIT', 'E_ORM'); bake('N', 'NORMAL')
# v2: texels on a metal / patina border bake an averaged (darker) colour but end up metal after the 0 / 1 threshold:
# lift them to the KB metal floor (luminance 150 sRGB = 0.305 linear) so bare metal never reads as dull grey-brown.
om = np.empty(R * R * 4, np.float32); IM['ORM'].pixels.foreach_get(om); om = om.reshape(-1, 4)[:, 2] > 0.5
bc = np.empty(R * R * 4, np.float32); IM['BC'].pixels.foreach_get(bc); bc = bc.reshape(-1, 4)
lin = np.where(bc[:, :3] <= 0.04045, bc[:, :3] / 12.92, ((bc[:, :3] + 0.055) / 1.055) ** 2.4)      # byte image: pixels are sRGB-encoded
Y = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32); low = om & (Y > 1e-4) & (Y < 0.32)
lin[low] = np.clip(lin[low] * (0.32 / Y[low])[:, None], 0, 1)
bc[:, :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
IM['BC'].pixels.foreach_set(bc.ravel()); print('LIFTED', int(low.sum()), 'metal border texels', flush=True)
for k, im in IM.items():
    if k == 'ORM':                                                              # KB: metallic strictly 0 / 1 (the bake's AA softens mask edges)
        px = np.empty(R * R * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(-1, 4); px[:, 2] = (px[:, 2] > 0.5).astype(np.float32); im.pixels.foreach_set(px.ravel())
    if k == 'N':                                                                # OpenGL -> DirectX
        px = np.empty(R * R * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(-1, 4); px[:, 1] = 1 - px[:, 1]; im.pixels.foreach_set(px.ravel())
    im.filepath_raw = os.path.join(TEX, im.name + '.png'); im.file_format = 'PNG'; im.save(); print('SAVED', im.name, flush=True)
# final shading material: textures (for the lookdev and the FBX slot names)
for m in g.data.materials:
    nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); nt.links.new(bs.outputs[0], out.inputs['Surface'])
mt = bpy.data.materials.new('MI_EagleGauntlets'); mt.use_nodes = True; nt = mt.node_tree; b = nt.nodes['Principled BSDF']
def ti(k, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = IM[k]; n.image.colorspace_settings.name = cs; return n
bc, orm, nm = ti('BC', 'sRGB'), ti('ORM', 'Non-Color'), ti('N', 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sp.inputs[0])
fl = nt.nodes.new('ShaderNodeRGBCurve'); fl.mapping.curves[1].points[0].location = (0, 1); fl.mapping.curves[1].points[1].location = (1, 0); nt.links.new(nm.outputs[0], fl.inputs['Color'])
nn = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(fl.outputs[0], nn.inputs['Color'])
nt.links.new(bc.outputs[0], b.inputs['Base Color']); nt.links.new(sp.outputs[1], b.inputs['Roughness']); nt.links.new(sp.outputs[2], b.inputs['Metallic']); nt.links.new(nn.outputs[0], b.inputs['Normal'])
g.data.materials.clear(); g.data.materials.append(mt)
for p in g.data.polygons: p.material_index = 0
# LODs + right hand (mirror, same UVs)
def dup(src, name):
    o = src.copy(); o.data = src.data.copy(); o.name = name; o.data.name = name; sc.collection.objects.link(o); return o
objs = [g]
for i, ratio in ((1, 0.5), (2, 0.25), (3, 0.12)):
    o = dup(g, 'SM_EagleGauntlets_L_LOD%d' % i); m_ = o.modifiers.new('D', 'DECIMATE'); m_.ratio = ratio
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.ops.object.modifier_apply(modifier='D'); objs.append(o)
for o in list(objs):
    r = dup(o, o.name.replace('_L', '_R', 1)); r.scale = (-1, 1, 1)
    bpy.ops.object.select_all(action='DESELECT'); r.select_set(True); bpy.context.view_layer.objects.active = r
    bpy.ops.object.transform_apply(scale=True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
stats = {}
for o in [x for x in sc.objects if x.name.startswith('SM_EagleGauntlets')]:
    stats[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(FBX, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE', use_tspace=True,
                             apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
print('STATS', stats, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'gauntlets_tex.blend')); print('TEX OK gauntlets', flush=True)
