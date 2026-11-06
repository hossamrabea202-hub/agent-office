# #541 staging preview: blender -b --factory-startup -P rise_preview.py -- <base A.blend> <base B.blend> <mesh.fbx> <erupt.fbx> <out.mp4> [STILLS="1.5,2.5"]
# The hero's view walking out along the road. Same layout, timing, sizes and easing as the game script. Workbench stand-ins, not the game's look.
import bpy, sys, os, math, random
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; BA, BB, MESH, CLIP, OUT = a[:5]; STILLS = [float(x) for x in os.environ.get('STILLS', '').split(',') if x]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24; random.seed(5)
FPS, SEC = 24, 15.0; S, H, TOP = 1.8, 40.0, 80.0; GATE = -3.4
# metres. Hero walks -X at 6 m/s from the gate; triggers at 20 m and 45 m; the second waits for the first to finish
hero_x = lambda t: GATE - 6.0 * t
T1_START = 20.0 / 6.0; T1_BURST = T1_START + 1.3; T2_START = max(45.0 / 6.0, T1_BURST + 3.4 + 0.3); T2_BURST = T2_START + 1.3
SPOTS = [(BB, -52.0, 53.0, T1_BURST, 201), (BA, -95.0, -19.0, T2_BURST, 37)]
def eo(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def key_vis(o, f, on, scl=1.0):
    o.scale = (scl, scl, scl) if on else (0.0001, 0.0001, 0.0001); o.keyframe_insert('scale', frame=f)
act = None; F0 = 1
for BL, cx, cy, burst, yaw in SPOTS:
    with bpy.data.libraries.load(BL) as (fr, to): to.objects = [n for n in fr.objects if not n.startswith('UCX_') and not n.endswith('_Col')]
    b = next(o for o in to.objects if o); sc.collection.objects.link(b); size = 7.25 * S / 30.0; b.location = (cx, cy, -0.6); b.rotation_euler.z = math.radians(yaw)
    fb = F0 + int(burst * FPS); key_vis(b, fb - 1, False); key_vis(b, fb, True, size * 0.01)
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=MESH, use_anim=False); new = [o for o in bpy.data.objects if o not in before]; ar = next(o for o in new if o.type == 'ARMATURE'); tm = next(o for o in new if o.type == 'MESH')
    root = next(o for o in new if o.parent is None); root.scale = (S,) * 3; ar.scale = (1, 1, 1)  # the clip keys the armature's scale to 1
    c = tm.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); [setattr(d, 'color', (0.42, 0.13, 0.14, 1)) for d in c.data]
    if act is None:
        be = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=CLIP, use_anim=True); s_ = next(o for o in bpy.data.objects if o not in be and o.type == 'ARMATURE'); act = s_.animation_data.action; act.use_fake_user = True; [bpy.data.objects.remove(o, do_unlink=True) for o in bpy.data.objects if o not in be]
    final, start = -H * S, -TOP * S
    for f in range(F0, int(SEC * FPS) + 2):
        t = (f - F0) / FPS; u = (t - burst) / 3.4; root.location = (cx + 3.0 * S, cy - 1.1 * S, start + (final - start) * eo(u)); root.keyframe_insert('location', frame=f)
    ar.animation_data_create(); nla = ar.animation_data.nla_tracks.new(); st = nla.strips.new('e', fb, act); st.action_frame_start, st.action_frame_end = act.frame_range[0], act.frame_range[1]
    if act.slots: st.action_slot = act.slots[0]
    for k in range(24):                        # thrown rocks: same speed range as the game, in metres
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5 * random.uniform(1, 6)); o = bpy.context.object; col = o.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); [setattr(d, 'color', (0.14, 0.12, 0.1, 1)) for d in col.data]
        an = random.random() * 6.283; rr = 25 * random.random(); P0 = Vector((cx + rr * math.cos(an), cy + rr * math.sin(an), 15)); sp = random.uniform(22, 62); ang = math.radians(random.uniform(0, 48)); V = Vector((math.sin(ang) * math.cos(an), math.sin(ang) * math.sin(an), math.cos(ang))) * sp; g = 9.8 * 1.6
        for f in range(fb - 1, min(fb + 8 * FPS, int(SEC * FPS) + 1)):
            u = (f - fb) / FPS
            if u < 0: o.location = P0; o.scale = (0.001,) * 3
            else:
                p = P0 + V * u + Vector((0, 0, -0.5 * g * u * u)); land = p.z <= 0.4; o.location = (p.x, p.y, max(p.z, 0.4)); o.scale = (1, 1, 1)
            o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, 0)); g_ = bpy.context.object; col = g_.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); [setattr(d, 'color', (0.075, 0.062, 0.045, 1)) for d in col.data]
bpy.ops.mesh.primitive_cube_add(size=1, location=(-40, 17, 0.02)); r_ = bpy.context.object; r_.scale = (140, 8, 0.03); col = r_.data.color_attributes.new('Col', 'BYTE_COLOR', 'POINT'); [setattr(d, 'color', (0.12, 0.10, 0.075, 1)) for d in col.data]
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.lens = 20
for f in range(F0, int(SEC * FPS) + 2):
    t = (f - F0) / FPS; x = hero_x(t); shake = 0.0
    for b_ in (T1_BURST, T2_BURST):
        u = t - b_
        if 0 <= u < 1.5: shake += 0.5 * math.exp(-u * 2.5) * math.sin(u * 70)
    cam.location = (x + 32, 17 + shake, 5.0 + shake * 0.6); look = Vector((x - 40, 17, 26)); cam.rotation_euler = (look - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
sc.frame_start, sc.frame_end = F0, int(SEC * FPS) + 1
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = True; sh.show_shadows = True; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
w = bpy.data.worlds.new('w'); sc.world = w
print('TIMES', round(T1_START, 1), round(T1_BURST, 1), round(T2_START, 1), round(T2_BURST, 1))
if STILLS:
    for s in STILLS:
        sc.frame_set(F0 + int(s * FPS)); sc.render.filepath = OUT.replace('.mp4', '_%05.2fs.png' % s); sc.render.image_settings.file_format = 'PNG'; bpy.ops.render.render(write_still=True)
else:
    sc.render.image_settings.file_format = 'FFMPEG'; sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'; sc.render.filepath = OUT; bpy.ops.render.render(animation=True)
print('RISEPREV OK', OUT)
