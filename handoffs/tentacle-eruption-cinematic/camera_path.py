# First-eruption camera (adjustedfilm, 2026-11-06): numbers for BP_TentacleEruption, no Sequencer. blender -b --factory-startup -P camera_path.py -- <out png> [hero to base m]
# All in metres. H = hero on the ground, B = base centre on the ground. u = unit vector H to B on the ground, v = u turned 90 deg to the side with the clear trace (try +v, if a trace from H to the camera hits, use -v).
# Camera = H - back*u + side*v, height z above the ground. Look at = B, height look. Breach at t = 2.2 s. Between keys use smooth interpolation (smoothstep per segment). Hold hero input, keep the HUD, shake plays on top.
# t: 0 ground tell, low on the ground. 2.2 breach, nearly at the hero's heels, still looking low. 3.2 tilt up with the arm. 4.0 cut back to gameplay on the rise.
KEYS = [  # t, back, side, z, look, hFOV
 (0.0, 7.0, 2.4, 0.45, 2.0, 62.0),
 (2.2, 5.2, 2.0, 0.40, 9.0, 58.0),
 (3.2, 4.8, 1.9, 0.55, 18.0, 66.0),
 (4.0, 4.6, 1.8, 0.70, 24.0, 70.0),
]
# Far base rule: the arm must fill the shot, so if H to B is over 70 m, look only at 0.8 x the look height and narrow hFOV by 10 deg.
if __name__ == '__main__':
    import bpy, sys, math, os
    from mathutils import Vector
    a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; D = float(a[1]) if len(a) > 1 else 45.0; S = bpy.context.scene
    bpy.ops.wm.read_factory_settings(use_empty=True); S = bpy.context.scene; S.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'; S.render.resolution_x, S.render.resolution_y = 800, 450
    w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.62, 0.72, 1); S.world = w
    def mat(c):
        m = bpy.data.materials.new('m'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (*c, 1); return m
    bpy.ops.mesh.primitive_plane_add(size=800); bpy.context.object.data.materials.append(mat((0.25, 0.23, 0.2)))
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=16.0, radius2=1.0, depth=39.0, location=(D, 0, 19.5)); bpy.context.object.data.materials.append(mat((0.35, 0.12, 0.12)))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=30.0, depth=2.0, location=(D, 0, 1.0)); bpy.context.object.data.materials.append(mat((0.3, 0.28, 0.25)))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=1.8, location=(0, 0, 0.9)); bpy.context.object.data.materials.append(mat((0.75, 0.72, 0.6)))
    bpy.ops.object.light_add(type='SUN', rotation=(0.9, 0.2, 0.6)); bpy.context.object.data.energy = 3.0
    cd = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cd); S.collection.objects.link(co); S.camera = co; cd.sensor_fit = 'HORIZONTAL'; shots = []
    for (t, back, side, z, look, fov) in KEYS:
        if D > 70: look *= 0.8; fov -= 10.0
        p = Vector((-back, side, z)); q = Vector((D, 0, look)); co.location = p; co.rotation_euler = (q - p).to_track_quat('-Z', 'Y').to_euler(); cd.angle = math.radians(fov); f = OUT.replace('.png', '_%.1f.png' % t); S.render.filepath = f; bpy.ops.render.render(write_still=True); shots.append(f); print('CAM t %.1f pos %s look %s hFOV %.0f' % (t, tuple(round(v, 2) for v in p), tuple(round(v, 1) for v in q), fov))
