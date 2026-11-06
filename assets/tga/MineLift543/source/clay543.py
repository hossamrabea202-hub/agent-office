# Clay / silhouette checks for #543 (TGA PC). blender -b work/mine543.blend -P clay543.py   env VIEW sword|bucket|door|room|shaft|bottom
import bpy, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(bpy.data.filepath); VIEW = os.environ.get('VIEW', 'sword'); sc = bpy.context.scene
O = bpy.data.objects
clay = bpy.data.materials.new('clay'); clay.use_nodes = True; clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1)
clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
for o in O:
    if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(clay); o.hide_render = True
def show(*names):
    for n in names: O[n].hide_render = False
# kit layout in the top set (the same numbers the UE placement script uses)
DOOR_X, SHAFT = 1.2, Vector((3.9, 0, 0))
O['SM_MineShaft_Cribbing_Top'].location = SHAFT; O['SM_MineShaft_Collar'].location = SHAFT
O['SM_MineWindlass_Drum'].location = SHAFT + Vector((0.22, 0, 1.15))
O['SM_MineBucket'].location = SHAFT + Vector((0.0, 0, 1.15 - 0.2 - 0.16 - 1.83))
O['SM_MineRope_1m'].location = O['SM_MineBucket'].location + Vector((0, 0, 1.83)); O['SM_MineRope_1m'].scale.z = 0.36
O['SM_MineGate_Door'].location = (DOOR_X, -0.6, 0); O['SM_MineGate_Door'].rotation_euler.z = math.radians(80)   # open, swung into the room
O['SM_MineGate_Bulkhead'].location = (DOOR_X, 0, 0)
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
def look(p, t, lens=35):
    cam.location = p; cd.lens = lens; cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (0.7, 0.2, 0.9)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.4
def lamp(p, e=60):
    L = bpy.data.objects.new('L', bpy.data.lights.new('L', 'POINT')); L.data.energy = e; L.data.color = (1, 0.7, 0.45); L.location = p; sc.collection.objects.link(L)
if VIEW == 'sword':
    show('SM_Ulfberht'); O['SM_Ulfberht'].rotation_euler = (0, math.radians(90), 0); look((0, -1.6, 0.0), (0, 0, 0.0), 50); sc.render.resolution_x, sc.render.resolution_y = 1800, 600
    cd.type = 'ORTHO'; cd.ortho_scale = 1.15
elif VIEW == 'bucket':
    show('SM_MineBucket', 'SM_MineWindlass_Drum', 'SM_MineShaft_Collar', 'SM_MineRope_1m')
    for n in ('SM_MineBucket', 'SM_MineWindlass_Drum', 'SM_MineShaft_Collar', 'SM_MineRope_1m'): O[n].location -= SHAFT
    O['SM_MineBucket'].location.z += 0.2; O['SM_MineRope_1m'].location.z += 0.2
    look((-3.2, -3.0, 2.2), (0, 0, 0.3), 35)
elif VIEW == 'door':
    show('SM_MineGate_Door', 'SM_MineGate_Bulkhead'); O['SM_MineGate_Door'].rotation_euler.z = math.radians(25); look((3.0, -1.6, 1.4), (1.2, 0, 1.2), 35)
elif VIEW == 'room':
    show('SM_MineShaft_Top', 'SM_MineShaft_Cribbing_Top', 'SM_MineShaft_Collar', 'SM_MineWindlass_Drum', 'SM_MineBucket', 'SM_MineRope_1m', 'SM_MineGate_Door', 'SM_MineGate_Bulkhead')
    sun.hide_render = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    lamp((2.2, -1.8, 2.3), 120); lamp((5.6, 1.9, 2.4), 90); lamp((3.9, 0.9, -3.0), 40)
    look((1.6, 1.9, 1.75), (3.9, -0.3, 0.2), 20)
elif VIEW == 'shaft':
    show('SM_MineShaft_Top', 'SM_MineShaft_Cribbing_Top', 'SM_MineBucket', 'SM_MineRope_1m')
    sun.hide_render = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    O['SM_MineBucket'].location.z -= 6.0; O['SM_MineRope_1m'].location.z -= 6.0; O['SM_MineRope_1m'].scale.z = 6.36
    lamp(O['SM_MineBucket'].location + Vector((0.5, 0.3, 1.6)), 25); look(O['SM_MineBucket'].location + Vector((-0.7, -0.6, 3.1)), O['SM_MineBucket'].location + Vector((0, 0, 0.5)), 18)
elif VIEW == 'bottom':
    show('SM_MineShaft_Bottom', 'SM_MineShaft_Cribbing_Bottom', 'SM_MineBucket')
    O['SM_MineShaft_Cribbing_Bottom'].location = (3.25, 0, 14.5); O['SM_MineBucket'].location = (3.25, 0, 0.0)
    sun.hide_render = True; w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    lamp((1.0, 0.8, 2.2), 60); lamp((3.2, -1.2, 2.5), 50); look((-0.8, -0.5, 1.6), (3.25, 0, 0.9), 20)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'; pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = True
sc.cycles.samples = 48; sc.cycles.use_denoising = True
if VIEW != 'sword': sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.render.filepath = os.path.join(D, 'out', 'clay_%s.png' % VIEW); bpy.ops.render.render(write_still=True); print('CLAY OK', sc.render.filepath)

