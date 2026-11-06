# Blender: find the jaw angle that closes the maw (rest pose = showcase gape). Renders head profile stills.
import bpy, sys, os, math
from mathutils import Vector, Quaternion, Matrix
a = sys.argv[sys.argv.index('--')+1:]; FBX, OUT = a[0], a[1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.data.objects if o.type == 'MESH']
sc = bpy.context.scene
pb = arm.pose.bones['jaw']; tip = arm.pose.bones['tongue_01']
L = arm.data.bones['upper_arm_01_L'].head_local; R = arm.data.bones['upper_arm_01_R'].head_local
lat_arm = (L-R).normalized()                       # armature-space left axis
def set_angle(deg):
    # rotate the jaw about the armature-space lateral axis, expressed in the bone's local frame
    bm = arm.data.bones['jaw'].matrix_local.to_3x3()
    ax = (bm.inverted() @ lat_arm).normalized()
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(ax, math.radians(deg))
    bpy.context.view_layer.update()
set_angle(0); z0 = (arm.matrix_world @ tip.head).z
set_angle(10); z1 = (arm.matrix_world @ tip.head).z
CLOSE = +1 if z1 > z0 else -1                     # closing raises the lower jaw / tongue tip
print('CALIB close sign (blender lateral axis)', CLOSE, 'tip z', z0, z1)
for m in mesh:
    for s in m.material_slots:
        if s.material: s.material.diffuse_color = (0.55, 0.42, 0.38, 1)
head = arm.matrix_world @ arm.pose.bones['head'].head
latw = (arm.matrix_world.to_3x3() @ lat_arm).normalized()
up = Vector((0, 0, 1)); fwd = up.cross(latw).normalized()
H = (arm.matrix_world @ arm.data.bones['head'].head_local).z
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
for view, d in (('side', latw),):
    cam.location = head + d*1.6*H/1.7 + Vector((0, 0, 0.05))
    cam.rotation_euler = (head + Vector((0, 0, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 640, 640
    for deg in (30, 40, 50, 60):
        set_angle(-CLOSE*deg); sc.render.filepath = os.path.join(OUT, 'jaw_%s_shut%02d.png' % (view, deg))
        bpy.ops.render.render(write_still=True)
print('CALIB OK')
