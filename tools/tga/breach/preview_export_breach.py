# Breach preview strip + FBX export (#327, TGA): blender -b breach.blend -P preview_export_breach.py   (env WORK, SAMPLES, NOEXPORT)
# Preview: 6 frames of A_WallBreach_Collapse (0, 0.25, 0.5, 0.8, 1.3, 2.5 s) from inside the castle, one strip JPG.
# Export: SK_WallBreach (rig + mesh + the A_WallBreach_Collapse action) and SM_Rubble_Masonry_01..06 (each at the origin).
import bpy, os, math, numpy as np
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(bpy.data.filepath)); OUT = os.path.join(D, 'out'); os.makedirs(OUT, exist_ok=True)
TEX = os.path.join(D, 'out', 'tex'); sc = bpy.context.scene
arm, mesh = bpy.data.objects['SK_WallBreach_Rig'], bpy.data.objects['SK_WallBreach']
rubble = [o for o in bpy.data.objects if o.name.startswith('SM_Rubble_Masonry_')]
if not os.environ.get('NOEXPORT'):
    fbx = os.path.join(OUT, 'fbx'); os.makedirs(fbx, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=os.path.join(fbx, 'SK_WallBreach.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'}, mesh_smooth_type='FACE',
                             use_tspace=True, apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
                             bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0)
    for o in rubble:
        keep = o.location.copy(); o.location = (0, 0, 0); bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.export_scene.fbx(filepath=os.path.join(fbx, o.name + '.fbx'), use_selection=True, object_types={'MESH'}, mesh_smooth_type='FACE',
                                 use_tspace=True, apply_scale_options='FBX_SCALE_UNITS', add_leaf_bones=False, bake_anim=False)
        o.location = keep
    print('EXPORTED SK_WallBreach + %d rubble' % len(rubble), flush=True)
# ---- preview
for o in rubble: o.hide_render = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '48')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 640, 420
def setmat(m, bc_rgb=None, tex=None):
    m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, tex)); nt.links.new(t.outputs[0], bs.inputs['Base Color'])
    else: bs.inputs['Base Color'].default_value = bc_rgb
    bs.inputs['Roughness'].default_value = 0.85
setmat(bpy.data.materials['M_WallStone'], (0.22, 0.17, 0.12, 1)); setmat(bpy.data.materials['M_WallFracture'], tex='T_BreachFracture_BC.png')
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); g = bpy.context.active_object
gm = bpy.data.materials.new('G'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.1, 0.08, 1); g.data.materials.append(gm)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(55), 0, math.radians(120))); bpy.context.active_object.data.energy = 4
wd = bpy.data.worlds.new('W'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.55, 0.62, 1)
bpy.ops.object.camera_add(location=(-17, -9, 5.5)); cam = bpy.context.active_object; sc.camera = cam; cam.data.lens = 28
tg = bpy.data.objects.new('t', None); tg.location = (-3.5, 0, 2.0); sc.collection.objects.link(tg)
c = cam.constraints.new('TRACK_TO'); c.target = tg; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
tiles = []
for sec in (0.0, 0.25, 0.5, 0.8, 1.3, 2.5):
    f = 1 + int(round(sec * sc.render.fps)); sc.frame_set(min(f, sc.frame_end))
    p = os.path.join(OUT, 'pv_%02d.png' % f); sc.render.filepath = p; sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True); im = bpy.data.images.load(p); w, h = im.size
    a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); tiles.append(a.reshape(h, w, 4)); bpy.data.images.remove(im)
strip = np.concatenate([np.concatenate(tiles[:3], 1), np.concatenate(tiles[3:], 1)], 0)   # rows are bottom-up in Blender
strip = np.concatenate([np.concatenate(tiles[3:], 1), np.concatenate(tiles[:3], 1)], 0)
H_, W_ = strip.shape[:2]; im = bpy.data.images.new('strip', W_, H_); im.pixels.foreach_set(strip.ravel())
im.filepath_raw = os.path.join(OUT, 'breach_collapse_strip.png'); im.file_format = 'PNG'; im.save(); print('PREVIEW', im.filepath_raw, flush=True)
