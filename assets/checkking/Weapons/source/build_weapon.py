# Medieval weapon kit (checkking, night of 2026-10-30): one procedural Blender 4.5 script for swords, axes and spears.
#   blender -b --factory-startup -P build_weapon.py -- <weapon> <out_root> [tex=2048] [samples=32]
# <weapon>: one of WEAPONS below. Writes <out_root>/<Name>/:
#   SM_CK_<Name>.fbx (Z up = along the weapon, grip/haft origin at the hand, metres -> UE cm),
#   textures/T_CK_<Name>_BaseColor.png, _ORM.png (AO, roughness, metallic), _Normal_DirectX.png (2K, baked),
#   renders/<name>_preview.png (studio key/rim/fill, locked exposure, grey 0.18 card behind)
# Realism KB: bare steel sRGB ~190 metallic 1, forged iron darker/rougher, ash/oak haft 30-240 sRGB band, leather grip;
# roughness never flat (grinding streaks along the blade, polish at the edge); wear by cause: edge polish (curvature),
# dark scale in cavities (AO), grip darkened where the hand goes; one shared light rig (warm key, cool rim).
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['arming_sword', os.getcwd()]
WEAPON, OUT = argv[0], os.path.abspath(argv[1])
TEX = int(argv[2]) if len(argv) > 2 else 2048
SPP = int(argv[3]) if len(argv) > 3 else 32

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
sc = bpy.context.scene; col = sc.collection

def srgb(c): return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 for x in c)

# ======================================================================================= materials
def mat(name, base, rough, metal, kind):
    """kind: steel | iron | wood | leather | bronze. Base/rough are calibrated; texture variation is procedural."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    if kind in ('steel', 'iron', 'bronze'):
        mp.inputs['Scale'].default_value = (60, 60, 2)          # stretched along Z: grinding streaks run along the blade
    elif kind == 'wood':
        mp.inputs['Scale'].default_value = (40, 40, 3)          # grain along the haft
    else:
        mp.inputs['Scale'].default_value = (120, 120, 120)
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 10
    L.new(mp.outputs['Vector'], nz.inputs['Vector'])
    big = N.new('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 6.0; big.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], big.inputs['Vector'])
    # roughness: base +/- streaks + large smudges
    r1 = N.new('ShaderNodeMapRange'); r1.inputs['To Min'].default_value = rough[0]; r1.inputs['To Max'].default_value = rough[1]
    L.new(nz.outputs['Fac'], r1.inputs['Value'])
    r2 = N.new('ShaderNodeMath'); r2.operation = 'MULTIPLY_ADD'; r2.inputs[1].default_value = 0.12; r2.inputs[2].default_value = -0.06
    L.new(big.outputs['Fac'], r2.inputs[0])
    rs = N.new('ShaderNodeMath'); rs.operation = 'ADD'; rs.use_clamp = True
    L.new(r1.outputs['Result'], rs.inputs[0]); L.new(r2.outputs['Value'], rs.inputs[1])
    # curvature (edges polished: lighter + smoother on metal, rubbed on wood/leather) and cavities (AO: dark scale / grime)
    geo = N.new('ShaderNodeNewGeometry')
    edge = N.new('ShaderNodeValToRGB'); edge.color_ramp.elements[0].position = 0.5; edge.color_ramp.elements[1].position = 0.58
    L.new(geo.outputs['Pointiness'], edge.inputs['Fac'])
    ao = N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.01
    cav = N.new('ShaderNodeValToRGB'); cav.color_ramp.elements[0].position = 0.35; cav.color_ramp.elements[1].position = 0.9
    L.new(ao.outputs['AO'], cav.inputs['Fac'])
    c0 = N.new('ShaderNodeMix'); c0.data_type = 'RGBA'; c0.blend_type = 'MULTIPLY'; c0.inputs[0].default_value = 0.25
    c0.inputs[6].default_value = (*base, 1)
    L.new(big.outputs['Color'], c0.inputs[7])
    lite = tuple(min(1.0, x * (1.25 if kind in ('steel', 'bronze') else 1.35)) for x in base)
    c1 = N.new('ShaderNodeMix'); c1.data_type = 'RGBA'; L.new(edge.outputs['Color'], c1.inputs[0])
    L.new(c0.outputs[2], c1.inputs[6]); c1.inputs[7].default_value = (*lite, 1)
    dark = tuple(x * 0.45 for x in base)
    c2 = N.new('ShaderNodeMix'); c2.data_type = 'RGBA'
    inv = N.new('ShaderNodeInvert'); L.new(cav.outputs['Color'], inv.inputs['Color'])
    L.new(inv.outputs['Color'], c2.inputs[0]); L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = (*dark, 1)
    if kind == 'wood':   # growth-ring grain: dark lines running along the haft
        wv = N.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
        wv.inputs['Scale'].default_value = 0.6; wv.inputs['Distortion'].default_value = 6.0; wv.inputs['Detail'].default_value = 4
        wm = N.new('ShaderNodeMapping'); wm.inputs['Scale'].default_value = (90, 90, 1.5); L.new(tc.outputs['Object'], wm.inputs['Vector'])
        L.new(wm.outputs['Vector'], wv.inputs['Vector'])
        gr = N.new('ShaderNodeMix'); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'
        rmp = N.new('ShaderNodeMapRange'); rmp.inputs['To Min'].default_value = 0.0; rmp.inputs['To Max'].default_value = 0.35
        L.new(wv.outputs['Fac'], rmp.inputs['Value']); L.new(rmp.outputs['Result'], gr.inputs[0])
        L.new(c2.outputs[2], gr.inputs[6]); gr.inputs[7].default_value = (0.55, 0.5, 0.45, 1)
        L.new(gr.outputs[2], bsdf.inputs['Base Color'])
    else:
        L.new(c2.outputs[2], bsdf.inputs['Base Color'])
    re = N.new('ShaderNodeMath'); re.operation = 'MULTIPLY_ADD'; re.use_clamp = True
    re.inputs[1].default_value = -0.12 if kind in ('steel', 'bronze') else -0.08
    L.new(edge.outputs['Color'], re.inputs[0]); L.new(rs.outputs['Value'], re.inputs[2])
    L.new(re.outputs['Value'], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = metal
    bm = N.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = {'steel': 0.05, 'iron': 0.25, 'bronze': 0.08, 'wood': 0.35, 'leather': 0.45}[kind]
    bm.inputs['Distance'].default_value = 0.0006
    L.new(nz.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], bsdf.inputs['Normal'])
    return m

STEEL = mat('Steel', (0.53, 0.53, 0.54), (0.22, 0.42), 1.0, 'steel')            # sRGB ~192
IRON = mat('Iron', (0.24, 0.235, 0.23), (0.55, 0.78), 1.0, 'iron')            # forged, oxide scale: darker + rougher than bare steel
BRONZE = mat('Bronze', (0.83, 0.52, 0.30), (0.30, 0.48), 1.0, 'bronze')
WOOD = mat('Wood', srgb((104, 82, 62)), (0.58, 0.78), 0.0, 'wood')              # ash, oiled
OAK = mat('Oak', srgb((84, 62, 44)), (0.6, 0.8), 0.0, 'wood')
LEATHER = mat('Leather', srgb((62, 40, 28)), (0.5, 0.72), 0.0, 'leather')
MATS = [STEEL, IRON, BRONZE, WOOD, OAK, LEATHER]

# ======================================================================================= geometry helpers
parts = []
def mesh_obj(name, verts, faces, m, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.data.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth
    parts.append(o); return o

def loft(name, stations, m, cap_tip=True, cap_base=True):
    """stations: list of (z, half_width, half_thick, edge_half, x_offset[, fuller_depth, fuller_half_width]).
    Cross-section: thin edge flats (-w,±e)/(w,±e), shoulders at ±fw with full thickness t, and a centre that sinks by
    fuller_depth (a fuller groove; 0 = plain lenticular/diamond section). A real blade: thick spine, thin edges."""
    ring = []
    for s in stations:
        z, w, t, e, xo = s[:5]; d = s[5] if len(s) > 5 else 0.0; fw = s[6] if len(s) > 6 else w * 0.35
        fw = min(fw, w * 0.6)
        ring.append([(xo - w, -e, z), (xo - fw, -t, z), (xo, -t + d, z), (xo + fw, -t, z), (xo + w, -e, z),
                     (xo + w, e, z), (xo + fw, t, z), (xo, t - d, z), (xo - fw, t, z), (xo - w, e, z)])
    verts = [v for r in ring for v in r]; faces = []
    n = 10
    for i in range(len(ring) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n): faces.append((a + k, a + (k + 1) % n, b + (k + 1) % n, b + k))
    if cap_base: faces.append(tuple(range(n - 1, -1, -1)))
    if cap_tip: faces.append(tuple((len(ring) - 1) * n + k for k in range(n)))
    o = mesh_obj(name, verts, faces, m)
    bev = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); bev.keep_sharp = True
    return o

def cyl(name, r, z0, z1, m, verts=24, r1=None, oval=1.0, x=0.0):
    r1 = r if r1 is None else r1
    vs, fs = [], []
    for zz, rr in ((z0, r), (z1, r1)):
        for k in range(verts):
            a = 2 * math.pi * k / verts; vs.append((x + rr * math.cos(a), rr * math.sin(a) * oval, zz))
    for k in range(verts): fs.append((k, (k + 1) % verts, verts + (k + 1) % verts, verts + k))
    fs.append(tuple(range(verts - 1, -1, -1))); fs.append(tuple(verts + k for k in range(verts)))
    o = mesh_obj(name, vs, fs, m); bv = o.modifiers.new('bev', 'BEVEL'); bv.width = min(r, r1) * 0.25; bv.segments = 2
    return o

def box(name, sx, sy, sz, loc, m, bevel=0.002, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); parts.append(o); return o

def sphere(name, r, loc, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12); o = bpy.context.object; o.name = name
    o.scale = scale; bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); bpy.ops.object.shade_smooth()
    parts.append(o); return o

def profile_slab(name, outline, thick_at, m, ny=1):
    """2D outline in XZ (counter-clockwise), extruded in Y with thickness thick_at(x, z) (half thickness): axe heads, wings."""
    bm_ = bmesh.new()
    top = [bm_.verts.new((x, thick_at(x, z), z)) for x, z in outline]
    bot = [bm_.verts.new((x, -thick_at(x, z), z)) for x, z in outline]
    bm_.faces.new(top); bm_.faces.new(list(reversed(bot)))
    n = len(outline)
    for k in range(n): bm_.faces.new((top[k], bot[k], bot[(k + 1) % n], top[(k + 1) % n]))
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces)
    # subdivide the big caps so the taper reads (triangulate + poke)
    bmesh.ops.triangulate(bm_, faces=[f for f in bm_.faces if len(f.verts) > 4])
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    for v in me.vertices:   # re-apply the taper on all verts (triangulation added none, but keeps it explicit)
        x, y, z = v.co; t = thick_at(x, z); v.co.y = t if y > 0 else -t
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.data.materials.append(m)
    for p in me.polygons: p.use_smooth = False
    b = o.modifiers.new('bev', 'BEVEL'); b.width = 0.0012; b.segments = 2; b.limit_method = 'ANGLE'
    wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True
    parts.append(o); return o

def grip_wrap(z0, z1, r, m):
    """leather-wrapped grip: a cylinder with spiral ridges (displaced rings) so the wrap reads in silhouette."""
    o = cyl('Grip', r, z0, z1, m, 20)
    bpy.context.view_layer.objects.active = o
    turns = int((z1 - z0) / 0.012)
    for k in range(turns):
        zz = z0 + (k + 0.5) * (z1 - z0) / turns
        cyl('Wrap%d' % k, r * 1.06, zz - 0.0035, zz + 0.0035, m, 20)
    return o

def blade(name, L, base_w, tip_len, t_base, t_tip, z0=0.0, taper=0.55, m=None, curve=0.0, fuller=0.0):
    """straight double-edged blade from z0, length L: width tapers to taper*base_w before the tip, then a point.
    fuller = groove length as a fraction of L (0 = none); it is 0.35 of the blade width wide and fades out at its end."""
    st = []; N_ = 24
    for i in range(N_ + 1):
        f = i / N_; z = z0 + L * f
        if z < z0 + L - tip_len:
            w = base_w * (1 - (1 - taper) * (f / ((L - tip_len) / L)))
        else:
            g = (z - (z0 + L - tip_len)) / tip_len; w = base_w * taper * math.sqrt(max(0.0, 1 - g * g)) * max(0.0, 1 - g) ** 0.3
        w = max(w, 0.0008); t = t_base + (t_tip - t_base) * f
        d = 0.0
        if fuller and f < fuller:
            d = t * 0.45 * min(1.0, f / 0.04) * min(1.0, (fuller - f) / 0.08)   # eases in at the guard, runs out before the tip
        st.append((z, w, max(t, 0.0006), 0.0004, curve * f * f, d, w * 0.38))
    return loft(name, st, m or STEEL)

# ======================================================================================= weapons (grip/haft hand point at origin, Z along)
def arming_sword():
    blade('Blade', 0.78, 0.026, 0.12, 0.0042, 0.0018, z0=0.06, fuller=0.7)
    box('Guard', 0.20, 0.018, 0.016, (0, 0, 0.052), IRON, 0.003)
    for s in (-1, 1): sphere('GuardEnd', 0.011, (s * 0.1, 0, 0.052), IRON, (1, 0.9, 1.2))
    grip_wrap(-0.06, 0.044, 0.0135, LEATHER)
    cyl('Ferrule', 0.016, 0.040, 0.046, IRON, 20)
    cyl('Pommel', 0.026, -0.085, -0.062, IRON, 32, oval=0.55)                  # wheel pommel
    cyl('PommelBoss', 0.012, -0.090, -0.057, IRON, 16, oval=0.7)

def longsword():
    blade('Blade', 0.92, 0.024, 0.15, 0.0048, 0.0022, z0=0.07, taper=0.45, fuller=0.45)
    box('Guard', 0.24, 0.02, 0.016, (0, 0, 0.06), IRON, 0.003)
    for s in (-1, 1): box('Quillon', 0.03, 0.022, 0.024, (s * 0.12, 0, 0.066), IRON, 0.004, rot=(0, s * 0.35, 0))
    grip_wrap(-0.17, 0.052, 0.0145, LEATHER)
    cyl('Pommel', 0.022, -0.215, -0.17, IRON, 8, r1=0.016)                      # scent-stopper style: octagonal, tapered
    sphere('PommelCap', 0.012, (0, 0, -0.218), IRON)

def falchion():
    # single-edged, clipped wide tip: loft with the ridge offset to the back, curve to the edge side
    st = []
    for i in range(25):
        f = i / 24; z = 0.06 + 0.66 * f
        w = 0.024 + 0.022 * f ** 1.6 if f < 0.86 else (0.024 + 0.022 * 0.86 ** 1.6) * (1 - (f - 0.86) / 0.14) ** 0.6 + 0.001
        st.append((z, w, 0.0045 - 0.002 * f, 0.0005, 0.018 * f ** 2))
    loft('Blade', st, STEEL)
    box('Guard', 0.15, 0.018, 0.014, (0, 0, 0.052), IRON, 0.003, rot=(0, 0.1, 0))
    grip_wrap(-0.06, 0.044, 0.0135, LEATHER)
    sphere('Pommel', 0.022, (0, 0, -0.075), BRONZE, (1, 0.7, 1.15))

def axe_head(name, x0, x1, ztop, zbot, thick, bulge, m, NX=36, NZ=14):
    """Axe blade lofted along X (eye at x0 -> cutting edge at x1). ztop(f)/zbot(f): top and bottom outline at f = 0..1,
    thick(f): half thickness (thick at the eye, ~0.6 mm at the edge), bulge: how far the cutting edge curves out (convex
    edge, widest at mid height). Closed lens-section shell, smooth shading, so it shades like forged steel, not facets."""
    ring = []
    for i in range(NX + 1):
        f = i / NX; x = x0 + (x1 - x0) * f; zt, zb, t = ztop(f), zbot(f), thick(f)
        row = []
        for j in range(NZ + 1):                                    # front side, bottom -> top
            g = j / NZ; zz = zb + (zt - zb) * g
            xb = x + bulge * (f ** 3) * math.sin(math.pi * g)      # the edge bows out, the eye stays straight
            tt = t * (0.35 + 0.65 * math.sin(math.pi * g) ** 0.5)  # thinner toward top and bottom outline (rounded spine)
            row.append((xb, tt, zz))
        row += [(v[0], -v[1], v[2]) for v in reversed(row)]        # back side, top -> bottom
        ring.append(row)
    n = len(ring[0]); verts = [v for r in ring for v in r]; faces = []
    for i in range(NX):
        a_, b_ = i * n, (i + 1) * n
        for k in range(n): faces.append((a_ + k, a_ + (k + 1) % n, b_ + (k + 1) % n, b_ + k))
    faces.append(tuple(range(n - 1, -1, -1))); faces.append(tuple(NX * n + k for k in range(n)))
    o = mesh_obj(name, verts, faces, m)
    wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True
    return o

def eye(z0, z1, m, r=0.024, oval=0.72, x=-0.004):
    """the socket around the haft (the head is forged around it): an oval sleeve, a little proud of the haft."""
    return cyl('Eye', r, z0, z1, m, 24, oval=oval, x=x)

def bearded_axe():   # Viking bearded axe: short haft, the beard hooks far below the eye
    cyl('Haft', 0.016, -0.42, 0.31, WOOD, 16, r1=0.015, oval=0.75)
    cyl('Knob', 0.019, -0.45, -0.42, WOOD, 16, oval=0.75)
    axe_head('Head', 0.012, 0.13, lambda f: 0.282 + 0.02 * f ** 1.5,
             lambda f: 0.232 - 0.13 * f ** 1.8, lambda f: max(0.0006, 0.010 * (1 - f) ** 1.3), 0.012, IRON)
    eye(0.225, 0.29, IRON)
    box('Wedge', 0.012, 0.004, 0.012, (-0.004, 0, 0.295), OAK, 0.001)

def dane_axe():      # two-handed Dane axe: long haft, broad thin crescent head
    cyl('Haft', 0.017, -1.05, 0.38, OAK, 16, r1=0.016, oval=0.78)
    axe_head('Head', 0.012, 0.19, lambda f: 0.325 + 0.09 * f ** 1.6,
             lambda f: 0.268 - 0.105 * f ** 1.7, lambda f: max(0.0006, 0.0095 * (1 - f) ** 1.5), 0.022, IRON)
    eye(0.26, 0.335, IRON, r=0.025)
    for k in range(3): cyl('Band%d' % k, 0.0185, -0.2 - 0.04 * k, -0.19 - 0.04 * k, IRON, 16, oval=0.78)

def war_axe():       # horseman's axe: narrow steel head, back spike, langets down the haft, leather grip
    cyl('Haft', 0.015, -0.30, 0.29, OAK, 16, r1=0.0145, oval=0.8)
    grip_wrap(-0.30, -0.15, 0.016, LEATHER)
    axe_head('Head', 0.012, 0.13, lambda f: 0.247 + 0.035 * f ** 2, lambda f: 0.212 - 0.03 * f ** 2,
             lambda f: max(0.0006, 0.009 * (1 - f) ** 1.2), 0.008, STEEL)
    axe_head('Spike', -0.012, -0.105, lambda f: 0.238 - 0.008 * f, lambda f: 0.222 + 0.006 * f,
             lambda f: max(0.0008, 0.008 * (1 - f)), 0.0, IRON, NX=12, NZ=6)
    eye(0.205, 0.255, IRON, r=0.021)
    for s_ in (-1, 1): box('Langet', 0.006, 0.003, 0.16, (0, s_ * 0.0125, 0.13), IRON, 0.001)

def spear_head(L, w, socket_len, z0, wings=False, m=STEEL):
    st = []
    for i in range(25):
        f = i / 24; z = z0 + socket_len + L * f
        ww = w * math.sin(math.pi * min(1.0, f * 1.6) / 2) * (1 - f) ** 0.9 + 0.0008
        st.append((z, ww, 0.0055 * (1 - f) + 0.0008, 0.0004, 0.0))
    loft('SpearHead', st, m)
    cyl('Socket', 0.0175, z0, z0 + socket_len, IRON, 16, r1=0.011)
    if wings:
        for s in (-1, 1): box('Wing', 0.05, 0.006, 0.01, (s * 0.035, 0, z0 + socket_len * 0.4), IRON, 0.002, rot=(0, s * -0.25, 0))

def winged_spear():
    cyl('Shaft', 0.0165, -1.25, 0.75, WOOD, 16, r1=0.0155)
    spear_head(0.30, 0.032, 0.11, 0.73, wings=True)
    cyl('ButtCap', 0.018, -1.29, -1.24, IRON, 16, r1=0.0168)

def boar_spear():
    cyl('Shaft', 0.017, -1.1, 0.70, OAK, 16, r1=0.016)
    spear_head(0.36, 0.045, 0.12, 0.68, wings=True)
    for k in range(4): cyl('Grip%d' % k, 0.0185, -0.05 - 0.02 * k, -0.045 - 0.02 * k, LEATHER, 16)

def glaive():
    cyl('Shaft', 0.0175, -1.2, 0.80, OAK, 16, r1=0.0165)
    st = []
    for i in range(25):
        f = i / 24; z = 0.92 + 0.50 * f
        w = 0.022 + 0.018 * math.sin(math.pi * min(f, 0.8) / 0.8 * 0.5) if f < 0.8 else (0.04) * (1 - (f - 0.8) / 0.2) ** 0.8 + 0.001
        st.append((z, w, 0.005 - 0.003 * f, 0.0005, 0.02 * f ** 2))
    loft('Blade', st, STEEL)
    cyl('Socket', 0.02, 0.76, 0.93, IRON, 16, r1=0.014)
    profile_slab('BackHook', [(-0.02, 1.0), (-0.07, 1.06), (-0.025, 1.04)], lambda x, z: 0.004, IRON)
    cyl('ButtCap', 0.019, -1.24, -1.19, IRON, 16, r1=0.0175)

def halberd():       # 15th c. halberd: axe blade, back fluke, long top spike, langets
    cyl('Shaft', 0.0175, -1.25, 0.62, OAK, 16, r1=0.0165, oval=0.85)
    axe_head('Blade', 0.014, 0.17, lambda f: 0.70 + 0.03 * f, lambda f: 0.54 - 0.03 * f ** 2,
             lambda f: max(0.0006, 0.007 * (1 - f) ** 1.2), 0.02, STEEL)
    axe_head('Fluke', -0.014, -0.10, lambda f: 0.655 - 0.03 * f ** 0.8, lambda f: 0.605 + 0.02 * f,
             lambda f: max(0.0008, 0.007 * (1 - f)), 0.0, IRON, NX=14, NZ=6)
    blade('Spike', 0.34, 0.012, 0.12, 0.007, 0.003, z0=0.70, taper=0.8, m=STEEL)
    eye(0.53, 0.72, IRON, r=0.021, oval=0.85)
    for s_ in (-1, 1): box('Langet', 0.006, 0.003, 0.30, (0, s_ * 0.0145, 0.40), IRON, 0.001)
    cyl('ButtCap', 0.019, -1.29, -1.24, IRON, 16, r1=0.0175)

def bardiche():      # long crescent blade fixed to the haft at two points
    cyl('Shaft', 0.018, -1.1, 0.55, OAK, 16, r1=0.017)
    axe_head('Blade', 0.016, 0.15, lambda f: 0.92 - 0.06 * f + 0.10 * f ** 3, lambda f: 0.36 + 0.12 * f - 0.05 * f ** 3,
             lambda f: max(0.0006, 0.0075 * (1 - f) ** 1.4), 0.03, IRON, NX=30, NZ=20)
    eye(0.50, 0.56, IRON, r=0.022)
    eye(0.34, 0.40, IRON, r=0.022)
    blade('Tip', 0.10, 0.008, 0.05, 0.004, 0.002, z0=0.88, taper=0.9, m=IRON, curve=0.0)

def partisan():      # broad triangular spear head with two side lugs
    cyl('Shaft', 0.017, -1.25, 0.72, WOOD, 16, r1=0.016)
    st = []
    for i in range(25):
        f = i / 24; z = 0.84 + 0.42 * f
        w = (0.05 * (1 - f) ** 1.1 + 0.0008) if f > 0.06 else 0.016 + (0.05 - 0.016) * f / 0.06
        st.append((z, w, 0.0065 * (1 - f) + 0.0008, 0.0004, 0.0, 0.0024 * (1 - f) if f < 0.7 else 0.0, w * 0.2))
    loft('Head', st, STEEL)
    for s_ in (-1, 1):
        axe_head('Lug%d' % (s_ + 1), 0.016 * s_, 0.075 * s_, lambda f: 0.86 + 0.05 * f ** 1.5, lambda f: 0.83 + 0.02 * f,
                 lambda f: max(0.0008, 0.0055 * (1 - f)), 0.0, STEEL, NX=12, NZ=6)
    cyl('Socket', 0.02, 0.70, 0.85, IRON, 16, r1=0.016)
    cyl('ButtCap', 0.0185, -1.29, -1.24, IRON, 16, r1=0.017)

def messer():        # German messer: single-edged, slight curve, nagel on the guard, riveted wooden grip slabs
    st = []
    for i in range(25):
        f = i / 24; z = 0.06 + 0.74 * f
        w = 0.019 if f < 0.82 else 0.019 * max(0.0, 1 - (f - 0.82) / 0.18) ** 0.6 + 0.0008
        st.append((z, w, 0.0045 - 0.0022 * f, 0.0005, 0.022 * f ** 2 + (0.0 if f < 0.82 else -0.01 * ((f - 0.82) / 0.18) ** 2),
                   0.0012 if 0.05 < f < 0.6 else 0.0, w * 0.3))
    loft('Blade', st, STEEL)
    box('Guard', 0.16, 0.014, 0.012, (0, 0, 0.054), IRON, 0.003, rot=(0, -0.12, 0))
    box('Nagel', 0.008, 0.03, 0.008, (0, -0.02, 0.054), IRON, 0.002)
    for s_ in (-1, 1): box('Slab', 0.03, 0.009, 0.12, (0.003, s_ * 0.007, -0.01), OAK, 0.003)
    for k in range(3):
        cyl('Rivet%d' % k, 0.0035, -0.0125, 0.0125, IRON, 10, x=0.003)
        parts[-1].rotation_euler = (math.pi / 2, 0, 0); parts[-1].location.z = -0.05 + 0.04 * k
    box('Cap', 0.034, 0.02, 0.012, (0.006, 0, -0.075), IRON, 0.003, rot=(0, 0.25, 0))

def flanged_mace():  # 15th c. flanged mace: seven iron flanges on a socket, iron haft with a leather grip
    cyl('Haft', 0.0135, -0.30, 0.30, IRON, 16, r1=0.013)
    grip_wrap(-0.30, -0.16, 0.0155, LEATHER)
    cyl('Socket', 0.022, 0.24, 0.38, IRON, 20, r1=0.019)
    for k in range(7):
        a = 2 * math.pi * k / 7
        fl_ = axe_head('Flange%d' % k, 0.018, 0.055, lambda f: 0.37 - 0.012 * f, lambda f: 0.25 + 0.02 * f ** 1.5,
                       lambda f: max(0.0012, 0.004 * (1 - f) + 0.0012), 0.012, IRON, NX=10, NZ=8)
        fl_.rotation_euler = (0, 0, a)
    sphere('Finial', 0.016, (0, 0, 0.392), IRON, (1, 1, 1.3))

def war_hammer():    # horseman's war hammer: square face, back beak, langets, leather grip
    cyl('Haft', 0.0145, -0.33, 0.33, OAK, 16, r1=0.014)
    grip_wrap(-0.33, -0.19, 0.016, LEATHER)
    box('Block', 0.04, 0.036, 0.05, (0, 0, 0.30), IRON, 0.004)
    box('Face', 0.035, 0.034, 0.034, (0.05, 0, 0.30), STEEL, 0.003)
    axe_head('Beak', -0.02, -0.12, lambda f: 0.318 - 0.012 * f, lambda f: 0.282 + 0.024 * f ** 0.8,
             lambda f: max(0.0012, 0.012 * (1 - f) ** 0.8), 0.0, STEEL, NX=16, NZ=8)
    blade('TopSpike', 0.09, 0.008, 0.05, 0.006, 0.003, z0=0.325, taper=0.9, m=STEEL)
    for s_ in (-1, 1): box('Langet', 0.005, 0.003, 0.18, (0, s_ * 0.0125, 0.19), IRON, 0.001)

def rondel_dagger(): # rondel dagger: stiff triangular-section blade, disc guard and pommel
    st = []
    for i in range(25):
        f = i / 24; z = 0.03 + 0.30 * f
        w = 0.011 * (1 - f) ** 0.9 + 0.0006
        st.append((z, w, 0.0055 * (1 - f) + 0.0007, 0.0003, 0.0))
    loft('Blade', st, STEEL)
    cyl('GuardDisc', 0.026, 0.018, 0.028, IRON, 24)
    grip_wrap(-0.075, 0.018, 0.0125, OAK)
    cyl('PommelDisc', 0.028, -0.09, -0.078, IRON, 24)

WEAPONS = {'arming_sword': ('ArmingSword', arming_sword), 'longsword': ('Longsword', longsword), 'falchion': ('Falchion', falchion),
           'flanged_mace': ('FlangedMace', flanged_mace), 'war_hammer': ('WarHammer', war_hammer), 'rondel_dagger': ('RondelDagger', rondel_dagger),
           'bearded_axe': ('BeardedAxe', bearded_axe), 'dane_axe': ('DaneAxe', dane_axe), 'war_axe': ('WarAxe', war_axe),
           'winged_spear': ('WingedSpear', winged_spear), 'boar_spear': ('BoarSpear', boar_spear), 'glaive': ('Glaive', glaive),
           'halberd': ('Halberd', halberd), 'bardiche': ('Bardiche', bardiche), 'partisan': ('Partisan', partisan), 'messer': ('Messer', messer)}
NAME, fn = WEAPONS[WEAPON]
fn()

# ======================================================================================= join, UV, bake
for o in parts:
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
obj = bpy.context.object; obj.name = 'SM_CK_' + NAME
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.6)
bpy.ops.object.mode_set(mode='OBJECT')
# v2 texel priority: the long wood/leather hafts were eating the UV square. Shrink their islands to 35 % (they read fine at
# lower density: grain runs along them), keep the metal at full size, then repack so the metal gets the space.
low = {i for i, m in enumerate(obj.data.materials) if m and m.name.split('.')[0] in ('Wood', 'Oak', 'Leather')}
uvl = obj.data.uv_layers.active.data
for p in obj.data.polygons:
    if p.material_index in low:
        for li in p.loop_indices: uvl[li].uv = uvl[li].uv * 0.35
sc_ts = bpy.context.scene.tool_settings; sc_ts.use_uv_select_sync = True      # pack every island, not only UV-selected ones
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
try:
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True, scale=True, shape_method='CONCAVE')
except TypeError:
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)

outd = os.path.join(OUT, NAME); os.makedirs(os.path.join(outd, 'textures'), exist_ok=True); os.makedirs(os.path.join(outd, 'renders'), exist_ok=True)
sc.render.engine = 'CYCLES'
cp = bpy.context.preferences.addons['cycles'].preferences
try:
    cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
    for d in cp.devices: d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
except Exception: pass

def new_img(n, alpha=False, non_color=False):
    im = bpy.data.images.new(n, TEX, TEX, alpha=alpha, float_buffer=False)
    if non_color: im.colorspace_settings.name = 'Non-Color'
    return im
def set_target(im):
    for m in obj.data.materials:
        N = m.node_tree.nodes; t = N.get('BakeTarget') or N.new('ShaderNodeTexImage'); t.name = 'BakeTarget'; t.image = im
        N.active = t
def emit_socket(sock_name):
    """route a Principled input (its link or value) into an Emission surface, remember the old output link"""
    for m in obj.data.materials:
        N, L = m.node_tree.nodes, m.node_tree.links; b = N['Principled BSDF']; out = N['Material Output']
        em = N.get('BakeEmit') or N.new('ShaderNodeEmission'); em.name = 'BakeEmit'
        for l in list(em.inputs['Color'].links): L.remove(l)
        s = b.inputs[sock_name]
        if s.is_linked:
            src = s.links[0].from_socket; L.new(src, em.inputs['Color'])
        else:
            v = s.default_value; em.inputs['Color'].default_value = (v, v, v, 1) if isinstance(v, float) else tuple(v)
        L.new(em.outputs['Emission'], out.inputs['Surface'])
def restore():
    for m in obj.data.materials:
        N, L = m.node_tree.nodes, m.node_tree.links; L.new(N['Principled BSDF'].outputs['BSDF'], N['Material Output'].inputs['Surface'])
sc.cycles.samples = SPP
sc.render.bake.margin = 8
obj.select_set(True); bpy.context.view_layer.objects.active = obj
def bake(kind, im):
    set_target(im); bpy.ops.object.bake(type=kind)

bc = new_img('BC'); emit_socket('Base Color'); bake('EMIT', bc)
rg = new_img('RG', non_color=True); emit_socket('Roughness'); bake('EMIT', rg)
mt = new_img('MT', non_color=True); emit_socket('Metallic'); bake('EMIT', mt)
restore()
aoi = new_img('AO', non_color=True); bake('AO', aoi)
nm = new_img('NM', non_color=True); sc.render.bake.normal_space = 'TANGENT'; bake('NORMAL', nm)

import numpy as np
def px(im):
    a = np.empty(TEX * TEX * 4, np.float32); im.pixels.foreach_get(a); return a.reshape(TEX, TEX, 4)
def save(arr, path, non_color=False):
    im = bpy.data.images.new(os.path.basename(path), TEX, TEX, alpha=False)
    if non_color: im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(arr.astype(np.float32).ravel()); im.filepath_raw = path; im.file_format = 'PNG'; im.save()
TN = 'T_CK_' + NAME
b_ = px(bc); b_[..., 3] = 1; save(b_, os.path.join(outd, 'textures', TN + '_BaseColor.png'))
orm = np.dstack([px(aoi)[..., 0], px(rg)[..., 0], px(mt)[..., 0], np.ones((TEX, TEX))])
save(orm, os.path.join(outd, 'textures', TN + '_ORM.png'), True)
n_ = px(nm); n_[..., 1] = 1 - n_[..., 1]; n_[..., 3] = 1                  # OpenGL -> DirectX (UE)
save(n_, os.path.join(outd, 'textures', TN + '_Normal_DirectX.png'), True)
# albedo gate (KB): non-metal 30-240 sRGB, bare metal >= 180 is checked on the material values above; report the baked range
lum = (b_[..., :3].mean(axis=2) * 255); used = lum[lum > 2]
print('ALBEDO sRGB p2/p50/p98: %.0f %.0f %.0f' % tuple(np.percentile(used, (2, 50, 98))))

# ======================================================================================= FBX + preview render
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(outd, 'SM_CK_%s.fbx' % NAME), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                         axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_space_transform=True)
zs = [ (obj.matrix_world @ v.co).z for v in obj.data.vertices ]; zmin, zmax = min(zs), max(zs); L_ = zmax - zmin
def area(name, loc, energy, color, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, (zmin + zmax) / 2)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
mid = (zmin + zmax) / 2
area('Key', (-1.2 * L_, -1.6 * L_, mid + 0.8 * L_), 120 * L_ * L_, (1.0, 0.88, 0.74), 0.8 * L_)
area('Rim', (1.4 * L_, 1.2 * L_, mid + 0.4 * L_), 160 * L_ * L_, (0.72, 0.82, 1.0), 0.4 * L_)
area('Fill', (1.4 * L_, -1.3 * L_, mid - 0.3 * L_), 18 * L_ * L_, (1, 1, 1), 1.2 * L_)
bpy.ops.mesh.primitive_plane_add(size=6 * L_, location=(0, 0.6 * L_, mid), rotation=(math.pi / 2, 0, 0))
card = bpy.context.object; cm = bpy.data.materials.new('Grey18'); cm.use_nodes = True
cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1)
cm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9; card.data.materials.append(cm)
obj.rotation_euler = (0, math.radians(-90 + 18), math.radians(-28))         # lay it diagonally, edge toward the key
cam_d = bpy.data.cameras.new('Cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = L_ * 1.08
cam = bpy.data.objects.new('Cam', cam_d); col.objects.link(cam); sc.camera = cam
cam.location = (0, -3 * L_, mid); cam.rotation_euler = (math.pi / 2, 0, 0)
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
cx_, cz_ = sum(v.x for v in bb) / 8, sum(v.z for v in bb) / 8
cam.location.x, cam.location.z = cx_, cz_
cam_d.ortho_scale = max(max(v.x for v in bb) - min(v.x for v in bb), (max(v.z for v in bb) - min(v.z for v in bb)) * 16 / 9) * 1.1
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05
sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.render.filepath = os.path.join(outd, 'renders', '%s_preview.png' % WEAPON); bpy.ops.render.render(write_still=True)
print('WEAPON DONE', NAME, 'tris', tris, 'length_m %.3f' % L_)
