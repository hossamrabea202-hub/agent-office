# #296 (adjustedfilm, 2026-10-31): give laptop2's SM_Camp_MineEntrance two material slots, rock (0) and timber/iron/rest (1),
# so the rock can take the scanned cave material (M_CaveRock) while the timber keeps its baked texture.
#   blender -b --factory-startup -P split_entrance.py -- <in.fbx> <BaseColor.png> <out_dir>
# Each loose part is classed by the mean colour of its own baked BaseColor (sampled at its face UV centres): grey / low
# saturation = rock, brown or saturated or metal-dark = other. Writes SM_Camp_MineEntrance_Split.fbx (same pivot, UVs, normals)
# and split_check.png (rock grey-blue, other orange) to check the classing.
import bpy, bmesh, sys, os, colorsys, math, mathutils

argv = sys.argv[sys.argv.index('--') + 1:]
FBX, BC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1]), os.path.abspath(argv[2])
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
img = bpy.data.images.load(BC); W, H = img.size; px = img.pixels[:]


def sample(u, v):
    x = min(W - 1, max(0, int((u % 1.0) * W))); y = min(H - 1, max(0, int((v % 1.0) * H)))
    i = (y * W + x) * 4
    return px[i], px[i + 1], px[i + 2]


bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
uv = bm.loops.layers.uv.active
# loose parts by flood fill over shared edges
seen, parts = set(), []
for f in bm.faces:
    if f.index in seen: continue
    stack, part = [f], []
    seen.add(f.index)
    while stack:
        g = stack.pop(); part.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: seen.add(h.index); stack.append(h)
    parts.append(part)
rock_faces, stats = set(), []
for part in parts:
    cols = []
    for f in part[:: max(1, len(part) // 200)]:
        uu = sum(l[uv].uv.x for l in f.loops) / len(f.loops); vv = sum(l[uv].uv.y for l in f.loops) / len(f.loops)
        cols.append(sample(uu, vv))
    r = sum(c[0] for c in cols) / len(cols); g = sum(c[1] for c in cols) / len(cols); b = sum(c[2] for c in cols) / len(cols)
    h, s, val = colorsys.rgb_to_hsv(r, g, b)
    area = sum(f.calc_area() for f in part)
    vs = [v.co for f in part for v in f.verts]
    ext = [max(c[i] for c in vs) - min(c[i] for c in vs) for i in range(3)]
    thin = min(ext) < 0.2 * max(ext)                # boards, slabs, rails: never rock
    is_rock = s < 0.17 and val > 0.12 and not thin  # grey stone; timber is brown (s > ~0.25), iron is dark
    stats.append((len(part), round(area, 2), round(s, 2), round(val, 2), is_rock))
    if is_rock: rock_faces.update(f.index for f in part)
# the biggest part is the hill: always rock
big = max(parts, key=len); rock_faces.update(f.index for f in big)
me = ob.data
while len(me.materials) < 2: me.materials.append(None)
mr = bpy.data.materials.new('M_Rock'); mo = bpy.data.materials.new('M_Timber')
me.materials[0] = mr; me.materials[1] = mo
for f in bm.faces: f.material_index = 0 if f.index in rock_faces else 1
bm.to_mesh(me); bm.free()
print('parts', len(parts), 'rock faces', len(rock_faces), 'of', len(me.polygons))
for s_ in sorted(stats, key=lambda t: -t[0])[:25]: print('  part faces %5d area %7.2f sat %.2f val %.2f rock %s' % s_)
ob.name = 'SM_Camp_MineEntrance_Split'; ob.data.name = ob.name
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'SM_Camp_MineEntrance_Split.fbx'), use_selection=True, apply_unit_scale=True,
                         mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, path_mode='STRIP', axis_forward='-Y', axis_up='Z')   # = laptop2's export
# check render: rock grey-blue, other orange
for m, c in ((mr, (0.35, 0.4, 0.5, 1)), (mo, (0.9, 0.35, 0.05, 1))):
    m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = c
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'EEVEE_NEXT') or bpy.app.version >= (4, 2, 0) else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1280, 900
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(30))); bpy.context.object.data.energy = 3
d = max(ob.dimensions)
bpy.ops.object.camera_add(location=(d * 1.3, -d * 1.0, d * 0.8)); cam = bpy.context.object
cam.rotation_euler = (mathutils.Vector((0, 0, ob.dimensions.z * 0.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
sc.render.filepath = os.path.join(OUT, 'split_check.png'); bpy.ops.render.render(write_still=True)
print('wrote', sc.render.filepath)
