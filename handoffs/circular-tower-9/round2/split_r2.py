"""Tower #9 round 2 (checkking 2026-10-28): axis fix + modular split.
Source: Tower9_Round1/x/.../Circular_Tower_09_Round1.blend (kept untouched; this script saves a versioned copy).
Axis: UE's FBX import mirrors Blender Y. Round-1 fit needed yaw 90 in UE; mirrorY o Rz(-90) == Rz(90) o mirrorY, so the
source is ROTATED -90 deg about Z here (no mirroring, design handedness kept) and the parts place at yaw 0, (50,50,0).
Export settings unchanged from Codex (apply_unit_scale, forward -Y, up Z). Run: blender -b <src.blend> --python split_r2.py"""
import bpy, math, json, os
from mathutils import Matrix

OUT = r'C:/Unreal Backups/Castle Defender/Tools/Tower9_R2'
GROUPS = [  # part name, object-name prefixes
    ('Drum', ('Ashlar_shell', 'Structural_drum', 'Footing', 'Plinth', 'Lower_string', 'Wallwalk_string', 'Crown_lower', 'Crown_upper')),
    ('Floors', ('Wallwalk_floor', 'Cannon_deck', 'Mid_landing', 'Roof_arrival_landing')),
    ('Stairs', ('Stair_A_', 'Stair_B_')),
    ('Iron', ('Rail_post', 'Roof_guard_post', 'Roof_stair_guard', 'Stair_handrail', 'Stair_stringer')),
    ('Parapet', ('Parapet_breastwork', 'Merlon_')),
    ('Portals', ('Portal_jamb', 'Voussoir')),
]
ROT = Matrix.Rotation(math.radians(-90.0), 4, 'Z')

# 2026-10-28 owner: the U-turn at the mid landing was too tight for the hero (64 cm landing, inner posts Rail_post.009/.010
# at y 1.80, roof deck from y 2.30). Remove those two posts and end both inner handrails at the y 0.90 posts, so the hero
# turns across the top treads under the open hatch.
for nm in ('Rail_post.009', 'Rail_post.010'):
    bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
# (+ flight B's inner stringer: its low end stood ~15 cm proud of the landing right in the crossing path -> end it at y 1.20)
for nm, end in (('Stair_handrail.001', 0.95), ('Stair_handrail.002', 0.95), ('Stair_stringer.002', 1.20)):
    o = bpy.data.objects[nm]; mw = o.matrix_world; inv = mw.inverted()
    ws = [mw @ v.co for v in o.data.vertices]
    ymax = max(w.y for w in ws)
    lo, hi = min(ws, key=lambda w: w.y), max(ws, key=lambda w: w.y)
    slope = (hi.z - lo.z) / (hi.y - lo.y)
    cut = ymax - end
    for v, w in zip(o.data.vertices, ws):
        if w.y > ymax - 0.10:                                  # end-cap vertices only
            w2 = w.copy(); w2.y -= cut; w2.z -= cut * slope
            v.co = inv @ w2
    o.data.update()
src = [o for o in bpy.data.collections['TOWER_09_REVIEW'].objects if o.type == 'MESH']
used = set()
report = {'rotation_deg_z': -90, 'export': {'axis_forward': '-Y', 'axis_up': 'Z', 'apply_unit_scale': True}, 'parts': {}}
for part, prefixes in GROUPS:
    objs = [o for o in src if o.name.startswith(prefixes)]
    used.update(o.name for o in objs)
    bpy.ops.object.select_all(action='DESELECT')
    dups = []
    for o in objs:
        d = o.copy(); d.data = o.data.copy(); bpy.context.scene.collection.objects.link(d); dups.append(d)
    for d in dups:
        d.select_set(True)
    bpy.context.view_layer.objects.active = dups[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = 'SM_Tower09_' + part
    j.matrix_world = ROT @ j.matrix_world
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    j.data.update()
    # perf: the 7 preview limestone variants + mortar all get the same castle wall stone in UE -> one slot (draw calls 9 -> 2)
    mats = list(j.data.materials)
    if any(m and m.name.startswith(('Limestone', 'Mortar')) for m in mats):
        wall = bpy.data.materials.get('Limestone_Wall') or bpy.data.materials.new('Limestone_Wall')
        keep = [m for m in mats if m and not m.name.startswith(('Limestone', 'Mortar'))]
        new = [wall] + keep
        remap = [new.index(wall) if (m and m.name.startswith(('Limestone', 'Mortar'))) else new.index(m) for m in mats]
        idx = [remap[p.material_index] for p in j.data.polygons]
        j.data.materials.clear()
        for m in new:
            j.data.materials.append(m)
        for p, k in zip(j.data.polygons, idx):
            p.material_index = k
    xs = [v.co for v in j.data.vertices]
    bb = [[round(min(c[i] for c in xs), 3), round(max(c[i] for c in xs), 3)] for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in j.data.polygons)
    report['parts'][part] = {'objects': len(objs), 'tris': tris, 'bounds_m': bb, 'materials': sorted({m.name for m in j.data.materials if m})}
    bpy.ops.object.select_all(action='DESELECT'); j.select_set(True)
    # hard edges above 30 deg: smooth ring bands were averaging their riser normals with the top faces, and the castle's
    # world-aligned (triplanar) stone then sampled the top projection on vertical faces = vertical streaks in UE
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30.0), keep_sharp_edges=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'fbx', j.name + '.fbx'), use_selection=True, object_types={'MESH'},
                             apply_unit_scale=True, axis_forward='-Y', axis_up='Z', mesh_smooth_type='OFF')
report['unassigned'] = sorted(o.name for o in src if o.name not in used)

# asymmetric axis/portal marker fixture (same rotation + export path): long bar = Blender +X, short bar = Blender +Y,
# post = +Z, plus cubes at the two portal centres (Blender +X / +Y portals before rotation, 680 cm floor)
def box(name, loc, size):
    bpy.ops.mesh.primitive_cube_add(location=loc); b = bpy.context.object; b.scale = [s / 2 for s in size]; b.name = name; return b
marks = [box('MK_PlusX_long', (3.0, 0, 0.1), (6.0, 0.2, 0.2)), box('MK_PlusY_short', (0, 1.5, 0.1), (0.2, 3.0, 0.2)),
         box('MK_PlusZ_post', (0, 0, 2.0), (0.2, 0.2, 4.0)),
         box('MK_PortalX', (4.9, 1.4, 6.8 + 1.0), (0.3, 0.3, 2.0)), box('MK_PortalY', (1.4, 4.9, 6.8 + 1.0), (0.3, 0.3, 2.0))]
bpy.ops.object.select_all(action='DESELECT')
for m in marks:
    m.select_set(True)
bpy.context.view_layer.objects.active = marks[0]
bpy.ops.object.join()
mk = bpy.context.view_layer.objects.active; mk.name = 'SM_Tower09_AxisMarkers'
mk.matrix_world = ROT @ mk.matrix_world
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.select_all(action='DESELECT'); mk.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'fbx', 'SM_Tower09_AxisMarkers.fbx'), use_selection=True, object_types={'MESH'},
                         apply_unit_scale=True, axis_forward='-Y', axis_up='Z')
report['markers_after_rotation_m'] = {'PlusX_long_end': [0, -6.0, 0.1], 'PlusY_short_end': [3.0, 0, 0.1],
                                      'PortalX_centre': [1.4, -4.9, 7.8], 'PortalY_centre': [4.9, -1.4, 7.8]}
report['blender'] = bpy.app.version_string
json.dump(report, open(os.path.join(OUT, 'split_report.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Circular_Tower_09_R2_split.blend'), copy=True)
print('SPLIT OK')
