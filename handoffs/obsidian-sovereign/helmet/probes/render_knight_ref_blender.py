# Internal reference render of the knight (NOT for hand-off; licensed mesh). blender -b -P this -- fbx outprefix
import bpy, sys, math, mathutils
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.import_scene.fbx(filepath=a[0])
for n in ('Cube','Camera','Light'):
    o=bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_cavity=True
sc.render.resolution_x=sc.render.resolution_y=900
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
for nm,(tz,ortho) in {'full':(1.0,2.3),'head':(1.6,0.8)}.items():
  cam.data.ortho_scale=ortho
  for v,d in {'minusY':(0,-3,0),'plusX':(3,0,0)}.items():
    cam.location=mathutils.Vector((0,0.04,tz))+mathutils.Vector(d)
    cam.rotation_euler=(mathutils.Vector((0,0.04,tz))-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{a[1]}_{nm}_{v}.png'; bpy.ops.render.render(write_still=True)
