# look renders: blender -b X.blend -P render_heater.py -- out_prefix [clay|mat|keep]
#   clay = grey, mat = build the procedural shieldmat materials (high poly), keep = materials in the file (baked low)
import bpy, sys, math, mathutils, os
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; mode = args[1] if len(args) > 1 else 'clay'
D = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ['KITDIR']
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '64')); sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('RW', '1200')), int(os.environ.get('RH', '1200'))
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '0'))
if mode == 'mat':
    sys.path.insert(0, os.environ.get('KITDIR', D)); import shieldmat, swordmat, potionmat, gatemat, floramat, propmat, ballistamat; (swordmat if os.environ.get('SHIELD') == 'Sword' else potionmat if os.environ.get('VIEWSET') == 'potion' else gatemat if os.environ.get('VIEWSET') == 'gate' else floramat if os.environ.get('VIEWSET') == 'flora' else propmat if os.environ.get('VIEWSET') == 'props' else ballistamat if os.environ.get('SHIELD') == 'Ballista' else shieldmat).build_all()
elif mode == 'clay':
    for m in bpy.data.materials:
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        b = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(b.outputs[0], o.inputs[0])
        b.inputs['Base Color'].default_value = (0.45, 0.45, 0.45, 1); b.inputs['Roughness'].default_value = 0.6
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.45, 0.5, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.85
if os.environ.get('VIEWSET') == 'sword':   # metal needs something to reflect: a real sky instead of flat grey
    nt_ = w.node_tree; sky = nt_.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(140)
    nt_.links.new(sky.outputs[0], nt_.nodes['Background'].inputs['Color']); nt_.nodes['Background'].inputs['Strength'].default_value = 0.25
    gp = bpy.data.meshes.new('floor'); gp.from_pydata([(-5, -5, -0.3), (5, -5, -0.3), (5, 5, -0.3), (-5, 5, -0.3)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('floor', gp); sc.collection.objects.link(go); gm = bpy.data.materials.new('floorM'); gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.08, 0.07, 0.06, 1); gp.materials.append(gm)
def light(name, kind, energy, rot, size=None):
    l = bpy.data.lights.new(name, kind); l.energy = energy
    if size: l.size = size
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(v) for v in rot]; return o
k = light('Key', 'SUN', 3.2, tuple(float(v) for v in os.environ.get('KEYROT', '55,0,-40').split(','))); k.data.angle = math.radians(4)
r = light('Rim', 'SUN', 1.6, (-60, 0, 150)); r.data.angle = math.radians(8)
if os.environ.get('LOOKDEV') == '1':
    # calibrated lookdev (playbook rank 2): physical sky, fixed exposure, grey ball (albedo 0.18), chrome ball and a
    # 24-patch colour chart beside the asset, sized from its bounds. Judge assets only here.
    import numpy as _np
    nt_ = w.node_tree; sky = nt_.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(150)
    nt_.links.new(sky.outputs[0], nt_.nodes['Background'].inputs['Color']); nt_.nodes['Background'].inputs['Strength'].default_value = 0.18
    for o in [o for o in sc.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o)
    mn = _np.array([1e9] * 3); mx = -mn
    for o in sc.objects:
        if o.type == 'MESH':
            for c in o.bound_box:
                v = o.matrix_world @ mathutils.Vector(c); mn = _np.minimum(mn, v); mx = _np.maximum(mx, v)
    hgt = float(mx[2] - mn[2]); r = max(min(hgt * 0.07, 0.25), 0.02); x0 = float(mx[0]) + r * 2.5; y0 = float(mn[1])
    def ball(name, loc, mk):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24); o = bpy.context.object; o.name = name
        bpy.ops.object.shade_smooth(); m = bpy.data.materials.new(name); m.use_nodes = True; b_ = m.node_tree.nodes['Principled BSDF']; mk(b_); o.data.materials.append(m)
    ball('LD_Grey', (x0, y0, float(mn[2]) + r), lambda b_: (b_.inputs['Base Color'].__setattr__('default_value', (0.18, 0.18, 0.18, 1)), b_.inputs['Roughness'].__setattr__('default_value', 0.9)))
    ball('LD_Chrome', (x0, y0, float(mn[2]) + r * 3.3), lambda b_: (b_.inputs['Metallic'].__setattr__('default_value', 1.0), b_.inputs['Roughness'].__setattr__('default_value', 0.02), b_.inputs['Base Color'].__setattr__('default_value', (0.95, 0.95, 0.95, 1))))
    chart = [(115,82,68),(194,150,130),(98,122,157),(87,108,67),(133,128,177),(103,189,170),(214,126,44),(80,91,166),(193,90,99),(94,60,108),(157,188,64),(224,163,46),
             (56,61,150),(70,148,73),(175,54,60),(231,199,31),(187,86,149),(8,133,161),(243,243,242),(200,200,200),(160,160,160),(122,122,121),(85,85,85),(52,52,52)]
    cs = r * 0.55
    for k, (R, G, B) in enumerate(chart):
        bpy.ops.mesh.primitive_plane_add(size=cs * 0.92, location=(x0 + r * 1.5 + (k % 6) * cs, y0 - 0.001, float(mn[2]) + r * 0.6 + (3 - k // 6) * cs))
        o = bpy.context.object; o.rotation_euler = (math.radians(90), 0, 0)
        m = bpy.data.materials.new('LD_%d' % k); m.use_nodes = True; b_ = m.node_tree.nodes['Principled BSDF']
        b_.inputs['Base Color'].default_value = tuple(((c / 255) ** 2.2) for c in (R, G, B)) + (1,); b_.inputs['Roughness'].default_value = 0.85
        o.data.materials.append(m)
    sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '0'))
    if os.environ.get('METER', '1') == '1':
        # meter: render only the grey ball in the Standard (linear) transform, set exposure so it averages 0.18
        import numpy as _np2
        gb = bpy.data.objects['LD_Grey']; hidden = []
        for o in sc.objects:
            if o.type == 'MESH' and o is not gb and not o.hide_render: o.hide_render = True; hidden.append(o)
        mc = bpy.data.objects.new('MeterCam', bpy.data.cameras.new('MeterCam')); sc.collection.objects.link(mc); sc.camera = mc
        mc.data.lens = 85; d_ = mathutils.Vector((-0.6, -1.0, 0.45)).normalized(); mc.location = gb.location + d_ * r * 14
        mc.rotation_euler = (-d_).to_track_quat('-Z', 'Y').to_euler()
        rx, ry, pct = sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage
        sc.render.resolution_x = sc.render.resolution_y = 96; sc.render.resolution_percentage = 100
        sc.render.film_transparent = True; vt = sc.view_settings.view_transform; sc.view_settings.view_transform = 'Standard'
        ex0 = sc.view_settings.exposure; sc.view_settings.exposure = 0.0; smp = sc.cycles.samples; sc.cycles.samples = 16
        sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'
        mp = os.path.join(os.environ.get('TEMP', '.'), 'meter.exr'); sc.render.filepath = mp; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(mp); px = _np2.empty(96 * 96 * 4, _np2.float32); im.pixels.foreach_get(px); px = px.reshape(-1, 4)
        ball = px[px[:, 3] > 0.5][:, :3].mean(); ev = math.log2(0.18 / max(ball, 1e-6))
        sc.view_settings.exposure = ex0 + ev; print('METER grey ball %.4f -> exposure %+.2f EV' % (ball, sc.view_settings.exposure))
        bpy.data.images.remove(im); sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = rx, ry, pct
        sc.render.film_transparent = False; sc.view_settings.view_transform = vt; sc.cycles.samples = smp
        for o in hidden: o.hide_render = False
        bpy.data.objects.remove(mc)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 60
views = {'front': ((0.0, -2.2, 0.44), (0, 0.03, 0.42)), 'front34': ((-1.25, -1.75, 0.95), (0, 0.03, 0.42)),
         'back34': ((1.2, 1.8, 0.85), (0.02, 0.03, 0.45)), 'side': ((2.1, -0.35, 0.55), (0, 0.03, 0.42)),
         'close_paint': ((-0.25, -0.62, 0.62), (0.02, 0.0, 0.42)), 'close_arrow': ((-0.35, -0.42, 0.50), (0.10, -0.03, 0.33)),
         'close_grip': ((0.30, 0.48, 0.60), (0.03, 0.04, 0.49)), 'close_rim': ((-0.55, -0.45, 0.98), (-0.20, 0.02, 0.76))}
if os.environ.get('VIEWSET') == 'sword':
    views = {'full': ((0.95, -1.10, 0.35), (0, 0, 0.20)), 'side': ((1.45, -0.05, 0.20), (0, 0, 0.20)),
             'close_hilt': ((0.16, -0.26, 0.06), (0, 0, -0.04)), 'close_blade': ((0.10, -0.22, 0.30), (0, 0, 0.22)),
             'close_pommel': ((0.05, -0.16, -0.10), (0, 0, -0.118)), 'close_guard': ((0.10, -0.18, 0.05), (0, 0, 0.015))}

def potion_glass():   # the potions' glass and liquid slots get preview materials (UE has its own translucent ones)
    lc = (0.75, 0.04, 0.03) if 'Health' in bpy.data.filepath else (0.12, 0.65, 0.08)
    for m in bpy.data.materials:
        if m.name.startswith('M_PotionGlass') or m.name.startswith('M_PotionLiquid'):
            m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF') or m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            o = m.node_tree.nodes.get('Material Output') or m.node_tree.nodes.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(b.outputs[0], o.inputs[0])
            if 'Glass' in m.name:
                b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.04; b.inputs['IOR'].default_value = 1.48
            else:
                b.inputs['Transmission Weight'].default_value = 0.85; b.inputs['Base Color'].default_value = (*lc, 1); b.inputs['Roughness'].default_value = 0.1
                b.inputs['Emission Color'].default_value = (*lc, 1); b.inputs['Emission Strength'].default_value = 0.6
if os.environ.get('VIEWSET') in ('flora', 'props', 'auto'):   # auto-framed from the bounds: a 3/4 view and a close-up of the top third
    import numpy as _np3
    mn = _np3.array([1e9] * 3); mx = -mn
    for o in sc.objects:
        if o.type == 'MESH' and not o.name.startswith('LD_'):
            for c_ in o.bound_box:
                v_ = o.matrix_world @ mathutils.Vector(c_); mn = _np3.minimum(mn, v_); mx = _np3.maximum(mx, v_)
    ctr = (mn + mx) / 2; ext = float(max(mx - mn)); top = _np3.array([ctr[0], ctr[1], mn[2] + (mx[2] - mn[2]) * 0.8])
    views = {'f34': ((ctr[0] - ext * 1.2, ctr[1] - ext * 1.9, ctr[2] + ext * 0.7), tuple(ctr)),
             'close': ((top[0] - ext * 0.35, top[1] - ext * 0.6, top[2] + ext * 0.25), tuple(top)),
             'top': ((ctr[0] + ext * 0.1, ctr[1] - ext * 0.9, ctr[2] + ext * 2.0), tuple(ctr))}
if os.environ.get('VIEWSET') == 'gate':
    views = {'front': ((0.0, -9.5, 2.0), (0, 0, 2.1)), 'g34': ((-5.5, -7.5, 3.2), (0, 0, 2.0)), 'back': ((4.5, 7.5, 2.6), (-0.6, 0, 1.9)),
             'close_rot': ((1.2, -2.4, 0.7), (0.9, 0, 0.45)), 'close_hinge': ((-2.2, -1.9, 1.1), (-2.7, 0, 0.55)), 'lever': ((-6.4, 3.2, 2.0), (-4.3, 0.5, 1.4))}
if os.environ.get('VIEWSET') == 'potion':
    potion_glass()
    views = {'front': ((0.0, -0.42, 0.10), (0, 0, 0.065)), 'p34': ((-0.22, -0.34, 0.16), (0, 0, 0.065)),
             'close_top': ((-0.06, -0.14, 0.15), (0, 0, 0.11)), 'close_tag': ((0.03, -0.12, 0.08), (0.004, -0.012, 0.085))}
    lc = (0.75, 0.04, 0.03) if 'Health' in bpy.data.filepath else (0.12, 0.65, 0.08)
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name not in ('Glass', 'Liquid'): continue
        m = bpy.data.materials.new('P_' + o.name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        if o.name == 'Glass':
            b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.04; b.inputs['IOR'].default_value = 1.48
            b.inputs['Base Color'].default_value = (0.92, 0.95, 0.92, 1)
        else:
            b.inputs['Transmission Weight'].default_value = 0.85; b.inputs['Base Color'].default_value = (*lc, 1); b.inputs['Roughness'].default_value = 0.1
            b.inputs['Emission Color'].default_value = (*lc, 1); b.inputs['Emission Strength'].default_value = 0.6
        o.data.materials.clear(); o.data.materials.append(m)
for kk, (p, t) in views.items():
    if os.environ.get('VIEWS') and kk not in os.environ['VIEWS'].split(','): continue
    cam.location = p; d = mathutils.Vector(t) - mathutils.Vector(p); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 85 if kk.startswith('close') else 60
    if os.environ.get('VIEWSET') == 'potion': cam.data.lens = 70
    if os.environ.get('VIEWSET') == 'gate': cam.data.lens = 35 if not kk.startswith('close') else 50
    if os.environ.get('VIEWSET') in ('flora', 'props', 'auto'): cam.data.lens = 50
    sc.render.filepath = out + '_' + kk + '.png'; bpy.ops.render.render(write_still=True)
print('RENDER OK')
